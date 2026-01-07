FROM python:3.12-slim

# Install system dependencies for image processing
RUN apt-get update && apt-get install -y \
    gcc \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libtiff-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory for mapping file
RUN mkdir -p /app/data

# Create non-root user
RUN useradd -m -u 1000 mediaarr && chown -R mediaarr:mediaarr /app
USER mediaarr

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/', timeout=2)" || exit 1

# Run the application
CMD ["python", "app.py"]
