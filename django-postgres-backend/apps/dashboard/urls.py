from django.urls import path

from .views import (
    DashboardSummaryView,
    MonthlyChartView,
    InventoryStatusView,
    RecentSalesView,
    LowStockListView,
)

urlpatterns = [
    path("summary/", DashboardSummaryView.as_view(), name="dashboard-summary"),
    path("monthly/", MonthlyChartView.as_view(), name="dashboard-monthly"),
    path("inventory-status/", InventoryStatusView.as_view(), name="dashboard-inventory-status"),
    path("recent-sales/", RecentSalesView.as_view(), name="dashboard-recent-sales"),
    path("low-stock/", LowStockListView.as_view(), name="dashboard-low-stock"),
]
