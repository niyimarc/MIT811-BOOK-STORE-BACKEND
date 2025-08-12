from django.urls import path
from .views import (
    GetUserCartView, 
    AddToCartView, 
    SyncCartView, 
    CartItemDeleteView, 
    GuestCartDetailView, 
    ContactUsCreateView, 
    OrderCreateView
    )

urlpatterns = [
    path('api/cart/add_to_cart/', AddToCartView.as_view(), name='add-to-cart'),
    path('api/cart/get_user_cart/', GetUserCartView.as_view(), name='get-user-cart'),
    path('api/cart/guest_cart_details/', GuestCartDetailView.as_view(), name='guest_cart_details'),
    path('api/cart/sync_cart/', SyncCartView.as_view(), name='get_user_cart'),
    path('api/cart/delete_cart_item/<int:product_id>/', CartItemDeleteView.as_view(), name='delete_cart_item'),
    path('api/orders/create/', OrderCreateView.as_view(), name='create_order'),
    path('api/contact_us/', ContactUsCreateView.as_view(), name='contact_us'),
]
