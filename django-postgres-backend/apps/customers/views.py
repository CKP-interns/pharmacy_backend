from rest_framework import viewsets, filters, permissions, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from django.db.models import Sum, Count
from datetime import date, timedelta
from .models import Customer
from .serializers import CustomerSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by("name")
    serializer_class = CustomerSerializer
    permission_classes = [permissions.AllowAny] #allowany only for the testing purpose,change it later
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "phone", "email", "gstin", "code"]
    ordering_fields = ["name", "type", "credit_limit", "outstanding_balance"]
    
    @extend_schema(
        tags=["Customers"],
        summary="Customers dashboard stats",
        parameters=[
            OpenApiParameter("from", OpenApiTypes.DATE, OpenApiParameter.QUERY),
            OpenApiParameter("to", OpenApiTypes.DATE, OpenApiParameter.QUERY),
        ],
        responses={200: OpenApiTypes.OBJECT},
    )
    def list(self, request, *args, **kwargs):
        # Allow normal listing with stats via query flag to keep compatibility
        if request.query_params.get("stats") == "true":
            from apps.sales.models import SalesInvoice
            from_str = request.query_params.get("from")
            to_str = request.query_params.get("to")
            inv = SalesInvoice.objects.filter(status=SalesInvoice.Status.POSTED)
            if from_str:
                inv = inv.filter(invoice_date__date__gte=from_str)
            if to_str:
                inv = inv.filter(invoice_date__date__lte=to_str)
            total_customers = Customer.objects.count()
            revenue = inv.aggregate(s=Sum("net_total")).get("s") or 0
            txn = inv.count()
            avg_purchase_value = float(revenue) / txn if txn else 0
            # active this month
            today = date.today()
            month_start = today.replace(day=1)
            active = inv.filter(invoice_date__date__gte=month_start).values("customer_id").distinct().count()
            return Response({
                "total_customers": total_customers,
                "avg_purchase_value": round(avg_purchase_value, 2),
                "active_this_month": active,
            })
        return super().list(request, *args, **kwargs)

    @extend_schema(tags=["Customers"], summary="Customer summary (totals and this month)", responses={200: OpenApiTypes.OBJECT})
    def retrieve(self, request, *args, **kwargs):
        # normal retrieve returns basic info; add ?summary=true to include aggregates
        instance = self.get_object()
        if request.query_params.get("summary") == "true":
            from apps.sales.models import SalesInvoice
            inv = SalesInvoice.objects.filter(customer_id=instance.id, status=SalesInvoice.Status.POSTED)
            total_bills = inv.count()
            revenue = inv.aggregate(s=Sum("net_total")).get("s") or 0
            avg_bill = float(revenue) / total_bills if total_bills else 0
            today = date.today(); month_start = today.replace(day=1)
            month_inv = inv.filter(invoice_date__date__gte=month_start)
            visits = month_inv.count()
            amount_spent = month_inv.aggregate(s=Sum("net_total")).get("s") or 0
            data = CustomerSerializer(instance).data
            data.update({
                "stats": {
                    "total_bills": total_bills,
                    "total_purchases": float(revenue),
                    "average_bill_value": round(avg_bill, 2),
                    "this_month": {"visits": visits, "amount_spent": float(amount_spent)},
                }
            })
            return Response(data)
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        tags=["Customers"],
        summary="Customer invoices list (compact)",
        responses={200: OpenApiTypes.OBJECT},
    )
    @filters.action(detail=True, methods=["get"], url_path="invoices")
    def customer_invoices(self, request, pk=None):
        from apps.sales.models import SalesInvoice
        inv = SalesInvoice.objects.filter(customer_id=pk).order_by("-invoice_date")[:100]
        rows = [{
            "invoice_no": i.invoice_no or i.id,
            "date": i.invoice_date,
            "items": i.lines.count(),
            "amount": i.net_total,
            "payment_status": i.payment_status,
            "id": i.id,
        } for i in inv]
        return Response(rows)
