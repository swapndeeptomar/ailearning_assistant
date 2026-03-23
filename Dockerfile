FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
COPY constraints.txt .

RUN pip install --upgrade pip

RUN pip install --no-cache-dir --default-timeout=100 --retries 10 \
    -r requirements.txt \
    -c constraints.txt \
    --extra-index-url https://download.pytorch.org/whl/cpu

COPY . .

RUN mkdir -p /app/persistent_data

EXPOSE 8000