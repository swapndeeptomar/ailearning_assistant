from django.db import models
from django.conf import settings

class PromptTemplate(models.Model):
    """
    Stores system prompts in the database so you can tweak the AI's behavior 
    from the Django Admin panel without having to redeploy your code.
    """
    TASK_CHOICES = (
        ('SUMMARY', 'Summarization'),
        ('QUIZ', 'Quiz Generation'),
        ('INTERVIEW_Q', 'Interview Question Generation'),
    )
    task_type = models.CharField(max_length=20, choices=TASK_CHOICES, unique=True)
    system_prompt = models.TextField(help_text="The instructions given to Gemini.")
    model_version = models.CharField(max_length=50, default="gemini-2.5-flash")
    temperature = models.FloatField(default=0.7)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_task_type_display()} Template ({self.model_version})"

class APILog(models.Model):
    """
    (Optional) Logs every call made to Gemini or HuggingFace to monitor latency and token usage.
    Crucial for calculating the real cost of your SaaS platform.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    service_name = models.CharField(max_length=50) # 'Gemini', 'HuggingFace STT', etc.
    endpoint_used = models.CharField(max_length=100)
    
    # Tracking performance and cost
    tokens_used = models.IntegerField(default=0)
    latency_seconds = models.FloatField(default=0.0)
    successful = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.service_name} log by {self.user} at {self.created_at}"


from django.db import models
from apps.documents.models import Document

class GeneratedContent(models.Model):
    CONTENT_TYPES = (
        ('summary', 'Summary'),
        ('notes', 'Notes'),
        ('flashcards', 'Flashcards'),
        ('quiz','Quiz'),
        ('interview', 'Interview Context'),
        ('search_query', 'Search Query')
    )

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='generated_content')
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    data = models.JSONField() # Stores the clean JSON from Gemini
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('document', 'content_type') # Prevents duplicate generations for the same doc


class ChatMessage(models.Model):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('ai', 'AI Assistant'),
    )
    
    # Link the message directly to the document it's discussing
    document = models.ForeignKey('documents.Document', on_delete=models.CASCADE, related_name='chat_messages')
    
    # Who is speaking?
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    
    # The actual text (User's question or Gemini's answer)
    content = models.TextField()
    
    # To keep the chat in the correct chronological order
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at'] # Automatically sort oldest to newest

    def __str__(self):
        return f"{self.role} - {self.document.file_name}"