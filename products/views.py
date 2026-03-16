from rest_framework import generics
from .models import Product
from .serializers import ProductSerializer
from .permissions import IsAdmin
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from django.db.models import Q



class ProductListCreate(generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    queryset = Product.objects.all().order_by("-created_at")

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdmin()]
        return []

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

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()

        search = request.query_params.get("search")
        category = request.query_params.get("category")
        pet_type = request.query_params.get("petType")
        in_stock = request.query_params.get("inStock")
        min_price = request.query_params.get("minPrice")
        max_price = request.query_params.get("maxPrice")
        ordering = request.query_params.get("ordering")

        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(category__icontains=search) |
                Q(petType__icontains=search)
            )

        if category:
            qs = qs.filter(category__iexact=category)

        if pet_type:
            qs = qs.filter(petType__iexact=pet_type)

        if in_stock is not None:
            val = in_stock.lower() in ("1", "true", "yes", "y")
            if val:
                qs = qs.filter(stock__gt=0)

        if min_price:
            try:
                qs = qs.filter(price__gte=float(min_price))
            except ValueError:
                pass

        if max_price:
            try:
                qs = qs.filter(price__lte=float(max_price))
            except ValueError:
                pass

        allowed_ordering = {
            "price": "price",
            "-price": "-price",
            "created_at": "created_at",
            "-created_at": "-created_at",
            "rating": "rating",
            "-rating": "-rating",
            "stock": "stock",
            "-stock": "-stock",
        }
        if ordering in allowed_ordering:
            qs = qs.order_by(allowed_ordering[ordering])

        # Simple pagination (keeps frontend flexible)
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("pageSize", 24))
        page = max(page, 1)
        page_size = max(1, min(page_size, 100))

        total = qs.count()
        start = (page - 1) * page_size
        end = start + page_size
        items = qs[start:end]

        data = ProductSerializer(items, many=True).data
        return Response({
            "items": data,
            "page": page,
            "pageSize": page_size,
            "total": total,
        })

class ProductDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_permissions(self):
        if self.request.method in ["PUT", "DELETE"]:
            return [IsAdmin()]
        return []

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return Response({"success": False, "message": "Invalid input data"})
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response({
            "success": True,
            "data": serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            "success": True,
            "message": "Product deleted successfully"
        })
    

# ------------------------------
class ProductSearchByName(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = []  # public endpoint
    queryset = Product.objects.all().order_by("-created_at")

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.query_params.get("search", "")
        if search:
            qs = qs.filter(name__icontains=search)
        return qs


# ------------------------------
# Search products by DESCRIPTION only
# ------------------------------
class ProductSearchByDescription(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = []  # public endpoint
    queryset = Product.objects.all().order_by("-created_at")

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.query_params.get("search", "")
        if search:
            qs = qs.filter(description__icontains=search)
        return qs