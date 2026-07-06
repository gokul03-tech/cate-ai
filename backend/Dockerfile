# =============================================================================
# Backend Dockerfile — Python 3.11 + Tesseract OCR + spaCy
# =============================================================================

FROM python:3.11-slim

# Build arguments
ARG DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Install system dependencies including Tesseract OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Tesseract OCR
    tesseract-ocr \
    tesseract-ocr-eng \
    # PDF and image processing
    libpoppler-cpp-dev \
    poppler-utils \
    libmagic1 \
    # Network tools for healthchecks
    curl \
    # Build tools
    gcc \
    g++ \
    build-essential \
    libssl-dev \
    libffi-dev \
    # Clean up
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Copy and install Python dependencies (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy English model
RUN python -m spacy download en_core_web_sm

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads reports logs .cache

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV TRANSFORMERS_CACHE=/app/.cache
ENV HF_HOME=/app/.cache

# Expose port
EXPOSE 8000

# Start with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
