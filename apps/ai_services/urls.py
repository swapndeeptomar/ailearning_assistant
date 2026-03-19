from django.urls import path
from .views import GenerateAIContentView,GradeInterviewAnswerView,ChatWithPDFView,GetDocumentContentView,DocumentChatHistoryView

urlpatterns = [
    path('generate/', GenerateAIContentView.as_view(), name='generate_ai_content'),
    path('grade-answer/', GradeInterviewAnswerView.as_view(), name='grade_answer'),
    path('chat/', ChatWithPDFView.as_view(), name='chat_with_pdf'),
    path('content/<uuid:document_id>/', GetDocumentContentView.as_view(), name='ai-get-content'),
    path('chat/history/<uuid:document_id>/', DocumentChatHistoryView.as_view(), name='chat-history'),
]