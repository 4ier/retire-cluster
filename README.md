# Retire-Cluster

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS%20%7C%20Android-lightgrey.svg)

> Transform your idle devices into a unified AI work cluster! A distributed system based on TCP socket communication that organizes old phones, tablets, and laptops into a powerful computing cluster.

[中文文档](README_CN.md)

## 🎯 Overview

Retire-Cluster is an innovative solution for repurposing idle devices, designed for users with multiple unused devices. It transforms "retired" phones, tablets, and old laptops into a unified work cluster, bringing new life to these devices.

The system supports automatic device discovery, real-time status monitoring, intelligent task scheduling, and provides a natural language interface for cluster management.

### ✨ Key Features

- **♻️ Device Repurposing**: Give new life to old phones, tablets, and laptops
- **🤖 Intelligent Scheduling**: Automatically select the best execution node based on device capabilities
- **📊 Real-time Monitoring**: Heartbeat mechanism ensures real-time status updates with automatic failure detection
- **🔧 Auto-Discovery**: Self-aware system that automatically collects and reports hardware/software information
- **🔄 Dynamic Scaling**: Support hot-plugging of devices without service restart
- **🛡️ Fault Tolerance**: Automatic failure detection and task redistribution
- **🌍 Cross-Platform**: Support for Windows, Linux, macOS, and Android (Termux)
- **⚡ Task Execution**: Distributed task execution with priority queuing and requirement matching
- **🌐 REST API**: Comprehensive HTTP API for programmatic cluster management
- **🔐 Security**: API authentication, rate limiting, and input validation
- **🔗 Integrations**: Support for Temporal, Celery, and custom framework integrations
- **📦 Easy Installation**: Single pip install with automatic configuration

## 🏗️ Architecture

```
┌─────────────────────┐         ┌─────────────────────┐
│   Main Node         │         │   Worker Node        │
│                     │◄────────┤                     │
│ ┌─────────────────┐ │         │ ┌─────────────────┐ │
│ │Device Registry  │ │         │ │Device Profiler  │ │
│ │Task Scheduler   │ │         │ │System Monitor   │ │
│ │Heartbeat Monitor│ │         │ │Task Executor    │ │
│ └─────────────────┘ │         │ └─────────────────┘ │
└─────────────────────┘         └─────────────────────┘
        TCP Socket                    TCP Socket
```

### Node Types

- **Main Node**: Cluster coordinator and management center
- **Worker Node**: Task execution units supporting various platforms
- **Storage Node**: Data storage and file services (planned)

## 🚀 Quick Start

### Requirements

- Python 3.10+
- Network connectivity (all devices on the same network)
- Optional: psutil for enhanced system monitoring

### Installation

```bash
# Basic installation
pip install retire-cluster

# With REST API support
pip install retire-cluster[api]

# With framework integrations
pip install retire-cluster[integrations]

# Full installation with all features
pip install retire-cluster[all]

# Or install from source
git clone https://github.com/4ier/retire-cluster.git
cd retire-cluster
pip install .[all]
```

### Start Main Node

```bash
# Start main node with default settings
retire-cluster-main

# Start with custom port and data directory
retire-cluster-main --port 9090 --data-dir /opt/retire-cluster

# Initialize configuration file
retire-cluster-main --init-config
```

### Start Worker Node

```bash
# Join cluster with auto-detection
retire-cluster-worker --join 192.168.1.100

# Join with custom device ID and role
retire-cluster-worker --join 192.168.1.100:8080 --device-id my-laptop --role compute

# Test connection only
retire-cluster-worker --test 192.168.1.100
```

### Monitor Cluster Status

```bash
# View cluster overview
retire-cluster-status 192.168.1.100

# List all devices
retire-cluster-status 192.168.1.100 --devices

# View specific device details
retire-cluster-status 192.168.1.100 --device worker-001

# Filter devices by role
retire-cluster-status 192.168.1.100 --devices --role mobile

# Output in JSON format
retire-cluster-status 192.168.1.100 --json
```

### Start REST API Server

```bash
# Start API server with default settings
retire-cluster-api

# Start with authentication and custom port
retire-cluster-api --port 8081 --auth --api-key your-secret-key

# Connect to specific cluster node
retire-cluster-api --cluster-host 192.168.1.100 --cluster-port 8080
```

### Use REST API

```bash
# Check API health
curl http://localhost:8081/health

# Get cluster status
curl http://localhost:8081/api/v1/cluster/status

# List devices
curl http://localhost:8081/api/v1/devices

# Submit a task
curl -X POST http://localhost:8081/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"task_type": "echo", "payload": {"message": "Hello API!"}}'

# Check task status
curl http://localhost:8081/api/v1/tasks/{task_id}/status
```

### Task Execution

```python
# Submit tasks programmatically
from retire_cluster.tasks import Task, TaskRequirements, TaskPriority

# Simple task
task = Task(
    task_type="echo",
    payload={"message": "Hello World!"},
    priority=TaskPriority.NORMAL
)

# Task with specific requirements
compute_task = Task(
    task_type="python_eval",
    payload={"expression": "sum(range(1000000))"},
    requirements=TaskRequirements(
        min_cpu_cores=4,
        min_memory_gb=8,
        required_platform="linux"
    )
)

# Submit to scheduler
task_id = scheduler.submit_task(task)
```

## 📖 Documentation

### Core Documentation

