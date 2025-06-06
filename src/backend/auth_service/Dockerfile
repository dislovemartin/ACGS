# backend/auth_service/Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install any needed packages specified in requirements.txt
COPY ./requirements_simple.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && apt-get update && apt-get install -y curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the application code into the container
COPY . /app

# Shared module is mounted as a volume at runtime via docker-compose
# No need to copy during build

# Expose the port the app runs on
EXPOSE 8000

# Add non-root user for security
RUN useradd -m appuser
USER appuser

# Health check for the service
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command to run the application
# The main.py in app/ directory defines an 'app' instance of FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]