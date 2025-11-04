from django.urls import path
from .views import SalesSmokeView, SalesInvoiceSmokeView

urlpatterns = [
    path("", SalesSmokeView.as_view(), name="sales-smoke"),
    path("invoices/", SalesInvoiceSmokeView.as_view(), name="sales-invoices-smoke"),
]
