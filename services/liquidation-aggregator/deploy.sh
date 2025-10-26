#!/bin/bash
# Production Deployment Script for Liquidation Aggregator
# Author: Opus 4.1
# Date: October 25, 2025

set -e  # Exit on any error
set -u  # Exit on undefined variable
set -o pipefail  # Exit on pipe failure

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="liquidation-aggregator"
ENV_FILE=".env"
DOCKER_COMPOSE="docker-compose.yml"
LOG_DIR="./logs"
BACKUP_DIR="./backups"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi

    # Check environment file
    if [ ! -f "$ENV_FILE" ]; then
        log_error "Environment file $ENV_FILE not found"
        log_info "Creating from template..."
        cp .env.example .env
        log_warn "Please configure $ENV_FILE before deployment"
        exit 1
    fi

    log_info "Prerequisites check passed"
}

# Create necessary directories
setup_directories() {
    log_info "Setting up directories..."

    mkdir -p "$LOG_DIR"
    mkdir -p "$BACKUP_DIR"
    mkdir -p "./data/redis"
    mkdir -p "./data/postgres"

    log_info "Directories created"
}

# Backup existing data
backup_data() {
    log_info "Creating backup..."

    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.tar.gz"

    if [ -d "./data" ]; then
        tar -czf "$BACKUP_FILE" ./data 2>/dev/null || true
        log_info "Backup created: $BACKUP_FILE"
    else
        log_warn "No data to backup"
    fi
}

# Build Docker images
build_images() {
    log_info "Building Docker images..."

    docker-compose build --no-cache

    if [ $? -eq 0 ]; then
        log_info "Docker images built successfully"
    else
        log_error "Failed to build Docker images"
        exit 1
    fi
}

# Deploy services
deploy_services() {
    log_info "Deploying services..."

    # Stop existing services
    docker-compose down --remove-orphans

    # Start services
    docker-compose up -d

    if [ $? -eq 0 ]; then
        log_info "Services deployed successfully"
    else
        log_error "Failed to deploy services"
        exit 1
    fi
}

# Health check
health_check() {
    log_info "Performing health check..."

    sleep 10  # Give services time to start

    # Check Redis
    if docker-compose exec -T redis redis-cli ping | grep -q PONG; then
        log_info "Redis is healthy"
    else
        log_error "Redis health check failed"
        exit 1
    fi

    # Check application
    if docker-compose ps | grep -q "Up"; then
        log_info "Application containers are running"
    else
        log_error "Some containers are not running"
        docker-compose ps
        exit 1
    fi

    log_info "Health check passed"
}

# Show deployment info
show_info() {
    log_info "Deployment Information:"
    echo "========================="
    echo "Project: $PROJECT_NAME"
    echo "Environment: Production"
    echo "Timestamp: $(date)"
    echo "========================="
    echo ""
    log_info "Container Status:"
    docker-compose ps
    echo ""
    log_info "Logs: docker-compose logs -f"
    log_info "Stop: docker-compose down"
    log_info "Monitoring: http://localhost:3000 (Grafana)"
}

# Main deployment flow
main() {
    log_info "Starting deployment of $PROJECT_NAME..."

    check_prerequisites
    setup_directories
    backup_data
    build_images
    deploy_services
    health_check
    show_info

    log_info "Deployment completed successfully!"
}

# Handle script arguments
case "${1:-deploy}" in
    deploy)
        main
        ;;
    stop)
        log_info "Stopping services..."
        docker-compose down
        ;;
    restart)
        log_info "Restarting services..."
        docker-compose restart
        ;;
    logs)
        docker-compose logs -f
        ;;
    status)
        docker-compose ps
        ;;
    backup)
        backup_data
        ;;
    *)
        echo "Usage: $0 {deploy|stop|restart|logs|status|backup}"
        exit 1
        ;;
esac
