# Base image
FROM python:3.10-slim

# Env settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY requirements.txt .
COPY constraints.txt .

# Upgrade pip (important for stability)
RUN pip install --upgrade pip

# 🔥 Install dependencies with constraints (KEY STEP)
RUN pip install --no-cache-dir --default-timeout=100 --retries 10 \
    -r requirements.txt \
    -c constraints.txt \
    --index-url https://download.pytorch.org/whl/cpu

# Copy project code
COPY . .

# Create persistent directory
RUN mkdir -p /app/persistent_data

# Expose port
EXPOSE 8000