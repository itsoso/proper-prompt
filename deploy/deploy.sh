#!/bin/bash

# Proper Prompts Deployment Script
# For Alibaba Cloud ECS deployment to prompt.westwetlandtech.com

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="prompt.westwetlandtech.com"
PROJECT_NAME="proper-prompts"
DEPLOY_DIR="/opt/${PROJECT_NAME}"
BACKUP_DIR="/opt/backups/${PROJECT_NAME}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Proper Prompts Deployment Script${NC}"
echo -e "${BLUE}  Domain: ${DOMAIN}${NC}"
echo -e "${BLUE}========================================${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root${NC}"
    exit 1
fi

# Function to print step
print_step() {
    echo -e "\n${GREEN}[STEP]${NC} $1"
}

# Function to print info
print_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

# Function to check command exists
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}$1 is not installed. Installing...${NC}"
        return 1
    fi
    return 0
}

# Docker Compose command (V2 uses 'docker compose', V1 uses 'docker-compose')
DOCKER_COMPOSE="docker compose"

# Install dependencies
install_dependencies() {
    print_step "Installing system dependencies..."
    
    # Update system
    apt-get update -y
    
    # Install Docker if not present
    if ! check_command docker; then
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        systemctl enable docker
        systemctl start docker
        rm get-docker.sh
    fi
    
    # Docker Compose V2 is included with Docker, verify it works
    if ! docker compose version &> /dev/null; then
        echo -e "${RED}Docker Compose plugin not found, installing...${NC}"
        apt-get install -y docker-compose-plugin
    fi
    
    # Install certbot for SSL
    if ! check_command certbot; then
        apt-get install -y certbot
    fi
    
    print_info "Dependencies installed successfully"
}

# Setup directories
setup_directories() {
    print_step "Setting up directories..."
    
    mkdir -p ${DEPLOY_DIR}
    mkdir -p ${BACKUP_DIR}
    mkdir -p ${DEPLOY_DIR}/deploy/ssl
    mkdir -p ${DEPLOY_DIR}/logs
    
    print_info "Directories created"
}

