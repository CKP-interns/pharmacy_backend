from decimal import Decimal
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.catalog.models import ProductCategory, Product, MedicineForm, Uom, BatchLot
from apps.inventory.models import InventoryMovement, RackLocation
from apps.locations.models import Location
from apps.settingsx.models import TaxBillingSettings, DocCounter


class BillingFefoTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="billuser", password="pass123", is_staff=True)
        self.client.force_authenticate(self.user)
        self.location = Location.objects.create(code="LOC1", name="Main")
        self.category = ProductCategory.objects.create(name="Analgesics")
        self.form = MedicineForm.objects.create(name="Tablet")
        self.uom = Uom.objects.create(name="TAB")
        self.rack = RackLocation.objects.create(name="Rack A")
        self.product = Product.objects.create(
            code="P001",
            name="Paracetamol",
            category=self.category,
            medicine_form=self.form,
            mrp=Decimal("100.00"),
            base_unit="TAB",
            pack_unit="TAB",
            units_per_pack=Decimal("1.000"),
            base_unit_step=Decimal("1.000"),
            gst_percent=Decimal("5.00"),
            reorder_level=Decimal("5.000"),
            base_uom=self.uom,
            selling_uom=self.uom,
            rack_location=self.rack,
        )
        self.batch_old = BatchLot.objects.create(
            product=self.product,
            batch_no="OLD",
            expiry_date=timezone.now().date() + timedelta(days=10),
            status=BatchLot.Status.ACTIVE,
        )
        self.batch_new = BatchLot.objects.create(
            product=self.product,
            batch_no="NEW",
            expiry_date=timezone.now().date() + timedelta(days=100),
            status=BatchLot.Status.ACTIVE,
        )
        InventoryMovement.objects.create(
            location=self.location,
            batch_lot=self.batch_old,
            qty_change_base=Decimal("5.000"),
            reason=InventoryMovement.Reason.PURCHASE,
            ref_doc_type="TEST",
            ref_doc_id=1,
        )
        InventoryMovement.objects.create(
            location=self.location,
            batch_lot=self.batch_new,
            qty_change_base=Decimal("10.000"),
            reason=InventoryMovement.Reason.PURCHASE,
            ref_doc_type="TEST",
            ref_doc_id=2,
        )
        TaxBillingSettings.objects.create(gst_rate=Decimal("5.00"), calc_method="INCLUSIVE", invoice_prefix="INV-", invoice_start=1)

    def test_fefo_allocation_and_invoice_number(self):
        url = "/api/v1/sales/invoices/"
        body = {
            "location": self.location.id,
            "customer_name": "Walkin",
            "customer_phone": "9999999999",
            "customer_city": "City",
            "lines": [
                {"product": self.product.id, "qty_base": "12.000", "rate_per_base": "10.00"}
            ]
        }
        resp = self.client.post(url, body, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        inv_id = resp.data["id"]
        # Invoice number should be generated with prefix
        self.assertTrue(resp.data.get("invoice_no", "").startswith("INV-"))
        # FEFO: first batch OLD 5, then NEW 7
        from apps.sales.models import SalesLine
        lines = SalesLine.objects.filter(sale_invoice_id=inv_id).order_by("batch_lot__batch_no")
        self.assertEqual(lines.count(), 2)
        qtys = {ln.batch_lot.batch_no: ln.qty_base for ln in lines}
        self.assertEqual(qtys["OLD"], Decimal("5.0000"))
        self.assertEqual(qtys["NEW"], Decimal("7.0000"))
