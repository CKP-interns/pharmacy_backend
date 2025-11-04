# apps/reports/views.py

from rest_framework.views import APIView
from rest_framework.response import Response

class ReportsExportsSmokeView(APIView):
    """GET /api/v1/reports/exports/ -> {"ok": true}"""
    def get(self, request):
        return Response({"ok": True})
