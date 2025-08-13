from rest_framework import generics
from rest_framework.views import APIView
from .models import Author, Category, Publisher, Tag, Product, ProductImage
from .serializers import AuthorSerializer, CategorySerializer, PublisherSerializer, TagSerializer, BookListSerializer, BookDetailSerializer, BookImageSerializer
from auth_core.views import PublicViewMixin, PrivateUserViewMixin
from django.db.models import Q, Count, Avg, IntegerField
from .pagination import BookPagination
from django.db.models.functions import Round, Coalesce
from django.http import JsonResponse

class AuthorListView(PublicViewMixin, generics.ListAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer

class CategoryListView(PublicViewMixin, generics.ListAPIView):
    serializer_class = CategorySerializer

    def get_queryset(self):
        return (
            Category.objects
            .annotate(product_count=Count("books"))
            .filter(product_count__gt=0)
            .order_by("-product_count", "name")
        )

class PublisherListView(PublicViewMixin, generics.ListAPIView):
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer

class TagListView(PublicViewMixin, generics.ListAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

class BookListView(PublicViewMixin, generics.ListAPIView):
    serializer_class = BookListSerializer
    pagination_class = BookPagination

    def get_queryset(self):
        queryset = Product.objects.all()

        # Filter by category if provided
        category_slug = self.request.query_params.get("category")
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # Filter by format type
        format_type = self.request.query_params.get("format_type")
        if format_type:
            if format_type in ["ebook", "physical"]:
                queryset = queryset.filter(Q(format_type=format_type) | Q(format_type="both"))
            else:
                queryset = queryset.filter(format_type=format_type)
            
        # Filter by stock status (maps ebook + physical)
        stock_status = self.request.query_params.get("stock_status")
        if stock_status:
            status_map = {
                "in_stock": Q(physical_stock_status="in_stock") | Q(ebook_stock_status="available"),
                "out_of_stock": Q(physical_stock_status="out_of_stock") & Q(ebook_stock_status="unavailable"),
                "pre_order": Q(physical_stock_status="pre_order") | Q(ebook_stock_status="pre_order"),
                "backorder": Q(physical_stock_status="backorder"),
                "out_of_print": Q(physical_stock_status="out_of_print"),
                "print_on_demand": Q(physical_stock_status="print_on_demand"),
                "available": Q(ebook_stock_status="available"),
                "unavailable": Q(ebook_stock_status="unavailable"),
            }

            if stock_status in status_map:
                queryset = queryset.filter(status_map[stock_status])
            else:
                # Fallback: match directly in either field
                queryset = queryset.filter(
                    Q(physical_stock_status__iexact=stock_status) |
                    Q(ebook_stock_status__iexact=stock_status)
                )

        # Filter by price range
        price_min = self.request.query_params.get("price_min")
        price_max = self.request.query_params.get("price_max")
        if price_min:
            queryset = queryset.filter(price__gte=price_min)
        if price_max:
            queryset = queryset.filter(price__lte=price_max)

        # Filter by average rating (frontend sends 1–5, return < that OR no reviews)
        rating_threshold = self.request.query_params.get("rating")
        if rating_threshold:
            try:
                rating_threshold = int(rating_threshold)
                queryset = queryset.annotate(avg_rating=Avg("ratings__score"))
                queryset = queryset.filter(
                    Q(avg_rating__lt=rating_threshold) | Q(avg_rating__isnull=True)
                )
            except ValueError:
                pass

        # Handle ordering
        order_by_params = []

        repeated_params = self.request.query_params.getlist("order_by")
        order_by_params.extend(repeated_params)

        single_param = self.request.query_params.get("order_by")
        if single_param and "," in single_param:
            order_by_params.extend(single_param.split(","))

        order_by_params = [param.strip() for param in order_by_params if param.strip()]

        valid_fields = ["title", "price", "created_at"]
        cleaned_orders = []
        for field in order_by_params:
            clean_field = field.lstrip('-')
            if clean_field in valid_fields:
                cleaned_orders.append(field)

        if cleaned_orders:
            queryset = queryset.order_by(*cleaned_orders)
        else:
            queryset = queryset.order_by("-created_at")

        return queryset

class BookDetailView(PublicViewMixin, generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = BookDetailSerializer
    lookup_field = "id"

class BookImageListView(PublicViewMixin, generics.ListAPIView):
    queryset = ProductImage.objects.all()
    serializer_class = BookImageSerializer

class RatingCountsView(PublicViewMixin, APIView):
    def get(self, request, *args, **kwargs):
        # Annotate each product with its rounded average rating (force integer output)
        products_with_avg = Product.objects.annotate(
            avg_rating=Round(
                Coalesce(Avg("ratings__score"), 0.0),
                output_field=IntegerField()
            )
        )

        # Group by avg_rating and count
        counts = products_with_avg.values("avg_rating").annotate(
            product_count=Count("id")
        )

        # Ensure we always return ratings 1–5 with count 0 if missing
        results = []
        for rating in range(1, 6):
            count = next((c["product_count"] for c in counts if c["avg_rating"] == rating), 0)
            results.append({
                "rating": rating,
                "product_count": count
            })

        return JsonResponse(results, safe=False)