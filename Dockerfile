# Use an official Python runtime as a base image
FROM python:3.9-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Install build dependencies (if needed) and pip dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the application code
COPY . /app/

# Expose port 5000 for Flask
EXPOSE 5000

# Run the Flask application
CMD ["python", "app.py"]
