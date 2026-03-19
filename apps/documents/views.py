import os
import hashlib
import cloudinary.uploader
from datetime import timedelta
import logging
from django.conf import settings
from django.core.files.storage import default_storage
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Document
from .serializers import DocumentSerializer
from .extractors import extract_text_from_pdf,chunk_text
from .vector_store import store_chunks_in_vector_db
from .permissions import CanUploadDocument

logger = logging.getLogger(__name__)

# # upload to cloudinary instead of local media storage# #

class DocumentUploadView(APIView):
    permission_classes = [IsAuthenticated, CanUploadDocument]

    def post(self, request):
        uploaded_file = request.FILES.get('file')
        
        if not uploaded_file:
            return Response({"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)
            
        if not uploaded_file.name.lower().endswith('.pdf'):
            return Response({"error": "Only PDF files are supported."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 1. Extract text FIRST directly from the uploaded memory stream
            extracted_text = extract_text_from_pdf(uploaded_file)
            text_chunks = chunk_text(extracted_text, chunk_size=300, overlap=50)

            # Create a unique SHA-256 fingerprint of the extracted text
            content_hash = hashlib.sha256(extracted_text.encode('utf-8')).hexdigest()
            # ------------------------------------------------

            # --- NEW CLOUDINARY STORAGE LOGIC ---
            # Reset the file pointer to the beginning before uploading!
            uploaded_file.seek(0)
            
            # 2. Upload the file to Cloudinary
            upload_result = cloudinary.uploader.upload(
                uploaded_file, 
                resource_type="raw",
                folder="ai_assistant_documents" # Organizes them neatly in your Cloudinary dashboard
            )
            
            # Grab the secure, permanent cloud URL
            file_url = upload_result.get('secure_url')
            # ------------------------------------

            # 3. Save to Database using the new cloud URL
            document = Document.objects.create(
                user=request.user,
                file_name=uploaded_file.name,
                file_url=file_url,
                extracted_text=extracted_text,
                text_chunks=text_chunks,
                content_hash=content_hash,
            )
            
            # 4. Save to ChromaDB exactly as before
            store_chunks_in_vector_db(document.id, text_chunks,user=request.user)
            
            serializer = DocumentSerializer(document)
            
            return Response({
                "message": "Document uploaded and processed successfully.",
                "total_chunks": len(text_chunks),
                "document": serializer.data
            }, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except Exception as e:
            # Tip: You might want to print(e) or use a logger here during testing 
            # to catch any Cloudinary configuration errors!
            return Response({"error": "An internal error occurred during processing."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)   


from django.core.cache import cache
from django.http import HttpResponse

def test_redis(request):
    cache.set("test_key", "Redis Working", timeout=60)
    return HttpResponse(cache.get("test_key"))

from rest_framework import generics
from .models import Document
from .serializers import DocumentSerializer # Assuming you created this in Phase 3!

class UserDocumentsListView(generics.ListAPIView):
    """
    Returns a list of all documents uploaded by the logged-in user, newest first.
    """
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only return the documents belonging to the user making the request
        return Document.objects.filter(user=self.request.user).order_by('-created_at')

from apps.ai_services.gemini_client import generate_master_text_from_topic
from apps.users.permissions import HasSufficientCredits

class GenerateTopicDocumentView(APIView):
    """
    Takes a text topic, generates a comprehensive textbook-style text using Gemini,
    and saves it as a 'Virtual Document' so the rest of the RAG/Interview system can use it.
    """
    permission_classes = [IsAuthenticated, HasSufficientCredits]

    def post(self, request):
        topic = request.data.get('topic')
        
        if not topic:
            return Response({"error": "A topic is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 1. Ask Gemini to write the textbook chapter
            master_text = generate_master_text_from_topic(topic)
            
            # 2. Slice text into RAG-ready chunks (Reusing your Phase 3 logic!)
            text_chunks = chunk_text(master_text, chunk_size=300, overlap=50)

            # 3. Save to Database as a "Virtual Document"
            # We use a dummy URL to satisfy the URLField in your model without needing migrations
            clean_topic_url = topic.replace(' ', '-').lower()
            dummy_url = f"https://virtual-doc.local/topic/{clean_topic_url}"

            document = Document.objects.create(
                user=request.user,
                file_name=f"Topic: {topic.title()}",
                file_url=dummy_url,
                extracted_text=master_text,
                text_chunks=text_chunks
            )

            # 4. Save to Vector DB (ChromaDB) for the Chat feature
            store_chunks_in_vector_db(document.id, text_chunks)

            # 5. Deduct 1 Credit for the generation
            user = request.user
            user.credits -= 3
            user.save(update_fields=['credits'])

            serializer = DocumentSerializer(document)
            
            return Response({
                "message": f"Virtual document for '{topic}' generated successfully.",
                "total_chunks": len(text_chunks),
                "credits_remaining": user.credits,
                "document": serializer.data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Topic Document generation error: {e}")
            return Response({"error": "An internal error occurred while generating the topic."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserDocumentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Fetch only the documents belonging to the user, newest first
        documents = Document.objects.filter(user=request.user).order_by('-created_at')
        
        serializer = DocumentSerializer(documents, many=True)
        return Response(serializer.data, status=200)
    
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from apps.documents.models import Document
from apps.ai_services.models import GeneratedContent # Adjust import path as needed
from apps.documents.utils import fetch_youtube_videos

class DocumentYouTubeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, document_id):
        document = get_object_or_404(Document, id=document_id)

        # 1. FAST PATH: If videos are already saved in the Document model, return them instantly
        if document.youtube_video:
            return Response({
                "source": "database",
                "videos": document.youtube_video
            }, status=status.HTTP_200_OK)

        # 2. SLOW PATH: Fetch the search query generated by Gemini
        try:
            search_content = GeneratedContent.objects.get(
                document=document,
                content_type='search_query'
            )
        except GeneratedContent.DoesNotExist:
            return Response(
                {"error": "Search query has not been generated for this document yet."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # 3. Extract the actual string from the JSON structure you provided:
        # data = [{"query": "youtube data api v3 search..."}]
        query_data = search_content.data
        search_string = ""
        
        if isinstance(query_data, list) and len(query_data) > 0:
            search_string = query_data[0].get('query', '')
        elif isinstance(query_data, dict):
            search_string = query_data.get('query', '')

        if not search_string:
            return Response({"error": "Invalid search query format."}, status=status.HTTP_400_BAD_REQUEST)

        # 4. Call the YouTube API with the extracted string
        videos = fetch_youtube_videos(search_string)

        if not videos:
            return Response(
                {"error": "Failed to fetch videos from YouTube. API might be down or quota exceeded."}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        # 5. Save the 3 videos into the Document model so we never hit the API again for this document
        document.youtube_video = videos
        document.save()

        # 6. Return the fresh data
        return Response({
            "source": "youtube_api",
            "search_query_used": search_string,
            "videos": videos
        }, status=status.HTTP_201_CREATED)