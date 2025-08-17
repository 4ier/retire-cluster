# Docker Deployment Scripts

This directory contains scripts and configurations for deploying Retire-Cluster Main Node in Docker containers, optimized for NAS environments.

## Quick Start

```bash
# Configure environment
cp ../.env.example ../.env
# Edit .env with your settings

# Deploy with automated script
./deploy.sh

# Access services
# Main Node API: http://nas-ip:8080
# Web Dashboard: http://nas-ip:5000
```

## Files Overview

- **deploy.sh** - Automated deployment script with health checks
- **backup.sh** - Backup and restore functionality with scheduling
- **health-monitor.sh** - Continuous health monitoring with alerts
- **nginx.conf** - Reverse proxy configuration (optional)

## Usage Examples

```bash
# Deployment options
./deploy.sh --data-path /volume1/docker/retire-cluster
./deploy.sh --with-proxy --skip-build

# Backup management  
./backup.sh                                    # Create backup
./backup.sh restore backup_20240115.tar.gz    # Restore

# Health monitoring
./health-monitor.sh --daemon --email admin@example.com
```

## NAS Platform Setup

### Synology DSM
```bash
# Data path: /volume1/docker/retire-cluster
# Enable SSH and Docker package
./deploy.sh --data-path /volume1/docker/retire-cluster
```

### QNAP QTS
```bash
# Data path: /share/Container/retire-cluster  
# Enable SSH and Container Station
./deploy.sh --data-path /share/Container/retire-cluster
```

## Directory Structure

```
/data-path/
├── config/          # Configuration files
├── database/        # SQLite database
├── logs/           # Application logs
└── nginx_logs/     # Proxy logs (if enabled)
```

## Monitoring

```bash
# View logs
docker logs -f retire-cluster-main

# Check health
curl http://localhost:8080/api/health

# Monitor resources
docker stats retire-cluster-main
```

See [Deployment Guide](../docs/deployment-guide.md) for complete documentation.