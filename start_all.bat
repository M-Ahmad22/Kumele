@echo off
echo Activating virtual environment...
call .\venv310\Scripts\activate

echo Starting FastAPI server...
start cmd /k "uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

echo Starting Celery Worker...
start cmd /k "celery -A app.workers.celery_app.celery_app worker --loglevel=info"

echo Starting Moderation Celery Worker...
start cmd /k "python -m celery -A app.workers.celery_app.celery_app worker --loglevel=info --pool=solo -Q moderation_queue"

echo Starting Rewards Worker...
start cmd /k "celery -A app.workers.celery_app.celery_app worker -Q rewards_queue --loglevel=info"

echo Starting Celery Beat...
start cmd /k "celery -A app.workers.celery_app.celery_app beat --loglevel=info"

echo Starting Trend Worker...
start cmd /k "python -m app.services.nlp.trend_worker"


echo All services started in separate windows.
