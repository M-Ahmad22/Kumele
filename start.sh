#!/usr/bin/env bash
set -e

echo "🔄 Activating virtual environment..."
# Works for Linux/Mac virtual env
source venv310/bin/activate

echo "📁 Ensuring models directory exists..."
mkdir -p models

########################################
# 🚀 Start FastAPI
########################################
echo "🚀 Starting FastAPI Server..."
uvicorn app.main:app \
    --host 127.0.0.1 \
    --port 8000 \
    --reload &
API_PID=$!

########################################
# ⚙️ Start Celery Worker (General)
########################################
echo "⚙️ Starting Celery Worker..."
celery -A app.workers.celery_app.celery_app worker \
    --loglevel=info &
WORKER_PID=$!

########################################
# 🔥 Start Moderation Celery Worker
########################################
echo "🧠 Starting Moderation Celery Worker (solo mode)..."
python -m celery -A app.workers.celery_app.celery_app worker \
    --loglevel=info \
    --pool=solo \
    -Q moderation_queue &
MOD_WORKER_PID=$!

########################################
# ⏱ Start Celery Beat
########################################
echo "⏱ Starting Celery Beat..."
celery -A app.workers.celery_app.celery_app beat \
    --loglevel=info &
BEAT_PID=$!

########################################
# 📊 NLP Trend Worker
########################################
echo "📊 Starting Trend Worker..."
python -m app.services.nlp.trend_worker &
TREND_PID=$!

########################################
# 🎉 Summary
########################################
echo ""
echo "==============================================="
echo "✅ All services started successfully!"
echo "-----------------------------------------------"
echo "FastAPI PID:                $API_PID"
echo "Celery Worker PID:          $WORKER_PID"
echo "Moderation Worker PID:      $MOD_WORKER_PID"
echo "Celery Beat PID:            $BEAT_PID"
echo "Trend Worker PID:           $TREND_PID"
echo "==============================================="
echo ""

# Keep script alive
wait $API_PID $WORKER_PID $MOD_WORKER_PID $BEAT_PID $TREND_PID
