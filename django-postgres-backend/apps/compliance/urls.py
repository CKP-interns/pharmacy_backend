from django.urls import path
from .views import CompliancePrescriptionsSmokeView

urlpatterns = [
    path("prescriptions/", CompliancePrescriptionsSmokeView.as_view(), name="compliance-prescriptions-smoke"),
]
