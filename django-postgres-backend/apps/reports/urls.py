from django.urls import path
from .views import ReportsExportsSmokeView

urlpatterns = [
    path("exports/", ReportsExportsSmokeView.as_view(), name="reports-exports-smoke"),
]
