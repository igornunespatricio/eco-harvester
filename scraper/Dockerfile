# Scraper Base Image - Python 3.11 Slim
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better docker caching
COPY scraper/requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy scraper code
COPY scraper/ .

COPY utils/storage_client.py /app/src/storage_client.py

# Default command
# CMD ["python", "main.py"]