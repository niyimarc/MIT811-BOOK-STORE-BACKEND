from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from .models import Cart, CartItem
from .serializers import CartSerializer, ContactUsSerializer, OrderSerializer
from auth_core.views import PrivateUserViewMixin, PublicViewMixin
from catalog.views import Product

class GetUserCartView(PrivateUserViewMixin, APIView):
    def get(self, request):
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class GuestCartDetailView(PublicViewMixin, APIView):
    def post(self, request):
        items = request.data.get('cart_items', [])

        if not isinstance(items, list):
            return Response({'error': 'Invalid format'}, status=400)

        response_data = []
        for item in items:
            product_id = item.get('product_id')
            quantity = int(item.get('quantity', 1))

            try:
                product = Product.objects.get(id=product_id)
                price = float(product.price)

                images = product.productimage_set.all()
                image_urls = [
                    request.build_absolute_uri(img.image.url) for img in images if img.image
                ]

                response_data.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'product_price': f"{price:.2f}",
                    'quantity': quantity,
                    'get_total_price': round(price * quantity, 2),
                    'images': image_urls
                })
            except Product.DoesNotExist:
                continue

        return Response(response_data)
       
class AddToCartView(PrivateUserViewMixin, APIView):
    def post(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)

        if not product_id:
            return Response({'error': 'product_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        # This method should be implemented in your Cart model
        cart.add_product(product_id, quantity)  
        cart.save()

        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)

class SyncCartView(PrivateUserViewMixin, APIView):
    def post(self, request):
        cart_items = request.data.get('cart_items', [])

        if not isinstance(cart_items, list):
            return Response({'success': False, 'error': 'Invalid data format'}, status=400)

        cart, _ = Cart.objects.get_or_create(user=request.user)

        for item in cart_items:
            product_id = item.get('product_id')
            quantity = item.get('quantity', 1)

            try:
                product = Product.objects.get(id=product_id)
                cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
                if not created:
                    cart_item.quantity += quantity
                else:
                    cart_item.quantity = quantity
                cart_item.save()
            except Product.DoesNotExist:
                continue  # Skip invalid product

        return Response({'success': True})

class CartItemDeleteView(PrivateUserViewMixin, APIView):
    def delete(self, request, product_id):
        cart_item = CartItem.objects.filter(cart__user=request.user, product=product_id).first()

        if not cart_item:
            return Response({"error": "Cart item not found."}, status=status.HTTP_404_NOT_FOUND)

        cart_item.delete()
        return Response({"detail": "Cart item deleted successfully."}, status=status.HTTP_200_OK)

class OrderCreateView(PrivateUserViewMixin, APIView):
    def post(self, request):
        serializer = OrderSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            order = serializer.save()
            # Clear cart items after order is created
            user = request.user
            CartItem.objects.filter(cart__user=user).delete()
            return Response({
                "success": True,
                "message": "Order created successfully.",
                "order_id": order.order_reference
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
     
class ContactUsCreateView(APIView):
    def post(self, request):
        serializer = ContactUsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "Message received!"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)