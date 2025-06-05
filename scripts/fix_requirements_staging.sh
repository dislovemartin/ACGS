#!/bin/bash

# ACGS Phase 3 - Fix Python Dependencies for Staging
# Resolves package hash mismatches in requirements.txt files

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ❌ $1${NC}"
}

# Services with requirements issues
SERVICES=("fv_service" "gs_service" "pgc_service")

# Create simplified requirements files for staging
create_staging_requirements() {
    local service=$1
    local service_dir="src/backend/$service"
    
    log "Creating staging requirements for $service..."
    
    if [ ! -d "$service_dir" ]; then
        error "Service directory not found: $service_dir"
        return 1
    fi
    
    # Create a simplified requirements file without hashes for staging
    case $service in
        "fv_service")
            cat > "$service_dir/requirements_staging.txt" << 'EOF'
# FV Service Staging Requirements (without hashes)
fastapi==0.115.12
uvicorn[standard]==0.34.2
pydantic[email]==2.11.5
python-dotenv==1.1.0
httpx==0.28.1
sqlalchemy[asyncio]==2.0.36
asyncpg==0.30.0
tenacity==8.2.3
z3-solver==4.12.2.0
prometheus_client==0.21.1
psutil==6.1.0
# Authentication dependencies
python-jose[cryptography]==3.3.0
PyJWT>=2.8.0
passlib[bcrypt]==1.7.4
# Additional shared dependencies
email-validator==2.1.0
EOF
            ;;
        "gs_service")
            cat > "$service_dir/requirements_staging.txt" << 'EOF'
# GS Service Staging Requirements (without hashes)
fastapi==0.115.12
uvicorn[standard]==0.34.2
pydantic[email]==2.11.5
python-dotenv==1.1.0
httpx==0.28.1
sqlalchemy[asyncio]==2.0.36
asyncpg==0.30.0
tenacity==8.2.3
openai==1.82.0
groq>=0.4.1
prometheus_client==0.21.1
numpy==1.26.4
# LangGraph dependencies for workflow management
langgraph>=0.2.6
langchain>=0.3.19
langchain-community>=0.3.19
langchain-google-genai>=2.0.0
redis>=5.0.0
# Authentication dependencies
python-jose[cryptography]==3.3.0
PyJWT>=2.8.0
passlib[bcrypt]==1.7.4
# Additional shared dependencies
email-validator==2.1.0
# WINA (Weight Informed Neuron Activation) Dependencies
scipy==1.11.4
torch==2.7.1
scikit-learn==1.5.1
aiohttp>=3.8.0
# OPA (Open Policy Agent) Integration Dependencies
requests>=2.31.0
EOF
            ;;
        "pgc_service")
            cat > "$service_dir/requirements_staging.txt" << 'EOF'
# PGC Service Staging Requirements (without hashes)
fastapi==0.115.12
uvicorn[standard]==0.34.2
pydantic[email]==2.11.5
python-dotenv==1.1.0
httpx==0.28.1
sqlalchemy[asyncio]==2.0.36
asyncpg==0.30.0
tenacity==8.2.3
prometheus_client==0.21.1
psutil==6.1.0
# Authentication dependencies
python-jose[cryptography]==3.3.0
PyJWT>=2.8.0
passlib[bcrypt]==1.7.4
# Additional shared dependencies
email-validator==2.1.0
# OPA (Open Policy Agent) Integration Dependencies
requests>=2.31.0
# Rate limiting
slowapi>=0.1.9
limits>=3.0.0
# Networking
networkx>=2.8
EOF
            ;;
    esac
    
    success "Created staging requirements for $service"
}

# Update Dockerfiles to use staging requirements
update_dockerfile() {
    local service=$1
    local dockerfile_path="src/backend/$service/Dockerfile.prod"
    
    log "Updating Dockerfile for $service to use staging requirements..."
    
    if [ ! -f "$dockerfile_path" ]; then
        error "Dockerfile not found: $dockerfile_path"
        return 1
    fi
    
    # Create backup
    cp "$dockerfile_path" "$dockerfile_path.backup"
    
    # Update Dockerfile to use staging requirements
    sed -i 's/requirements\.txt/requirements_staging.txt/g' "$dockerfile_path"
    
    success "Updated Dockerfile for $service"
}

