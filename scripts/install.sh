#!/bin/bash
"""
Installation script for Retire-Cluster
"""

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
INSTALL_DIR="/opt/retire-cluster"
SERVICE_USER="retire-cluster"
CONFIG_DIR="/etc/retire-cluster"
LOG_DIR="/var/log/retire-cluster"
DATA_DIR="/var/lib/retire-cluster"

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Detect operating system
detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$ID
        VER=$VERSION_ID
    elif [[ -f /etc/redhat-release ]]; then
        OS="centos"
    elif [[ -f /etc/debian_version ]]; then
        OS="debian"
    else
        OS=$(uname -s)
    fi
    
    log_info "Detected OS: $OS"
}

# Install Python and pip
install_python() {
    log_info "Installing Python and pip..."
    
    case "$OS" in
        ubuntu|debian)
            apt update
            apt install -y python3 python3-pip python3-venv
            ;;
        centos|rhel|fedora)
            if command -v dnf >/dev/null; then
                dnf install -y python3 python3-pip
            else
                yum install -y python3 python3-pip
            fi
            ;;
        arch)
            pacman -S --noconfirm python python-pip
            ;;
        *)
            log_warning "Unknown OS. Please install Python 3.7+ and pip manually"
            return 1
            ;;
    esac
    
    log_success "Python and pip installed"
}

# Create system user
create_user() {
    if ! id "$SERVICE_USER" &>/dev/null; then
        log_info "Creating system user: $SERVICE_USER"
        useradd --system --shell /bin/false --home-dir "$DATA_DIR" --create-home "$SERVICE_USER"
        log_success "User $SERVICE_USER created"
    else
        log_info "User $SERVICE_USER already exists"
    fi
}

# Create directories
create_directories() {
    log_info "Creating directories..."
    
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "$DATA_DIR"
    
    # Set permissions
    chown "$SERVICE_USER:$SERVICE_USER" "$LOG_DIR" "$DATA_DIR"
    chmod 755 "$INSTALL_DIR" "$CONFIG_DIR"
    chmod 750 "$LOG_DIR" "$DATA_DIR"
    
    log_success "Directories created"
}

# Install retire-cluster
install_retire_cluster() {
    log_info "Installing Retire-Cluster..."
    
    # Create virtual environment
    python3 -m venv "$INSTALL_DIR/venv"
    
    # Activate virtual environment and install
    source "$INSTALL_DIR/venv/bin/activate"
    
    # Install from current directory if setup.py exists, otherwise from PyPI
    if [[ -f "setup.py" ]]; then
        log_info "Installing from local source..."
        pip install .
    else
        log_info "Installing from PyPI..."
        pip install retire-cluster
    fi
    
    # Install optional dependencies
    pip install psutil
    
    log_success "Retire-Cluster installed"
}

# Create configuration files
create_config() {
    log_info "Creating configuration files..."
    
    # Main node config
    cat > "$CONFIG_DIR/main_config.json" << EOF
{
  "server": {
    "host": "0.0.0.0",
    "port": 8080,
    "max_connections": 50,
    "timeout": 10
  },
  "database": {
    "path": "$DATA_DIR/cluster_metadata.json",
    "backup_enabled": true,
    "backup_interval": 3600
  },
  "heartbeat": {
    "interval_seconds": 60,
    "timeout_threshold": 300,
    "cleanup_interval": 1800
  },
  "logging": {
    "level": "INFO",
    "file_path": "$LOG_DIR/main_node.log",
    "max_size_mb": 100,
    "backup_count": 5
  }
}
EOF
    
    # Worker node config template
    cat > "$CONFIG_DIR/worker_config.json" << EOF
{
  "device": {
    "id": "worker-001",
    "role": "worker"
  },
  "main_node": {
    "host": "192.168.0.116",
    "port": 8080
  },
  "heartbeat": {
    "interval_seconds": 60
  },
  "capabilities": {
    "max_concurrent_tasks": 2
  }
}
EOF
    
    log_success "Configuration files created"
}

# Create systemd services
create_services() {
    log_info "Creating systemd services..."
    
    # Main node service
    cat > "/etc/systemd/system/retire-cluster-main.service" << EOF
[Unit]
Description=Retire-Cluster Main Node Server
After=network.target
Wants=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$DATA_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
ExecStart=$INSTALL_DIR/venv/bin/retire-cluster-main --config $CONFIG_DIR/main_config.json --data-dir $DATA_DIR
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=retire-cluster-main

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$DATA_DIR $LOG_DIR

[Install]
WantedBy=multi-user.target
EOF
    
    # Worker node service
    cat > "/etc/systemd/system/retire-cluster-worker.service" << EOF
[Unit]
Description=Retire-Cluster Worker Node Client
After=network.target
Wants=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$DATA_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
ExecStart=$INSTALL_DIR/venv/bin/retire-cluster-worker --auto-id --role worker --config $CONFIG_DIR/worker_config.json
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=retire-cluster-worker

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$DATA_DIR $LOG_DIR

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd
    systemctl daemon-reload
    
    log_success "Systemd services created"
}

# Create management scripts
create_scripts() {
    log_info "Creating management scripts..."
    
    # Control script
    cat > "/usr/local/bin/retire-cluster" << 'EOF'
#!/bin/bash
# Retire-Cluster management script

case "$1" in
    start-main)
        systemctl start retire-cluster-main
        ;;
    stop-main)
        systemctl stop retire-cluster-main
        ;;
    restart-main)
        systemctl restart retire-cluster-main
        ;;
    start-worker)
        systemctl start retire-cluster-worker
        ;;
    stop-worker)
        systemctl stop retire-cluster-worker
        ;;
    restart-worker)
        systemctl restart retire-cluster-worker
        ;;
    status)
        echo "=== Main Node ==="
        systemctl status retire-cluster-main --no-pager
        echo "=== Worker Node ==="
        systemctl status retire-cluster-worker --no-pager
        ;;
    logs-main)
        journalctl -u retire-cluster-main -f
        ;;
    logs-worker)
        journalctl -u retire-cluster-worker -f
        ;;
    enable)
        systemctl enable retire-cluster-main retire-cluster-worker
        ;;
    disable)
        systemctl disable retire-cluster-main retire-cluster-worker
        ;;
    *)
        echo "Usage: $0 {start-main|stop-main|restart-main|start-worker|stop-worker|restart-worker|status|logs-main|logs-worker|enable|disable}"
        exit 1
        ;;
esac
EOF
    
    chmod +x "/usr/local/bin/retire-cluster"
    
    log_success "Management scripts created"
}

# Main installation process
main() {
    log_info "Starting Retire-Cluster installation..."
    
    check_root
    detect_os
    install_python
    create_user
    create_directories
    install_retire_cluster
    create_config
    create_services
    create_scripts
    
    log_success "Installation completed successfully!"
    echo
    log_info "Next steps:"
    echo "1. Edit configuration files in $CONFIG_DIR"
    echo "2. Start services: retire-cluster start-main (or start-worker)"
    echo "3. Enable auto-start: retire-cluster enable"
    echo "4. Check status: retire-cluster status"
    echo "5. View logs: retire-cluster logs-main (or logs-worker)"
    echo
    log_info "For more information, see the documentation"
}

# Run main function
main "$@"