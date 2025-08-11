from django.urls import path
from .views import (
    UserProfileView,
    BillingAddressView
)
app_name = 'user_profile'

urlpatterns = [
    path('api/user/profile/', UserProfileView.as_view(), name='user_profile'),
    path('api/user/billing_address/', BillingAddressView.as_view(), name='billing_address'),
]