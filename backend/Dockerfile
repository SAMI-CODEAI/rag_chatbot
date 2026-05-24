FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Ensure data directories exist and set permissions
RUN mkdir -p uploads chroma_db && chmod 777 uploads chroma_db

EXPOSE 8000

# Metadata
LABEL maintainer="Antigravity Team"
LABEL version="1.0"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
