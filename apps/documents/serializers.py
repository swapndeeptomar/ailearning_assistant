from rest_framework import serializers
from .models import Document

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'file_name', 'file_url', 'created_at']
        read_only_fields = ['id', 'file_url', 'created_at']