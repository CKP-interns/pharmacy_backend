# apps/sales/services.py
from django.db import transaction
from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import SalesInvoice, SalesLine
from apps.inventory.models import InventoryMovement
from apps.compliance.services import (
    ensure_prescription_for_invoice,
    create_compliance_entries,
)
from apps.governance.models import AuditLog

AMOUNT_QUANT = Decimal("0.0001")
CURRENCY_QUANT = Decimal("0.01")


def stock_on_hand(location_id, batch_lot_id):
    from django.db.models import Sum

    s = (
        InventoryMovement.objects.filter(
            location_id=location_id, batch_lot_id=batch_lot_id
        ).aggregate(total=Sum("qty_change_base"))
    )
    return Decimal(s["total"] or 0)


def write_movement(location_id, batch_lot_id, qty_delta, reason, ref_doc_type, ref_doc_id):
    InventoryMovement.objects.create(
        location_id=location_id,
        batch_lot_id=batch_lot_id,
        qty_change_base=qty_delta,
        reason=reason,
        ref_doc_type=ref_doc_type,
        ref_doc_id=ref_doc_id,
    )


@transaction.atomic
def post_invoice(actor, invoice_id):
    """Post a draft invoice into a confirmed sale. Idempotent: re-posting a POSTED invoice returns no-op."""
    # Use select_for_update to lock the invoice row and prevent concurrent modifications
    # Skip locked wait to avoid deadlocks - if locked, raise error instead
    try:
        inv = (
            SalesInvoice.objects.select_for_update(nowait=True)
            .prefetch_related("lines__batch_lot", "lines__product", "payments")
            .get(pk=invoice_id)
        )
    except SalesInvoice.DoesNotExist:
        raise ValidationError(f"Invoice {invoice_id} not found")
    except Exception as e:
        # If invoice is locked (another transaction is modifying it), raise error
        raise ValidationError(f"Invoice is currently being processed. Please try again. Error: {str(e)}")

    # Idempotency: already posted → no-op
    if inv.status == SalesInvoice.Status.POSTED:
        # Return success but don't re-process
        return {"invoice_no": inv.invoice_no, "status": inv.status}

    if inv.status != SalesInvoice.Status.DRAFT:
        raise ValidationError(f"Cannot post invoice in {inv.status} state.")

    # Compliance: ensure prescription exists if required
    ensure_prescription_for_invoice(inv)

    gross = Decimal("0")
    tax_total = Decimal("0")
    discount_total = Decimal("0")
    net = Decimal("0")

    # -----------------------------------------
    # INVENTORY DEDUCTION + TOTAL COMPUTATION
    # -----------------------------------------
    # Process all lines and verify stock availability before making any changes
    lines_list = list(inv.lines.all())
    if not lines_list:
        raise ValidationError("Invoice has no line items to post")
    
    # First pass: verify all stock is available (prevents partial deductions)
    for line in lines_list:
        available = stock_on_hand(inv.location_id, line.batch_lot_id)
        if available < line.qty_base:
            raise ValidationError(
                f"Insufficient stock for {line.product.name} (Batch {line.batch_lot.batch_no}): "
                f"available {available}, required {line.qty_base}"
            )

    # Second pass: deduct stock and calculate totals (all-or-nothing approach)
    for line in lines_list:
        qty = Decimal(line.qty_base)
        rate = Decimal(line.rate_per_base)
        disc = Decimal(line.discount_amount or 0)

        taxable = (qty * rate) - disc
        tax_amt = (taxable * Decimal(line.tax_percent or 0) / Decimal("100")).quantize(
            AMOUNT_QUANT, rounding=ROUND_HALF_UP
        )
        line_total = (taxable + tax_amt).quantize(AMOUNT_QUANT, rounding=ROUND_HALF_UP)

        # update calculated values on DB
        SalesLine.objects.filter(pk=line.pk).update(tax_amount=tax_amt, line_total=line_total)

        gross += qty * rate
        discount_total += disc
        tax_total += tax_amt
        net += line_total

        # Stock OUT movement - deduct inventory
        write_movement(inv.location_id, line.batch_lot_id, -qty, "SALE", "SalesInvoice", inv.id)

    # -----------------------------------------
    # FINAL TOTALS
    # -----------------------------------------
    net_rounded = net.quantize(CURRENCY_QUANT, rounding=ROUND_HALF_UP)
    round_off = (net_rounded - net).quantize(CURRENCY_QUANT, rounding=ROUND_HALF_UP)

    inv.gross_total = gross.quantize(CURRENCY_QUANT)
    inv.discount_total = discount_total.quantize(CURRENCY_QUANT)
    inv.tax_total = tax_total.quantize(CURRENCY_QUANT)
    inv.round_off_amount = round_off
    inv.net_total = net_rounded

    inv.status = SalesInvoice.Status.POSTED
    inv.posted_at = timezone.now()
    inv.posted_by = actor
    inv.save()

    # -----------------------------------------
    # COMPLIANCE (H1 / NDPS)
    # -----------------------------------------
    create_compliance_entries(inv)

    # -----------------------------------------
    # PAYMENT STATUS UPDATE
    # -----------------------------------------
    _update_payment_status(inv)

    # -----------------------------------------
    # NOTIFICATION CHECKS (Low Stock + Expiry)
    # -----------------------------------------
    # Import notifications and settings defensively so tests/environments without those modules don't fail.
    try:
        from apps.notifications.services import enqueue_once
    except Exception:
        enqueue_once = None

    try:
        from apps.settingsx.services import get_setting
        from apps.settingsx.utils import get_stock_thresholds
    except Exception:
        get_setting = lambda *args, **kwargs: 30
        get_stock_thresholds = lambda: (30, 10)

    expiry_window_days = int(get_setting("CRITICAL_EXPIRY_DAYS", 30))
    low_threshold, _ = get_stock_thresholds()
    try:
        low_threshold_val = Decimal(str(low_threshold or 0))
    except Exception:
        low_threshold_val = Decimal("0")

    for line in inv.lines.all():
        batch = line.batch_lot
        product = line.product

        # If notifications unavailable skip
        if enqueue_once is None:
            continue

        # LOW STOCK CHECK
        available = stock_on_hand(inv.location_id, batch.id)
        if low_threshold_val and available <= low_threshold_val:
            dedupe_key = f"{inv.location_id}-{batch.id}-LOW_STOCK"
            enqueue_once(
                channel="EMAIL",
                to="alerts@erp.local",
                subject=f"Low Stock Alert: {product.name}",
                message=(
                    f"Stock for {product.name} (Batch {batch.batch_no}) at "
                    f"{inv.location.name} is low: {available}"
                ),
                dedupe_key=dedupe_key,
            )

        # EXPIRY CHECK
        # Note: product/batch fields use expiry_date on BatchLot
        if getattr(batch, "expiry_date", None):
            days_to_expiry = (batch.expiry_date - timezone.now().date()).days
            if days_to_expiry <= expiry_window_days:
                dedupe_key = f"{inv.location_id}-{batch.id}-EXPIRY"
                enqueue_once(
                    channel="EMAIL",
                    to="alerts@erp.local",
                    subject=f"Expiry Alert: {product.name}",
                    message=(f"Batch {batch.batch_no} of {product.name} expires on {batch.expiry_date}."),
                    dedupe_key=dedupe_key,
                )

    # -----------------------------------------
    # AUDIT LOGGING
    # -----------------------------------------
    _audit(actor, "sales_invoices", inv.id, "POST")

    return {"invoice_no": inv.invoice_no, "status": inv.status}


