from django.urls import path
from .views import StartInterviewSessionView, SubmitInterviewAnswerView, EndInterviewSessionView, UserInterviewHistoryView, GetInterviewTaskStatus

urlpatterns = [
    path('start/', StartInterviewSessionView.as_view(), name='start_session'),
    path('submit-answer/', SubmitInterviewAnswerView.as_view(), name='submit_answer'),
    path('end/', EndInterviewSessionView.as_view(), name='end_session'),
    path('history/', UserInterviewHistoryView.as_view(), name='interview_history'),
    path('status/<str:task_id>/', GetInterviewTaskStatus.as_view(), name='get_interview_task_status'),
]