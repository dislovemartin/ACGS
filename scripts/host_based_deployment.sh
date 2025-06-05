#!/bin/bash
# Host-based ACGS deployment fallback

set -e

echo "🚀 Starting host-based ACGS deployment"

# Function to check if service is running
check_service() {
    local service_name=$1
    local port=$2
    
    if curl -f -s "http://localhost:$port/health" > /dev/null 2>&1; then
        echo "✅ $service_name is running on port $port"
        return 0
    else
        echo "❌ $service_name is not running on port $port"
        return 1
    fi
}

# Start PostgreSQL if not running
if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "Starting PostgreSQL..."
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
fi

# Start Redis if not running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "Starting Redis..."
    sudo systemctl start redis-server
    sudo systemctl enable redis-server
fi

# Set up Python virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -r src/backend/shared/requirements.txt

# Run database migrations
echo "Running database migrations..."
cd migrations
alembic upgrade head
cd ..

echo "✅ Host-based deployment setup completed"
echo "Note: Services need to be started manually in separate terminals"
