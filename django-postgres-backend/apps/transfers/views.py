from rest_framework.views import APIView
from rest_framework.response import Response

class TransfersVouchersSmokeView(APIView):
    """
    GET /api/v1/transfers/vouchers/ -> {"message": "Transfers Vouchers API is working"}
    """
    def get(self, request, *args, **kwargs):
        return Response({"ok": True, "message": "Transfers Vouchers API is working"})
