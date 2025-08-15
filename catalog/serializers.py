from rest_framework import serializers
from .models import Author, Category, Publisher, Tag, Product, ProductImage, ProductRating
from django.db.models import Avg, Count
import random

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = "__all__"

class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = "__all__"

class PublisherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publisher
        fields = "__all__"

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"


class BookImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image", "is_main", "created_at"]

class BookListSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    authors = AuthorSerializer(many=True, read_only=True)
    publisher = PublisherSerializer(read_only=True)
    main_image = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    rating_counts = serializers.SerializerMethodField()
    rating_count = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id", "title", "slug", "isbn", "price", "stock_quantity",
            "format_type", "physical_stock_status", "ebook_stock_status",
            "language", "ebook_file_size", "pages", "categories", "authors",
            "publisher", "main_image", "average_rating", "rating_counts", "rating_count"
        ]

    def get_main_image(self, obj):
        request = self.context.get('request')
        main_img = obj.images.filter(is_main=True).first()
        if main_img and main_img.image:
            return request.build_absolute_uri(main_img.image.url)
        return None

    def get_average_rating(self, obj):
        avg = obj.average_rating
        if avg is None:
            return 0
        return int(avg) if avg == int(avg) else round(avg, 1)

    def get_rating_counts(self, obj):
        return {
            "1": ProductRating.objects.filter(product=obj, score=1).count(),
            "2": ProductRating.objects.filter(product=obj, score=2).count(),
            "3": ProductRating.objects.filter(product=obj, score=3).count(),
            "4": ProductRating.objects.filter(product=obj, score=4).count(),
            "5": ProductRating.objects.filter(product=obj, score=5).count(),
        }


    def get_rating_count(self, obj):
        return ProductRating.objects.filter(product=obj).distinct().count()

class BookDetailSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    authors = AuthorSerializer(many=True, read_only=True)
    publisher = PublisherSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    images = BookImageSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    rating_counts = serializers.SerializerMethodField()
    total_rating_count = serializers.SerializerMethodField()
    related_books = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = "__all__"

    def get_average_rating(self, obj):
        return obj.average_rating
    
    def get_rating_counts(self, obj):
        counts = (
            ProductRating.objects
            .filter(product=obj)
            .values("score")
            .annotate(product_count=Count("id"))
        )
        count_map = {rating: 0 for rating in range(1, 6)}
        for c in counts:
            count_map[int(c["score"])] = c["product_count"]
        return count_map

    def get_total_rating_count(self, obj):
        total = ProductRating.objects.filter(product=obj).count()
        return total or 0
    
    def get_related_books(self, obj):
        related_books = []

        # Same categories
        category_books = Product.objects.filter(
            categories__in=obj.categories.all()
        ).exclude(id=obj.id).distinct()
        related_books.extend(list(category_books))

        # Same tags
        if len(related_books) < 4 and obj.tags.exists():
            tag_books = Product.objects.filter(
                tags__in=obj.tags.all()
            ).exclude(id__in=[p.id for p in related_books] + [obj.id]).distinct()
            related_books.extend(list(tag_books))

        # Random fallback
        if len(related_books) < 4:
            remaining_books = Product.objects.exclude(
                id__in=[p.id for p in related_books] + [obj.id]
            )
            remaining_count = min(4 - len(related_books), remaining_books.count())
            if remaining_count > 0:
                related_books.extend(random.sample(list(remaining_books), remaining_count))

        # Limit to 4 and serialize using BookListSerializer
        serializer = BookListSerializer(related_books[:4], many=True, context=self.context)
        return serializer.data

class ProductRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductRating
        fields = ['id', 'user', 'product', 'score', 'review']
        read_only_fields = ['id', 'user']

    def validate_score(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError("Score must be between 1 and 5.")
        return value

    @classmethod
    def get_rating_counts(cls):
        """Returns counts of ratings from 1 to 5 as a dictionary."""
        counts = (
            ProductRating.objects
            .values("score")
            .annotate(product_count=Count("id"))
        )

        # Create dict with all ratings 1–5, default 0
        count_map = {str(rating): 0 for rating in range(1, 6)}

        for c in counts:
            count_map[str(c["score"])] = c["product_count"]

        return count_map
