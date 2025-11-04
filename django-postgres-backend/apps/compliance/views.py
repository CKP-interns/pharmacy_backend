from rest_framework.views import APIView
from rest_framework.response import Response

class CompliancePrescriptionsSmokeView(APIView):
    """GET /api/v1/compliance/prescriptions/ -> {"ok": true}"""
    def get(self, request):
        return Response({"ok": True})
