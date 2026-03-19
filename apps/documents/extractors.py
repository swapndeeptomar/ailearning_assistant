import fitz  # PyMuPDF
import logging

logger = logging.getLogger(__name__)

def extract_text_from_pdf(uploaded_file):
    """
    Reads a PDF directly from Django's memory stream and extracts text.
    """
    try:
        # Ensure the file pointer is at the beginning
        uploaded_file.seek(0)
        file_bytes = uploaded_file.read()
        
        # Open the PDF directly from the byte stream
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        full_text = ""
        
        for page in doc:
            full_text += page.get_text("text") + "\n"
            
        doc.close()
        
        # CRITICAL: Reset the file pointer back to 0 so Django can 
        # actually save the file to the hard drive in the next step!
        uploaded_file.seek(0)
        
        if not full_text.strip():
            return "No readable text found in this document. It might be a scanned image."
            
        return full_text.strip()
        
    except Exception as e:
        logger.error(f"Failed to extract text from PDF: {e}")
        raise ValueError("Could not process the PDF file. Please ensure it is a valid PDF and not corrupted.")
    
def chunk_text(text, chunk_size=300, overlap=50):
    """
    Splits a massive string of text into smaller overlapping chunks.
    - chunk_size: The maximum number of words per chunk.
    - overlap: How many words to overlap so sentences aren't cut completely in half.
    """
    if not text:
        return []

    words = text.split()
    chunks = []
    
    # Step through the text and slice it into overlapping arrays
    for i in range(0, len(words), chunk_size - overlap):
        chunk_segment = " ".join(words[i:i + chunk_size])
        chunks.append(chunk_segment)
        
    return chunks