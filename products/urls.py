from django.urls import path
from .views import (
    ProductListCreate,
    ProductDetail,
    ProductSearchByName,
    ProductSearchByDescription,
)

urlpatterns = [
    path("", ProductListCreate.as_view(), name="products-list-create"),
    path("<uuid:pk>/", ProductDetail.as_view(), name="product-detail"),
    path("search/name/", ProductSearchByName.as_view(), name="product-search-name"),
    path("search/description/", ProductSearchByDescription.as_view(), name="product-search-description"),
]