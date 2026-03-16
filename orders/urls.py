from django.urls import path
from .views import (
    OrderListCreate,
    ValidateCouponView,
    UpdateOrderStatus,
    AdminAnalyticsView,
    MonthlyRevenueView,
    TopSellingProductsView,
    OrderStatusStatsView,
    CouponCreateView,
    NotificationListView,
)

urlpatterns = [
    path("", OrderListCreate.as_view(), name="orders"),
    path("validate-coupon/", ValidateCouponView.as_view(), name="validate-coupon"),
    path("<uuid:pk>/status/", UpdateOrderStatus.as_view(), name="order-status"),

    # Admin analytics
    path("analytics/", AdminAnalyticsView.as_view(), name="admin-analytics"),
    path("analytics/monthly-revenue/", MonthlyRevenueView.as_view(), name="monthly-revenue"),
    path("analytics/top-products/", TopSellingProductsView.as_view(), name="top-products"),
    path("analytics/status-stats/", OrderStatusStatsView.as_view(), name="status-stats"),

    # Coupons
    path("coupons/", CouponCreateView.as_view(), name="create-coupon"),

    # Notifications
    path("notifications/", NotificationListView.as_view(), name="notifications"),
]