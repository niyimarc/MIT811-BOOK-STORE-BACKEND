from django.shortcuts import get_object_or_404
from .models import Cart, CartItem
from product.models import Product
from django.db import transaction

def move_session_cart_to_db(request, user):
        session_cart = request.request.session.get('cart', {})

        if not session_cart:
            return

        cart, created = Cart.objects.get_or_create(user=user)

        # Use transaction to ensure atomicity
        with transaction.atomic():
            for item_key, item_data in session_cart.items():
                try:
                    product = get_object_or_404(Product, id=item_data['product_id'], status="Publish")
                    quantity = item_data.get('quantity', 1)
                    size = item_data.get('size', None)
                    size_category = item_data.get('size_category', None)
                    color = item_data.get('color', None)

                    # Check if the CartItem already exists
                    try:
                        cart_item = CartItem.objects.get(
                            cart=cart,
                            product=product,
                            size=size,
                            size_category=size_category,
                            color=color
                        )
                        # Update the quantity if it already exists
                        cart_item.quantity += int(quantity)
                        cart_item.save()
                    except CartItem.DoesNotExist:
                        # Create a new CartItem if it doesn't exist
                        CartItem.objects.create(
                            cart=cart,
                            product=product,
                            size=size,
                            size_category=size_category,
                            color=color,
                            quantity=quantity
                        )

                except Product.DoesNotExist:
                    # Handle product not found (optional)
                    pass

        # Clear session cart after moving items to the database
        del request.request.session['cart']
        request.request.session.modified = True