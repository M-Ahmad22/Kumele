FROM python:3.10-slim

# Prevent python from writing pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y build-essential libpq-dev

# HuggingFace cache directory
ENV TRANSFORMERS_CACHE=/app/hf_cache
RUN mkdir -p /app/hf_cache

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
