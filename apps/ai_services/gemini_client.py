import json
import logging
import google.generativeai as genai
from django.conf import settings

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash', generation_config={"response_mime_type": "application/json"})

def generate_all_learning_assets(full_text):
    """
    Sends the document to Gemini ONCE and generates the Summary, Notes, Flashcards, and Interview Context 
    in a single massive JSON object to drastically save on token input costs.
    """
    prompt = f"""
    You are an expert educational AI . Read the following document and generate five distinct learning assets. 
    You MUST output strictly as a single JSON object with the exact structure below.
    - Generate EXACTLY 5 flashcards.
    - Generate EXACTLY 5 quiz questions.
    - Do NOT generate more or fewer items.
    - Ensure quiz questions are conceptually challenging.
    
    {{
        "summary": {{
            "overview": "A brief 2-3 sentence overview.",
            "key_takeaways": ["Point 1", "Point 2", "Point 3"]
        }},
        "notes": {{
            "sections": [
                {{
                    "title": "Section Heading",
                    "content": "Detailed explanatory text with bullet points.",
                    "visual_aid_type": "mermaid", 
                    "visual_aid_code": "The raw Mermaid code (graph TD...) or markdown table here, without markdown backticks. If none, put 'none'."
                }}
            ]
        }},
        "flashcards": [
            {{"front": "Question or Term", "back": "Answer or Definition"}}
        ],
        "interview": [
            {{"question": "Critical interview question?", "ideal_answer": "The expected perfect answer for AI grading."}}
        ],
        "quiz":[
            {{"question": "A challenging quiz question?", "options": ["A", "B", "C", "D"], "correct_option": "B"}}
        ],
        "search_query":[
            {{"query": "Your task is to generate a highly specific, 3 to 6 word search query that would yield the best educational YouTube video tutorials for this exact topic.DO NOT include quotes, explanations, or extra text. Output ONLY the raw search query."}}
        ]
    }}

    Document: 
    {full_text[:50000]}
    """
    
    try:
        logger.info("Sending Mega-Prompt to Gemini...")
        response = model.generate_content(prompt)
        tokens=response.usage_metadata.total_token_count
        return json.loads(response.text),tokens
    
    except json.JSONDecodeError:
        logger.error("Gemini failed to return valid Mega-JSON.")
        raise ValueError("The AI generated an invalid format. Please try again.")
    except Exception as e:
        logger.error(f"Gemini Generation Error: {e}")
        raise RuntimeError("Failed to generate learning assets from the AI service.")


def answer_pdf_question(context_chunks, user_question):
    """
    Takes the top 3 most relevant chunks from ChromaDB and the user's question, 
    and asks Gemini to answer it strictly based on the provided context.
    """
    # We use a standard model here (no JSON constraint) because chat needs natural text formatting.
    chat_model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    You are a helpful and precise AI learning assistant. Answer the user's question based ONLY on the provided context.
    If the answer is not contained in the context, politely state that you cannot find the exact answer in the document, 
    but you can offer general knowledge if they wish. Do not hallucinate external information as facts from the document.

    Context from the document:
    {context_chunks}

    User's Question:
    {user_question}
    """
    
    try:
        logger.info("Sending RAG Chat request to Gemini...")
        response = chat_model.generate_content(prompt)
        tokens=response.usage_metadata.total_token_count
        return response.text.strip(), tokens
    except Exception as e:
        logger.error(f"Gemini Chat Error: {e}")
        raise RuntimeError("Failed to generate an answer from the AI service.")

def generate_master_text_from_topic(topic_name):
    """
    Generates a comprehensive foundational text for a given topic, 
    acting as a 'Virtual PDF' for the rest of the system to process.
    """
    prompt = f"""
    You are an expert textbook author. Write a highly detailed, comprehensive, and structured 
    educational guide (at least 200 words) strictly about the topic: '{topic_name}'.
    
    Cover the following:
    1. Core concepts and definitions.
    2. Underlying architecture or how it works under the hood.
    3. Real-world use cases and examples.
    4. Advanced features or common pitfalls.
    
    Do not include introductory conversational filler. Output only the educational text.
    """
    
    try:
        logger.info(f"Generating Virtual Document for topic: {topic_name}")
        tokens=response.usage_metadata.total_token_count
        response = model.generate_content(prompt)
        return response.text.strip(),tokens
    except Exception as e:
        logger.error(f"Topic Generation Error: {e}")
        raise RuntimeError("Failed to generate topic content from the AI.")