# apps/notifications/views.py

from rest_framework.views import APIView
from rest_framework.response import Response

class NotificationsSmokeView(APIView):
    """GET /api/v1/notifications/ -> {"ok": true}"""
    def get(self, request):
        return Response({"ok": True})
