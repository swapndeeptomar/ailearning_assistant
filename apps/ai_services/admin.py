from django.contrib import admin
from .models import GeneratedContent
from .models import APILog

@admin.register(GeneratedContent)
class GeneratedContentAdmin(admin.ModelAdmin):
    list_display = ('document', 'content_type', 'created_at')
    search_fields = ('document__file_name', 'document__user__email', 'content_type')
    list_filter = ('content_type', 'created_at')
    readonly_fields = ('created_at',)

@admin.register(APILog)
class APILogAdmin(admin.ModelAdmin):
    list_display = ('user', 'service_name', 'endpoint_used', 'tokens_used', 'latency_seconds', 'successful', 'created_at')
    search_fields = ('user__email', 'service_name', 'endpoint_used')
    list_filter = ('service_name', 'successful', 'created_at')
    readonly_fields = ('created_at',)