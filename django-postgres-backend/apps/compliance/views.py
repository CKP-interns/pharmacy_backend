from rest_framework.response import Response
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db import transaction

from .models import Prescription, H1RegisterEntry, NDPSDailyEntry, RecallEvent
from .serializers import (
    PrescriptionSerializer,
    H1RegisterEntrySerializer,
    NDPSDailyEntrySerializer,
    RecallEventSerializer,
)

from rest_framework.views import APIView

class HealthView(APIView):
    def get(self, request):
        return Response({"ok": True})


from datetime import timedelta
from django.utils import timezone

class PrescriptionViewSet(viewsets.ModelViewSet):
    queryset = Prescription.objects.all()
    serializer_class = PrescriptionSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=True, methods=["post"], url_path="mark-valid")
    def mark_valid(self, request, pk=None):
        """Extend the prescription validity by 30 days."""
        presc = get_object_or_404(Prescription, pk=pk)
        presc.valid_till = timezone.now().date() + timedelta(days=30)
        presc.save(update_fields=["valid_till"])
        return Response({"valid_till": presc.valid_till}, status=status.HTTP_200_OK)



# 💊 H1 REGISTER ENTRIES (READ-ONLY)
class H1RegisterEntryViewSet(viewsets.ModelViewSet):
    queryset = H1RegisterEntry.objects.all()
    serializer_class = H1RegisterEntrySerializer
    permission_classes = [permissions.AllowAny]



# ⚗️ NDPS DAILY ENTRIES
class NDPSDailyEntryViewSet(viewsets.ModelViewSet):
    queryset = NDPSDailyEntry.objects.all()
    serializer_class = NDPSDailyEntrySerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=["post"], url_path="generate-report")
    @transaction.atomic
    def generate_report(self, request):
        """Generate or simulate NDPS daily report."""
        total = NDPSDailyEntry.objects.count()
        return Response({"entries_count": total}, status=status.HTTP_200_OK)


# ⚠️ RECALL EVENTS
class RecallEventViewSet(viewsets.ModelViewSet):
    queryset = RecallEvent.objects.all()
    serializer_class = RecallEventSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=True, methods=["post"], url_path="mark-complete")
    def mark_complete(self, request, pk=None):
        """Mark recall event as completed."""
        recall = get_object_or_404(RecallEvent, pk=pk)
        recall.is_completed = True
        recall.save(update_fields=["is_completed"])
        return Response({"completed": True}, status=status.HTTP_200_OK)
