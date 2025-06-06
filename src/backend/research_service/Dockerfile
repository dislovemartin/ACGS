FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Note: shared modules will be mounted as volume at runtime

# Set Python path to include shared modules
ENV PYTHONPATH=/app/shared:/app:$PYTHONPATH

# Create directories for research data
RUN mkdir -p /app/research_data /app/experiment_artifacts /app/analysis_results

# Create non-root user
RUN useradd -m appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8007

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8007/health || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8007", "--reload"]
