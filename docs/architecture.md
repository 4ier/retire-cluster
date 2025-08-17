# Retire-Cluster Architecture

## Overview

Retire-Cluster is a distributed system designed to repurpose idle devices into a unified computing cluster. The architecture follows a master-worker pattern with intelligent task scheduling and real-time monitoring.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Main Node                           │
│                    (NAS / Always-on Server)                 │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │              Core Components                        │     │
│  │                                                     │     │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │     │
│  │  │Device Registry│  │Task Scheduler │  │Heartbeat │ │     │
│  │  │& Metadata    │  │& Queue Mgmt  │  │Monitor   │ │     │
│  │  └──────────────┘  └──────────────┘  └──────────┘ │     │
│  │                                                     │     │
│  │  ┌──────────────────────────────────────────────┐  │     │
│  │  │             Communication Layer              │  │     │
│  │  │  - TCP Socket Server (Port 8080)            │  │     │
│  │  │  - JSON Message Protocol                     │  │     │
│  │  │  - Connection Pool Management                │  │     │
│  │  └──────────────────────────────────────────────┘  │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │                Web Dashboard                        │     │
│  │                                                     │     │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │     │
│  │  │CLI Interface │  │Terminal UI   │  │REST API  │ │     │
│  │  │(xterm.js)    │  │Renderer      │  │Endpoints │ │     │
│  │  └──────────────┘  └──────────────┘  └──────────┘ │     │
│  │                                                     │     │
│  │  ┌──────────────────────────────────────────────┐  │     │
│  │  │            Flask Web Server                  │  │     │
│  │  │  - Multi-format APIs (JSON/CSV/Text)        │  │     │
│  │  │  - Server-Sent Events (SSE)                 │  │     │
│  │  │  - Real-time Streaming                      │  │     │
│  │  └──────────────────────────────────────────────┘  │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │              Data Persistence                       │     │
│  │                                                     │     │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │     │
│  │  │SQLite        │  │Configuration │  │Log Files │ │     │
│  │  │Database      │  │JSON Files    │  │Rotation  │ │     │
│  │  └──────────────┘  └──────────────┘  └──────────┘ │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              ↕ TCP/JSON
                     Network Communication
                              ↕ Heartbeat/Tasks
┌─────────────────────────────────────────────────────────────┐
│                        Worker Nodes                         │
│                   (Distributed Devices)                     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Android     │  │   Old Laptop │  │ Raspberry Pi │     │
│  │   Device      │  │   / Desktop  │  │   / IoT      │     │
│  │              │  │              │  │              │     │
│  │ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────┐ │     │
│  │ │Termux    │ │  │ │Linux/Win │ │  │ │Linux ARM │ │     │
│  │ │Python    │ │  │ │Python    │ │  │ │Python    │ │     │
│  │ └──────────┘ │  │ └──────────┘ │  │ └──────────┘ │     │
│  │              │  │              │  │              │     │
│  │ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────┐ │     │
│  │ │Device    │ │  │ │System    │ │  │ │Hardware  │ │     │
│  │ │Profiler  │ │  │ │Monitor   │ │  │ │Interface │ │     │
│  │ └──────────┘ │  │ └──────────┘ │  │ └──────────┘ │     │
│  │              │  │              │  │              │     │
│  │ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────┐ │     │
│  │ │Task      │ │  │ │Task      │ │  │ │Task      │ │     │
│  │ │Executor  │ │  │ │Executor  │ │  │ │Executor  │ │     │
│  │ └──────────┘ │  │ └──────────┘ │  │ └──────────┘ │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### Main Node Components

#### 1. Device Registry & Metadata Manager
- **Purpose**: Centralized device information storage and management
- **Responsibilities**:
  - Device registration and deregistration
  - Capability tracking (CPU, memory, platform, services)
  - Device role management (compute, mobile, storage, etc.)
  - Metadata persistence in SQLite database

