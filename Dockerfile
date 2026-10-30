<<<<<<< HEAD
# Use stable Python 3.11
FROM python:3.11-slim

# Prevent Python from buffering stdout/stderr logs
=======
# Use stable Python (NOT 3.14 — breaks many deps)
FROM python:3.11-slim

# Prevent Python from buffering logs
>>>>>>> cc18f597ab75b4d6f338b20c1e80de7658dc5d46
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

<<<<<<< HEAD
# Install system dependencies needed for compiling C-extensions (FAISS / PyPDF)
=======
# Install system dependencies (needed for some ML libs)
>>>>>>> cc18f597ab75b4d6f338b20c1e80de7658dc5d46
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

<<<<<<< HEAD
# Copy requirements first for Docker layer caching
=======
# Copy requirements first (for caching)
>>>>>>> cc18f597ab75b4d6f338b20c1e80de7658dc5d46
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

<<<<<<< HEAD
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
=======
# Copy full project
COPY backend ./backend
COPY frontend ./frontend

# Move to backend folder
WORKDIR /app/backend

# Hugging Face Spaces uses port 7860
EXPOSE 7860

# Start FastAPI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
>>>>>>> cc18f597ab75b4d6f338b20c1e80de7658dc5d46
