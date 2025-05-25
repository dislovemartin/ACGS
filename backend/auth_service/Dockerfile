# backend/auth_service/Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install poetry (or pip if using requirements.txt directly)
# Assuming requirements.txt is used for simplicity here, matching other services
# RUN pip install poetry

# Copy requirements first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt

# Install dependencies
# RUN poetry install --no-root --no-dev
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
# This includes the 'app' directory inside 'auth_service'
COPY ./app /app/app

# Copy shared module (assuming it's one level up and then 'shared')
# This path needs to be correct based on how docker-compose builds this service.
# If docker-compose context is './backend/auth_service', then shared is '../shared'
COPY ../shared /app/shared

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
# The app/main.py should define an 'app' instance of FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
