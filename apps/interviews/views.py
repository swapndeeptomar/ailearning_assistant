import logging
from django.db.models import Avg
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from apps.documents.models import Document
from apps.ai_services.sbert_client import get_similarity_score
from .models import InterviewSession, InterviewResponse
from .tasks import grade_interview_answer_task
from celery.result import AsyncResult

logger = logging.getLogger(__name__)

class StartInterviewSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        document_id = request.data.get('document_id')
        
        if not document_id:
            return Response({"error": "document_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            document = Document.objects.get(id=document_id)
            
            # Creates the session using your UUID model
            session = InterviewSession.objects.create(
                user=request.user,
                document=document
            )
            
            return Response({
                "message": "Interview session started successfully.",
                "session_id": str(session.id)
            }, status=status.HTTP_201_CREATED)
            
        except Document.DoesNotExist:
            return Response({"error": "Document not found."}, status=status.HTTP_404_NOT_FOUND)

class SubmitInterviewAnswerView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session_id = request.data.get('session_id')
        question_text = request.data.get('question_text')
        reference_context = request.data.get('reference_context')
        user_response_text = request.data.get('user_response_text')

        # Basic Validation
        if not all([session_id, question_text, reference_context, user_response_text]):
            return Response({"error": "Missing fields."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Ensure session exists before queueing
            InterviewSession.objects.get(id=session_id, user=request.user)

            # --- THE CELERY TRIGGER ---
            # .delay() pushes the data to Redis and returns immediately
            task = grade_interview_answer_task.delay(
                session_id, 
                question_text, 
                reference_context, 
                user_response_text
            )

            return Response({
                "task_id": task.id,
                "status": "processing",
                "message": "AI is evaluating your answer in the background."
            }, status=status.HTTP_202_ACCEPTED)

        except InterviewSession.DoesNotExist:
            return Response({"error": "Session not found."}, status=status.HTTP_404_NOT_FOUND)

# --- NEW VIEW FOR POLLING ---
class GetInterviewTaskStatus(APIView):
    """
    Endpoint for React to check if the AI is done grading.
    URL Pattern: /api/interview/status/<task_id>/
    """
    def get(self, request, task_id):
        task_result = AsyncResult(task_id)
        
        response_data = {
            "task_id": task_id,
            "status": task_result.status, # PENDING, PROGRESS, SUCCESS, FAILURE
        }

        if task_result.ready():
            # Task is finished (Success or Error)
            response_data["result"] = task_result.result
            
        return Response(response_data, status=status.HTTP_200_OK)
# class SubmitInterviewAnswerView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         session_id = request.data.get('session_id')
#         question_text = request.data.get('question_text')
#         reference_context = request.data.get('reference_context') # This is the ideal answer from Gemini
#         user_response_text = request.data.get('user_response_text') # What the user spoke/typed

#         if not all([session_id, question_text, reference_context, user_response_text]):
#             return Response({"error": "Missing required fields for grading."}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             session = InterviewSession.objects.get(id=session_id, user=request.user)

#             # 1. Get the semantic score from Hugging Face SBERT
#             score = get_similarity_score(reference_context, user_response_text)

#             # 2. Generate dynamic AI evaluation feedback
#             if score >= 85:
#                 evaluation = "Excellent response! You captured the core concepts perfectly."
#             elif score >= 60:
#                 evaluation = "Good attempt. You got the general idea, but missed a few specific details."
#             else:
#                 evaluation = "That wasn't quite right. Let's review the notes and try this concept again."

#             # 3. Save directly to your exact InterviewResponse model
#             InterviewResponse.objects.create(
#                 session=session,
#                 question_text=question_text,
#                 reference_context=reference_context,
#                 user_response_text=user_response_text,
#                 semantic_similarity_score=score,
#                 ai_evaluation=evaluation
#             )

#             return Response({
#                 "score": score,
#                 "feedback": evaluation,
#                 "status": "success"
#             }, status=status.HTTP_200_OK)

#         except InterviewSession.DoesNotExist:
#             return Response({"error": "Invalid session ID."}, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             logger.error(f"Grading error: {e}")
#             return Response({"error": "An internal error occurred during grading."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EndInterviewSessionView(APIView):
    """
    Called when the user finishes the last question. Calculates the final score.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session_id = request.data.get('session_id')

        try:
            session = InterviewSession.objects.get(id=session_id, user=request.user)
            
            # Calculate the average of all SBERT scores in this session
            avg_data = session.responses.aggregate(Avg('semantic_similarity_score'))
            average_score = avg_data['semantic_similarity_score__avg'] or 0.0

            # Update your session model
            session.overall_accuracy_score = round(average_score, 2)
            session.is_completed = True
            
            # (Optional) You could call Gemini here to generate a final_feedback_summary based on all answers!
            session.final_feedback_summary = f"You completed the interview with an overall accuracy of {round(average_score, 2)}%."
            session.save()

            return Response({
                "message": "Interview completed.",
                "overall_accuracy": session.overall_accuracy_score,
                "final_feedback": session.final_feedback_summary
            }, status=status.HTTP_200_OK)

        except InterviewSession.DoesNotExist:
            return Response({"error": "Invalid session ID."}, status=status.HTTP_404_NOT_FOUND)
        
        
class UserInterviewHistoryView(APIView):
    """
    Returns a summary of all completed interviews for the user's dashboard.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Fetch only completed sessions, newest first
        sessions = InterviewSession.objects.filter(
            user=request.user, 
            is_completed=True
        ).select_related('document').order_by('-created_at')
        
        history_data = [
            {
                "session_id": str(session.id),
                "document_name": session.document.file_name,
                "overall_score": session.overall_accuracy_score,
                "feedback": session.final_feedback_summary,
                "date": session.created_at.strftime("%Y-%m-%d %H:%M")
            }
            for session in sessions
        ]
        
        return Response({"history": history_data}, status=status.HTTP_200_OK)