from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = "__all__"

    def get_images(self, obj):
        return [obj.image.url] if obj.image else []