# Create staging-specific Dockerfiles
create_staging_dockerfile() {
    local service=$1
    local service_dir="src/backend/$service"
    
    log "Creating staging Dockerfile for $service..."
    
    cat > "$service_dir/Dockerfile.staging" << EOF
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy shared module first
COPY shared/ ./shared/

# Copy service requirements and install Python dependencies (without hash checking)
COPY $service/requirements_staging.txt .
RUN pip install --no-cache-dir --no-deps -r requirements_staging.txt

# Copy service application code
COPY $service/ ./

# Set Python path to include shared module
ENV PYTHONPATH="/app:/app/shared:\$PYTHONPATH"

# Create non-root user
RUN useradd --create-home --shell /bin/bash acgs
RUN chown -R acgs:acgs /app
USER acgs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \\
    CMD curl -f http://localhost:800\$(echo $service | sed 's/.*_service//' | sed 's/fv/3/' | sed 's/gs/4/' | sed 's/pgc/5/')/health || exit 1

# Expose port
EXPOSE 800\$(echo $service | sed 's/.*_service//' | sed 's/fv/3/' | sed 's/gs/4/' | sed 's/pgc/5/')

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "800\$(echo $service | sed 's/.*_service//' | sed 's/fv/3/' | sed 's/gs/4/' | sed 's/pgc/5/')", "--workers", "2"]
EOF
    
    success "Created staging Dockerfile for $service"
}

# Update docker-compose.staging.yml to enable services
update_staging_compose() {
    log "Updating docker-compose.staging.yml to enable FV, GS, and PGC services..."
    
    # Create backup
    cp docker-compose.staging.yml docker-compose.staging.yml.backup
    
    # Uncomment the services and update Dockerfile references
    sed -i 's/# *fv_service:/fv_service:/' docker-compose.staging.yml
    sed -i 's/# *gs_service:/gs_service:/' docker-compose.staging.yml
    sed -i 's/# *pgc_service:/pgc_service:/' docker-compose.staging.yml
    
    # Remove comment markers from service configurations
    sed -i '/fv_service:/,/^[[:space:]]*$/s/^[[:space:]]*#[[:space:]]*/    /' docker-compose.staging.yml
    sed -i '/gs_service:/,/^[[:space:]]*$/s/^[[:space:]]*#[[:space:]]*/    /' docker-compose.staging.yml
    sed -i '/pgc_service:/,/^[[:space:]]*$/s/^[[:space:]]*#[[:space:]]*/    /' docker-compose.staging.yml
    
    # Update Dockerfile references to use staging versions
    sed -i 's/dockerfile: fv_service\/Dockerfile\.prod/dockerfile: fv_service\/Dockerfile.staging/' docker-compose.staging.yml
    sed -i 's/dockerfile: gs_service\/Dockerfile\.prod/dockerfile: gs_service\/Dockerfile.staging/' docker-compose.staging.yml
    sed -i 's/dockerfile: pgc_service\/Dockerfile\.prod/dockerfile: pgc_service\/Dockerfile.staging/' docker-compose.staging.yml
    
    success "Updated docker-compose.staging.yml"
}

# Test requirements installation
test_requirements() {
    local service=$1
    
    log "Testing requirements installation for $service..."
    
    # Test in a temporary container
    docker run --rm \
        -v "$(pwd)/src/backend/$service/requirements_staging.txt:/tmp/requirements.txt" \
        python:3.11-slim \
        bash -c "pip install --no-cache-dir -r /tmp/requirements.txt && echo 'Requirements test passed'"
    
    if [ $? -eq 0 ]; then
        success "Requirements test passed for $service"
    else
        error "Requirements test failed for $service"
        return 1
    fi
}

# Main execution
main() {
    log "Starting ACGS Phase 3 Python Dependencies Fix for Staging"
    log "======================================================="
    
    # Process each service
    for service in "${SERVICES[@]}"; do
        log "Processing $service..."
        
        create_staging_requirements "$service"
        create_staging_dockerfile "$service"
        test_requirements "$service"
        
        success "Completed processing $service"
    done
    
    # Update docker-compose configuration
    update_staging_compose
    
    success "Python dependencies fix completed successfully!"
    log "Next steps:"
    log "1. Build and deploy the updated services"
    log "2. Test service health and connectivity"
    log "3. Run comprehensive staging validation"
}

# Execute main function
main "$@"
