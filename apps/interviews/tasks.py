from celery import shared_task
from .models import InterviewSession, InterviewResponse
from ai_services.sbert_client import get_similarity_score
import logging

logger = logging.getLogger(__name__)

@shared_task
def grade_interview_answer_task(session_id, question_text, reference_context, user_response_text):
    try:
        session = InterviewSession.objects.get(id=session_id)
        
        # SBERT Similarity (Heavy Compute)
        score = get_similarity_score(reference_context, user_response_text)
        
        # Logic for evaluation
        if score >= 85:
            evaluation = "Excellent response!"
        elif score >= 60:
            evaluation = "Good attempt."
        else:
            evaluation = "Let's review this concept."

        # Save result to DB
        InterviewResponse.objects.create(
            session=session,
            question_text=question_text,
            reference_context=reference_context,
            user_response_text=user_response_text,
            semantic_similarity_score=score,
            ai_evaluation=evaluation
        )
        return {"score": score, "status": "completed"}
    except Exception as e:
        logger.error(f"Task Error: {str(e)}")
        return {"status": "failed", "error": str(e)}