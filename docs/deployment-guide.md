# Retire-Cluster Deployment Guide

## Overview

This guide covers all deployment scenarios for Retire-Cluster, from simple development setups to production Docker deployments on NAS systems.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Development Setup](#development-setup)
3. [Production Deployment](#production-deployment)
4. [Docker Deployment](#docker-deployment)
5. [Platform-Specific Setup](#platform-specific-setup)
6. [Monitoring & Maintenance](#monitoring--maintenance)

## Quick Start

### Basic Requirements

- Python 3.8+ (Python 3.10+ recommended)
- Network connectivity (all devices on the same network)
- At least one device for Main Node (preferably NAS or always-on computer)

### Installation

```bash
# Install from PyPI (when available)
pip install retire-cluster

# Or install from source
git clone https://github.com/yourusername/retire-cluster.git
cd retire-cluster
pip install -e .
```

### Simple Setup

```bash
# 1. Start Main Node (on NAS or main computer)
python -m retire_cluster.main_node --host 0.0.0.0 --port 8080

# 2. Start Worker Node (on any device)
python -m retire_cluster.worker_node \
    --device-id "my-device" \
    --main-host 192.168.1.100 \
    --main-port 8080

# 3. Start Web Dashboard (optional)
python -m retire_cluster.web.app --port 5000
```

## Development Setup

### Local Development

```bash
# Clone repository
git clone https://github.com/yourusername/retire-cluster.git
cd retire-cluster

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Run tests
python -m pytest tests/

# Start development server
python examples/simple_main_server.py
```

### Testing with Multiple Nodes

```bash
# Terminal 1: Main Node
python examples/simple_main_server.py --port 8080

# Terminal 2: Worker Node 1
python examples/simple_worker_client.py \
    --device-id worker-001 \
    --main-host localhost

# Terminal 3: Worker Node 2
python examples/simple_worker_client.py \
    --device-id worker-002 \
    --main-host localhost

# Terminal 4: Web Dashboard
python -m retire_cluster.web.app
```

## Production Deployment

### Main Node Configuration

Create `/etc/retire-cluster/config.json`:

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8080,
    "max_connections": 100
  },
  "database": {
    "path": "/var/lib/retire-cluster/cluster.db",
    "backup_enabled": true,
    "backup_interval": 3600
  },
  "logging": {
    "level": "INFO",
    "file": "/var/log/retire-cluster/cluster.log",
    "max_size": "10MB",
    "backup_count": 5
  },
  "cluster": {
    "heartbeat_interval": 60,
    "offline_threshold": 300,
    "task_timeout": 3600
  }
}
```

### Systemd Service (Linux)

Create `/etc/systemd/system/retire-cluster-main.service`:

```ini
[Unit]
Description=Retire-Cluster Main Node
After=network.target

[Service]
Type=simple
User=retire-cluster
Group=retire-cluster
ExecStart=/opt/retire-cluster/venv/bin/python -m retire_cluster.main_node --config /etc/retire-cluster/config.json
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
# Create user
sudo useradd -r -s /bin/false retire-cluster

# Create directories
sudo mkdir -p /var/lib/retire-cluster /var/log/retire-cluster /etc/retire-cluster
sudo chown retire-cluster:retire-cluster /var/lib/retire-cluster /var/log/retire-cluster

# Enable service
sudo systemctl enable retire-cluster-main
sudo systemctl start retire-cluster-main
```

## Docker Deployment

### Why Docker for Main Node Only?

**Main Node Benefits:**
- Consistent environment on NAS/server
- Easy updates and rollbacks
- Resource isolation
- Simplified backup and migration

**Worker Node Considerations:**
- Diverse platforms (Android, old laptops, Raspberry Pi)
- Resource constraints on mobile devices
- Native performance requirements
- Platform-specific features (Termux, GPIO, sensors)

### Quick Docker Setup

```bash
# Clone repository
git clone https://github.com/yourusername/retire-cluster.git
cd retire-cluster

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Deploy using automated script
chmod +x docker/deploy.sh
./docker/deploy.sh

# Or use Docker Compose directly
docker-compose up -d
```

### Docker Compose Configuration

```yaml
version: '3.8'

services:
  retire-cluster-main:
    container_name: retire-cluster-main
    image: retire-cluster:latest
    build: .
    restart: unless-stopped
    
    ports:
      - "8080:8080"  # Main node server
      - "5000:5000"  # Web dashboard
    
    volumes:
      - ./data/config:/data/config
      - ./data/database:/data/database
      - ./data/logs:/data/logs
    
    environment:
      - TZ=Asia/Shanghai
      - LOG_LEVEL=INFO
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/api/health"]
      interval: 30s
      timeout: 5s
      retries: 3
```

### Docker Management Scripts

**Deployment:**
```bash
./docker/deploy.sh [OPTIONS]
  --data-path PATH    # Custom data directory
  --with-proxy        # Deploy with Nginx proxy
  --skip-build        # Skip image build
```

**Backup:**
```bash
./docker/backup.sh              # Create backup
./docker/backup.sh restore file # Restore from backup
```

**Health Monitoring:**
```bash
./docker/health-monitor.sh                    # Interactive monitoring
./docker/health-monitor.sh --daemon           # Background monitoring
./docker/health-monitor.sh --email admin@...  # Email alerts
```

## Platform-Specific Setup

### NAS Deployment

#### Synology DSM

```bash
# SSH into Synology NAS
ssh admin@synology-ip

# Enable Docker
# Package Center → Docker → Install

# Deploy Retire-Cluster
cd /volume1/docker
git clone https://github.com/yourusername/retire-cluster.git
cd retire-cluster

# Configure for Synology
cp .env.example .env
sed -i 's|DATA_PATH=.*|DATA_PATH=/volume1/docker/retire-cluster|' .env

# Deploy
./docker/deploy.sh

# Set up scheduled tasks
# Control Panel → Task Scheduler → Create
# Daily backup: /volume1/docker/retire-cluster/docker/backup.sh
```

#### QNAP QTS

```bash
# SSH into QNAP NAS
ssh admin@qnap-ip

# Use Container Station
# App Center → Container Station → Install

# Deploy via Container Station GUI or CLI
cd /share/Container
git clone https://github.com/yourusername/retire-cluster.git
cd retire-cluster

# Configure for QNAP
cp .env.example .env
sed -i 's|DATA_PATH=.*|DATA_PATH=/share/Container/retire-cluster|' .env

# Deploy
./docker/deploy.sh
```

### Worker Node Setup

#### Android (Termux)

```bash
# Install Termux from F-Droid
# In Termux terminal:

# Update packages
pkg update && pkg upgrade

# Install Python and dependencies
pkg install python
pip install psutil requests

# Download worker script
curl -O https://raw.githubusercontent.com/yourusername/retire-cluster/main/examples/simple_worker_client.py

# Run worker
python simple_worker_client.py \
    --device-id android-$(hostname) \
    --role mobile \
    --main-host 192.168.1.100
```

#### Raspberry Pi

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv -y

# Install worker
pip3 install psutil requests

# Download and run worker
wget https://raw.githubusercontent.com/yourusername/retire-cluster/main/examples/simple_worker_client.py
python3 simple_worker_client.py \
    --device-id rpi-$(hostname) \
    --role compute \
    --main-host 192.168.1.100

# Optional: Create systemd service
sudo tee /etc/systemd/system/retire-cluster-worker.service << EOF
[Unit]
Description=Retire-Cluster Worker Node
After=network.target

[Service]
Type=simple
User=pi
ExecStart=/usr/bin/python3 /home/pi/simple_worker_client.py --device-id rpi-$(hostname) --role compute --main-host 192.168.1.100
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable retire-cluster-worker
sudo systemctl start retire-cluster-worker
```

#### Old Laptop/Desktop

```bash
# Linux
sudo apt install python3 python3-pip
pip3 install psutil requests

# Windows
# Download Python from python.org
pip install psutil requests

# macOS
brew install python3
pip3 install psutil requests

# Download and run worker
curl -O https://raw.githubusercontent.com/yourusername/retire-cluster/main/examples/simple_worker_client.py
python3 simple_worker_client.py \
    --device-id laptop-$(hostname) \
    --role compute \
    --main-host 192.168.1.100
```

## Web Dashboard

### CLI-Style Terminal Interface

The web dashboard provides a terminal-style interface accessible via:
- **Web Browser**: http://your-main-node:5000
- **CLI Browsers**: w3m, lynx, links (AI-friendly)
- **API Access**: Multiple formats (JSON, CSV, TSV, plain text)

### Features

- **Terminal Emulation**: Full xterm.js terminal with command execution
- **Real-time Updates**: Server-Sent Events for live monitoring
- **Multi-format Output**: Supports human and machine-readable formats
- **Command Auto-completion**: Tab completion for commands
- **History**: Command history with up/down arrow navigation

### API Endpoints

```bash
# Text API (AI-friendly)
curl http://main-node:5000/text/devices              # Pipe-delimited
curl http://main-node:5000/text/devices -H "Accept: text/csv"  # CSV
curl http://main-node:5000/text/status               # Key-value pairs

# JSON API
curl http://main-node:5000/api/v1/devices           # Structured JSON
curl http://main-node:5000/api/v1/cluster/status    # Cluster info

# Streaming API
curl http://main-node:5000/stream/devices -H "Accept: text/event-stream"
curl http://main-node:5000/stream/logs               # Real-time logs
```

## Monitoring & Maintenance

### Health Monitoring

```bash
# Check cluster status
curl http://main-node:8080/api/health
curl http://main-node:5000/text/status

# View logs
tail -f /var/log/retire-cluster/cluster.log  # Native
docker logs -f retire-cluster-main           # Docker

# Monitor resources
docker stats retire-cluster-main             # Docker
systemctl status retire-cluster-main         # Systemd
```

### Backup Strategy

**Manual Backup:**
```bash
# Native deployment
tar -czf backup-$(date +%Y%m%d).tar.gz \
    /var/lib/retire-cluster \
    /etc/retire-cluster

# Docker deployment
./docker/backup.sh
```

**Automated Backup (Crontab):**
```bash
# Add to crontab
0 2 * * * /path/to/retire-cluster/docker/backup.sh
```

### Updates and Upgrades

**Docker Deployment:**
```bash
# Pull latest code
git pull origin main

# Rebuild and redeploy
./docker/deploy.sh

# Or manual update
docker-compose down
docker-compose build
docker-compose up -d
```

**Native Deployment:**
```bash
# Update code
git pull origin main
pip install -e .

# Restart services
sudo systemctl restart retire-cluster-main
```

### Troubleshooting

**Common Issues:**

1. **Connection Refused:**
   ```bash
   # Check if service is running
   systemctl status retire-cluster-main
   docker ps | grep retire-cluster
   
   # Check ports
   netstat -tulpn | grep 8080
   
   # Check firewall
   sudo ufw status
   ```

2. **Worker Can't Connect:**
   ```bash
   # Test connectivity
   telnet main-node-ip 8080
   
   # Check worker logs
   python simple_worker_client.py --test --main-host main-node-ip
   ```

3. **Database Issues:**
   ```bash
   # Check database integrity
   sqlite3 /var/lib/retire-cluster/cluster.db "PRAGMA integrity_check;"
   
   # Restore from backup
   ./docker/backup.sh restore backup_file.tar.gz
   ```

**Log Analysis:**
```bash
# Main node logs
tail -f /var/log/retire-cluster/cluster.log
docker logs -f retire-cluster-main

# Web dashboard logs
tail -f /var/log/retire-cluster/web.log

# Worker node logs (check worker output)
```

## Security Considerations

### Network Security

1. **Firewall Configuration:**
   ```bash
   # Allow cluster communication
   sudo ufw allow 8080/tcp
   sudo ufw allow 5000/tcp
   
   # Restrict to local network
   sudo ufw allow from 192.168.1.0/24 to any port 8080
   ```

2. **Internal Network Only:**
   ```yaml
   # Docker Compose - bind to specific IP
   ports:
     - "192.168.1.100:8080:8080"
   ```

### Application Security

1. **API Authentication** (Future):
   ```json
   {
     "security": {
       "api_key_required": true,
       "api_keys": ["your-secret-key"],
       "rate_limiting": {
         "requests_per_minute": 60
       }
     }
   }
   ```

2. **Container Security:**
   - Runs as non-root user (UID 1000)
   - Resource limits enforced
   - Read-only root filesystem (optional)

### Data Protection

1. **Encrypted Backups:**
   ```bash
   # Encrypt backup files
   gpg --symmetric --cipher-algo AES256 backup.tar.gz
   ```

2. **Access Control:**
   ```bash
   # Set proper file permissions
   chmod 600 /etc/retire-cluster/config.json
   chown retire-cluster:retire-cluster /var/lib/retire-cluster
   ```

## Performance Optimization

### Resource Tuning

**Docker Limits:**
```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
    reservations:
      cpus: '0.5'
      memory: 512M
```

**Database Optimization:**
```json
{
  "database": {
    "wal_mode": true,
    "cache_size": 10000,
    "synchronous": "NORMAL"
  }
}
```

### Network Optimization

```json
{
  "cluster": {
    "heartbeat_interval": 30,
    "connection_pool_size": 50,
    "tcp_keepalive": true
  }
}
```

## Production Checklist

- [ ] Main Node deployed on reliable hardware (NAS/server)
- [ ] Docker deployment with automated backups
- [ ] Health monitoring configured
- [ ] Firewall rules configured
- [ ] Worker nodes registered and online
- [ ] Web dashboard accessible
- [ ] Log rotation configured
- [ ] Backup schedule tested
- [ ] Update procedure documented
- [ ] Monitoring alerts configured

## Support and Resources

- **Documentation**: `/docs/` directory
- **Examples**: `/examples/` directory
- **Issues**: GitHub Issues
- **Community**: GitHub Discussions

---

**Next Steps:**
1. Choose your deployment method (Docker recommended for production)
2. Set up Main Node on NAS or always-on device
3. Configure Worker Nodes on idle devices
4. Access Web Dashboard for management
5. Set up monitoring and backups