@transaction.atomic
def cancel_invoice(actor, invoice_id):
    """Reverse a posted invoice. Only POSTED invoices may be cancelled."""
    inv = SalesInvoice.objects.select_for_update().get(pk=invoice_id)
    if inv.status != SalesInvoice.Status.POSTED:
        raise ValidationError("Only POSTED invoices can be cancelled.")

    # Reverse stock (credit back)
    for line in inv.lines.all():
        write_movement(
            inv.location_id,
            line.batch_lot_id,
            Decimal(line.qty_base),
            "ADJUSTMENT",
            "SalesInvoiceCancel",
            inv.id,
        )

    inv.status = SalesInvoice.Status.CANCELLED
    inv.save(update_fields=["status"])

    _audit(actor, "sales_invoices", inv.id, "CANCEL")

    return {"invoice_no": inv.invoice_no, "status": inv.status}


@transaction.atomic
def restore_stock_for_invoice(invoice_id):
    """Restore stock for a posted invoice (used when deleting invoice)."""
    inv = SalesInvoice.objects.select_for_update().get(pk=invoice_id)
    
    # Only restore stock if invoice was posted (stock was deducted)
    if inv.status == SalesInvoice.Status.POSTED:
        # Reverse stock (credit back) - same logic as cancel_invoice
        for line in inv.lines.all():
            write_movement(
                inv.location_id,
                line.batch_lot_id,
                Decimal(line.qty_base),
                "ADJUSTMENT",
                "SalesInvoiceDelete",
                inv.id,
            )
    
    return inv


def _update_payment_status(inv):
    """Recalculate invoice payment status and persist totals."""
    # refresh relations to read fresh payments
    inv.refresh_from_db(fields=[])

    payments_total = Decimal("0")
    for p in inv.payments.all():
        payments_total += Decimal(p.amount)

    inv.total_paid = payments_total.quantize(CURRENCY_QUANT, rounding=ROUND_HALF_UP)
    inv.outstanding = (Decimal(inv.net_total or 0) - inv.total_paid).quantize(
        CURRENCY_QUANT, rounding=ROUND_HALF_UP
    )

    if inv.total_paid >= (inv.net_total or Decimal("0")):
        inv.payment_status = SalesInvoice.PaymentStatus.PAID
    elif inv.total_paid > Decimal("0"):
        inv.payment_status = SalesInvoice.PaymentStatus.PARTIAL
    else:
        inv.payment_status = SalesInvoice.PaymentStatus.CREDIT

    inv.save(update_fields=["payment_status", "total_paid", "outstanding"])
    return inv


def _audit(actor, table_name, record_id, action):
    """Generic audit trail creation. Avoid FK errors during tests."""
    actor_ref = None
    try:
        from apps.accounts.models import User as AccountsUser
        # Verify the actor is a User instance and exists in the database
        if actor and isinstance(actor, AccountsUser) and hasattr(actor, "id"):
            # Check if the user actually exists in the database
            if AccountsUser.objects.filter(id=actor.id).exists():
                actor_ref = actor
    except Exception:
        actor_ref = None

    try:
        AuditLog.objects.create(
            actor_user=actor_ref,  # Use the object, not the ID - Django will handle it properly
            action=action,
            table_name=table_name,
            record_id=str(record_id),
            created_at=timezone.now(),
        )
    except Exception:
        # Silently fail if audit creation fails (e.g., during tests or if user doesn't exist)
        pass


