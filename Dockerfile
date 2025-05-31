# =====================================================
# 🐳 DOCKERFILE CONSOLIDADO - COTAI BACKEND
# Suporte completo para Backend + LLM + AI Processing
# =====================================================

# Base image with Python 3.11
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    pkg-config \
    git \
    ffmpeg \
    tesseract-ocr \
    tesseract-ocr-por \
    poppler-utils \
    libreoffice \
    imagemagick \
    ghostscript \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==1.7.1

# Configure Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Set work directory
WORKDIR /app

# Copy Poetry files
COPY pyproject.toml poetry.lock* ./

# =====================================================
# DEVELOPMENT STAGE
# =====================================================
FROM base AS development

# Install all dependencies (including dev dependencies)
RUN poetry install --no-root && rm -rf $POETRY_CACHE_DIR

# Copy application code
COPY . .

# Install the package in development mode
RUN poetry install

# Create directories for logs and data
RUN mkdir -p /app/logs /app/data /app/temp

# Expose ports
EXPOSE 8000
EXPOSE 5555

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command for development (with hot reload)
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# =====================================================
# PRODUCTION STAGE
# =====================================================
FROM base AS production

# Install only production dependencies
RUN poetry install --only=main --no-root && rm -rf $POETRY_CACHE_DIR

# Create non-root user
RUN useradd --create-home --shell /bin/bash --uid 1000 app

# Copy application code
COPY . .

# Install the package in production mode
RUN poetry install --only=main

# Create directories with proper permissions
RUN mkdir -p /app/logs /app/data /app/temp && \
    chown -R app:app /app && \
    chmod -R 755 /app

# Switch to non-root user
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command for production (with Gunicorn)
CMD ["poetry", "run", "gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--access-logfile", "/app/logs/access.log", "--error-logfile", "/app/logs/error.log"]

# =====================================================
# CELERY WORKER STAGE
# =====================================================
FROM production AS celery-worker

# Switch back to root for setup
USER root

# Install additional dependencies for background processing
RUN poetry install --only=main

# Switch back to app user
USER app

# Command for Celery worker
CMD ["poetry", "run", "celery", "-A", "app.tasks.celery_app", "worker", "--loglevel=info", "--concurrency=4"]

# =====================================================
# CELERY BEAT STAGE
# =====================================================
FROM production AS celery-beat

# Switch back to root for setup
USER root

# Install additional dependencies
RUN poetry install --only=main

# Switch back to app user
USER app

# Command for Celery beat scheduler
CMD ["poetry", "run", "celery", "-A", "app.tasks.celery_app", "beat", "--loglevel=info"]

# =====================================================
# LLM PROCESSING STAGE
# =====================================================
FROM base AS llm-processor

# Install additional AI/ML dependencies
RUN pip install \
    torch \
    transformers \
    sentence-transformers \
    langchain \
    ollama \
    && rm -rf /root/.cache/pip

# Install all dependencies including AI packages
RUN poetry install --no-root && rm -rf $POETRY_CACHE_DIR

# Copy application code
COPY . .

# Install the package
RUN poetry install

# Create non-root user
RUN useradd --create-home --shell /bin/bash --uid 1000 app && \
    mkdir -p /app/logs /app/data /app/temp /app/models && \
    chown -R app:app /app

# Switch to non-root user
USER app

# Expose port for LLM API
EXPOSE 8001

# Health check for LLM service
HEALTHCHECK --interval=60s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Command for LLM processing service
CMD ["poetry", "run", "uvicorn", "llm.api:app", "--host", "0.0.0.0", "--port", "8001"]
