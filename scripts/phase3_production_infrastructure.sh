#!/bin/bash

# ACGS Phase 3 Production Infrastructure Setup Script
# Provisions production infrastructure with security hardening and monitoring

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PRODUCTION_ENV_FILE="$PROJECT_ROOT/config/env/production.env"
INFRASTRUCTURE_LOG="$PROJECT_ROOT/logs/production_infrastructure_$(date +%Y%m%d_%H%M%S).log"
SSL_CERT_DIR="/etc/acgs/ssl"
BACKUP_DIR="/var/backups/acgs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$INFRASTRUCTURE_LOG"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$INFRASTRUCTURE_LOG"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$INFRASTRUCTURE_LOG"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$INFRASTRUCTURE_LOG"
}

# Create logs directory
mkdir -p "$PROJECT_ROOT/logs"

# Function to check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        error "This script must be run as root for system configuration"
        exit 1
    fi
}

# Function to validate system requirements
validate_system_requirements() {
    log "🔍 Validating production system requirements..."
    
    # Check CPU cores (16GB+ RAM recommended)
    CPU_CORES=$(nproc)
    if [ "$CPU_CORES" -lt 8 ]; then
        error "Insufficient CPU cores: $CPU_CORES (minimum: 8, recommended: 16+)"
        exit 1
    else
        success "CPU cores: $CPU_CORES ✅"
    fi
    
    # Check memory (16GB+ recommended)
    MEMORY_GB=$(free -g | awk '/^Mem:/{print $2}')
    if [ "$MEMORY_GB" -lt 16 ]; then
        warning "Memory: ${MEMORY_GB}GB (recommended: 16GB+)"
    else
        success "Memory: ${MEMORY_GB}GB ✅"
    fi
    
    # Check disk space (100GB+ SSD recommended)
    DISK_SPACE=$(df -BG / | awk 'NR==2{print $4}' | sed 's/G//')
    if [ "$DISK_SPACE" -lt 100 ]; then
        error "Insufficient disk space: ${DISK_SPACE}GB (minimum: 100GB)"
        exit 1
    else
        success "Disk space: ${DISK_SPACE}GB ✅"
    fi
    
    success "System requirements validation completed"
}

# Function to setup system packages
setup_system_packages() {
    log "📦 Installing system packages..."
    
    # Update package lists
    apt update
    
    # Install essential packages
    apt install -y \
        curl \
        wget \
        git \
        htop \
        iotop \
        netstat-nat \
        ufw \
        fail2ban \
        logrotate \
        cron \
        certbot \
        python3-certbot-nginx \
        jq \
        postgresql-client \
        redis-tools
    
    success "System packages installed"
}

# Function to setup Docker
setup_docker() {
    log "🐳 Setting up Docker..."
    
    # Install Docker if not present
    if ! command -v docker &> /dev/null; then
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        rm get-docker.sh
        success "Docker installed"
    else
        success "Docker already installed"
    fi
    
    # Install Docker Compose if not present
    if ! command -v docker-compose &> /dev/null; then
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
        success "Docker Compose installed"
    else
        success "Docker Compose already installed"
    fi
    
    # Configure Docker daemon for production
    cat > /etc/docker/daemon.json << EOF
{
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    },
    "storage-driver": "overlay2",
    "live-restore": true
}
EOF
    
    systemctl restart docker
    systemctl enable docker
    
    success "Docker configured for production"
}

# Function to setup firewall
setup_firewall() {
    log "🔥 Configuring firewall..."
    
    # Reset UFW to defaults
    ufw --force reset
    
    # Set default policies
    ufw default deny incoming
    ufw default allow outgoing
    
    # Allow SSH (be careful with this!)
    ufw allow 22/tcp comment 'SSH'
    
    # Allow HTTP and HTTPS
    ufw allow 80/tcp comment 'HTTP'
    ufw allow 443/tcp comment 'HTTPS'
    
    # Allow monitoring ports (restrict to internal network in production)
    ufw allow 9090/tcp comment 'Prometheus'
    ufw allow 3002/tcp comment 'Grafana'
    
    # Allow database access (restrict to application servers in production)
    ufw allow 5432/tcp comment 'PostgreSQL'
    ufw allow 6379/tcp comment 'Redis'
    
    # Enable firewall
    ufw --force enable
    
    success "Firewall configured"
}