```python
class DeviceRegistry:
    def register_device(self, device_info: DeviceInfo) -> bool
    def update_device_status(self, device_id: str, status: DeviceStatus)
    def get_devices_by_capability(self, requirements: TaskRequirements) -> List[Device]
    def mark_device_offline(self, device_id: str, reason: str)
```

#### 2. Task Scheduler & Queue Manager
- **Purpose**: Intelligent task distribution and execution management
- **Features**:
  - Priority-based task queuing
  - Device capability matching
  - Load balancing algorithms
  - Task timeout and retry mechanisms
  - Fault tolerance and failover

```python
class TaskScheduler:
    def submit_task(self, task: Task) -> str  # Returns task_id
    def schedule_task(self, task: Task) -> Optional[Device]
    def handle_task_completion(self, task_id: str, result: TaskResult)
    def handle_device_failure(self, device_id: str)
```

#### 3. Heartbeat Monitor
- **Purpose**: Real-time device health monitoring and failure detection
- **Features**:
  - Periodic heartbeat collection (60-second intervals)
  - Device offline detection (300-second timeout)
  - Automatic failover and task redistribution
  - Performance metrics aggregation

```python
class HeartbeatMonitor:
    def process_heartbeat(self, device_id: str, metrics: SystemMetrics)
    def check_device_timeouts(self) -> List[str]  # Returns offline devices
    def update_cluster_metrics(self)
```

#### 4. Communication Layer
- **Protocol**: TCP sockets with JSON messaging
- **Features**:
  - Asynchronous connection handling
  - Message type routing and validation
  - Connection pool management
  - Error handling and recovery

```python
class ClusterServer:
    def start_server(self, host: str, port: int)
    def handle_client_connection(self, client_socket: socket.socket)
    def process_message(self, message: Message) -> Response
    def broadcast_message(self, message: Message, target_devices: List[str])
```

### Web Dashboard Components

#### 1. CLI Interface (xterm.js)
- **Purpose**: Terminal-style web interface for cluster management
- **Features**:
  - Full terminal emulation with xterm.js
  - Command auto-completion and history
  - Real-time command execution
  - Multi-theme support (Matrix, Amber, Blue)

#### 2. Terminal UI Renderer
- **Purpose**: ASCII art and table rendering for CLI output
- **Features**:
  - ASCII table generation
  - Progress bars and status indicators
  - Device grid visualization
  - Log entry formatting
  - Color-coded output

#### 3. REST API Layer
- **Purpose**: Multi-format APIs for human and machine access
- **Endpoints**:
  - `/text/*` - Plain text, CSV, TSV formats (AI-friendly)
  - `/api/v1/*` - JSON APIs for programmatic access
  - `/stream/*` - Server-Sent Events for real-time updates

```python
# Text API Examples
GET /text/devices              # Pipe-delimited device list
GET /text/status               # Key-value cluster status
GET /text/metrics              # Prometheus format metrics

# JSON API Examples
GET /api/v1/devices            # Structured device data
POST /api/v1/command           # Execute CLI commands
GET /api/v1/cluster/status     # Cluster information

# Streaming API Examples
GET /stream/devices            # Real-time device updates
GET /stream/logs               # Live log streaming
```

### Worker Node Components

#### 1. Device Profiler
- **Purpose**: Automatic hardware and software capability detection
- **Capabilities Detected**:
  - System information (OS, architecture, Python version)
  - Hardware resources (CPU cores, memory, disk space)
  - Network configuration
  - Available services and tools
  - Platform-specific features

```python
class DeviceProfiler:
    def get_system_info(self) -> SystemInfo
    def get_hardware_specs(self) -> HardwareSpecs
    def detect_capabilities(self) -> List[Capability]
    def get_performance_metrics(self) -> PerformanceMetrics
```

#### 2. System Monitor
- **Purpose**: Continuous resource monitoring and reporting
- **Metrics Collected**:
  - CPU usage and load average
  - Memory utilization
  - Disk I/O and space usage
  - Network statistics
  - Temperature and battery status (mobile devices)

