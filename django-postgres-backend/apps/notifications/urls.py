# apps/notifications/urls.py

from django.urls import path
from .views import NotificationsSmokeView

urlpatterns = [
    path("", NotificationsSmokeView.as_view(), name="notifications-smoke"),
]
