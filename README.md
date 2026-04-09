# 🚀 AI Learning Assistant – Backend API

[![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> An advanced AI-powered Learning Assistant backend built with **Django** that transforms static study materials into intelligent, interactive learning experiences using **RAG**, asynchronous processing, and modern AI integrations.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [System Architecture](#system-architecture)
- [Core Workflows](#core-workflows)
- [API Documentation](#api-documentation)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Environment Variables](#environment-variables)
  - [Local Setup](#local-setup)
  - [Docker Setup (Recommended)](#docker-setup-recommended)
- [Database Design](#database-design)
- [Technical Highlights](#technical-highlights)
- [Use Cases](#use-cases)
- [Future Enhancements](#future-enhancements)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

This backend powers a scalable **SaaS-based EdTech platform** that enables users to:

- Upload PDFs and interact with them using AI
- Generate intelligent notes, quizzes, and flashcards
- Practice interviews with AI-driven evaluation
- Receive personalized YouTube video recommendations
- Track learning progress and manage AI usage through a credit system

Built with modern backend architecture principles, the system ensures **scalability**, **responsiveness**, and **maintainability**.

---

## ✨ Key Features

### 🧠 AI-Powered Learning
- Context-aware document chat using **Retrieval-Augmented Generation (RAG)**
- AI-generated summaries, quizzes, and flashcards
- Intelligent concept explanations

### 📄 Asynchronous Document Processing
- Heavy tasks (PDF parsing, chunking, embeddings) handled via **Celery** workers
- Non-blocking API responses for better user experience

### 🔍 Semantic Search
- Vector embeddings generated using **sentence-transformers**
- Highly accurate contextual retrieval

### 💬 Real-Time AI Chat
- Streaming responses using **Django Channels + WebSockets**
- Token-by-token streaming for smooth UX

### 🎤 AI Interview System
- Simulates real interview scenarios
- AI-generated questions with response evaluation and feedback
- Ready for integration with 3D avatars

### 🎥 Personalized YouTube Recommendations
- AI concept extraction
- Relevant video suggestions via YouTube API

### 💳 Credit-Based Usage System
- Tracks AI usage and deducts credits
- Enables cost control and SaaS monetization

### 💰 Payment Integration
- Integrated with **Razorpay** for premium subscriptions

---

## 🛠️ Tech Stack

| Layer              | Technologies |
|--------------------|--------------|
| **Backend**        | Django, Django REST Framework |
| **Async & Real-time** | Celery, Redis, Django Channels + WebSockets |
| **AI / ML**        | Google Gemini API, sentence-transformers, RAG Architecture |
| **Database**       | MySQL |
| **Storage**        | AWS S3 / Cloudinary |
| **Documentation**  | drf-spectacular (OpenAPI) |
| **Deployment**     | Render (backend), Vercel (frontend) |

---


---

## 🔄 Core Workflows

### 📌 Document Processing Pipeline
1. User uploads PDF → Django API saves file
2. Celery task triggered
3. Text extraction → Chunking → Embeddings generation
4. Store in vector database → Status updated to "Ready"

### 💬 RAG Chat Flow
1. User query received
2. Relevant chunks retrieved via semantic search
3. Context sent to Gemini API
4. Contextual response generated and streamed back

### 🎤 Interview Flow
1. Interview session starts
2. AI generates domain-specific questions
3. User answers → AI evaluates with score and feedback

### 🎥 YouTube Recommendation Flow
1. AI extracts key concepts
2. YouTube API called for relevant videos
3. Results stored and returned to user

---

## 📡 API Documentation

Interactive API documentation is available at:

- **Swagger UI**: `/api/docs/`
- **ReDoc**: `/api/redoc/`

**Features**:
- Fully structured request/response schemas
- Authentication support
- Live API testing

---

## Getting Started

### Prerequisites

- Python 3.10+
- Docker & Docker Compose (recommended)
- MySQL / Redis

### Environment Variables

Create `.env` file in the root directory with the following:

```env
DJANGO_SECRET_KEY=your_secret_key
DEBUG=True

# Database
DB_NAME=learning_assistant
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306

# Redis
REDIS_HOST=localhost

# Payment
RAZORPAY_KEY_ID=your_key_id
RAZORPAY_KEY_SECRET=your_key_secret

# AI
GEMINI_API_KEY=your_gemini_api_key
```

Local Setup
# 1. Clone the repository
git clone https://github.com/yourusername/ai-learning-assistant-backend.git
cd ai-learning-assistant-backend

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate    # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Apply migrations
python manage.py migrate

# 5. Create superuser (optional)
python manage.py createsuperuser

# 6. Run development server
python manage.py runserver

Run Celery worker (in a separate terminal):
Bashcelery -A learning_assistant worker --loglevel=info
Docker Setup (Recommended)
Bashdocker-compose up --build

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

Database Design Highlights

User → Documents (1:M)
Document → Chunks (1:M)
Document → Quizzes / Flashcards
User → ChatHistory
User → InterviewSession
User → CreditTransactions

Fully relational and optimized for AI-generated content.

🔥 Technical Highlights

Chunk-based processing for large PDFs
Fully asynchronous architecture (Celery + Redis)
Production-ready RAG implementation
Real-time streaming via WebSockets
Credit-based cost management
Modular multi-app Django structure
Auto-generated OpenAPI documentation


Use Cases

Students seeking smart, interactive learning
Interview preparation platforms
EdTech SaaS products
AI-powered content analysis tools


Future Enhancements

Full 3D avatar integration for interviews
Voice-based interaction
Multi-language support
Advanced analytics dashboard
Mobile application backend support


Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

License
This project is licensed under the MIT License - see the LICENSE file for details.