# Copy project files
copy_files() {
    print_step "Copying project files..."
    
    # Get script directory
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
    
    # Copy all files
    cp -r ${PROJECT_ROOT}/* ${DEPLOY_DIR}/
    
    print_info "Files copied to ${DEPLOY_DIR}"
}

# Setup SSL certificates
setup_ssl() {
    print_step "Setting up SSL certificates..."
    
    SSL_DIR="${DEPLOY_DIR}/deploy/ssl"
    
    if [ -f "${SSL_DIR}/fullchain.pem" ] && [ -f "${SSL_DIR}/privkey.pem" ]; then
        print_info "SSL certificates already exist"
        return 0
    fi
    
    # Stop nginx if running
    ${DOCKER_COMPOSE} -f ${DEPLOY_DIR}/deploy/docker-compose.yml down nginx 2>/dev/null || true
    
    # Get certificate
    certbot certonly --standalone -d ${DOMAIN} --non-interactive --agree-tos --email admin@westwetlandtech.com
    
    # Copy certificates
    cp /etc/letsencrypt/live/${DOMAIN}/fullchain.pem ${SSL_DIR}/
    cp /etc/letsencrypt/live/${DOMAIN}/privkey.pem ${SSL_DIR}/
    
    print_info "SSL certificates installed"
}

# Setup environment
setup_environment() {
    print_step "Setting up environment variables..."
    
    ENV_FILE="${DEPLOY_DIR}/deploy/.env"
    
    if [ -f "${ENV_FILE}" ]; then
        print_info "Environment file exists, skipping..."
        return 0
    fi
    
    # Generate secure passwords
    DB_PASSWORD=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 32)
    SECRET_KEY=$(openssl rand -base64 64 | tr -dc 'a-zA-Z0-9' | head -c 64)
    
    cat > ${ENV_FILE} << EOF
# Database
DB_PASSWORD=${DB_PASSWORD}

# Security
SECRET_KEY=${SECRET_KEY}

# LLM Configuration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
DEFAULT_MODEL=gpt-4o-mini
EOF
    
    chmod 600 ${ENV_FILE}
    
    print_info "Environment file created at ${ENV_FILE}"
    print_info "Please update OPENAI_API_KEY in ${ENV_FILE}"
}

# Build and deploy
deploy() {
    print_step "Building and deploying containers..."
    
    cd ${DEPLOY_DIR}/deploy
    
    # Pull latest images
    ${DOCKER_COMPOSE} pull
    
    # Build custom images
    ${DOCKER_COMPOSE} build --no-cache
    
    # Start services
    ${DOCKER_COMPOSE} up -d
    
    # Wait for services to start
    print_info "Waiting for services to start..."
    sleep 10
    
    # Check health
    if curl -s http://localhost:8000/health | grep -q "healthy"; then
        print_info "Backend is healthy"
    else
        echo -e "${RED}Backend health check failed${NC}"
    fi
    
    print_info "Deployment completed"
}

# Setup auto-renewal for SSL
setup_ssl_renewal() {
    print_step "Setting up SSL auto-renewal..."
    
    # Create renewal script
    cat > /etc/cron.d/certbot-renew << EOF
0 0 1 * * root certbot renew --quiet --post-hook "cp /etc/letsencrypt/live/${DOMAIN}/*.pem ${DEPLOY_DIR}/deploy/ssl/ && docker compose -f ${DEPLOY_DIR}/deploy/docker-compose.yml restart nginx"
EOF
    
    print_info "SSL auto-renewal configured"
}

# Setup systemd service
setup_systemd() {
    print_step "Setting up systemd service..."
    
    cat > /etc/systemd/system/proper-prompts.service << EOF
[Unit]
Description=Proper Prompts Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${DEPLOY_DIR}/deploy
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable proper-prompts
    
    print_info "Systemd service configured"
}

# Backup function
backup() {
    print_step "Creating backup..."
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.tar.gz"
    
    cd ${DEPLOY_DIR}
    
    # Backup database
    ${DOCKER_COMPOSE} -f deploy/docker-compose.yml exec -T postgres pg_dump -U proper_prompts proper_prompts > ${BACKUP_DIR}/db_${TIMESTAMP}.sql
    
    # Backup files
    tar -czf ${BACKUP_FILE} --exclude='node_modules' --exclude='.git' --exclude='__pycache__' .
    
    # Keep only last 7 backups
    ls -t ${BACKUP_DIR}/backup_*.tar.gz | tail -n +8 | xargs -r rm
    ls -t ${BACKUP_DIR}/db_*.sql | tail -n +8 | xargs -r rm
    
    print_info "Backup created: ${BACKUP_FILE}"
}

# Show logs
logs() {
    cd ${DEPLOY_DIR}/deploy
    ${DOCKER_COMPOSE} logs -f --tail=100
}

# Show status
status() {
    print_step "Service Status"
    cd ${DEPLOY_DIR}/deploy
    ${DOCKER_COMPOSE} ps
    echo ""
    print_info "Backend health:"
    curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || echo "Unable to reach backend"
}

# Main execution
case "${1:-deploy}" in
    install)
        install_dependencies
        ;;
    setup)
        setup_directories
        copy_files
        setup_environment
        ;;
    ssl)
        setup_ssl
        setup_ssl_renewal
        ;;
    deploy)
        install_dependencies
        setup_directories
        copy_files
        setup_environment
        setup_ssl
        deploy
        setup_systemd
        setup_ssl_renewal
        status
        ;;
    update)
        copy_files
        deploy
        ;;
    backup)
        backup
        ;;
    logs)
        logs
        ;;
    status)
        status
        ;;
    restart)
        cd ${DEPLOY_DIR}/deploy
        ${DOCKER_COMPOSE} restart
        ;;
    stop)
        cd ${DEPLOY_DIR}/deploy
        ${DOCKER_COMPOSE} down
        ;;
    *)
        echo "Usage: $0 {install|setup|ssl|deploy|update|backup|logs|status|restart|stop}"
        exit 1
        ;;
esac

echo -e "\n${GREEN}Done!${NC}"

