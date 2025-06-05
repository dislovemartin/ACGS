# backend/auth_service/Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install any needed packages specified in requirements.txt
COPY ./requirements_simple.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY . /app

# Shared module is mounted as a volume at runtime via docker-compose
# No need to copy during build

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
# The main.py in app/ directory defines an 'app' instance of FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]