from django.test import TestCase
from rest_framework import serializers

from apps.inventory.serializers import RackLocationSerializer


class RackLocationSerializerTests(TestCase):
    def test_capacity_validation(self):
        data = {"name": "Rack X", "max_capacity": 10, "current_capacity": 5}
        ser = RackLocationSerializer(data=data)
        self.assertTrue(ser.is_valid(), ser.errors)

        data_bad = {"name": "Rack Y", "max_capacity": 5, "current_capacity": 6}
        ser = RackLocationSerializer(data=data_bad)
        self.assertFalse(ser.is_valid())
        self.assertIn("current_capacity", ser.errors)
