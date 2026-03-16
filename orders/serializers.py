from rest_framework import serializers
from django.utils import timezone
from products.models import Product
from .models import Order, Coupon, Notification


class OrderSerializer(serializers.ModelSerializer):
    couponCode = serializers.CharField(write_only=True, required=False, allow_blank=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    class Meta:
        model = Order
        fields = ["id", "user", "items", "address", "delivery", "paymentMethod", "total", "coupon_code", "discount_percent", "status", "createdAt"]
        read_only_fields = ("status", "user", "discount_percent")

    def validate(self, data):
        code = data.pop("couponCode", None)
        if code:
            try:
                coupon = Coupon.objects.get(code__iexact=code, is_active=True)
            except Coupon.DoesNotExist:
                raise serializers.ValidationError({"couponCode": "Invalid coupon code."})

            if coupon.expires_at and coupon.expires_at < timezone.now():
                raise serializers.ValidationError({"couponCode": "Coupon has expired."})

            user = self.context["request"].user
            if coupon.user and coupon.user != user:
                raise serializers.ValidationError({"couponCode": "Coupon is not valid for this user."})

            data["coupon_code"] = coupon.code
            data["discount_percent"] = float(coupon.discount_percent)

        return data

    def create(self, validated_data):
        items = validated_data["items"]

        subtotal = 0
        for item in items:
            product = Product.objects.get(id=item["productId"])
            if product.stock < item["qty"]:
                raise serializers.ValidationError("Insufficient stock")

            product.stock -= item["qty"]
            product.save()

            price = float(product.price)
            discount_pct = float(getattr(product, "discount_percent", 0) or 0)
            if discount_pct:
                price = price * (1 - discount_pct / 100)

            subtotal += item["qty"] * price

        discount_percent = float(validated_data.get("discount_percent", 0) or 0)
        total = subtotal * (1 - discount_percent / 100)

        validated_data["total"] = total
        validated_data["user"] = self.context["request"].user

        return super().create(validated_data)


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = "__all__"


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"