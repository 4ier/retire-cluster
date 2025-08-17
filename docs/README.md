# Retire-Cluster Documentation

## Overview

This directory contains comprehensive documentation for the Retire-Cluster distributed computing system.

## Documentation Index

### Core Guides

- **[Architecture](architecture.md)** - Complete system architecture, components, and design patterns
- **[Deployment Guide](deployment-guide.md)** - Comprehensive deployment instructions for all scenarios

### Web Interface Documentation

- **[Web Interface Design](web-interface-design.md)** - Terminal-style web dashboard design and architecture
- **[CLI Interface Specification](cli-interface-specification.md)** - Complete command reference and usage
- **[AI Integration Guide](ai-integration-guide.md)** - AI-friendly interface patterns and examples

### API Documentation

- **[REST API](rest_api.md)** - HTTP API endpoints and usage examples
- **[Task Execution Framework](task_execution_framework.md)** - Task scheduling and execution system

## Quick Reference

### Deployment Methods

1. **Docker (Recommended for Production)**
   ```bash
   git clone https://github.com/yourusername/retire-cluster.git
   cd retire-cluster
   ./docker/deploy.sh
   ```

2. **Native Installation**
   ```bash
   pip install retire-cluster
   retire-cluster-main --init-config
   ```

### Key Endpoints

- **Main Node**: `http://main-node:8080` (TCP socket server)
- **Web Dashboard**: `http://main-node:5000` (HTTP interface)
- **Health Check**: `http://main-node:8080/api/health`

### Common Commands

```bash
# CLI-style commands (via web interface)
devices list --status=online
cluster status
tasks submit echo --payload='{"message":"hello"}'
monitor logs --tail=100

# REST API calls
curl http://main-node:5000/text/devices
curl http://main-node:5000/api/v1/cluster/status
```

## Architecture Overview

```
Main Node (NAS/Server)           Worker Nodes (Distributed)
┌─────────────────────┐         ┌──────────────────────────┐
│ ┌─────────────────┐ │         │ Android │ Laptop │ RPi  │
│ │   Core System   │ │◄───────►│ Termux  │ Native │ ARM  │
│ │ Device Registry │ │         │         │        │      │
│ │ Task Scheduler  │ │         │ ┌─────────────────────┐ │
│ │ Heartbeat Mon.  │ │         │ │ Device Profiler     │ │
│ └─────────────────┘ │         │ │ System Monitor      │ │
│                     │         │ │ Task Executor       │ │
│ ┌─────────────────┐ │         │ └─────────────────────┘ │
│ │  Web Dashboard  │ │         └──────────────────────────┘
│ │ Terminal UI     │ │
│ │ REST API        │ │
│ │ Real-time SSE   │ │
│ └─────────────────┘ │
└─────────────────────┘
```

## Getting Started

1. **Read the [Architecture Guide](architecture.md)** to understand the system design
2. **Follow the [Deployment Guide](deployment-guide.md)** for your specific scenario
3. **Explore the [Web Interface](web-interface-design.md)** documentation for dashboard usage
4. **Check the [CLI Specification](cli-interface-specification.md)** for command reference

## Contributing

When adding new documentation:

1. Follow the existing structure and style
2. Include practical examples and code snippets
3. Update this index when adding new files
4. Keep documentation synchronized with code changes

## Support

- **GitHub Issues**: Report bugs or request features
- **GitHub Discussions**: Ask questions and share ideas
- **Main Documentation**: See project README.md for overview