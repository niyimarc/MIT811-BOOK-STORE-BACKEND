from rest_framework import serializers
from .models import Author, Category, Publisher, Tag, Product, ProductImage

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = "__all__"

class CategorySerializer(serializers.ModelSerializer):
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
    category = CategorySerializer(read_only=True)
    authors = AuthorSerializer(many=True, read_only=True)
    publisher = PublisherSerializer(read_only=True)
    main_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id", "title", "slug", "isbn", "price", "stock_quantity",
            "category", "authors", "publisher", "main_image"
        ]

    def get_main_image(self, obj):
        main_img = obj.images.filter(is_main=True).first()
        return main_img.image.url if main_img else None


class BookDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    authors = AuthorSerializer(many=True, read_only=True)
    publisher = PublisherSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    images = BookImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = "__all__"