#### 3. Task Executor
- **Purpose**: Execute assigned tasks and report results
- **Features**:
  - Sandboxed task execution
  - Resource limit enforcement
  - Progress reporting
  - Error handling and recovery
  - Platform-specific optimizations

```python
class TaskExecutor:
    def execute_task(self, task: Task) -> TaskResult
    def monitor_task_progress(self, task_id: str) -> ProgressReport
    def cancel_task(self, task_id: str) -> bool
    def cleanup_task_resources(self, task_id: str)
```

## Communication Protocol

### Message Types

The system uses a JSON-based messaging protocol over TCP sockets:

#### 1. Registration Message
```json
{
  "message_type": "register",
  "sender_id": "device-001",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "device_info": {
      "hostname": "android-phone",
      "platform": "android",
      "architecture": "aarch64",
      "python_version": "3.11.0",
      "role": "mobile"
    },
    "hardware_specs": {
      "cpu_cores": 8,
      "memory_total": 8589934592,
      "disk_space": 128849018880,
      "network_interfaces": ["wlan0"]
    },
    "capabilities": [
      "computational",
      "network_services",
      "mobile_specific"
    ]
  }
}
```

#### 2. Heartbeat Message
```json
{
  "message_type": "heartbeat",
  "sender_id": "device-001",
  "timestamp": "2024-01-15T10:31:00Z",
  "data": {
    "system_metrics": {
      "cpu_usage": 25.5,
      "memory_usage": 45.2,
      "disk_usage": 12.8,
      "load_average": [0.5, 0.3, 0.2],
      "uptime": 86400
    },
    "status": "online",
    "active_tasks": 2,
    "last_activity": "2024-01-15T10:30:45Z"
  }
}
```

#### 3. Task Assignment Message
```json
{
  "message_type": "task_assign",
  "sender_id": "main-node",
  "target_id": "device-001",
  "timestamp": "2024-01-15T10:32:00Z",
  "data": {
    "task": {
      "task_id": "task-abc123",
      "task_type": "python_eval",
      "priority": "normal",
      "timeout": 300,
      "payload": {
        "expression": "sum(range(100000))",
        "environment": {}
      },
      "requirements": {
        "min_cpu_cores": 2,
        "min_memory_gb": 1
      }
    }
  }
}
```

#### 4. Task Result Message
```json
{
  "message_type": "task_result",
  "sender_id": "device-001",
  "timestamp": "2024-01-15T10:32:30Z",
  "data": {
    "task_id": "task-abc123",
    "status": "completed",
    "execution_time": 28.5,
    "result": {
      "output": "4999950000",
      "exit_code": 0,
      "metrics": {
        "cpu_time": 25.2,
        "memory_peak": 1048576
      }
    }
  }
}
```

### Connection Management

#### Connection Lifecycle
1. **Client Connect**: Worker node establishes TCP connection to Main node
2. **Registration**: Worker sends device info and capabilities
3. **Heartbeat Loop**: Periodic status updates every 60 seconds
4. **Task Execution**: Bidirectional task assignment and result reporting
5. **Graceful Disconnect**: Proper connection cleanup on shutdown

#### Error Handling
- **Connection Loss**: Automatic reconnection with exponential backoff
- **Message Corruption**: JSON validation and error recovery
- **Timeout Handling**: Configurable timeouts for different operations
- **Resource Cleanup**: Proper cleanup of resources on errors

## Data Flow

### Device Registration Flow
```
Worker Node                    Main Node
     │                            │
     │──── TCP Connect ──────────►│
     │◄─── Connection ACK ───────│
     │                            │
     │──── Register Message ────►│
     │                            │ ┌─────────────────┐
     │                            │ │ Validate Device │
     │                            │ │ Store Metadata  │
     │                            │ │ Update Registry │
     │                            │ └─────────────────┘
     │◄─── Registration ACK ─────│
     │                            │
     │──── Heartbeat Loop ──────►│
```

