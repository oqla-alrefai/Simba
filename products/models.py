from django.db import models
import uuid

class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=100)
    petType = models.CharField(max_length=50)
    image = models.ImageField(upload_to="products/")
    stock = models.IntegerField(default=0)
    rating = models.FloatField(default=0)
    discount_percent = models.FloatField(default=0)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)