# ACGS/backend/ac_service/Dockerfile
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Install system dependencies if any (e.g., for psycopg2 if not using -binary)
# RUN apt-get update && apt-get install -y ... && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the service-specific application code
COPY ./app /app/app

# Copy the shared library code
# The Docker context for this build should be the ACGS project root
# So, ../shared will correctly point to the shared directory.
COPY ../shared /app/shared

EXPOSE 8001

# Command to run the Uvicorn server for the FastAPI application
# Ensure the module path 'app.main:app' is correct relative to WORKDIR
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
