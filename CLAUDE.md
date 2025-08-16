# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Retire-Cluster is an idle device reuse solution that organizes old phones, tablets, and laptops into a unified AI work cluster using the MCP (Model Context Protocol). The system enables device auto-discovery, real-time status monitoring, and intelligent task scheduling integrated with Claude Code.

## Architecture

The system follows a distributed architecture with three node types:

1. **Main Node**: Cluster coordinator and management center (requires high-performance device)
2. **Worker Node**: Task execution units (supports Linux, Android/Termux, macOS, Windows)
3. **Storage Node**: Data storage and file services (recommended: NAS devices)

The Main node manages device metadata, monitors heartbeats, and schedules tasks across the cluster. Worker nodes self-report capabilities and execute assigned tasks.

## Development Commands

### Setting Up Main Node
```bash
# Install dependencies
pip install psutil requests mcp-sdk sqlite3 asyncio

# Start Main MCP server
python main_node_server.py

# Configure Claude Code integration
claude mcp add retire-cluster --server "python main_node_server.py"
```

### Setting Up Worker Node
```bash
# Install worker dependencies
pip install psutil requests mcp-sdk

# Start Worker service with device ID and role
python worker_node_client.py --device-id "worker-001" --role "worker"
```

### Testing and Debugging
```bash
# Enable debug mode
python main_node_server.py --debug

# Run network diagnostics
python tools/network_diagnostic.py

# Check logs
tail -f logs/cluster_manager.log
tail -f logs/worker_node.log
```

## Key Implementation Areas

### Device Management System
- Device registration and metadata storage in `cluster_metadata.db`
- Heartbeat mechanism with 60-second intervals and 300-second timeout threshold
- Device capability tracking (computational, services, automation)

### Task Scheduling
- Smart weighted scheduling algorithm with load balancing
- Task type to device role mapping in `main_node_server.py`
- Fallback and retry mechanisms for fault tolerance

### MCP Integration
- Main node exposes MCP tools for cluster management
- Worker nodes use MCP client for communication
- Natural language interface through Claude Code

## Configuration Structure

### Main Node Config (`config.json`)
- Server settings (host, port, max connections)
- Database path and backup settings
- Heartbeat intervals and thresholds
- Scheduling algorithm and load balancing options

### Worker Node Config (`worker_config.json`)
- Device ID, role, and tags
- Main node connection details
- Resource limits (CPU, memory, storage thresholds)
- Maximum concurrent tasks

## Implementation Status ✅ COMPLETED

The project has been fully implemented and tested:

### Completed Features
1. ✅ **Modular Python Package Structure** (`retire_cluster/`)
   - Core configuration and logging (`core/`)
   - Device profiling and registry (`device/`)
   - Communication protocol and networking (`communication/`)

2. ✅ **Main Node Server** - DEPLOYED on 192.168.0.116:8080
   - Legacy-compatible server for Python 3.7+
   - Device registration and management
   - Heartbeat monitoring and offline detection
   - JSON-based messaging protocol
   - Thread-safe device registry

3. ✅ **Worker Node Client** - READY for Android deployment
   - Cross-platform compatibility (Windows/Linux/Android/Termux)
   - Automatic device profiling and hardware detection
   - Platform-specific capability detection
   - Persistent heartbeat reporting
   - Graceful error handling and reconnection

4. ✅ **Communication Protocol**
   - TCP socket-based messaging
   - JSON message format with type validation
   - Register, heartbeat, status, and error messages
   - Response acknowledgment system

### Testing Results
- ✅ Main node deployed and running on QNAP NAS
- ✅ Local worker connection test successful
- ✅ Device registration and heartbeat verified
- ✅ Cluster status monitoring functional
- ✅ Cross-platform compatibility confirmed

## Test Environment

### Test Nodes
- **Main Node**: `ssh 18617007050@192.168.0.116` (Standard Linux environment)
- **Worker Node**: `ssh u0_a463@192.168.0.111 -p 8022` (Android Termux environment)

### Deployment Commands
```bash
# Deploy to Main Node (192.168.0.116) - COMPLETED ✅
scp simple_legacy_main.py 18617007050@192.168.0.116:~/
ssh 18617007050@192.168.0.116 "/share/CACHEDEV1_DATA/.samba_python3/Python3/bin/python3 ~/simple_legacy_main.py"

# Deploy to Worker Node (192.168.0.111:8022) - READY
scp -P 8022 simple_legacy_worker.py u0_a463@192.168.0.111:~/
ssh -p 8022 u0_a463@192.168.0.111 "python simple_legacy_worker.py --device-id android-001 --role mobile --main-host 192.168.0.116"

# Test Connection
python simple_legacy_worker.py --device-id test-001 --test --main-host 192.168.0.116
```

## Important Notes

- All devices must be on the same network for communication
- Python 3.8+ is required on all nodes
- The system uses MIT license
- Security considerations: implement SSH key auth, firewall rules, and API token validation