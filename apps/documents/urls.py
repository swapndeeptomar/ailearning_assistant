from django.urls import path
from .views import DocumentUploadView, test_redis, UserDocumentsListView, GenerateTopicDocumentView, UserDocumentsView, DocumentYouTubeView
urlpatterns = [
    path('upload/', DocumentUploadView.as_view(), name='document_upload'),
    path('test-redis/', test_redis, name='test_redis'),
    path('my-documents/', UserDocumentsListView.as_view(), name='my_documents'),
    path('generate-topic/', GenerateTopicDocumentView.as_view(), name='generate_topic'),
    path('', UserDocumentsView.as_view(), name='user-documents-list'),
    path('<str:document_id>/videos/', DocumentYouTubeView.as_view(), name='document-videos'),
]