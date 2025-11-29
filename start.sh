#!/usr/bin/env bash
set -e

# -----------------------------
# Activate virtual environment
# -----------------------------
echo "🔄 Activating virtual environment..."
source ./venv310/Scripts/activate

# -----------------------------
# Ensure models folder exists
# -----------------------------
mkdir -p models
echo "📁 Using local models from: models/"

# -----------------------------
# Start FastAPI
# -----------------------------
echo "🚀 Starting FastAPI (Uvicorn)..."
uvicorn app.main:app \
    --host 127.0.0.1 \
    --port 8000 \
    --reload &
API_PID=$!

# -----------------------------
# Start Celery Worker
# -----------------------------
echo "⚙️ Starting Celery Worker..."
celery -A app.workers.celery_app.celery_app worker \
    --loglevel=info &
WORKER_PID=$!

# -----------------------------
# Start Celery Beat
# -----------------------------
echo "⏱ Starting Celery Beat..."
celery -A app.workers.celery_app.celery_app beat \
    --loglevel=info &
BEAT_PID=$!

# -----------------------------
# Start Trend Worker
# -----------------------------
echo "📊 Starting Trend Worker..."
python -m app.services.nlp.trend_worker &
TREND_PID=$!

# -----------------------------
# Keep all processes alive
# -----------------------------
echo "✅ All services started successfully!"
echo "API PID: $API_PID"
echo "Worker PID: $WORKER_PID"
echo "Beat PID: $BEAT_PID"
echo "Trend PID: $TREND_PID"

wait $API_PID $WORKER_PID $BEAT_PID $TREND_PID
