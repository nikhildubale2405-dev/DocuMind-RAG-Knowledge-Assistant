# Use stable Python 3.11
FROM python:3.11-slim

# Prevent Python from buffering stdout/stderr logs
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies needed for compiling C-extensions (FAISS / PyPDF)
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for Docker layer caching
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend and frontend source directories
COPY backend ./backend
COPY frontend ./frontend

# Ensure vector store data directory exists and is writable
RUN mkdir -p /app/backend/data/vector_store

# Set execution directory to backend
WORKDIR /app/backend

# Expose service port (7860 for Hugging Face Spaces & standard deployments)
EXPOSE 7860

# Container healthcheck using standard library urllib
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7860/health')" || exit 1

# Start FastAPI server via Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
