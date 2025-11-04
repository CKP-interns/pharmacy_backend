from django.urls import path
from .views import TransfersVouchersSmokeView

urlpatterns = [
    path("vouchers/", TransfersVouchersSmokeView.as_view(), name="transfers-vouchers-smoke"),
]
