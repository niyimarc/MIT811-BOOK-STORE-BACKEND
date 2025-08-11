from django.db import models
from django.contrib.auth.models import User
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
import uuid
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .constants import ROLE, ADDRESS_TYPE
from django.core.exceptions import ValidationError

# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    referred_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referrer', null=True, blank=True)
    role = models.CharField(choices=ROLE, max_length=16, default="Customer")
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    email_verified = models.BooleanField(default=False)
    profile_is_submited = models.BooleanField(default=False)
    verification_token = models.UUIDField(default=uuid.uuid4, editable=False)
    password_reset_token = models.UUIDField(editable=False, null=True, blank=True)
    password_reset_token_is_used = models.BooleanField(default=True)
    password_reset_token_created_on = models.DateTimeField(null=True, blank=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def generate_verification_token(self):
        if not self.verification_token:
            self.verification_token = uuid.uuid4()
        return str(self.verification_token)

    def get_verification_url(self):
        
        token = self.generate_verification_token()
        return reverse('user_profile:verify_email', kwargs={'token': token})
    
    def generate_password_reset_token(self):
        # Check if there's an existing token and if it's still valid
        if self.password_reset_token and self.is_password_reset_token_valid():
            return str(self.password_reset_token)
        self.password_reset_token = uuid.uuid4()
        self.password_reset_token_created_on = timezone.now()
        self.password_reset_token_is_used = False
        self.save()
        return str(self.password_reset_token)
    
    def get_password_reset_token_url(self):
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.id))
        token = self.generate_password_reset_token()
        return reverse('user_profile:set_password', kwargs={'uidb64': uidb64, 'token': token})
    
    def is_password_reset_token_valid(self):
        # Check if the password reset token is still valid
        if self.password_reset_token_created_on:
            expiration_time = self.password_reset_token_created_on + timedelta(minutes=15)
            return timezone.now() <= expiration_time
        return False

    def verification_progress(self):
        if self.email_verified and self.is_verified:
            progress = 100
            completed = 2
            verification_completed = True
        elif self.email_verified:
            progress = 50
            completed = 1
            verification_completed = False
        else:
            progress = 0
            completed = 0
            verification_completed = False
        
        return {
            'progress': progress,
            'completed': completed,
            'verification_completed': verification_completed,
        }
    def __str__(self):
        return self.user.username

class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    login_time = models.DateTimeField(default=timezone.now)
    logout_time = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    browser_info = models.CharField(max_length=255, null=True, blank=True)
    device_info = models.CharField(max_length=255, null=True, blank=True)
    login_successful = models.BooleanField(default=True)
    session_duration = models.DurationField(null=True, blank=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"{self.user.username} - {self.login_time}"
        
    
class Address(models.Model):
    address = models.CharField(max_length=200,)
    state = models.CharField(max_length=30,)
    nearest_bus_stop = models.CharField(max_length=50,)
    country = models.CharField(max_length=50,)
    zip_code = models.CharField(max_length=10,)
    is_verified = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

class BillingAddress(Address):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="billing_address")

class Phone(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="user_phone")
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True)
    is_submitted = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'phone'], name='unique_user_phone')
        ]

