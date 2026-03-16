from django.contrib import admin
from .models import Order, Coupon

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "total", "coupon_code", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("id", "user__email")


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_percent", "user", "is_active", "expires_at", "created_at")
    list_filter = ("is_active",)
    search_fields = ("code", "user__email")