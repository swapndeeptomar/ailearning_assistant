# Use a stable Python 3.10 slim image
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .

# Step 1: remove torch line from requirements dynamically
RUN grep -v "torch" requirements.txt > req.txt

# Step 2: install CPU torch FIRST
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.5.1

# Step 3: install rest dependencies
RUN pip install --no-cache-dir -r req.txt

# Copy project
COPY . .

# Create persistent directory
RUN mkdir -p /app/persistent_data

EXPOSE 8000