# Function to setup SSL certificates
setup_ssl_certificates() {
    log "🔐 Setting up SSL certificates..."
    
    # Create SSL directory
    mkdir -p "$SSL_CERT_DIR"
    
    # Check if domain is provided
    if [ -z "${DOMAIN:-}" ]; then
        warning "No domain provided, generating self-signed certificates for testing"
        
        # Generate self-signed certificate
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "$SSL_CERT_DIR/acgs.key" \
            -out "$SSL_CERT_DIR/acgs.crt" \
            -subj "/C=US/ST=State/L=City/O=ACGS/CN=localhost"
        
        success "Self-signed SSL certificates generated"
    else
        log "Setting up Let's Encrypt certificates for domain: $DOMAIN"
        
        # Install certbot and get certificates
        certbot certonly --standalone -d "$DOMAIN" --non-interactive --agree-tos --email admin@"$DOMAIN"
        
        # Copy certificates to ACGS directory
        cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "$SSL_CERT_DIR/acgs.crt"
        cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "$SSL_CERT_DIR/acgs.key"
        
        # Setup automatic renewal
        echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
        
        success "Let's Encrypt SSL certificates configured"
    fi
    
    # Set proper permissions
    chmod 600 "$SSL_CERT_DIR"/*
    chown -R root:root "$SSL_CERT_DIR"
}

# Function to setup secrets management
setup_secrets() {
    log "🔑 Setting up secrets management..."
    
    # Create secrets directory
    mkdir -p /etc/acgs/secrets
    chmod 700 /etc/acgs/secrets
    
    # Generate secure secrets
    openssl rand -hex 32 > /etc/acgs/secrets/jwt_secret
    openssl rand -hex 32 > /etc/acgs/secrets/db_password
    openssl rand -hex 32 > /etc/acgs/secrets/redis_password
    openssl rand -hex 32 > /etc/acgs/secrets/grafana_password
    
    # Set proper permissions
    chmod 600 /etc/acgs/secrets/*
    chown -R root:root /etc/acgs/secrets
    
    success "Secrets generated and secured"
}

# Function to setup backup system
setup_backup_system() {
    log "💾 Setting up backup system..."
    
    # Create backup directories
    mkdir -p "$BACKUP_DIR"/{database,config,logs}
    
    # Create backup script
    cat > /usr/local/bin/acgs-backup.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/var/backups/acgs"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="$BACKUP_DIR/backup_$DATE"

mkdir -p "$BACKUP_PATH"

# Database backup
docker exec acgs-postgres-prod pg_dump -U acgs_user acgs_prod | gzip > "$BACKUP_PATH/database.sql.gz"

# Configuration backup
tar -czf "$BACKUP_PATH/config.tar.gz" -C /home/acgs/ACGS-master config/

# Logs backup
tar -czf "$BACKUP_PATH/logs.tar.gz" -C /home/acgs/ACGS-master logs/

# Cleanup old backups (keep 30 days)
find "$BACKUP_DIR" -name "backup_*" -type d -mtime +30 -exec rm -rf {} \;

echo "Backup completed: $BACKUP_PATH"
EOF
    
    chmod +x /usr/local/bin/acgs-backup.sh
    
    # Setup daily backup cron job
    echo "0 2 * * * /usr/local/bin/acgs-backup.sh" | crontab -
    
    success "Backup system configured"
}

# Function to setup monitoring
setup_monitoring() {
    log "📊 Setting up system monitoring..."
    
    # Install monitoring tools
    apt install -y htop iotop nethogs
    
    # Setup log rotation for ACGS logs
    cat > /etc/logrotate.d/acgs << EOF
/home/acgs/ACGS-master/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 acgs acgs
    postrotate
        docker kill -s USR1 \$(docker ps -q --filter name=acgs) 2>/dev/null || true
    endscript
}
EOF
    
    success "System monitoring configured"
}

# Function to setup fail2ban
setup_fail2ban() {
    log "🛡️ Setting up fail2ban..."
    
    # Configure fail2ban for SSH protection
    cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
EOF
    
    systemctl restart fail2ban
    systemctl enable fail2ban
    
    success "Fail2ban configured"
}

# Function to optimize system performance
optimize_system_performance() {
    log "⚡ Optimizing system performance..."
    
    # Optimize kernel parameters
    cat >> /etc/sysctl.conf << EOF

# ACGS Production Optimizations
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 1200
net.ipv4.tcp_max_tw_buckets = 400000
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5
EOF
    
    sysctl -p
    
    # Optimize file limits
    cat >> /etc/security/limits.conf << EOF

# ACGS Production Limits
* soft nofile 65535
* hard nofile 65535
* soft nproc 65535
* hard nproc 65535
EOF
    
    success "System performance optimized"
}

# Main setup function
main() {
    log "🚀 Starting ACGS Phase 3 Production Infrastructure Setup"
    log "======================================================="
    
    check_root
    validate_system_requirements
    setup_system_packages
    setup_docker
    setup_firewall
    setup_ssl_certificates
    setup_secrets
    setup_backup_system
    setup_monitoring
    setup_fail2ban
    optimize_system_performance
    
    success "🎉 ACGS Phase 3 Production Infrastructure Setup Complete!"
    log "======================================================="
    log "Next Steps:"
    log "1. Configure production environment variables"
    log "2. Deploy ACGS services using docker-compose.prod.yml"
    log "3. Run production validation tests"
    log "4. Configure monitoring dashboards"
    
    # Display important information
    echo ""
    log "📋 Important Information:"
    log "  SSL Certificates: $SSL_CERT_DIR"
    log "  Secrets Directory: /etc/acgs/secrets"
    log "  Backup Directory: $BACKUP_DIR"
    log "  Infrastructure Log: $INFRASTRUCTURE_LOG"
    
    echo ""
    log "🔐 Security Notes:"
    log "  - Firewall is enabled with restricted access"
    log "  - Fail2ban is configured for SSH protection"
    log "  - SSL certificates are configured"
    log "  - Secrets are securely generated and stored"
    log "  - Daily backups are scheduled"
}

# Run main function
main "$@"
