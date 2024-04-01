# Use the official Python image as the base image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libtiff-dev libjpeg-dev zlib1g-dev libfreetype6-dev \
    liblcms2-dev libopenjp2-7 libtiff5 \
    && rm -rf /var/lib/apt/lists/*  

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the FastAPI application code into the container
COPY . /app

# Expose the port that the FastAPI application will run on
EXPOSE 8000

# Command to run the FastAPI application with uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
