import logging
import hashlib
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from apps.users.permissions import HasSufficientCredits
from apps.documents.models import Document
from .models import GeneratedContent
from . import gemini_client
from apps.documents.vector_store import retrieve_relevant_chunks, check_semantic_cache, add_to_semantic_cache
import re
import time 
from django.utils import timezone
from apps.ai_services.models import APILog
from apps.ai_services.utils import log_api_call

logger = logging.getLogger(__name__)

class GenerateAIContentView(APIView):
    permission_classes = [IsAuthenticated, HasSufficientCredits]

    def post(self, request):
        document_id = request.data.get('document_id')
        content_type = request.data.get('content_type')

        user = request.user
        start_time = time.time()

        valid_types = [choice[0] for choice in GeneratedContent.CONTENT_TYPES]
        if not document_id or content_type not in valid_types:
            return Response({"error": "Valid document_id and content_type are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            document = Document.objects.get(id=document_id)
        except Document.DoesNotExist:
            return Response({"error": "Document not found."}, status=status.HTTP_404_NOT_FOUND)

        # =================================================================
        # 1. THE REDIS-FIRST GLOBAL INTERCEPTOR
        # =================================================================
        unique_identifier = document.content_hash
        
        print(f"\n--- 🚀 DEBUG: Starting Generate for type: {content_type} ---")

        if unique_identifier:
            # STEP A: Try to pull EVERYTHING directly from Redis RAM first!
            cached_mega_data = {}
            for c_type in valid_types:
                cached_val = cache.get(f"ai_content_{c_type}_{unique_identifier}")
                if cached_val:
                    cached_mega_data[c_type] = cached_val
            
            # Did we find what they asked for in Redis?
            if content_type in cached_mega_data:
                print(f"--- ⚡ REDIS HIT: Found '{content_type}' in RAM! Bypassing DB and Gemini. ---")
                
                # Copy the Redis data into Account B's local database so their UI works on refresh
                for c_type, ram_data in cached_mega_data.items():
                    GeneratedContent.objects.get_or_create(
                        document=document,
                        content_type=c_type,
                        defaults={'data': ram_data}
                    )
                
                cache.delete(f"doc_content_{document.id}") # Bust local UI cache
                
                return Response({
                    "message": f"{content_type.title()} retrieved instantly from Redis cache for FREE.",
                    "data": cached_mega_data[content_type],
                    "credits_remaining": request.user.credits
                }, status=status.HTTP_200_OK)

            # STEP B: Redis was empty (evicted or restarted). Fallback to the Database Jugaad.
            print("--- 🐌 REDIS MISS: Checking Global Database for the hash... ---")
            global_contents = GeneratedContent.objects.filter(document__content_hash=unique_identifier)
            
            if global_contents.exists():
                requested_data = None
                
                for gc in global_contents:
                    # 1. Create Account B's local copy
                    GeneratedContent.objects.get_or_create(
                        document=document,
                        content_type=gc.content_type,
                        defaults={'data': gc.data}
                    )
                    # 2. HEAL REDIS so the next user gets the lightning-fast Step A!
                    cache.set(f"ai_content_{gc.content_type}_{unique_identifier}", gc.data, timeout=86400)
                    
                    if gc.content_type == content_type:
                        requested_data = gc.data

                if requested_data:
                    print("--- 🗄️ DB HIT: Recovered from DB, healed Redis, bypassed Gemini. ---")
                    cache.delete(f"doc_content_{document.id}")
                    
                    return Response({
                        "message": f"Full document recovered from global database for FREE.",
                        "data": requested_data,
                        "credits_remaining": request.user.credits
                    }, status=status.HTTP_200_OK)

        print("--- ⚠️ GLOBAL MISS: Hash not found anywhere. Falling through to Gemini API... ---")

        user = request.user
        start_time = time.time()
        
        try:
            # Send the document ONCE to get ALL data
            mega_json , token_count= gemini_client.generate_all_learning_assets(document.extracted_text)
            
            # Slice it up and save everything simultaneously!
            for c_type in valid_types:
                if c_type in mega_json:
                    # Save to Database
                    GeneratedContent.objects.update_or_create(
                        document=document, 
                        content_type=c_type,
                        defaults={'data': mega_json[c_type]}
                    )
                    # Save to Redis Cache
                    # specific_cache_key = f"ai_content_{c_type}_{document_id}"
                    specific_cache_key = f"ai_content_{c_type}_{unique_identifier}"
                    cache.set(specific_cache_key, mega_json[c_type], timeout=86400)
            log_api_call(
                user=user,
                service_name="Gemini 2.5 Flash", 
                endpoint_used="generate_all_learning_assets",
                start_time=start_time,
                tokens_used=token_count,
                successful=True
            )
            # Deduct the credit for the heavy lifting
            user.credits -= 5
            user.save(update_fields=['credits'])

            # Bust the UI Reader cache so React instantly sees the new Quiz!
            cache.delete(f"doc_content_{document.id}")

            # Return just the specific piece the frontend requested this time
            return Response({
                "message": f"Full document processed. {content_type.title()} generated successfully.",
                "data": mega_json.get(content_type),
                "credits_remaining": user.credits
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            log_api_call(
                user=user,
                service_name="Gemini 2.5 Flash",
                endpoint_used="generate_all_learning_assets",
                start_time=start_time,
                tokens_used=0, # Failed requests usually don't return accurate token counts
                successful=False
            )
            logger.error(f"Error during mega-generation: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
from .sbert_client import get_similarity_score

class GradeInterviewAnswerView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ideal_answer = request.data.get('ideal_answer')
        user_answer = request.data.get('user_answer')

        if not ideal_answer or not user_answer:
            return Response({"error": "Both ideal_answer and user_answer are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 1. Get the semantic score from SBERT
            score = get_similarity_score(ideal_answer, user_answer)

            # 2. Generate dynamic feedback for the Avatar to speak back
            if score >= 85:
                feedback = "Excellent response! You captured the core concepts perfectly."
            elif score >= 60:
                feedback = "Good attempt. You got the general idea, but missed a few specific details."
            else:
                feedback = "That wasn't quite right. Let's review the notes and try this concept again."

            # 3. Return the payload to the frontend
            return Response({
                "score": score,
                "feedback": feedback,
                "status": "success"
            }, status=status.HTTP_200_OK)

        except RuntimeError as e:
            return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            logger.error(f"Grading error: {e}")
            return Response({"error": "An internal error occurred during grading."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

from apps.documents.vector_store import retrieve_relevant_chunks

class ChatWithPDFView(APIView):
    permission_classes = [IsAuthenticated, HasSufficientCredits]

    def post(self, request):
        document_id = request.data.get('document_id')
        user_question = request.data.get('question')

        if not document_id or not user_question:
            return Response({"error": "document_id and question are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            document = Document.objects.get(id=document_id)
        except Document.DoesNotExist:
            return Response({"error": "Document not found."}, status=status.HTTP_404_NOT_FOUND)

        ChatMessage.objects.create(
            document=document,
            role='user',
            content=user_question
        )

        unique_identifier = document.content_hash if document.content_hash else str(document.id)

        # 1. FIX THE SPACES: Normalize the String
        # This regex replaces any amount of spaces (e.g., "  ") with a single space " "
        clean_question = re.sub(r'\s+', ' ', user_question).lower().strip()
        question_hash = hashlib.md5(clean_question.encode('utf-8')).hexdigest()
        # redis_cache_key = f"chat_{document_id}_{question_hash}"
        redis_cache_key = f"chat_{unique_identifier}_{question_hash}"

        # LAYER 1: Redis Cache (Exact Matches)
        cached_answer = cache.get(redis_cache_key)
        if cached_answer:
            logger.info("Serving from Redis Cache (Exact Match)")
            return Response({"answer": cached_answer, "credits_remaining": request.user.credits}, status=status.HTTP_200_OK)
        
        # LAYER 2: Semantic Cache (Synonym Matches)

        semantic_answer = check_semantic_cache(document.id, clean_question)
        if semantic_answer:
            logger.info("Serving from ChromaDB Semantic Cache (Meaning Match)")
            # Save it to Redis so next time we don't even have to do the math!
            cache.set(redis_cache_key, semantic_answer, timeout=86400)
            return Response({"answer": semantic_answer, "credits_remaining": request.user.credits}, status=status.HTTP_200_OK)

        # LAYER 3: RAG Retrieval + Gemini Generation
        try:
            context_text = retrieve_relevant_chunks(document.id, clean_question, top_k=3,user=request.user)
        except Exception as e:
            return Response({"error": "Failed to search the document database."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if not context_text.strip():
            return Response({"answer": "I couldn't find any relevant information.", "credits_remaining": request.user.credits}, status=status.HTTP_200_OK)
        
        start_time = time.time()
        try:
            answer,tokens = gemini_client.answer_pdf_question(context_text, clean_question)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # SAVE TO BOTH CACHES
        cache.set(redis_cache_key, answer, timeout=86400) # Save to Redis
        add_to_semantic_cache(document.id, clean_question, answer) # Save to ChromaDB

        ChatMessage.objects.create(
            document=document,
            role='ai',
            content=answer
        )
        log_api_call(
            user=request.user,
            service_name="Gemini 2.5 Flash",
            endpoint_used="answer_pdf_question",
            start_time=start_time,
            tokens_used=tokens,
            successful=True
        )

        # Deduct 1 Credit
        user = request.user
        user.credits -= 1
        user.save(update_fields=['credits'])

        return Response({
            "answer": answer,
            "credits_remaining": user.credits
        }, status=status.HTTP_201_CREATED)


class GetDocumentContentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, document_id):
        # 1. Define a unique, predictable Redis key for this specific document
        cache_key = f"doc_content_{document_id}"

        # 2. Check Redis FIRST
        cached_response = cache.get(cache_key)
        if cached_response:
            print("⚡ Serving from Redis Cache!")
            return Response(cached_response, status=status.HTTP_200_OK)

        print("🐌 Serving from Database...")
        # 3. If not in Redis, hit the Database
        try:
            document = Document.objects.get(id=document_id, user=request.user)
        except Document.DoesNotExist:
            return Response({"error": "Document not found or unauthorized."}, status=status.HTTP_404_NOT_FOUND)

        existing_content = GeneratedContent.objects.filter(document=document)

        content_dict = {}
        for item in existing_content:
            content_dict[item.content_type] = item.data

        # Build the final response payload
        response_data = {
            "document_id": str(document.id),
            "file_name": document.file_name,
            "content": content_dict
        }

       # ONLY cache it if the dictionary actually has the generated content inside it!
        if content_dict:
            cache.set(cache_key, response_data, timeout=3600)

        return Response(response_data, status=status.HTTP_200_OK)

from .models import ChatMessage
from .serializers import ChatMessageSerializer
from django.shortcuts import get_object_or_404

class DocumentChatHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, document_id):
        # 1. Security: Ensure the user owns this document
        document = get_object_or_404(Document, id=document_id, user=request.user)
        
        # 2. Fetch all messages for this document
        messages = ChatMessage.objects.filter(document=document)
        
        # 3. Serialize and return
        serializer = ChatMessageSerializer(messages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)