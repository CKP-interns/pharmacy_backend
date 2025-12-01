from decimal import Decimal
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.catalog.models import ProductCategory, Product, MedicineForm, Uom, BatchLot
from apps.inventory.models import InventoryMovement, RackLocation
from apps.locations.models import Location
from apps.customers.models import Customer
from apps.sales.models import SalesInvoice, SalesLine


class CustomerAnalyticsTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="custuser", password="pass123", is_staff=True)
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
        batch = BatchLot.objects.create(
            product=self.product,
            batch_no="B1",
            expiry_date=timezone.now().date() + timedelta(days=100),
            status=BatchLot.Status.ACTIVE,
        )
        InventoryMovement.objects.create(
            location=self.location,
            batch_lot=batch,
            qty_change_base=Decimal("50.000"),
            reason=InventoryMovement.Reason.PURCHASE,
            ref_doc_type="TEST",
            ref_doc_id=1,
        )
        self.customer = Customer.objects.create(name="Rajesh Kumar", code="C-0001", phone="9999999999")
        inv = SalesInvoice.objects.create(
            invoice_no="INV-1",
            location=self.location,
            customer=self.customer,
            created_by=self.user,
            invoice_date=timezone.now(),
            gross_total=Decimal("50.00"),
            net_total=Decimal("50.00"),
            tax_total=Decimal("5.00"),
            total_paid=Decimal("50.00"),
            outstanding=Decimal("0.00"),
            status=SalesInvoice.Status.POSTED,
            payment_status=SalesInvoice.PaymentStatus.PAID,
        )
        SalesLine.objects.create(
            sale_invoice=inv,
            product=self.product,
            batch_lot=batch,
            qty_base=Decimal("5.0000"),
            sold_uom="BASE",
            rate_per_base=Decimal("10.00"),
            tax_percent=Decimal("5.00"),
            line_total=Decimal("52.50"),
        )

    def test_customer_list_stats(self):
        resp = self.client.get("/api/v1/customers/?stats=true")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("total_customers", resp.data)
        self.assertGreaterEqual(resp.data["avg_purchase_value"], 0)

    def test_customer_detail_summary(self):
        resp = self.client.get(f"/api/v1/customers/{self.customer.id}/?summary=true")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["customer"]["id"], self.customer.id)
        self.assertIn("total_purchases", resp.data["purchase_status"])
