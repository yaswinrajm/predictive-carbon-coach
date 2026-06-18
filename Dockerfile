# Use an official, lightweight, secured runtime layer
FROM python:3.11-slim

# Set optimization and security flags
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

# Copy dependency mappings first to optimize image layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user for security hardening
RUN adduser --disabled-password --gecos "" --no-create-home appuser

# Structural code copy
COPY src/ ./src/

# Set ownership and switch to non-root user
RUN chown -R appuser:appuser /app
USER appuser

# Expose standard port mapping for Cloud Run container routing
EXPOSE 8080

# Spin up high-performance production server layer bound to internal interface
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]