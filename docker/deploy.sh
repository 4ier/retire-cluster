#!/bin/bash
# Retire-Cluster Docker Deployment Script
# Automated deployment for NAS environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
DATA_PATH="/volume1/docker/retire-cluster"
ENV_FILE=".env"
COMPOSE_FILE="docker-compose.yml"

# Functions
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    print_info "Checking requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_warn "docker-compose not found, trying docker compose..."
        if ! docker compose version &> /dev/null; then
            print_error "Docker Compose is not installed"
            exit 1
        fi
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_CMD="docker-compose"
    fi
    
    print_info "Requirements satisfied"
}

setup_directories() {
    print_info "Setting up directories..."
    
    # Create data directories
    mkdir -p "${DATA_PATH}/config"
    mkdir -p "${DATA_PATH}/database"
    mkdir -p "${DATA_PATH}/logs"
    mkdir -p "${DATA_PATH}/nginx_logs"
    
    # Set permissions (adjust UID/GID as needed)
    if [[ "$OSTYPE" == "linux-gnu"* ]] && [ "$EUID" -eq 0 ]; then
        chown -R 1000:1000 "${DATA_PATH}" 2>/dev/null || print_warn "Cannot change ownership, continuing..."
        chmod -R 755 "${DATA_PATH}" 2>/dev/null || print_warn "Cannot change permissions, continuing..."
    else
        print_info "Skipping permission changes (not running as root or not Linux)"
    fi
    
    print_info "Directories created at ${DATA_PATH}"
}

setup_config() {
    print_info "Setting up configuration..."
    
    # Copy environment file if not exists
    if [ ! -f "$ENV_FILE" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example "$ENV_FILE"
            print_info "Created .env file from template"
            print_warn "Please edit .env file with your settings"
        else
            print_error ".env.example not found"
            exit 1
        fi
    else
        print_info "Using existing .env file"
    fi
    
    # Update DATA_PATH in .env
    if grep -q "DATA_PATH=" "$ENV_FILE"; then
        sed -i.bak "s|DATA_PATH=.*|DATA_PATH=${DATA_PATH}|" "$ENV_FILE"
        print_info "Updated DATA_PATH in .env"
    fi
}

build_image() {
    print_info "Building Docker image..."
    
    # Build with proxy support if HTTP_PROXY is set
    if [ -n "$HTTP_PROXY" ]; then
        # Convert localhost proxy to Docker-accessible address
        if [[ "$HTTP_PROXY" == *"127.0.0.1"* ]] || [[ "$HTTP_PROXY" == *"localhost"* ]]; then
            # Get Docker host IP
            DOCKER_HOST_IP=$(ip route | grep docker0 | awk '{print $9}' | head -1)
            if [ -z "$DOCKER_HOST_IP" ]; then
                DOCKER_HOST_IP=$(docker network inspect bridge | grep "Gateway" | awk '{print $2}' | tr -d '",' | head -1)
            fi
            if [ -n "$DOCKER_HOST_IP" ]; then
                DOCKER_HTTP_PROXY=$(echo "$HTTP_PROXY" | sed "s/127\.0\.0\.1/$DOCKER_HOST_IP/g" | sed "s/localhost/$DOCKER_HOST_IP/g")
                DOCKER_HTTPS_PROXY=$(echo "$HTTPS_PROXY" | sed "s/127\.0\.0\.1/$DOCKER_HOST_IP/g" | sed "s/localhost/$DOCKER_HOST_IP/g")
                print_info "Converting proxy for Docker: $DOCKER_HTTP_PROXY"
            else
                DOCKER_HTTP_PROXY="$HTTP_PROXY"
                DOCKER_HTTPS_PROXY="$HTTPS_PROXY"
                print_warn "Could not detect Docker host IP, using original proxy"
            fi
        else
            DOCKER_HTTP_PROXY="$HTTP_PROXY"
            DOCKER_HTTPS_PROXY="$HTTPS_PROXY"
        fi
        
        print_info "Building with proxy: $DOCKER_HTTP_PROXY"
        docker build \
            --build-arg HTTP_PROXY="$DOCKER_HTTP_PROXY" \
            --build-arg HTTPS_PROXY="$DOCKER_HTTPS_PROXY" \
            -t retire-cluster:latest . || {
            print_error "Failed to build Docker image"
            exit 1
        }
    else
        docker build -t retire-cluster:latest . || {
            print_error "Failed to build Docker image"
            exit 1
        }
    fi
    
    print_info "Docker image built successfully"
}

deploy_services() {
    print_info "Deploying services..."
    
    # Stop existing services if running
    if $COMPOSE_CMD ps | grep -q "retire-cluster-main"; then
        print_info "Stopping existing services..."
        $COMPOSE_CMD down
    fi
    
    # Start services
    $COMPOSE_CMD up -d || {
        print_error "Failed to start services"
        exit 1
    }
    
    print_info "Services started successfully"
}

check_health() {
    print_info "Checking service health..."
    
    # Load port configuration from .env
    if [ -f "$ENV_FILE" ]; then
        source "$ENV_FILE"
    fi
    
    # Use configured ports or defaults
    local api_port="${CLUSTER_PORT:-8081}"
    local web_port="${WEB_PORT:-5001}"
    
    # Wait for services to start
    sleep 10
    
    # Check main node health
    if curl -f "http://localhost:${api_port}/api/health" &> /dev/null; then
        print_info "Main node is healthy"
    else
        print_warn "Main node health check failed, checking logs..."
        $COMPOSE_CMD logs --tail 50 retire-cluster-main
    fi
    
    # Check web dashboard
    if curl -f "http://localhost:${web_port}" &> /dev/null; then
        print_info "Web dashboard is accessible"
    else
        print_warn "Web dashboard not responding"
    fi
}

show_info() {
    print_info "Deployment completed!"
    
    # Load port configuration from .env
    if [ -f "$ENV_FILE" ]; then
        source "$ENV_FILE"
    fi
    
    # Use configured ports or defaults
    local api_port="${CLUSTER_PORT:-8081}"
    local web_port="${WEB_PORT:-5001}"
    
    echo ""
    echo "Services are running at:"
    echo "  Main Node API: http://localhost:${api_port}"
    echo "  Web Dashboard: http://localhost:${web_port}"
    echo ""
    echo "Useful commands:"
    echo "  View logs:     $COMPOSE_CMD logs -f"
    echo "  Stop services: $COMPOSE_CMD down"
    echo "  Restart:       $COMPOSE_CMD restart"
    echo "  Update:        git pull && ./docker/deploy.sh"
    echo ""
    echo "Data stored at: ${DATA_PATH}"
}

# Main execution
main() {
    echo "======================================"
    echo "Retire-Cluster Docker Deployment"
    echo "======================================"
    echo ""
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --data-path)
                DATA_PATH="$2"
                shift 2
                ;;
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            --with-proxy)
                WITH_PROXY=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --data-path PATH    Set data directory path (default: /volume1/docker/retire-cluster)"
                echo "  --skip-build        Skip Docker image build"
                echo "  --with-proxy        Deploy with Nginx proxy"
                echo "  --help              Show this help message"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Run deployment steps
    check_requirements
    setup_directories
    setup_config
    
    if [ "$SKIP_BUILD" != true ]; then
        build_image
    fi
    
    # Add proxy profile if requested
    if [ "$WITH_PROXY" = true ]; then
        export COMPOSE_PROFILES="with-proxy"
        print_info "Deploying with Nginx proxy"
    fi
    
    deploy_services
    check_health
    show_info
}

# Run main function
main "$@"