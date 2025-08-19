# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Retire-Cluster is a distributed system for repurposing idle devices (phones, tablets, laptops) into a unified computing cluster. Uses TCP socket communication for device coordination with REST API and web dashboard interfaces.

## Architecture

Three-tier distributed system:
- **Main Node**: Cluster coordinator with device registry, task scheduler, and heartbeat monitor
- **Worker Nodes**: Task execution units supporting Windows/Linux/macOS/Android (Termux)  
- **API/Web Layer**: REST API server and terminal-style web dashboard

Core package structure (`retire_cluster/`):
- `core/`: Configuration management and logging
- `device/`: Device profiling and registry
- `communication/`: TCP socket protocol and message handling
- `tasks/`: Task execution framework with scheduling and queue management
- `api/`: REST API with Flask
- `web/`: Terminal-style web interface
- `cli/`: Command-line interfaces
- `mcp/`: Model Context Protocol integration

## Commands

### Installation
```bash
# Install from source with all features
pip install -e .[all]

# Run tests
pytest tests/ -v

# Code formatting and linting
black retire_cluster/ tests/
flake8 retire_cluster/ tests/
mypy retire_cluster/
```

### Running Services
```bash
# Main node server
python -m retire_cluster.main_node --host 0.0.0.0 --port 8080 --debug
retire-cluster-main --data-dir /opt/retire-cluster

# Worker node
python -m retire_cluster.worker_node --auto-id --role worker --main-host 192.168.0.116
retire-cluster-worker --join 192.168.0.116 --device-id my-device --role compute

# API server
retire-cluster-api --port 8081 --auth --api-key your-secret-key

# Cluster status
retire-cluster-status 192.168.0.116 --devices --json
```

### Docker Deployment
```bash
cd docker
./deploy.sh --data-path /volume1/docker/retire-cluster
./backup.sh  # Create backup
./health-monitor.sh --daemon
```

## Architecture Details

### Message Protocol
TCP socket JSON messages:
- `register`: Device registration with capabilities
- `heartbeat`: Status updates (60s intervals, 300s timeout)
- `status`: Query cluster/device status
- `task_assign`, `task_result`: Task management
- `error`: Error notifications

### Task System
- Priority queue with requirement matching
- Built-in tasks: echo, sleep, system_info, python_eval, shell_command
- Requirements: min_cpu_cores, min_memory_gb, required_platform
- Load balancing scheduler

### REST API
- `GET /api/v1/cluster/status` - Cluster overview
- `GET /api/v1/devices` - List devices
- `POST /api/v1/tasks` - Submit task
- `GET /api/v1/tasks/{id}/status` - Task status
- Bearer token authentication when enabled

## Test Environment

### Main Node (192.168.0.116)
```bash
ssh 18617007050@192.168.0.116
/share/CACHEDEV1_DATA/.samba_python3/Python3/bin/python3 ~/simple_legacy_main.py
```

### Worker Node (192.168.0.111:8022)
```bash
ssh -p 8022 u0_a463@192.168.0.111
python simple_legacy_worker.py --device-id android-001 --role mobile --main-host 192.168.0.116
```