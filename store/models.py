from django.db import models
from catalog.models import Product
from django.contrib.auth.models import User
from catalog.constants import PRODUCT_STATUS
from user_profile.models import Address
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from .notifications import notify_buyer_on_order
from django_pg.models import BaseOrder

# Create your models here.
class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

    def add_product(self, product_id, quantity=1):
        """Add or update a product in the cart."""
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            raise ValueError(f"Product with id {product_id} does not exist.")

        cart_item, created = self.cart_items.get_or_create(product=product)

        if not created:
            cart_item.quantity += int(quantity)
        else:
            cart_item.quantity = int(quantity)

        cart_item.save()
        
    def get_total_price(self):
        """ Calculate total price without any discounts. """
        return sum(item.get_total_price() for item in self.cart_items.all())

    def get_total_discount(self):
        """ Calculate the total discount applied across all items in the cart. """
        return sum(item.get_discount_amount() for item in self.cart_items.all())

    def get_total_discounted_price(self):
        """ Calculate total price after discount. """
        total_price = self.get_total_price()
        total_discount = self.get_total_discount()
        return total_price - total_discount

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='cart_items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product.name} - {self.quantity}"
    
    def get_total_price(self):
        """ Returns the total price for this item (quantity * price). """
        return self.product.price * self.quantity

    def get_discount_amount(self):
        """ Returns the discount amount for this item, based on active bulk discounts. """
        # Check if the product has any active discounts
        active_discount = self.product.bulk_discounts.filter(
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now(),
            min_quantity__lte=self.quantity  # Only apply discount if the cart quantity meets the min_quantity
        ).first()

        if active_discount:
            discount_amount = (active_discount.discount_percentage / Decimal(100)) * self.product.price
            total_discount = discount_amount * self.quantity
            # Round the discount to 2 decimal places
            return total_discount.quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
        return Decimal(0).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)

class Order(BaseOrder):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    packed = models.BooleanField(default=False)
    in_transit = models.BooleanField(default=False) 
    delivered = models.BooleanField(default=False)
    payment_date = models.DateTimeField(null=True)
    packed_date = models.DateTimeField(null=True)
    in_transit_date = models.DateTimeField(null=True)
    delivered_date = models.DateTimeField(null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def update_total_discount(self):
        total_discount = self.order_items.aggregate(total_discount=Sum('discount'))['total_discount'] or Decimal('0.00')
        self.total_discount = total_discount
        self.save()

    def update_total_price(self):
        total_price = self.order_items.aggregate(total_price=Sum('total'))['total_price'] or Decimal('0.00')
        self.total_price = total_price
        self.save()

    def clean(self):
        # Check if payment_made is True before changing to specific statuses
        if self.status in ["Order Placed","Packed", "In Transit", "Delivered", "Completed"] and not self.payment_made:
            raise ValidationError(_("Payment must be made before setting the order status to '%(status)s'.") % {'status': self.status})
            
    def save(self, *args, **kwargs):
        # Capture the current time for setting timestamps
        current_time = timezone.now()

        self.clean()

        # Check if status has changed to "Packed"
        if self.status == "Packed" and not self.packed:
            self.packed = True
            self.packed_date = current_time

        # Check if status has changed to "In Transit"
        elif self.status == "In Transit" and not self.in_transit:
            self.in_transit = True
            self.in_transit_date = current_time

        # Check if status has changed to "Delivered"
        elif self.status == "Delivered" and not self.delivered:
            self.delivered = True
            self.delivered_date = current_time

        # Check if payment_made is set to True
        if self.payment_made and self.payment_date is None:
            self.payment_date = current_time

        if self.pk:
            original = Order.objects.get(pk=self.pk)
            if original.status != self.status:
                notify_buyer_on_order(self)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='order_items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Always fetch the latest price from the related Product
        self.price = self.product.price

        # Check if there is any valid discount
        now = timezone.now()
        valid_discount = self.product.bulk_discounts.filter(
            start_date__lte=now,
            end_date__gte=now,
            min_quantity__lte=self.quantity
        ).first()

        if valid_discount:
            print("there is a valid discount")
            discount_amount = (valid_discount.discount_percentage / Decimal('100')) * (self.price * self.quantity)
            self.discount = discount_amount
        else:
            self.discount = Decimal('0.00')

        self.total = (self.quantity * self.price) - self.discount
        
        # Save the OrderItem
        super(OrderItem, self).save(*args, **kwargs)

        # Update the total_discount in the Order after saving the OrderItem
        self.order.update_total_discount()
        self.order.update_total_price()
    
    def __str__(self):
        return f"{self.product.name} - {self.quantity}"

class ShippingAddress(Address):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="shipping_address")

class OrderNote(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    note = models.TextField(null=True, blank=True)

class Wish(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)


class WishList(models.Model):
    wish = models.ForeignKey(Wish, related_name='wish_list', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.product.name}"
    
class Faq(models.Model):
    question = models.CharField(max_length=200)
    answer = models.TextField()
    status = models.CharField(choices=PRODUCT_STATUS, max_length=10, default="Published")
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

class EmailSubscriber(models.Model):
    email = models.EmailField(unique=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

class ContactUs(models.Model):
    name = models.CharField(max_length=100,)
    email = models.EmailField()
    subject = models.CharField(max_length=150,)
    message = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
