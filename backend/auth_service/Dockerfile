# backend/auth_service/Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install poetry (or pip if using requirements.txt directly)
# Assuming requirements.txt is used for simplicity here, matching other services
# RUN pip install poetry

# Copy requirements first to leverage Docker cache
COPY ./requirements_simple.txt /app/requirements.txt

# Install dependencies
# RUN poetry install --no-root --no-dev
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY . /app

# Shared module is mounted as a volume at runtime via docker-compose
# No need to copy during build

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
# The main.py defines an 'app' instance of FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
