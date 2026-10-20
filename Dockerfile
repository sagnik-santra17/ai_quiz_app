# ============================================================
# Dockerfile — AI Quiz App backend
# ============================================================
# Build:  docker build -t ai-quiz-app .
# Run:    docker run --env-file .env -p 8000:8000 ai-quiz-app
#
# On Render, $PORT is set automatically. Locally it falls back
# to 8000 via the ${PORT:-8000} default.
# ============================================================

FROM python:3.13-slim

# Prevents Python from writing .pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (cached layer — only rebuilds when requirements change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Run migrations, then start the server.
# Shell form is required so ${PORT:-8000} expands at runtime.
CMD alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips="*"