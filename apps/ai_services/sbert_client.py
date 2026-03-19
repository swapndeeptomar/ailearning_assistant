import time
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Using the updated Router API endpoint you provided!
API_URL = "https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2/pipeline/sentence-similarity"
headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"}

def get_similarity_score(ideal_answer, user_answer):
    """
    Sends the ideal answer and the user's spoken/typed answer to Hugging Face.
    Handles the 503 'Model Loading' state gracefully by waiting and retrying.
    """
    payload = {
        "inputs": {
            "source_sentence": ideal_answer,
            "sentences": [user_answer]
        }
    }
    
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            # We increased the timeout slightly just in case the network is slow
            response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
            
            # 1. Handle the "Sleeping Model" 503 Error
            if response.status_code == 503:
                error_data = response.json()
                if "estimated_time" in error_data:
                    wait_time = error_data.get("estimated_time", 15)
                    logger.warning(f"Hugging Face model is sleeping. Waiting {wait_time} seconds to wake it up (Attempt {attempt + 1}/{max_retries})...")
                    time.sleep(wait_time) # Pause execution, then loop back up and try again!
                    continue
            
            # 2. If it's any other error (like a 401 Unauthorized), crash normally
            response.raise_for_status()
            
            # 3. Success! Parse the score
            scores = response.json()
            percentage_score = round(scores[0] * 100, 2)
            return percentage_score
            
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1: # Only throw the error if we've used up all our retries
                logger.error(f"Hugging Face API Error: {e}")
                raise RuntimeError("Failed to connect to the grading engine after multiple attempts.")
        except (IndexError, TypeError, KeyError) as e:
            logger.error(f"Unexpected response format from Hugging Face: {response.text}")
            raise ValueError("The grading engine returned an invalid response format.")
            
    raise RuntimeError("Model took too long to load. Please try again.")