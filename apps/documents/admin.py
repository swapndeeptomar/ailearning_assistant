from django.contrib import admin
from .models import Document

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    # Notice we use 'user__email' to reach across the database and show the user's email!
    list_display = ('file_name', 'user', 'get_total_chunks', 'created_at')
    search_fields = ('file_name', 'user__email', 'content_hash')
    list_filter = ('created_at',)
    
    # We make these read-only so you don't accidentally break the ChromaDB sync
    readonly_fields = ('file_url', 'extracted_text', 'text_chunks', 'content_hash', 'created_at')

    # Custom column to show token usage/chunk count
    def get_total_chunks(self, obj):
        return len(obj.text_chunks) if obj.text_chunks else 0
    get_total_chunks.short_description = 'Total Vector Chunks'