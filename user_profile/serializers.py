from rest_framework import serializers
from user_profile.models import BillingAddress

class BillingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillingAddress
        fields = ['address', 'state', 'city', 'apartment', 'country', 'zip_code']