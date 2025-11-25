from decimal import Decimal
from django.db import transaction
from django.db.models import Sum

from apps.catalog.models import BatchLot, Product
from apps.catalog.services import packs_to_base
from apps.inventory.services import write_movement
from apps.inventory.models import RackRule
from .models import (
    Purchase, PurchaseLine, VendorReturn, GoodsReceipt, GoodsReceiptLine, PurchaseOrder, PurchaseOrderLine,
)
from apps.governance.services import audit, emit_event


def assign_rack(location_id: int, manufacturer_name: str) -> str | None:
    rule = RackRule.objects.filter(location_id=location_id, manufacturer_name__iexact=manufacturer_name, is_active=True).first()
    return rule.rack_code if rule else None


@transaction.atomic
def post_purchase(purchase_id, actor=None):
    # Legacy flow: write purchase into stock
    p = Purchase.objects.select_for_update().get(id=purchase_id)
    total = Decimal("0")
    for line in p.lines.select_related("product"):
        product: Product = line.product
        received = Decimal(line.qty_packs) * (product.units_per_pack or Decimal("0"))
        line.received_base_qty = received
        line.save(update_fields=["received_base_qty"])

        batch, _ = BatchLot.objects.get_or_create(
            product=product,
            batch_no=line.batch_no,
            defaults={"expiry_date": line.expiry_date, "status": BatchLot.Status.ACTIVE},
        )
        write_movement(
            location_id=p.location_id,
            batch_lot_id=batch.id,
            qty_change_base=received,
            reason="PURCHASE",
            ref_doc=("PURCHASE", p.id),
            actor=actor,
        )
        total += (line.unit_cost * Decimal(line.qty_packs))

    p.gross_total = total
    p.net_total = total
    p.save(update_fields=["gross_total", "net_total"])

    audit(
        actor,
        table="procurement_purchase",
        row_id=p.id,
        action="POST_PURCHASE",
        before=None,
        after={"gross_total": str(p.gross_total)},
    )
    return p


@transaction.atomic
def post_goods_receipt(grn_id: int, actor) -> None:
    grn = (
        GoodsReceipt.objects.select_for_update()
        .select_related("po")
        .prefetch_related("lines__product", "po__lines")
        .get(id=grn_id)
    )
    if grn.status == GoodsReceipt.Status.POSTED:
        raise ValueError("GRN already POSTED")

    for ln in grn.lines.select_related("po_line").all():
        if not ln.expiry_date or (ln.qty_packs_received or 0) <= 0:
            raise ValueError("Each GRN line must have expiry_date and qty_packs_received > 0")

        product: Product | None = ln.product
        if not product:
            product = _create_or_update_product_from_payload(
                ln.new_product_payload or {}, default_vendor_id=grn.po.vendor_id
            )
            ln.product = product
            ln.save(update_fields=["product"])
            if ln.po_line and not ln.po_line.product_id:
                pol = ln.po_line
                pol.product = product
                updates = ["product"]
                if not pol.requested_name:
                    pol.requested_name = product.name
                    updates.append("requested_name")
                if product.medicine_form_id and not pol.medicine_form_id:
                    pol.medicine_form_id = product.medicine_form_id
                    updates.append("medicine_form")
                pol.save(update_fields=updates)

        batch, _ = BatchLot.objects.get_or_create(
            product=product,
            batch_no=ln.batch_no,
            defaults={
                "mfg_date": ln.mfg_date,
                "expiry_date": ln.expiry_date,
                "status": BatchLot.Status.ACTIVE,
            },
        )
        # Update lot info if missing
        changed = False
        if ln.mfg_date and not batch.mfg_date:
            batch.mfg_date = ln.mfg_date
            changed = True
        if ln.expiry_date and not batch.expiry_date:
            batch.expiry_date = ln.expiry_date
            changed = True
        # Suggest/assign rack
        rack = ln.rack_no or assign_rack(grn.location_id, product.manufacturer or "")
        if rack and batch.rack_no != rack:
            batch.rack_no = rack
            changed = True
        if changed:
            batch.save()

        qty_base = packs_to_base(product.id, Decimal(ln.qty_packs_received))
        ln.qty_base_received = qty_base
        ln.save(update_fields=["qty_base_received"])
        write_movement(
            location_id=grn.location_id,
            batch_lot_id=batch.id,
            qty_change_base=qty_base - (ln.qty_base_damaged or Decimal("0")),
            reason="PURCHASE",
            ref_doc=("GRN", grn.id),
            actor=actor,
        )

    # Update PO line received qty and status
    po = grn.po
    # aggregate received per po_line
    recvd = (
        GoodsReceiptLine.objects.filter(po_line__po=po)
        .values("po_line_id")
        .annotate(total=Decimal("0") + Sum("qty_packs_received"))
    )
    recvd_map = {r["po_line_id"]: r["total"] for r in recvd}
    all_received = True
    any_received = False
    for pol in po.lines.all():
        got = recvd_map.get(pol.id, 0) or 0
        any_received = any_received or (got > 0)
        if got < (pol.qty_packs_ordered or 0):
            all_received = False
    po.status = (
        PurchaseOrder.Status.COMPLETED if all_received else (
            PurchaseOrder.Status.PARTIALLY_RECEIVED if any_received else PurchaseOrder.Status.OPEN
        )
    )
    po.save(update_fields=["status"])

    grn.status = GoodsReceipt.Status.POSTED
    grn.save(update_fields=["status"])

    audit(
        actor,
        table="procurement_goodsreceipt",
        row_id=grn.id,
        action="POSTED",
        before=None,
        after={"status": grn.status, "po_id": grn.po_id},
    )
    emit_event("GRN_POSTED", {"grn_id": grn.id, "po_id": grn.po_id})


