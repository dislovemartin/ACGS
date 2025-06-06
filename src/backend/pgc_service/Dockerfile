# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install any needed packages specified in requirements.txt
COPY requirements_simple.txt .
RUN pip install --no-cache-dir -r requirements_simple.txt \
    && apt-get update && apt-get install -y curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container at /app
COPY . /app

# Make port 8005 available to the world outside this container
EXPOSE 8005

# Create non-root user
RUN useradd -m appuser
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8005/health || exit 1

# Run main.py when the container launches
# The command should point to app.main:app since main.py is in the app/ directory
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8005", "--reload"]
