# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY news_agent_copy.py news_agent.py
COPY static/ static/

# Expose port (Railway will override with PORT env var)
EXPOSE 8000

# Set environment variable for production
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "news_agent.py"]
