# Use an official Python runtime as a base image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install build dependencies for PostgreSQL
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application
COPY . .

# Create required directories
RUN mkdir -p uploads logs

# Make sure the app can write to these directories
RUN chmod -R 777 uploads logs

# Environment variables
ENV FLASK_APP=app.py
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Encryption key will be set in docker-compose or at runtime

# Expose the port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