### Task Execution Flow
```
Main Node                     Worker Node
     │                            │
     │ ┌─────────────────┐        │
     │ │ Receive Task    │        │
     │ │ Match Device    │        │
     │ │ Check Resources │        │
     │ └─────────────────┘        │
     │                            │
     │──── Task Assignment ─────►│
     │                            │ ┌─────────────────┐
     │                            │ │ Validate Task   │
     │                            │ │ Execute Safely  │
     │                            │ │ Monitor Progress│
     │                            │ └─────────────────┘
     │◄─── Task Progress ────────│
     │◄─── Task Result ──────────│
     │                            │
     │ ┌─────────────────┐        │
     │ │ Process Result  │        │
     │ │ Update Status   │        │
     │ │ Notify Client   │        │
     │ └─────────────────┘        │
```

### Real-time Monitoring Flow
```
Worker Nodes              Main Node              Web Dashboard
     │                       │                       │
     │──── Heartbeats ─────►│                       │
     │                       │ ┌─────────────────┐   │
     │                       │ │ Aggregate       │   │
     │                       │ │ Metrics         │   │
     │                       │ │ Update Status   │   │
     │                       │ └─────────────────┘   │
     │                       │                       │
     │                       │◄─── API Requests ────│
     │                       │──── SSE Events ─────►│
     │                       │──── JSON/Text Data ──►│
```

## Deployment Architectures

### Single Host Development
```
┌─────────────────────────────────┐
│         Development Host         │
│                                 │
│  ┌───────────┐ ┌─────────────┐  │
│  │Main Node  │ │Worker Node  │  │
│  │(Terminal1)│ │(Terminal2)  │  │
│  └───────────┘ └─────────────┘  │
│                                 │
│  ┌─────────────────────────────┐ │
│  │      Web Dashboard          │ │
│  │     (Terminal3/Browser)     │ │
│  └─────────────────────────────┘ │
└─────────────────────────────────┘
```

### Distributed Production
```
┌─────────────────────┐         ┌──────────────────┐
│    NAS Server       │         │   Old Laptop     │
│                     │         │                  │
│ ┌─────────────────┐ │         │ ┌──────────────┐ │
│ │ Main Node       │ │         │ │ Worker Node  │ │
│ │ (Docker)        │ │◄───────►│ │ (Native)     │ │
│ └─────────────────┘ │         │ └──────────────┘ │
│                     │         └──────────────────┘
│ ┌─────────────────┐ │         
│ │ Web Dashboard   │ │         ┌──────────────────┐
│ │ (Docker)        │ │         │  Android Phone   │
│ └─────────────────┘ │         │                  │
└─────────────────────┘         │ ┌──────────────┐ │
                                │ │ Worker Node  │ │
┌─────────────────────┐         │ │ (Termux)     │ │
│   Raspberry Pi      │         │ └──────────────┘ │
│                     │         └──────────────────┘
│ ┌─────────────────┐ │         
│ │ Worker Node     │ │         ┌──────────────────┐
│ │ (Native)        │ │         │   Another Device │
│ └─────────────────┘ │         │                  │
└─────────────────────┘         │ ┌──────────────┐ │
                                │ │ Worker Node  │ │
                                │ │ (Native)     │ │
                                │ └──────────────┘ │
                                └──────────────────┘
```

