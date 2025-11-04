from rest_framework.views import APIView
from rest_framework.response import Response

class CustomersSmokeView(APIView):
    def get(self, request):
        return Response({"ok": True, "app": "customers"})
