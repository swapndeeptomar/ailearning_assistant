import os
import time
import chromadb
from django.conf import settings
from sentence_transformers import SentenceTransformer
import logging
import hashlib
from apps.ai_services.utils import log_api_call

logger = logging.getLogger(__name__)

# 1. Setup ChromaDB to save data persistently on the hard drive (not just in RAM)
VECTOR_DB_DIR = os.path.join(settings.BASE_DIR, 'chroma_db')
os.makedirs(VECTOR_DB_DIR, exist_ok=True)

chroma_client = chromadb.PersistentClient(path=VECTOR_DB_DIR)

# 2. Load the Embedding Model (MiniLM is extremely fast and accurate for document RAG)
# Note: The very first time this runs, it will download ~80MB of weights from HuggingFace.
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def store_chunks_in_vector_db(document_id, text_chunks,user=None):
    """
    Converts text chunks into embeddings and saves them to ChromaDB.
    """
    if not text_chunks:
        return
    
    # 1. Estimate Compute Load
    total_chars = sum(len(chunk) for chunk in text_chunks)
    estimated_tokens = total_chars // 4
    start_time = time.time()
        
    try:
        # We put all chunks into a single master collection, but attach the document_id as metadata 
        # so we can filter searches to only look at the specific PDF the user is asking about.
        collection = chroma_client.get_or_create_collection(name="learning_assistant_docs")
        
        # Convert text strings into lists of floats (Embeddings)
        logger.info(f"Generating embeddings for {len(text_chunks)} chunks...")
        embeddings = embedding_model.encode(text_chunks).tolist()
        
        # Generate unique IDs and metadata for each chunk
        ids = [f"{str(document_id)}_chunk_{i}" for i in range(len(text_chunks))]
        metadatas = [{"document_id": str(document_id), "chunk_index": i} for i in range(len(text_chunks))]
        
        # Insert into Vector DB
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=text_chunks,
            metadatas=metadatas
        )
        logger.info(f"Successfully stored vectors for Document {document_id}")

        log_api_call(
            user=user,
            service_name="Local Embeddings",
            endpoint_used="store_chunks_in_vector_db",
            start_time=start_time,
            tokens_used=estimated_tokens,
            successful=True
        )
        
    except Exception as e:
        log_api_call(
            user=user,
            service_name="Local Embeddings",
            endpoint_used="store_chunks_in_vector_db",
            start_time=start_time,
            tokens_used=estimated_tokens,
            successful=False
        )
        logger.error(f"Vector DB Storage Failed: {e}")
        raise RuntimeError("Failed to store document embeddings in the vector database.")

def retrieve_relevant_chunks(document_id, query_text, top_k=3,user=None):
    """
    Converts a user's question into a vector and finds the most relevant chunks in ChromaDB.
    """
    estimated_tokens = len(query_text) // 4
    start_time = time.time() #

    try:
        collection = chroma_client.get_collection(name="learning_assistant_docs")
        
        # Convert the query into a vector
        query_embedding = embedding_model.encode([query_text]).tolist()
        
        # Search the database, filtering ONLY for the current document
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=top_k,
            where={"document_id": str(document_id)}
        )
        log_api_call(
            user=user,
            service_name="Local Embeddings",
            endpoint_used="retrieve_relevant_chunks",
            start_time=start_time,
            tokens_used=estimated_tokens,
            successful=True
        )
        # Extract the text chunks from the results
        if results['documents'] and len(results['documents'][0]) > 0:
            return " ".join(results['documents'][0])
            
        return ""
        
    except Exception as e:
        #  Log failed vector search
        log_api_call(
            user=user,
            service_name="Local Embeddings",
            endpoint_used="retrieve_relevant_chunks",
            start_time=start_time,
            tokens_used=estimated_tokens,
            successful=False
        )
        logger.error(f"RAG Retrieval Failed: {e}")
        return ""

    import hashlib


def check_semantic_cache(document_id, query_text, distance_threshold=0.3):
    """
    Converts the question to a vector and checks ChromaDB for past questions 
    with the exact same meaning. Lower distance = higher similarity.
    """
    try:
        # We use a separate collection just for cached chats
        cache_collection = chroma_client.get_or_create_collection(name="semantic_chat_cache")
        query_embedding = embedding_model.encode([query_text]).tolist()
        
        results = cache_collection.query(
            query_embeddings=query_embedding,
            n_results=1,
            where={"document_id": str(document_id)}
        )
        
        # ChromaDB returns 'distances'. If distance < 0.3, it's virtually the same question!
        if results['distances'] and len(results['distances'][0]) > 0:
            distance = results['distances'][0][0]
            if distance < distance_threshold:
                logger.info(f"Semantic Cache Hit! Distance: {distance}")
                return results['metadatas'][0][0]['answer']
                
        return None
    except Exception as e:
        logger.error(f"Semantic Cache Error: {e}")
        return None

def add_to_semantic_cache(document_id, query_text, answer):
    """
    Saves a newly answered question into the ChromaDB semantic cache.
    """
    try:
        cache_collection = chroma_client.get_or_create_collection(name="semantic_chat_cache")
        query_embedding = embedding_model.encode([query_text]).tolist()
        
        # Create a unique ID for this Q&A pair
        question_hash = hashlib.md5(query_text.encode('utf-8')).hexdigest()
        chunk_id = f"cache_{document_id}_{question_hash}"
        
        cache_collection.add(
            ids=[chunk_id],
            embeddings=query_embedding,
            documents=[query_text], # Storing the question to match against later
            metadatas=[{"document_id": str(document_id), "answer": answer}] # Storing the answer to return
        )
    except Exception as e:
        logger.error(f"Failed to add to Semantic Cache: {e}")