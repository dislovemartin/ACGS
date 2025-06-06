# Use an official Python runtime as the base image
FROM python:3.10-slim

# Install system-level dependencies, including git
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /dgm

# Copy the entire repository into the container
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user
RUN useradd -m appuser && mkdir -p /home/appuser
USER appuser

# Simple health check just ensures the container is alive
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD [ -f /tmp/healthy ] || exit 1

# Keep the container running by default
CMD ["tail", "-f", "/dev/null"]