from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import User
from apps.documents.models import Document

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    monthly_upload_count = serializers.SerializerMethodField()
    upload_limit = serializers.ReadOnlyField()

    def get_monthly_upload_count(self, obj):
        now = timezone.now()
        return Document.objects.filter(
            user=obj,
            created_at__year=now.year,
            created_at__month=now.month
        ).count()
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'credits', 'subscription_plan', 'provider', 'monthly_upload_count', 'upload_limit')
        read_only_fields = ('id', 'credits', 'subscription_plan', 'provider','monthly_upload_count', 'upload_limit')

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        # Using create_user ensures the password is encrypted (hashed) properly
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        # Note: 'credits' defaults to 100 automatically based on your models.py
        return user