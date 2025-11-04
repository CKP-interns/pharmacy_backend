from rest_framework.views import APIView
from rest_framework.response import Response

class SalesSmokeView(APIView):
    """GET /api/v1/sales/ -> {"ok": true, "app": "sales"}"""
    def get(self, request):
        return Response({"ok": True, "app": "sales"})

class SalesInvoiceSmokeView(APIView):
    """GET /api/v1/sales/invoices/ -> {"ok": true, "app": "sales-invoices"}"""
    def get(self, request):
        return Response({"ok": True, "app": "sales-invoices"})
