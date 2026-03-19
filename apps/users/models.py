import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
import os
from django.conf import settings

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    credits = models.IntegerField(default=10)
    provider = models.CharField(max_length=50, blank=True, null=True)
    PLAN_CHOICES = (
        ('FREE', 'Free'),
        ('BASIC', 'Basic'),
        ('PRO', 'Pro'),
    )
    subscription_plan = models.CharField(max_length=10, choices=PLAN_CHOICES, default='FREE')
    avatar_url = models.URLField(blank=True, null=True)

    @property
    def upload_limit(self):
        limits = {'FREE': 2, 'BASIC': 5, 'PRO': 10}
        return limits.get(self.subscription_plan, 2)

class Transaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # Razorpay Specific Fields
    razorpay_order_id = models.CharField(max_length=100, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    
    # Transaction Details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    plan_type = models.CharField(max_length=50) # 'BASIC' or 'PRO'
    status = models.CharField(max_length=20, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.plan_type} - {self.status}"