def _create_or_update_product_from_payload(payload: dict, default_vendor_id=None) -> Product:
    if not payload:
        raise ValueError("Product details are required for new medicines.")
    from decimal import Decimal as _Decimal

    name = payload.get("name")
    product = None
    product_id = payload.get("product_id") or payload.get("id")
    if product_id:
        product = Product.objects.filter(id=product_id).first()
    if not product:
        code = payload.get("code")
        if code:
            product = Product.objects.filter(code__iexact=code).first()
    if not product and name:
        product = Product.objects.filter(name__iexact=name).first()

    fields = {
        "name": name,
        "generic_name": payload.get("generic_name"),
        "dosage_strength": payload.get("dosage_strength"),
        "hsn": payload.get("hsn"),
        "schedule": payload.get("schedule") or Product.Schedule.OTC,
        "category_id": payload.get("category") or payload.get("category_id"),
        "medicine_form_id": payload.get("medicine_form"),
        "pack_size": payload.get("pack_size"),
        "manufacturer": payload.get("manufacturer"),
        "mrp": _Decimal(str(payload.get("mrp"))) if payload.get("mrp") is not None else None,
        "base_unit": payload.get("base_unit"),
        "pack_unit": payload.get("pack_unit"),
        "units_per_pack": _Decimal(str(payload.get("units_per_pack")))
        if payload.get("units_per_pack") is not None
        else None,
        "base_unit_step": _Decimal(str(payload.get("base_unit_step")))
        if payload.get("base_unit_step") is not None
        else None,
        "gst_percent": _Decimal(str(payload.get("gst_percent")))
        if payload.get("gst_percent") is not None
        else None,
        "reorder_level": _Decimal(str(payload.get("reorder_level")))
        if payload.get("reorder_level") is not None
        else None,
        "description": payload.get("description"),
        "storage_instructions": payload.get("storage_instructions"),
        "preferred_vendor_id": payload.get("preferred_vendor")
        or payload.get("preferred_vendor_id")
        or default_vendor_id,
        "is_sensitive": payload.get("is_sensitive"),
    }

    if product:
        update_fields = []
        for attr, value in fields.items():
            if value is not None and getattr(product, attr) != value:
                setattr(product, attr, value)
                update_fields.append(attr)
        if update_fields:
            product.save(update_fields=update_fields)
        return product

    if not name:
        raise ValueError("Product name is required.")
    required = ["base_unit", "pack_unit", "units_per_pack", "mrp"]
    missing = [field for field in required if not payload.get(field)]
    if missing:
        raise ValueError(f"Missing product fields: {', '.join(missing)}")
    code = payload.get("code")
    if not code:
        last = Product.objects.order_by("-id").first()
        next_id = (last.id + 1) if last else 1
        code = f"PRD-{next_id:05d}"
    product = Product.objects.create(
        code=code,
        name=name,
        generic_name=fields["generic_name"] or "",
        dosage_strength=fields["dosage_strength"] or "",
        hsn=fields["hsn"] or "",
        schedule=fields["schedule"],
        category_id=fields["category_id"],
        medicine_form_id=fields["medicine_form_id"],
        pack_size=fields["pack_size"] or "",
        manufacturer=fields["manufacturer"] or "",
        mrp=fields["mrp"],
        base_unit=fields["base_unit"],
        pack_unit=fields["pack_unit"],
        units_per_pack=fields["units_per_pack"],
        base_unit_step=fields["base_unit_step"] or _Decimal("1.000"),
        gst_percent=fields["gst_percent"] or _Decimal("0"),
        reorder_level=fields["reorder_level"] or _Decimal("0"),
        description=fields["description"] or "",
        storage_instructions=fields["storage_instructions"] or "",
        preferred_vendor_id=fields["preferred_vendor_id"],
        is_sensitive=bool(fields["is_sensitive"]),
        is_active=True,
    )
    return product


@transaction.atomic
def post_vendor_return(vendor_return_id: int, actor) -> None:
    vr = (
        VendorReturn.objects.select_for_update()
        .select_related("purchase_line", "batch_lot", "purchase_line__purchase")
        .get(id=vendor_return_id)
    )
    purchase = vr.purchase_line.purchase

    # Ensure stock availability
    from apps.inventory.services import stock_on_hand

    soh = stock_on_hand(location_id=purchase.location_id, batch_lot_id=vr.batch_lot_id)
    if soh < vr.qty_base:
        raise ValueError("Insufficient stock to return to vendor")

    write_movement(
        location_id=purchase.location_id,
        batch_lot_id=vr.batch_lot_id,
        qty_change_base=-vr.qty_base,
        reason="RETURN_VENDOR",
        ref_doc=("VENDOR_RETURN", vr.id),
        actor=actor,
    )
    vr.status = "CREDITED"
    vr.save(update_fields=["status"])

    audit(
        actor,
        table="procurement_vendorreturn",
        row_id=vr.id,
        action="POSTED",
        before=None,
        after={"status": vr.status},
    )

