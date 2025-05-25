# ACGS/backend/auth_service/Dockerfile
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Install system dependencies if any (e.g., for psycopg2 if not using -binary, or for argon2 build if not wheel)
# RUN apt-get update && apt-get install -y build-essential libffi-dev python3-dev && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip &&     pip install --no-cache-dir -r requirements.txt

# Copy the service-specific application code
COPY ./app /app/app

# Copy the shared library code
COPY ../shared /app/shared

EXPOSE 8000

# Command to run the Uvicorn server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
