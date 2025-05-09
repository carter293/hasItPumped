# Use official Python image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    LOG_LEVEL=INFO

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN adduser --disabled-password --gecos "" appuser

# Create necessary directories
RUN mkdir -p /app/logs /app/data

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY src /app/src
COPY setup.py pyproject.toml .env* ./

# Copy model file
RUN mkdir -p /app/src/solana_token_api/assets
COPY src/solana_token_api/assets/model.ubj /app/src/solana_token_api/assets/

# Make directories writable for app user
RUN chown -R appuser:appuser /app/logs /app/data

# Change to non-root user
USER appuser

# Expose port for the API
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8000/ || exit 1

# Run the application
CMD ["uvicorn", "solana_token_api.main:app", "--host", "0.0.0.0", "--port", "8000"]