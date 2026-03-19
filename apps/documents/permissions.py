from rest_framework import permissions
from django.utils import timezone
from .models import Document

class CanUploadDocument(permissions.BasePermission):
    message = "You have reached your monthly document upload limit for your plan."

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
            
        # Get count of documents uploaded by this user in the current month
        now = timezone.now()
        monthly_uploads = Document.objects.filter(
            user=user,
            created_at__year=now.year,
            created_at__month=now.month
        ).count()

        return monthly_uploads < user.upload_limit