### Docker-based Production (Recommended)
```
┌─────────────────────────────────────────────────────────────┐
│                       NAS Server                            │
│                                                             │
│  ┌────────────────────────────────────────────────────┐     │
│  │              Docker Environment                     │     │
│  │                                                     │     │
│  │  ┌──────────────────────┐  ┌──────────────────┐   │     │
│  │  │    retire-cluster    │  │      nginx       │   │     │
│  │  │     main-node        │  │   reverse-proxy  │   │     │
│  │  │                      │  │   (optional)     │   │     │
│  │  │ ┌──────────────────┐ │  │                  │   │     │
│  │  │ │  Main Node       │ │  │                  │   │     │
│  │  │ │  (Port 8080)     │ │  │                  │   │     │
│  │  │ └──────────────────┘ │  │                  │   │     │
│  │  │                      │  │                  │   │     │
│  │  │ ┌──────────────────┐ │  │                  │   │     │
│  │  │ │  Web Dashboard   │ │  │                  │   │     │
│  │  │ │  (Port 5000)     │ │  │                  │   │     │
│  │  │ └──────────────────┘ │  │                  │   │     │
│  │  └──────────────────────┘  └──────────────────┘   │     │
│  └────────────────────────────────────────────────────┘     │
│                                                             │
│  ┌────────────────────────────────────────────────────┐     │
│  │            Persistent Volumes                       │     │
│  │  /volume1/docker/retire-cluster/                   │     │
│  │  ├── config/    (Configuration files)              │     │
│  │  ├── database/  (SQLite database)                  │     │
│  │  └── logs/      (Application logs)                 │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## Scalability and Performance

### Horizontal Scaling
- **Worker Nodes**: Unlimited worker nodes can join the cluster
- **Load Distribution**: Intelligent task distribution based on device capabilities
- **Fault Tolerance**: Automatic failover when devices go offline

### Performance Optimizations
- **Connection Pooling**: Efficient TCP connection management
- **Async Processing**: Non-blocking I/O for handling multiple connections
- **Database Optimization**: WAL mode, indexing, and query optimization
- **Caching**: In-memory caching of frequently accessed data

### Resource Management
- **Memory Limits**: Configurable memory limits for task execution
- **CPU Throttling**: Prevent tasks from consuming excessive CPU
- **Disk Space Monitoring**: Automatic cleanup of old logs and temporary files
- **Network Bandwidth**: Rate limiting for heartbeat and data transfer

## Security Architecture

### Network Security
- **Internal Network**: Designed for trusted internal networks
- **Firewall Integration**: Port-based access control
- **TLS/SSL**: Future support for encrypted communications

### Application Security
- **Input Validation**: JSON schema validation for all messages
- **Resource Limits**: Sandboxed task execution with resource constraints
- **Access Control**: Device-based access control and role management
- **Audit Logging**: Comprehensive logging of all operations

### Container Security (Docker)
- **Non-root Execution**: Containers run as non-privileged user
- **Resource Isolation**: CPU and memory limits enforced
- **Read-only Root**: Optional read-only root filesystem
- **Secret Management**: Secure handling of configuration and credentials

## Monitoring and Observability

### Metrics Collection
- **System Metrics**: CPU, memory, disk, network usage
- **Application Metrics**: Task execution times, success rates
- **Cluster Metrics**: Device counts, task queues, throughput

### Logging Strategy
- **Structured Logging**: JSON-formatted logs with correlation IDs
- **Log Levels**: Configurable logging levels (DEBUG, INFO, WARN, ERROR)
- **Log Rotation**: Automatic rotation and retention policies
- **Centralized Logging**: Option to forward logs to external systems

### Health Monitoring
- **Health Checks**: HTTP endpoints for service health validation
- **Alerting**: Configurable alerts for failures and performance issues
- **Dashboard**: Real-time cluster visualization
- **Metrics Export**: Prometheus-compatible metrics export

## Future Architecture Enhancements

### Planned Features
- **Multi-cluster Federation**: Connect multiple clusters
- **Advanced Scheduling**: ML-based task placement optimization
- **Persistent Storage**: Distributed file system integration
- **Auto-scaling**: Dynamic worker node provisioning
- **API Gateway**: Centralized API management and security

### Integration Points
- **Kubernetes**: Native Kubernetes operator for orchestration
- **Cloud Providers**: Integration with AWS, Azure, GCP
- **Monitoring Systems**: Prometheus, Grafana, ELK stack integration
- **CI/CD Pipelines**: GitHub Actions, GitLab CI integration

This architecture provides a solid foundation for the Retire-Cluster system while maintaining flexibility for future enhancements and scalability requirements.