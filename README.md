> > **Kumele – AI/ML Service**

A production-grade AI & Machine Learning backend microservice providing:

🔹 Email Support Automation (AI-assisted)

🔹 Translation Service

🔹 Content Moderation (Text + Image)

🔹 Semantic Matching & Recommendations

🔹 AI Operations/Health Monitoring

🔹 Chatbot With Dynamic Knowledge Base

🔹 Discount / Pricing For the Client AI Service

🔹 Prediction Insights Based on AI

🔹 Host Ratting Service AI Based

🔹 Background Task Processing (Celery Workers + Beat)

🔹 Fully containerized deployment (Railway, AWS, Docker)

Built using FastAPI, Celery, PostgreSQL, Redis, Qdrant, Sentence Transformers, and Torch CPU.

**Project Structure**

ML-Service/
│
├── app/
│ ├── api/ # REST API endpoints
│ ├── services/ # Business logic / AI logic
│ ├── workers/ # Celery tasks (moderation, email, etc.)
│ ├── db/ # Database models & session
│ ├── core/ # Config, security, utils
│ └── main.py # FastAPI entrypoint
│
├── models/ # Local ML models (HuggingFace, ST)
│
├── Dockerfile # FastAPI server
├── Dockerfile.worker # Celery worker
├── Dockerfile.beat # Celery beat scheduler
├── Dockerfile.trend # NLP trend worker
├── docker-compose.yml
├── requirements.txt
├── requirements-prod.txt
└── README.md

**Features Overview**

> Email Support Automation (Acelle SMTP) AI-powered processing of incoming support emails + automated replies.
> Content Moderation - Moderates harmful/toxic text or images asynchronously using Celery.
> Matching & Recommendations AI matching using Sentence Transformers embeddings, Cosine similarity, Qdrant / local vector search
> AI Operations / Health Monitoring, Provides container health status for dashboards.
> Chatbot With Dynamic Knowledge Base
> Discount / Pricing For the Client AI Service
> Prediction Insights Based on AI
> Host Ratting Service AI Based

**Docker Deployment**

1. Build API
   docker build -t kumele-api -f Dockerfile .
   docker run -p 8000:8000 kumele-api

2. Worker
   docker build -t kumele-worker -f Dockerfile.worker .
   docker run kumele-worker

3. ModerationWorker
   docker build -t kumele-worker -f Dockerfile.moderation .
   docker run kumele-moderation

4. Celery Beat
   docker build -t kumele-beat -f Dockerfile.beat .
   docker run kumele-beat

5. Trend Worker
   python -m app.services.nlp.trend_worker .
   docker run kumele-trend

   **Railway Deployment**

Build API, Worker, Celery Beat, Redis, Qdrant

**DataBase**

PostgreSQL hosted be NEON

Developed by **MATalogics**  
🌐 https://www.matalogics.com
