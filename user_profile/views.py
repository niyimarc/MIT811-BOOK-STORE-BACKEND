from rest_framework.response import Response
from rest_framework import status
from .models import BillingAddress
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .serializers import BillingAddressSerializer
from auth_core.views import PrivateUserViewMixin
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404
from .utils import generate_password_reset_token, is_password_reset_token_valid
from .signals import send_password_reset_email

class UserProfileView(PrivateUserViewMixin, APIView):
    def get(self, request):
        user = request.user
        billing = getattr(user, 'billing_address', None)

        billing_data = None
        if billing:
            billing_data = {
                "address": billing.address,
                "state": billing.state,
                "city": billing.city,
                "apartment": billing.apartment,
                "country": billing.country,
                "zip_code": billing.zip_code,
                "is_verified": billing.is_verified,
            }

        return Response({
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "billing_address": billing_data
        })
    
class BillingAddressView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        serializer = BillingAddressSerializer(data=request.data)

        if serializer.is_valid():
            validated_data = serializer.validated_data
            validated_data["is_verified"] = True 
            # Update if already exists, or create new
            billing_address, created = BillingAddress.objects.update_or_create(
                user=user,
                defaults=validated_data
            )
            return Response({
                "success": True,
                "created": created,
                "billing_address": BillingAddressSerializer(billing_address).data
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RequestPasswordResetView(APIView):
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"error": "No account found with that email"}, status=status.HTTP_404_NOT_FOUND)

        profile = user.profile
        token = generate_password_reset_token(profile)
        send_password_reset_email(user, profile, token)

        return Response({"message": "Password reset link sent to your email"}, status=status.HTTP_200_OK)


class ResetPasswordConfirmView(APIView):
    def post(self, request):
        uidb64 = request.data.get("uidb64")
        token = request.data.get("token")
        new_password = request.data.get("new_password")

        if not uidb64 or not token or not new_password:
            return Response({"error": "uidb64, token, and new_password are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = get_object_or_404(User, pk=uid)
        except Exception:
            return Response({"error": "Invalid link"}, status=status.HTTP_400_BAD_REQUEST)

        profile = user.profile

        # Validate token
        if str(profile.password_reset_token) != token or not is_password_reset_token_valid(profile):
            return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)

        # Update password
        user.password = make_password(new_password)
        user.save()

        # Mark token as used
        profile.password_reset_token_is_used = True
        profile.save()

        return Response({"message": "Password reset successful"}, status=status.HTTP_200_OK)
