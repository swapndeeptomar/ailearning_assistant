import uuid
from django.db import models
from django.conf import settings
from apps.documents.models import Document

class InterviewSession(models.Model):
    """
    Groups individual interview turns into a single session.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    
    # Aggregated metrics for the final report
    overall_accuracy_score = models.FloatField(default=0.0)
    final_feedback_summary = models.TextField(blank=True, null=True)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Session {self.id} - User: {self.user.username}"

class InterviewResponse(models.Model):
    """
    Stores each Q&A turn, the source context used for RAG, and the BERT score.
    """
    session = models.ForeignKey(InterviewSession, on_delete=models.CASCADE, related_name='responses')
    question_text = models.TextField()
    
    # The specific chunk from the PDF used to validate this answer
    reference_context = models.TextField() 
    
    # Transcription from Google STT
    user_response_text = models.TextField()
    
    # Assessment Data (from Hugging Face / BERT)
    semantic_similarity_score = models.FloatField(default=0.0)
    
    # Feedback from Gemini explaining the score
    ai_evaluation = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']