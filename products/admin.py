from django.contrib import admin
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "petType", "price", "stock", "rating")
    list_filter = ("category", "petType")
    search_fields = ("name", "category", "petType")