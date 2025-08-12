from rest_framework import generics
from .models import Author, Category, Publisher, Tag, Product, ProductImage
from .serializers import AuthorSerializer, CategorySerializer, PublisherSerializer, TagSerializer, BookListSerializer, BookDetailSerializer, BookImageSerializer
from auth_core.views import PublicViewMixin, PrivateUserViewMixin
from django.db.models import Q
from .pagination import BookPagination

class AuthorListView(PublicViewMixin, generics.ListAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer


class CategoryListView(PublicViewMixin, generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


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

        # Get query parameters
        category = self.request.query_params.get("category")
        tag = self.request.query_params.get("tag")
        search = self.request.query_params.get("search")

        # Filter by category name (case-insensitive)
        if category:
            queryset = queryset.filter(category__name__iexact=category)

        # Filter by tag name (case-insensitive)
        if tag:
            queryset = queryset.filter(tags__name__iexact=tag)

        # Optional text search on title, ISBN, or author name
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(isbn__icontains=search) |
                Q(authors__name__icontains=search)
            )

        return queryset.distinct()


class BookDetailView(PublicViewMixin, generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = BookDetailSerializer
    lookup_field = "id"


class BookImageListView(PublicViewMixin, generics.ListAPIView):
    queryset = ProductImage.objects.all()
    serializer_class = BookImageSerializer
