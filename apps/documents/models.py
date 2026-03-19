import uuid
from django.db import models
from apps.users.models import User

class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    file_name = models.CharField(max_length=255)
    file_url = models.URLField()
    extracted_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    text_chunks = models.JSONField(default=list, blank=True)
    content_hash = models.CharField(max_length=64, db_index=True, blank=True, null=True)
    youtube_video = models.JSONField(null=True, blank=True)



class GeneratedContent(models.Model):
    CONTENT_TYPES = (
        ('SUMMARY', 'Summary'),
        ('NOTES', 'Notes'),
        ('QUIZ', 'Quiz'),
        ('FLASHCARDS', 'Flashcards'),
    )
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    content_type = models.CharField(max_length=15, choices=CONTENT_TYPES)
    data = models.JSONField() # Stores structured text or list data
    created_at = models.DateTimeField(auto_now_add=True)