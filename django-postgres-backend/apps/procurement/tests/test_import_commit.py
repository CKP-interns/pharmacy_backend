from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient

from apps.procurement.models import Vendor, PurchaseOrder, GoodsReceipt, PurchaseOrderLine, GoodsReceiptLine
from apps.catalog.models import ProductCategory, Product, VendorProductCode, MedicineForm
from apps.locations.models import Location
from apps.procurement.services import post_goods_receipt
from datetime import date


class ImportCommitTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.vendor = Vendor.objects.create(name="Cipla")
        self.loc = Location.objects.create(code="LOC", name="Loc")
        cat = ProductCategory.objects.create(name="Cat")
        self.form = MedicineForm.objects.create(name="Tablet")
        self.p1 = Product.objects.create(
            code="TAB1", name="Tablet 1", category=cat, hsn="", schedule="OTC",
            pack_size="1x10", manufacturer="M1", mrp=Decimal("100.00"), base_unit="TAB", pack_unit="STRIP", units_per_pack=Decimal("10.000"), base_unit_step=Decimal("1.000"), gst_percent=Decimal("12.00"), reorder_level=Decimal("0.000"),
        )
        VendorProductCode.objects.create(vendor=self.vendor, product=self.p1, vendor_code="V-TAB1")

    def test_po_import_commit(self):
        body = {
            "vendor_id": self.vendor.id,
            "location_id": self.loc.id,
            "lines": [
                {"vendor_code": "V-TAB1", "qty": 2, "unit_cost": "45.00", "gst_percent": "12"}
            ]
        }
        r = self.client.post("/api/v1/procurement/purchase-orders/import-commit", body, format="json")
        assert r.status_code == 201, r.data
        po = PurchaseOrder.objects.get(id=r.data["id"]) if isinstance(r.data, dict) and "id" in r.data else PurchaseOrder.objects.first()
        assert po.gross_total == Decimal("90.00") and po.tax_total > 0

    def test_grn_import_commit(self):
        # Create a matching PO first
        po_r = self.client.post("/api/v1/procurement/purchase-orders/import-commit", {
            "vendor_id": self.vendor.id, "location_id": self.loc.id,
            "lines": [{"product_id": self.p1.id, "qty": 1, "unit_cost": "10.00"}],
        }, format="json")
        po_id = po_r.data.get("id") if isinstance(po_r.data, dict) else PurchaseOrder.objects.first().id
        r = self.client.post("/api/v1/procurement/grns/import-commit", {
            "vendor_id": self.vendor.id, "location_id": self.loc.id, "po_id": po_id,
            "lines": [{"product_id": self.p1.id, "qty": 1, "unit_cost": "10.00", "batch_no": "B1"}],
        }, format="json")
        assert r.status_code == 201, r.data
        assert GoodsReceipt.objects.filter(id=r.data.get("id")).exists()

    def test_po_import_commit_with_requested_name(self):
        body = {
            "vendor_id": self.vendor.id,
            "location_id": self.loc.id,
            "lines": [
                {
                    "product_name": "Custom Tablet",
                    "medicine_form": self.form.id,
                    "qty": 4,
                }
            ],
        }
        r = self.client.post("/api/v1/procurement/purchase-orders/import-commit", body, format="json")
        assert r.status_code == 201, r.data
        po = PurchaseOrder.objects.get(id=r.data["id"])
        pol = po.lines.first()
        assert pol.product_id is None
        assert pol.requested_name == "Custom Tablet"
        assert pol.medicine_form_id == self.form.id

    def test_grn_post_creates_product_from_payload(self):
        po = PurchaseOrder.objects.create(
            vendor=self.vendor,
            location=self.loc,
            po_number="PO-NEW",
            status=PurchaseOrder.Status.OPEN,
        )
        pol = PurchaseOrderLine.objects.create(
            po=po,
            product=None,
            requested_name="Brand New",
            medicine_form=self.form,
            qty_packs_ordered=5,
            expected_unit_cost=Decimal("0"),
        )
        grn = GoodsReceipt.objects.create(po=po, location=self.loc, status=GoodsReceipt.Status.DRAFT)
        GoodsReceiptLine.objects.create(
            grn=grn,
            po_line=pol,
            product=None,
            batch_no="BNEW-1",
            mfg_date=date.today(),
            expiry_date=date.today().replace(year=date.today().year + 1),
            qty_packs_received=5,
            qty_base_received=Decimal("0"),
            unit_cost=Decimal("0"),
            mrp=Decimal("0"),
            new_product_payload={
                "name": "Brand New",
                "base_unit": "TAB",
                "pack_unit": "STRIP",
                "units_per_pack": "10",
                "mrp": "25.00",
                "medicine_form": self.form.id,
            },
        )
        post_goods_receipt(grn.id, actor=None)
        grn.refresh_from_db()
        line = grn.lines.first()
        assert line.product_id is not None
        pol.refresh_from_db()
        assert pol.product_id == line.product_id
        assert pol.medicine_form_id == self.form.id

