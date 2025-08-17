from rest_framework import serializers
from .models import Cart, CartItem, ContactUs, Order, OrderItem, ShippingAddress, OrderNote
from django.conf import settings

class CartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.CharField(source='product.id')
    product_name = serializers.CharField(source='product.title')
    product_price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2)
    images = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'product_id', 'product_name', 'product_price', 'quantity', 'get_total_price', 'get_discount_amount', 'images']

    def get_images(self, obj):
        images = obj.product.images.all()
        base_url = getattr(settings, 'MEDIA_BASE_URL', '')
        result = []
        for image in images:
            if image.image:
                url = image.image.url
                if url.startswith('http'):
                    result.append(url)
                else:
                    result.append(f"{base_url}{url}")
        return result


class CartSerializer(serializers.ModelSerializer):
    cart_items = CartItemSerializer(many=True)
    total_price = serializers.SerializerMethodField()
    total_discount = serializers.SerializerMethodField()
    total_discounted_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'cart_items', 'total_price', 'total_discount', 'total_discounted_price']

    def get_total_price(self, obj):
        return obj.get_total_price()

    def get_total_discount(self, obj):
        return obj.get_total_discount()

    def get_total_discounted_price(self, obj):
        return obj.get_total_discounted_price()

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']

class ShippingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingAddress
        exclude = ['order']

class OrderNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderNote
        exclude = ['order']

class OrderSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(many=True, write_only=True)
    shipping_address = ShippingAddressSerializer(write_only=True)
    note = OrderNoteSerializer(write_only=True, required=False)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_discount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'order_items', 'shipping_address', 'note', 'total_price', 'total_discount',]

    def create(self, validated_data):
        user = self.context['request'].user
        order_items_data = validated_data.pop('order_items', [])
        shipping_data = validated_data.pop('shipping_address')
        note_data = validated_data.pop('note', None)

        # Set status to Pending
        order = Order.objects.create(user=user, status='Pending', **validated_data)

        # Create order items
        for item_data in order_items_data:
            OrderItem.objects.create(order=order, **item_data)

        # Create shipping address
        ShippingAddress.objects.create(order=order, **shipping_data)

        if note_data:
            OrderNote.objects.create(order=order, **note_data)

        # update totals before returning
        order.update_total_price()
        order.update_total_discount()

        return order
    
class ContactUsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactUs
        fields = ['name', 'email', 'subject', 'message']

