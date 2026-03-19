# Use a stable Python 3.10 slim image
FROM python:3.10-slim

# Prevent Python from writing pyc files and enable real-time logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies for SBERT, ChromaDB, and MySQL
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- AI MODEL PRE-DOWNLOAD ---
# This ensures the SBERT model is baked into the image layer
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy the rest of the application
COPY . .

# Create the directory for persistent data (ChromaDB)
RUN mkdir -p /app/persistent_data

# The actual command is handled in docker-compose.yml
EXPOSE 8000