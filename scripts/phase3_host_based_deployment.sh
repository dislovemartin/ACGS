#!/bin/bash

# ACGS Phase 3 Host-Based Deployment Script
# Alternative deployment strategy to bypass Docker cgroup issues
# Deploys services directly on host system for development and testing

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_BASE_DIR="$PROJECT_ROOT/venvs"
LOG_DIR="$PROJECT_ROOT/logs/host_deployment"
PID_DIR="$PROJECT_ROOT/pids"

# Service configuration
declare -A SERVICES=(
    ["ac_service"]="8011"
    ["integrity_service"]="8012"
    ["fv_service"]="8013"
    ["gs_service"]="8014"
    ["pgc_service"]="8015"
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS: $1${NC}"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Create necessary directories
setup_directories() {
    log "Setting up deployment directories..."
    mkdir -p "$VENV_BASE_DIR" "$LOG_DIR" "$PID_DIR"
    success "Directories created successfully"
}

# Check system requirements
check_system_requirements() {
    log "Checking system requirements..."
    
    # Check Python 3.11
    if ! command -v python3.11 &> /dev/null; then
        error "Python 3.11 not found. Installing..."
        sudo apt update
        sudo apt install -y python3.11 python3.11-venv python3.11-dev
    fi
    
    # Check PostgreSQL
    if ! command -v psql &> /dev/null; then
        error "PostgreSQL not found. Installing..."
        sudo apt update
        sudo apt install -y postgresql postgresql-contrib
    fi
    
    # Check Redis
    if ! command -v redis-cli &> /dev/null; then
        error "Redis not found. Installing..."
        sudo apt update
        sudo apt install -y redis-server
    fi
    
    success "System requirements validated"
}

# Setup PostgreSQL database
setup_postgresql() {
    log "Setting up PostgreSQL database..."
    
    # Start PostgreSQL service
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
    
    # Create database and user
    sudo -u postgres psql -c "CREATE DATABASE acgs_staging;" 2>/dev/null || true
    sudo -u postgres psql -c "CREATE USER acgs_user WITH PASSWORD 'acgs_staging_secure_password_2024';" 2>/dev/null || true
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE acgs_staging TO acgs_user;" 2>/dev/null || true
    
    # Update pg_hba.conf for local connections
    PG_VERSION=$(sudo -u postgres psql -t -c "SELECT version();" | grep -oP '\d+\.\d+' | head -1)
    PG_HBA_FILE="/etc/postgresql/$PG_VERSION/main/pg_hba.conf"
    
    if [ -f "$PG_HBA_FILE" ]; then
        sudo sed -i 's/local   all             all                                     peer/local   all             all                                     md5/' "$PG_HBA_FILE"
        sudo systemctl restart postgresql
    fi
    
    success "PostgreSQL configured successfully"
}

# Setup Redis
setup_redis() {
    log "Setting up Redis..."
    
    # Start Redis service
    sudo systemctl start redis-server
    sudo systemctl enable redis-server
    
    # Configure Redis for ACGS
    sudo tee /etc/redis/redis-acgs.conf > /dev/null <<EOF
port 6379
bind 127.0.0.1
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
EOF
    
    success "Redis configured successfully"
}

# Create virtual environment for a service
create_service_venv() {
    local service_name=$1
    local venv_path="$VENV_BASE_DIR/$service_name"
    
    log "Creating virtual environment for $service_name..."
    
    if [ -d "$venv_path" ]; then
        warning "Virtual environment for $service_name already exists, recreating..."
        rm -rf "$venv_path"
    fi
    
    python3.11 -m venv "$venv_path"
    source "$venv_path/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    local req_file="$PROJECT_ROOT/src/backend/$service_name/requirements.txt"
    if [ -f "$req_file" ]; then
        pip install -r "$req_file"
    else
        warning "Requirements file not found for $service_name: $req_file"
    fi
    
    deactivate
    success "Virtual environment created for $service_name"
}

# Setup all service virtual environments
setup_service_environments() {
    log "Setting up service virtual environments..."
    
    for service in "${!SERVICES[@]}"; do
        create_service_venv "$service"
    done
    
    success "All service environments configured"
}

# Start a service
start_service() {
    local service_name=$1
    local port=${SERVICES[$service_name]}
    local venv_path="$VENV_BASE_DIR/$service_name"
    local service_dir="$PROJECT_ROOT/src/backend/$service_name"
    local log_file="$LOG_DIR/${service_name}.log"
    local pid_file="$PID_DIR/${service_name}.pid"
    
    log "Starting $service_name on port $port..."
    
    # Check if service is already running
    if [ -f "$pid_file" ] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
        warning "$service_name is already running (PID: $(cat "$pid_file"))"
        return 0
    fi
    
    # Source environment variables
    if [ -f "$PROJECT_ROOT/.env.staging" ]; then
        set -a
        source "$PROJECT_ROOT/.env.staging"
        set +a
    fi
    
    # Start the service
    cd "$service_dir"
    source "$venv_path/bin/activate"
    
    # Start service in background
    nohup python -m uvicorn main:app --host 0.0.0.0 --port "$port" > "$log_file" 2>&1 &
    local service_pid=$!
    
    # Save PID
    echo "$service_pid" > "$pid_file"
    
    deactivate
    
    # Wait a moment and check if service started successfully
    sleep 3
    if kill -0 "$service_pid" 2>/dev/null; then
        success "$service_name started successfully (PID: $service_pid)"
    else
        error "$service_name failed to start. Check log: $log_file"
        return 1
    fi
}

# Stop a service
stop_service() {
    local service_name=$1
    local pid_file="$PID_DIR/${service_name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            log "Stopping $service_name (PID: $pid)..."
            kill "$pid"
            rm -f "$pid_file"
            success "$service_name stopped successfully"
        else
            warning "$service_name was not running"
            rm -f "$pid_file"
        fi
    else
        warning "No PID file found for $service_name"
    fi
}

# Check service health
check_service_health() {
    local service_name=$1
    local port=${SERVICES[$service_name]}
    
    log "Checking health of $service_name on port $port..."
    
    if curl -f -s "http://localhost:$port/health" > /dev/null; then
        success "$service_name is healthy"
        return 0
    else
        error "$service_name health check failed"
        return 1
    fi
}

# Deploy all services
deploy_services() {
    log "Deploying all ACGS services..."
    
    # Start services in dependency order
    local service_order=("ac_service" "integrity_service" "fv_service" "gs_service" "pgc_service")
    
    for service in "${service_order[@]}"; do
        start_service "$service"
        sleep 5  # Wait between service starts
    done
    
    success "All services deployment initiated"
}

# Validate deployment
validate_deployment() {
    log "Validating deployment..."
    
    local healthy_services=0
    local total_services=${#SERVICES[@]}
    
    for service in "${!SERVICES[@]}"; do
        if check_service_health "$service"; then
            ((healthy_services++))
        fi
    done
    
    log "Health check results: $healthy_services/$total_services services healthy"
    
    if [ "$healthy_services" -eq "$total_services" ]; then
        success "🎉 All services are healthy! Deployment successful!"
        return 0
    else
        error "⚠️  Some services are unhealthy. Check logs in $LOG_DIR"
        return 1
    fi
}

# Stop all services
stop_all_services() {
    log "Stopping all services..."
    
    for service in "${!SERVICES[@]}"; do
        stop_service "$service"
    done
    
    success "All services stopped"
}

# Show service status
show_status() {
    log "ACGS Services Status:"
    echo "====================="
    
    for service in "${!SERVICES[@]}"; do
        local port=${SERVICES[$service]}
        local pid_file="$PID_DIR/${service}.pid"
        
        if [ -f "$pid_file" ] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
            local pid=$(cat "$pid_file")
            if check_service_health "$service" 2>/dev/null; then
                echo -e "✅ $service (port $port, PID $pid) - ${GREEN}HEALTHY${NC}"
            else
                echo -e "⚠️  $service (port $port, PID $pid) - ${YELLOW}RUNNING BUT UNHEALTHY${NC}"
            fi
        else
            echo -e "❌ $service (port $port) - ${RED}NOT RUNNING${NC}"
        fi
    done
}

# Main function
main() {
    case "${1:-deploy}" in
        "deploy")
            log "🚀 Starting ACGS Phase 3 Host-Based Deployment"
            setup_directories
            check_system_requirements
            setup_postgresql
            setup_redis
            setup_service_environments
            deploy_services
            sleep 10  # Wait for services to fully start
            validate_deployment
            ;;
        "stop")
            stop_all_services
            ;;
        "status")
            show_status
            ;;
        "restart")
            stop_all_services
            sleep 5
            deploy_services
            sleep 10
            validate_deployment
            ;;
        *)
            echo "Usage: $0 {deploy|stop|status|restart}"
            echo "  deploy  - Deploy all services"
            echo "  stop    - Stop all services"
            echo "  status  - Show service status"
            echo "  restart - Restart all services"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
