FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into /app/backend
# This preserves the package structure so relative imports (from . import models) work
COPY . ./backend

# Run uvicorn from /app, targeting the backend package
# Cloud Run injects the PORT environment variable
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
