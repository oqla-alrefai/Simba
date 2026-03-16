from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from users.models import User
from products.models import Product
from django.db.models import Sum, Count
from datetime import timedelta
from django.utils import timezone
from django.db.models.functions import TruncMonth
from collections import defaultdict
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Order, Coupon, Notification
from .serializers import OrderSerializer, CouponSerializer, NotificationSerializer
from rest_framework.exceptions import PermissionDenied



class OrderListCreate(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == "admin":
            return Order.objects.all().order_by("-created_at")
        return Order.objects.filter(user=user).order_by("-created_at")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "message": "Invalid input data"})
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response({
            "success": True,
            "data": serializer.data
        }, headers=headers)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ValidateCouponView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        code = request.data.get("couponCode")
        if not code:
            return Response({"success": False, "message": "couponCode is required."})

        try:
            coupon = Coupon.objects.get(code__iexact=code, is_active=True)
        except Coupon.DoesNotExist:
            return Response({"success": False, "message": "Invalid coupon code."})

        if coupon.expires_at and coupon.expires_at < timezone.now():
            return Response({"success": False, "message": "Coupon has expired."})

        user = request.user
        if coupon.user and coupon.user != user:
            return Response({"success": False, "message": "Coupon is not valid for this user."})

        return Response({
            "success": True,
            "data": {
                "couponCode": coupon.code,
                "discount_percent": float(coupon.discount_percent),
            }
        })


class UpdateOrderStatus(generics.UpdateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        order = self.get_object()
        if request.user.role != "admin":
            return Response({"success": False, "message": "Admin only"})
        order.status = request.data.get("status")
        order.save()
        return Response({
            "success": True,
            "data": OrderSerializer(order).data
        })
    

class AdminAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "admin":
            return Response({"success": False, "message": "Admin only"})

        total_users = User.objects.count()
        total_products = Product.objects.count()
        total_orders = Order.objects.count()

        revenue = Order.objects.aggregate(
            total=Sum("total")
        )["total"] or 0

        pending_orders = Order.objects.filter(status="Pending").count()

        low_stock = Product.objects.filter(stock__lt=5).count()

        recent_orders = Order.objects.order_by("-created_at")[:5]

        recent_data = OrderSerializer(recent_orders, many=True).data

        return Response({
            "success": True,
            "data": {
                "totalUsers": total_users,
                "totalProducts": total_products,
                "totalOrders": total_orders,
                "totalRevenue": revenue,
                "pendingOrders": pending_orders,
                "lowStockProducts": low_stock,
                "recentOrders": recent_data,
            }
        })
    

from .models import Order

class MonthlyRevenueView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "admin":
            return Response({"success": False, "message": "Admin only"})

        # last 12 months window
        now = timezone.now()
        start = (now.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(days=365))

        qs = (
            Order.objects
            .filter(created_at__gte=start)
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(revenue=Sum("total"))
            .order_by("month")
        )

        data = [
            {
                "month": r["month"].strftime("%Y-%m"),
                "revenue": float(r["revenue"] or 0),
            }
            for r in qs
        ]

        return Response({
            "success": True,
            "data": {"series": data}
        })
    

class TopSellingProductsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "admin":
            return Response({"success": False, "message": "Admin only"})

        limit = int(request.query_params.get("limit", 10))

        qty_by_product = defaultdict(int)
        revenue_by_product = defaultdict(float)

        for order in Order.objects.all().only("items"):
            for item in (order.items or []):
                pid = item.get("productId")
                qty = int(item.get("qty") or 0)
                price = float(item.get("price") or 0)
                if pid:
                    qty_by_product[pid] += qty
                    revenue_by_product[pid] += qty * price

        top = sorted(qty_by_product.items(), key=lambda x: x[1], reverse=True)[:limit]
        product_ids = [pid for pid, _ in top]

        products = {str(p.id): p for p in Product.objects.filter(id__in=product_ids)}
        result = []
        for pid, qty in top:
            p = products.get(str(pid))
            result.append({
                "productId": pid,
                "name": p.name if p else None,
                "category": p.category if p else None,
                "petType": p.petType if p else None,
                "image": (p.image.url if (p and p.image) else None),
                "unitsSold": qty,
                "revenue": round(revenue_by_product[pid], 2),
            })

        return Response({
            "success": True,
            "data": {"items": result}
        })
    

class OrderStatusStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "admin":
            return Response({"success": False, "message": "Admin only"})

        rows = (
            Order.objects
            .values("status")
            .annotate(count=Count("id"))
            .order_by("status")
        )

        return Response({
            "success": True,
            "data": {
                "items": [{"status": r["status"], "count": r["count"]} for r in rows]
            }
        })


class CouponCreateView(generics.CreateAPIView):
    serializer_class = CouponSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        if self.request.user.role != "admin":
            return Response({"success": False, "message": "Admin only"})
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "message": "Invalid input data"})
        coupon = serializer.save()
        if coupon.user:
            Notification.objects.create(
                user=coupon.user,
                message=f"You have received a coupon: {coupon.code} for {coupon.discount_percent}% off!"
            )
        return Response({
            "success": True,
            "data": CouponSerializer(coupon).data
        })


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by("-created_at")