from django.urls import path
from .views import CustomersSmokeView

urlpatterns = [
    path("", CustomersSmokeView.as_view(), name="customers-smoke"),
]
