from django.contrib import admin
from .models import Author, Category, Publisher, Tag, Product, ProductImage


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("name", "date_of_birth", "created_at")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ("name", "website", "created_at")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)
    ordering = ("name",)


class BookImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "isbn", "price", "stock_quantity", "publication_date", "created_at")
    list_filter = ("publisher", "authors", "tags")
    search_fields = ("title", "isbn")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [BookImageInline]
    ordering = ("title",)


@admin.register(ProductImage)
class BookImageAdmin(admin.ModelAdmin):
    list_display = ("book", "is_main", "created_at")
    list_filter = ("is_main",)