- **[Architecture Guide](docs/architecture.md)** - Complete system architecture and design
- **[Deployment Guide](docs/deployment-guide.md)** - Comprehensive deployment instructions
- **[Web Interface Design](docs/web-interface-design.md)** - Terminal-style web dashboard
- **[CLI Interface Specification](docs/cli-interface-specification.md)** - Command reference
- **[AI Integration Guide](docs/ai-integration-guide.md)** - AI-friendly interface patterns

### Quick Examples

#### Start Main Node
```bash
# Using Docker (Recommended for production)
git clone https://github.com/yourusername/retire-cluster.git
cd retire-cluster
cp .env.example .env
./docker/deploy.sh

# Or run natively
python -m retire_cluster.main_node --host 0.0.0.0 --port 8080
```

#### Start Worker Node
```bash
# Download worker script
curl -O https://raw.githubusercontent.com/yourusername/retire-cluster/main/examples/simple_worker_client.py

# Run worker
python simple_worker_client.py \
    --device-id my-device \
    --main-host 192.168.1.100 \
    --role compute
```

#### Access Web Dashboard
```bash
# Open in browser
open http://your-main-node:5000

# CLI-friendly access (AI/automation)
curl http://your-main-node:5000/text/devices
curl http://your-main-node:5000/api/v1/cluster/status
```

### Platform-Specific Setup

#### Android (Termux)
```bash
# Install Termux from F-Droid
pkg update && pkg install python
pip install psutil requests

# Run worker
python simple_worker_client.py --device-id android-$(hostname) --role mobile --main-host 192.168.1.100
```

#### Raspberry Pi
```bash
# Install dependencies
sudo apt update && sudo apt install python3 python3-pip -y
pip3 install psutil requests

# Run worker
python3 simple_worker_client.py --device-id rpi-$(hostname) --role compute --main-host 192.168.1.100
```

#### NAS Deployment (Docker)
```bash
# Synology/QNAP NAS
ssh admin@nas-ip
cd /volume1/docker  # or /share/Container for QNAP
git clone https://github.com/yourusername/retire-cluster.git
cd retire-cluster
./docker/deploy.sh --data-path /volume1/docker/retire-cluster
```

## 🔧 Advanced Features

### Custom Device Roles

Define custom roles for specialized devices:

```python
# In worker configuration
config.role = "gpu-compute"  # For GPU-enabled devices
config.role = "storage"      # For NAS or storage servers
config.role = "mobile"       # For mobile devices
```

### Device Capabilities

The system automatically detects device capabilities:

- **Computational**: CPU cores, GPU availability
- **Storage**: Available disk space
- **Services**: Network services, automation capabilities

### Monitoring & Management

Monitor cluster status in real-time:

```python
# Get cluster statistics
stats = registry.get_cluster_stats()
print(f"Online devices: {stats['online_devices']}")
print(f"Total resources: {stats['total_resources']}")
```

## 📊 API Reference

### Message Protocol

The system uses JSON-based messaging over TCP sockets:

```json
{
  "message_type": "register|heartbeat|status",
  "sender_id": "device-id",
  "data": {
    // Message-specific data
  }
}
```

### Message Types

- **register**: Device registration with capabilities
- **heartbeat**: Periodic status updates with metrics
- **status**: Query cluster or device status
- **task_assign**: Assign task to device (planned)
- **task_result**: Return task execution results (planned)

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by distributed computing projects
- Built with Python's asyncio and socket libraries
- Special thanks to the open-source community

## 📞 Contact

- **GitHub Issues**: [Report bugs or request features](https://github.com/4ier/retire-cluster/issues)
- **Discussions**: [Join the conversation](https://github.com/4ier/retire-cluster/discussions)

## 🗺️ Roadmap

### v1.0.0 (Released)
- [x] Basic device management
- [x] TCP socket communication
- [x] Heartbeat monitoring
- [x] Cross-platform support
- [x] CLI package-based installation
- [x] Device profiling and auto-detection
- [x] Simple worker deployment

### v1.1.0 (Current)
- [x] Task execution framework
- [x] Intelligent task scheduling and queue management
- [x] Built-in task types (echo, sleep, system_info, etc.)
- [x] Task requirements and device capability matching
- [x] REST API with comprehensive endpoints
- [x] API authentication and security middleware
- [x] Complete API documentation and examples
- [x] Web dashboard with terminal-style interface
- [x] Docker deployment support with automated scripts

### v1.2.0 (In Progress)
- [x] CLI-style web interface with xterm.js terminal
- [x] Multi-format APIs (JSON, CSV, TSV, plain text)
- [x] Real-time streaming with Server-Sent Events
- [x] AI-friendly interface patterns
- [x] Docker containerization with health monitoring
- [x] Automated backup and recovery scripts
- [x] NAS deployment guides (Synology, QNAP)

### v2.0.0 (Future)
- [ ] Enhanced security with authentication and SSL/TLS
- [ ] Performance monitoring and metrics dashboard
- [ ] Advanced task scheduling algorithms
- [ ] Plugin system for custom task types
- [ ] Configuration management UI
- [ ] Multi-language worker support (Node.js, Go)

### Framework Integrations (Optional)
- [x] Temporal workflow integration support
- [x] Celery task queue integration  
- [x] HTTP bridge for external frameworks
- [ ] Basic monitoring integration (Prometheus metrics)

---

**Give your idle devices a new purpose! 🚀**