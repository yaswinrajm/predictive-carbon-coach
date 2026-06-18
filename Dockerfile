# Use an official, lightweight, secured runtime layer
FROM python:3.11-slim

# Set optimization flags for high-throughput API scaling
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Copy dependency mappings first to optimize image layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Structural code copy
COPY src/ ./src/

# Expose standard port mapping for Cloud Run container routing
EXPOSE 8080

# Spin up high-performance production server layer bound to internal interface
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]