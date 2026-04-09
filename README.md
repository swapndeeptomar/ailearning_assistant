🚀 AI Learning Assistant – Backend API

An advanced AI-powered Learning Assistant platform backend built using Django, designed to transform static study materials into intelligent, interactive learning experiences.

This system leverages Retrieval-Augmented Generation (RAG), asynchronous processing, and AI integrations to provide features like document-based chat, quiz generation, flashcards, interview preparation, and personalized video recommendations.

📌 Overview

The backend powers a scalable SaaS-based EdTech platform where users can:

Upload PDFs and interact with them using AI
Generate notes, quizzes, and flashcards
Practice interviews with an AI-driven system
Get personalized YouTube learning recommendations
Track performance and manage AI usage via credits

The system is designed using modern backend architecture principles, ensuring scalability, responsiveness, and maintainability.

✨ Key Features

🧠 AI-Powered Learning
Context-aware document chat (RAG-based)
AI-generated summaries, quizzes, and flashcards
Intelligent concept explanations

📄 Asynchronous Document Processing
Heavy tasks (PDF parsing, chunking, embeddings) handled via Celery workers
Ensures non-blocking API performance

🔍 Semantic Search with Vector Embeddings
Uses sentence-transformers to generate embeddings
Enables highly accurate contextual retrieval

💬 Real-Time AI Chat (Streaming)
Implemented using Django Channels + WebSockets
Streams responses token-by-token for real-time UX

🎤 AI Interview System (3D Avatar Ready)
Simulates real interview scenarios
Generates questions using AI
Evaluates responses and provides feedback
Designed to integrate with live 3D avatar interaction

🎥 AI-Based YouTube Recommendations
Extracts concepts using AI
Fetches relevant videos via YouTube API
Enhances multimodal learning experience

💳 Credit-Based Usage System
Tracks API usage
Deducts credits per AI action
Enables cost optimization and SaaS monetization

💰 Payment Integration
Integrated with Razorpay API
Supports premium subscription workflows

📚 API Documentation (OpenAPI)
Auto-generated API docs using drf-spectacular
Interactive Swagger UI for all endpoints
Structured request/response schemas

🛠️ Tech Stack
⚙️ Backend
Django
Django REST Framework

⚡ Async & Real-Time
Celery (background processing)
Redis (message broker + cache)

🧠 AI / ML
Google Gemini API
sentence-transformers (embeddings)
RAG architecture

🗄️ Database
MySQL
☁️ Cloud & Storage
AWS S3 / Cloudinary (file storage)
Vercel (frontend)
Render (backend hosting)

🏗️ System Architecture
The backend follows a layered and distributed architecture:

Frontend (React)
        ↓
Django REST API (Authentication, Business Logic)
        ↓
Celery + Redis (Async Processing Layer)
        ↓
AI Services (Gemini API, Embeddings)
        ↓
Database (MySQL) + Vector Storage
        ↓
Cloud Storage (S3 / Cloudinary)

🔄 Core Workflow
📌 Document Processing Pipeline

User Upload → Django API → Save File
        ↓
Trigger Celery Task
        ↓
Text Extraction → Chunking → Embeddings
        ↓
Store in Vector DB
        ↓
Status update → Ready

💬 Chat (RAG Flow)
User Query → Backend
        ↓
Fetch Relevant Chunks
        ↓
Send to AI (Gemini)
        ↓
Generate Contextual Answer
        ↓
Return Response + Store Chat

🎤 Interview Flow
Start Interview → Generate Questions (AI)
        ↓
User Answers
        ↓
AI Evaluation (Score + Feedback)
        ↓
Store Session + Return Result

🎥 YouTube Recommendation Flow
Extract Keywords (AI)
        ↓
Call YouTube API
        ↓
Fetch Relevant Videos
        ↓
Store + Return to User

📡 API Documentation

Interactive API documentation is available via:

/api/docs/ → Swagger UI
/api/redoc/ → ReDoc

Features:

Request/Response schemas
Authentication support
Live API testing

⚙️ Environment Setup

🔐 Environment Variables
.env (Secrets)
DJANGO_SECRET_KEY=your_secret_key
DEBUG=True
RAZORPAY_KEY_ID=your_key
RAZORPAY_KEY_SECRET=your_secret

.env.local
DB_NAME=learning_assistant
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
REDIS_HOST=localhost

.env.docker
DB_HOST=db
REDIS_HOST=redis

🐳 Running with Docker (Recommended)
docker-compose up --build
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser

💻 Running Locally
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py runserver

# Run Celery (separate terminal)
celery -A learning_assistant worker --loglevel=info
📊 Database Design Highlights
User → Documents (1:M)
Document → Chunks (1:M)
Document → Quiz / Flashcards
User → ChatHistory
User → InterviewSession
User → CreditTransactions

Ensures scalable relational structure with AI outputs

🔥 Technical Highlights
Chunk-based processing (handles large PDFs)
Asynchronous architecture (Celery + Redis)
RAG-based AI system
Real-time streaming (WebSockets)
Credit-based cost control
Modular multi-app Django structure
Production-ready API documentation

🎯 Use Cases
Students for smart learning
Interview preparation platforms
EdTech SaaS products
AI-powered content analysis tools

🚀 Future Enhancements
Full 3D avatar integration for interviews
Voice-based interaction
Multi-language support
Advanced analytics dashboard
Mobile application support

📌 Conclusion

This project demonstrates a real-world implementation of AI + scalable backend architecture in the EdTech domain.

It combines:

AI intelligence
Distributed systems
Real-time communication
SaaS-based design
to create a powerful and future-ready learning platform.
