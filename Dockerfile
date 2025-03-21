# Use an official Python runtime as a base image
FROM python:3.9-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Install build dependencies for psycopg2
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt /app/

# Install pip dependencies globally
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . /app/

# The React build files are already in the static/react directory
# No need to copy from react-src/build

# Expose port 5000 for Flask (container-side)
EXPOSE 5000

# Run the Flask application
CMD ["python", "app.py"]
