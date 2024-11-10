# Use Python slim base image
FROM python:3.11-slim
RUN apt-get update
# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Flask application code into the container
COPY ./ /app/

# Exposing port
EXPOSE 5000

# Copy approutes folder into the container
COPY approutes /app/approutes

# Run Gunicorn with 6 workers
CMD ["gunicorn", "-k", "eventlet", "-w", "6", "--bind", "0.0.0.0:5000", "main:app"]







