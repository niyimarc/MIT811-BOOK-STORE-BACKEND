from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from .constants import PRODUCT_STATUS
from mptt.models import MPTTModel, TreeForeignKey

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Author(TimeStampedModel):
    name = models.CharField(max_length=255)
    biography = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    photo = models.ImageField(upload_to="authors/photos/", blank=True, null=True)

    def __str__(self):
        return self.name

class Category(MPTTModel, TimeStampedModel):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='children',
        null=True,
        blank=True
    )
    icon = models.ImageField(upload_to="products/categories/", blank=True, null=True)

    class MPTTMeta:
        order_insertion_by = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Publisher(TimeStampedModel):
    name = models.CharField(max_length=255, unique=True)
    website = models.URLField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Tag(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Product(TimeStampedModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    isbn = models.CharField(max_length=13, unique=True)
    description = models.TextField(blank=True, null=True)
    publication_date = models.DateField(default=timezone.now)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(Category, related_name="books", on_delete=models.SET_NULL, null=True)
    authors = models.ManyToManyField(Author, related_name="books")
    publisher = models.ForeignKey(Publisher, related_name="books", on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.ManyToManyField(Tag, related_name="books", blank=True)
    status = models.CharField(max_length=50, choices=PRODUCT_STATUS, default="Publish")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class ProductImage(TimeStampedModel):
    book = models.ForeignKey(Product, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="books/images/")
    is_main = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Ensure only one main image per book
        if self.is_main:
            ProductImage.objects.filter(book=self.book, is_main=True).update(is_main=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Image for {self.book.title}"
