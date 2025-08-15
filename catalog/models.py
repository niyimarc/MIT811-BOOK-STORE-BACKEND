from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from django.contrib.auth.models import User
from .constants import PRODUCT_STATUS, BOOK_FORMAT_CHOICES, PHYSICAL_STOCK_STATUS, EBOOK_STOCK_STATUS, BOOK_LANGUAGES
from mptt.models import MPTTModel, TreeForeignKey
from django.db.models import Avg
from django.core.validators import MinValueValidator, MaxValueValidator
from .validators import validate_non_negative
from django.core.exceptions import ValidationError

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
    format_type = models.CharField(
        max_length=20,
        choices=BOOK_FORMAT_CHOICES,
        default="physical"
    )

    physical_stock_status = models.CharField(
        max_length=50,
        choices=PHYSICAL_STOCK_STATUS,
        default="in_stock",
        blank=True,
        null=True
    )

    ebook_stock_status = models.CharField(
        max_length=50,
        choices=EBOOK_STOCK_STATUS,
        default="available",
        blank=True,
        null=True
    )

    language = models.CharField(
        max_length=10,
        choices=BOOK_LANGUAGES,
        default="en",
        blank=True,
        null=True
    )

    ebook_file_size = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        help_text="File size in MB",
        blank=True,
        null=True
    )
    pages = models.PositiveIntegerField()
    file_url = models.URLField(blank=True, null=True)
    categories = models.ManyToManyField(Category, related_name="books", blank=True)
    authors = models.ManyToManyField(Author, related_name="books")
    publisher = models.ForeignKey(Publisher, related_name="books", on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.ManyToManyField(Tag, related_name="books", blank=True)
    status = models.CharField(max_length=50, choices=PRODUCT_STATUS, default="Publish")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Auto-set physical stock status
        if self.format_type in ["physical", "both"]:
            if self.stock_quantity == 0:
                self.physical_stock_status = "out_of_stock"
            elif self.stock_quantity <= 5:
                self.physical_stock_status = "low_stock"
            else:
                self.physical_stock_status = "in_stock"

        # Auto-set eBook stock status
        if self.format_type in ["ebook", "both"]:
            today = timezone.now().date()
            if self.publication_date > today:
                self.ebook_stock_status = "pre_order"
            else:
                self.ebook_stock_status = "available"

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
    
    @property
    def average_rating(self):
        # Returns the average rating for the book.
        return self.ratings.aggregate(avg=Avg("score"))["avg"] or 0

class ProductRating(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name="ratings", on_delete=models.CASCADE)
    score = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ]
    )
    review = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ("user", "product")

    def __str__(self):
        return f"{self.user} rated {self.product} - {self.score} stars"
    
class ProductImage(TimeStampedModel):
    book = models.ForeignKey(Product, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="books/images/")
    is_main = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # If no main image yet for this book, set this one as main
        if not ProductImage.objects.filter(book=self.book, is_main=True).exclude(pk=self.pk).exists():
            self.is_main = True

        # If this one is marked as main, unset all others
        elif self.is_main:
            ProductImage.objects.filter(book=self.book, is_main=True).exclude(pk=self.pk).update(is_main=False)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Image for {self.book.title}"
    
class Discount(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='bulk_discounts')
    min_quantity = models.PositiveIntegerField()
    discount_percentage = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        validators=[validate_non_negative], 
        help_text="Enter discount as percentage (e.g., 10 for 10 percent discount)"
        )
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    notify_customers = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def clean(self):
        # Check if there is already an existing discount for the same product
        existing_discount = Discount.objects.filter(product=self.product).exclude(id=self.id)  # Exclude current instance
        if existing_discount.exists():
            raise ValidationError(f"A discount for {self.product.name} already exists.")
        
        if self.start_date is not None and self.end_date is not None:
            if self.start_date > self.end_date:
                raise ValidationError(f"the start date of the discount can't me more than the end date.")

    def __str__(self):
        return f"{self.discount_percentage}% off for {self.min_quantity} {self.product.name}"
