from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.catalog.models import ProductCategory, Product, MedicineForm, Uom, BatchLot
from apps.inventory.models import InventoryMovement, RackLocation
from apps.locations.models import Location
from apps.settingsx.models import SettingKV


class ExpiryAlertsTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="expuser", password="pass123", is_staff=True)
        self.client.force_authenticate(self.user)
        self.location = Location.objects.create(code="LOC1", name="Main")
        self.category = ProductCategory.objects.create(name="Antibiotics")
        self.form = MedicineForm.objects.create(name="Tablet")
        self.uom = Uom.objects.create(name="TAB")
        self.rack = RackLocation.objects.create(name="Rack A")

        self.product = Product.objects.create(
            code="AB001",
            name="Amoxicillin",
            category=self.category,
            medicine_form=self.form,
            mrp=Decimal("100.00"),
            base_unit="TAB",
            pack_unit="TAB",
            units_per_pack=Decimal("1.000"),
            base_unit_step=Decimal("1.000"),
            gst_percent=Decimal("5.00"),
            reorder_level=Decimal("10.000"),
            base_uom=self.uom,
            selling_uom=self.uom,
            rack_location=self.rack,
        )

        self.batch_crit = BatchLot.objects.create(
            product=self.product,
            batch_no="B-CRIT",
            expiry_date=date.today() + timedelta(days=5),
            status=BatchLot.Status.ACTIVE,
        )
        self.batch_warn = BatchLot.objects.create(
            product=self.product,
            batch_no="B-WARN",
            expiry_date=date.today() + timedelta(days=40),
            status=BatchLot.Status.ACTIVE,
        )
        for batch in (self.batch_crit, self.batch_warn):
            InventoryMovement.objects.create(
                location=self.location,
                batch_lot=batch,
                qty_change_base=Decimal("5.000"),
                reason=InventoryMovement.Reason.PURCHASE,
                ref_doc_type="TEST",
                ref_doc_id=1,
            )

        SettingKV.objects.update_or_create(key="ALERT_EXPIRY_CRITICAL_DAYS", defaults={"value": "7"})
        SettingKV.objects.update_or_create(key="ALERT_EXPIRY_WARNING_DAYS", defaults={"value": "45"})

    def test_expiry_alerts_summary_and_filter(self):
        url = "/api/v1/inventory/expiry-alerts/"
        resp = self.client.get(url, {"location_id": self.location.id})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["summary"]["critical"], 1)
        self.assertEqual(resp.data["summary"]["warning"], 1)

        resp_crit = self.client.get(url, {"location_id": self.location.id, "bucket": "critical"})
        self.assertEqual(len(resp_crit.data["items"]), 1)
        self.assertEqual(resp_crit.data["items"][0]["batch_no"], "B-CRIT")
