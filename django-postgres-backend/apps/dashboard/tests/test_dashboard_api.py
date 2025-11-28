from decimal import Decimal
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.catalog.models import ProductCategory, Product, MedicineForm, Uom, BatchLot
from apps.customers.models import Customer
from apps.inventory.models import InventoryMovement, RackLocation
from apps.locations.models import Location
from apps.procurement.models import Purchase
from apps.sales.models import SalesInvoice


class DashboardAPITests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="tester", email="tester@example.com", password="pass123", is_staff=True
        )
        self.client.force_authenticate(self.user)
        self.location = Location.objects.create(code="LOC1", name="Main Store")
        self.category = ProductCategory.objects.create(name="Analgesics")
        self.form = MedicineForm.objects.create(name="Tablet")
        self.uom_tab = Uom.objects.create(name="TAB")
        self.uom_strip = Uom.objects.create(name="STRIP")
        self.rack = RackLocation.objects.create(name="Rack A")

        self.product = Product.objects.create(
            code="P001",
            name="Paracetamol 500mg",
            category=self.category,
            medicine_form=self.form,
            mrp=Decimal("100.00"),
            base_unit="TAB",
            pack_unit="STRIP",
            units_per_pack=Decimal("10.000"),
            base_unit_step=Decimal("1.000"),
            gst_percent=Decimal("5.00"),
            reorder_level=Decimal("50.000"),
            description="",
            storage_instructions="",
            base_uom=self.uom_tab,
            selling_uom=self.uom_strip,
            rack_location=self.rack,
        )

        self.batch = BatchLot.objects.create(
            product=self.product,
            batch_no="B1",
            expiry_date=timezone.now().date() + timedelta(days=365),
            status=BatchLot.Status.ACTIVE,
        )

        InventoryMovement.objects.create(
            location=self.location,
            batch_lot=self.batch,
            qty_change_base=Decimal("10.000"),
            reason=InventoryMovement.Reason.PURCHASE,
            ref_doc_type="TEST",
            ref_doc_id=1,
        )

        self.customer = Customer.objects.create(name="John Doe", code="CUST-1")
        self.invoice = SalesInvoice.objects.create(
            invoice_no="INV-1",
            location=self.location,
            customer=self.customer,
            created_by=self.user,
            invoice_date=timezone.now(),
            gross_total=Decimal("120.00"),
            net_total=Decimal("120.00"),
            tax_total=Decimal("10.00"),
            total_paid=Decimal("100.00"),
            outstanding=Decimal("20.00"),
            status=SalesInvoice.Status.POSTED,
            posted_by=self.user,
            posted_at=timezone.now(),
            payment_status=SalesInvoice.PaymentStatus.PARTIAL,
        )

        Purchase.objects.create(
            vendor=self._create_vendor(),
            location=self.location,
            invoice_date=timezone.now().date(),
            gross_total=Decimal("200.00"),
            tax_total=Decimal("20.00"),
            net_total=Decimal("220.00"),
        )

    def _create_vendor(self):
        from apps.procurement.models import Vendor

        return Vendor.objects.create(name="Acme Pharma")

    def test_dashboard_summary_returns_metrics(self):
        resp = self.client.get("/api/v1/dashboard/summary/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["totals"]["medicines"], 1)
        self.assertEqual(resp.data["sales"]["today_bills"], 1)
        self.assertEqual(resp.data["sales"]["pending_bills"], 1)
        self.assertEqual(len(resp.data["recent_sales"]), 1)
        self.assertEqual(resp.data["recent_sales"][0]["invoice_no"], "INV-1")
        self.assertGreaterEqual(resp.data["totals"]["low_stock"], 1)

    def test_monthly_chart_endpoint(self):
        resp = self.client.get("/api/v1/dashboard/monthly/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 6)
        self.assertIn("sales_total", resp.data[0])
        self.assertIn("purchases_total", resp.data[0])

    def test_requires_authentication(self):
        self.client.force_authenticate(user=None)
        resp = self.client.get("/api/v1/dashboard/summary/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
