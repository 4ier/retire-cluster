# Retire-Cluster REST API

The Retire-Cluster REST API provides comprehensive management and monitoring capabilities for your distributed computing cluster through HTTP endpoints.

## Quick Start

### Installation

Install with API support:
```bash
pip install retire-cluster[api]
```

### Starting the API Server

```bash
# Start with default settings
retire-cluster-api

# Start with custom configuration
retire-cluster-api --host 0.0.0.0 --port 8081 --auth --api-key your-secret-key

# Connect to specific cluster node
retire-cluster-api --cluster-host 192.168.1.100 --cluster-port 8080
```

### Basic Usage

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
  -d '{"task_type": "echo", "payload": {"message": "Hello World"}}'
```

## API Overview

### Base URL
```
http://localhost:8081/api/v1
```

### Authentication
API supports optional API key authentication:
```bash
# Include API key in header
curl -H "X-API-Key: your-secret-key" http://localhost:8081/api/v1/cluster/config

# Or use Authorization header
curl -H "Authorization: Bearer your-secret-key" http://localhost:8081/api/v1/cluster/config
```

### Response Format
All API responses follow a consistent format:
```json
{
  "status": "success|error",
  "data": {},
  "message": "Optional message",
  "timestamp": "2023-01-01T12:00:00Z",
  "request_id": "uuid"
}
```

## Cluster Management

### Get Cluster Status
```http
GET /api/v1/cluster/status
```

Returns comprehensive cluster statistics including device count, health percentage, and resource totals.

**Response:**
```json
{
  "status": "success",
  "data": {
    "cluster_stats": {
      "total_devices": 5,
      "online_devices": 4,
      "offline_devices": 1,
      "health_percentage": 80.0,
      "total_resources": {
        "cpu_cores": 32,
        "memory_gb": 128,
        "storage_gb": 2000
      },
      "by_role": {
        "compute": 2,
        "mobile": 2,
        "storage": 1
      },
      "by_platform": {
        "linux": 2,
        "android": 2,
        "windows": 1
      }
    },
    "server_info": {
      "version": "1.0.0",
      "uptime": "2d 4h 30m",
      "host": "0.0.0.0",
      "port": 8080
    }
  }
}
```

### Health Check
```http
GET /health
```

Simple health check endpoint for monitoring.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2023-01-01T12:00:00Z",
  "components": {
    "api": "healthy",
    "cluster_server": "healthy",
    "task_scheduler": "healthy"
  }
}
```

### Get Cluster Metrics
```http
GET /api/v1/cluster/metrics
```

Detailed performance and utilization metrics.

### Get Configuration
```http
GET /api/v1/cluster/config
```
**Requires Authentication**

Returns cluster configuration settings.

## Device Management

### List Devices
```http
GET /api/v1/devices?page=1&page_size=20&status=online&role=compute
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `page_size` (int): Items per page (default: 20, max: 100)
- `status` (string): Filter by status (`online`, `offline`, `all`)
- `role` (string): Filter by role (`worker`, `compute`, `storage`, `mobile`)
- `platform` (string): Filter by platform (`linux`, `windows`, `android`, `darwin`)
- `tags` (array): Filter by tags

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "device_id": "laptop-001",
      "role": "compute",
      "platform": "linux",
      "status": "online",
      "ip_address": "192.168.1.101",
      "last_heartbeat": "2023-01-01T12:00:00Z",
      "uptime": "2h 30m",
      "capabilities": {
        "cpu_count": 8,
        "memory_total_gb": 16,
        "storage_total_gb": 500,
        "has_gpu": true
      },
      "tags": ["development", "gpu-capable"]
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 5,
    "total_pages": 1,
    "has_next": false,
    "has_previous": false
  }
}
```

### Get Device Details
```http
GET /api/v1/devices/{device_id}
```

Returns detailed information about a specific device.

### Get Device Status
```http
GET /api/v1/devices/{device_id}/status
```

Get current status and health of a device.

### Ping Device
```http
POST /api/v1/devices/{device_id}/ping
```
**Requires Authentication**

Test connectivity to a specific device.

### Remove Device
```http
DELETE /api/v1/devices/{device_id}
```
**Requires Authentication**

Remove a device from the cluster.

### Device Summary
```http
GET /api/v1/devices/summary
```

Get summary statistics of all devices.

## Task Management

### Submit Task
```http
POST /api/v1/tasks
Content-Type: application/json
```

**Request Body:**
```json
{
  "task_type": "echo",
  "payload": {
    "message": "Hello World"
  },
  "priority": "normal",
  "requirements": {
    "min_cpu_cores": 2,
    "min_memory_gb": 4,
    "required_platform": "linux",
    "timeout_seconds": 300
  },
  "metadata": {
    "created_by": "api_user"
  }
}
```

**Task Types:**
- `echo`: Returns payload as-is
- `sleep`: Sleep for specified duration
- `system_info`: Returns device capabilities
- `python_eval`: Evaluate Python expression
- `http_request`: Make HTTP requests
- `command`: Execute shell commands

**Priority Levels:**
- `low`, `normal`, `high`, `urgent`

**Requirements:**
- `min_cpu_cores` (int): Minimum CPU cores
- `min_memory_gb` (float): Minimum memory in GB
- `min_storage_gb` (float): Minimum storage in GB
- `required_platform` (string): Required platform
- `required_role` (string): Required device role
- `required_tags` (array): Required device tags
- `gpu_required` (bool): GPU required
- `internet_required` (bool): Internet access required
- `timeout_seconds` (int): Maximum execution time
- `max_retries` (int): Maximum retry attempts

**Response:**
```json
{
  "status": "success",
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "task": {
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "task_type": "echo",
      "status": "queued",
      "priority": "normal",
      "created_at": "2023-01-01T12:00:00Z"
    }
  }
}
```

### List Tasks
```http
GET /api/v1/tasks?status=running&page=1&page_size=20
```

**Query Parameters:**
- `page` (int): Page number
- `page_size` (int): Items per page
- `status` (string): Filter by status
- `task_type` (string): Filter by task type
- `priority` (string): Filter by priority
- `device_id` (string): Filter by assigned device

**Task Statuses:**
- `pending`: Task created but not queued
- `queued`: Waiting for available device
- `assigned`: Assigned to specific device
- `running`: Currently executing
- `success`: Completed successfully
- `failed`: Failed with error
- `cancelled`: Cancelled by user
- `timeout`: Exceeded timeout limit

### Get Task Details
```http
GET /api/v1/tasks/{task_id}
```

Returns complete task information including payload, requirements, and results.

### Get Task Status
```http
GET /api/v1/tasks/{task_id}/status
```

Get current status and execution progress.

### Get Task Result
```http
GET /api/v1/tasks/{task_id}/result
```

Get execution result for completed tasks.

**Response:**
```json
{
  "status": "success",
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "success",
    "result_data": {
      "echo": {"message": "Hello World"}
    },
    "execution_time_seconds": 0.05,
    "worker_device_id": "laptop-001",
    "started_at": "2023-01-01T12:00:00Z",
    "completed_at": "2023-01-01T12:00:00Z"
  }
}
```

### Cancel Task
```http
POST /api/v1/tasks/{task_id}/cancel
```
**Requires Authentication**

Cancel a running or queued task.

### Retry Task
```http
POST /api/v1/tasks/{task_id}/retry
```
**Requires Authentication**

Retry a failed task.

### Task Statistics
```http
GET /api/v1/tasks/statistics
```

Get task execution statistics and performance metrics.

### Supported Task Types
```http
GET /api/v1/tasks/types
```

Get list of supported task types across all devices.

## Configuration Management

### Get Configuration
```http
GET /api/v1/config
```
**Requires Authentication**

Get complete system configuration.

### Get Server Config
```http
GET /api/v1/config/server
```
**Requires Authentication**

### Update Server Config
```http
PUT /api/v1/config/server
Content-Type: application/json
```
**Requires Authentication**

```json
{
  "max_connections": 100
}
```

### Get Heartbeat Config
```http
GET /api/v1/config/heartbeat
```
**Requires Authentication**

### Update Heartbeat Config
```http
PUT /api/v1/config/heartbeat
Content-Type: application/json
```
**Requires Authentication**

```json
{
  "interval": 60,
  "timeout": 300,
  "max_missed": 3
}
```

### Reset Configuration
```http
POST /api/v1/config/reset
```
**Requires Authentication**

Reset all configuration to defaults.

## Error Handling

### Error Response Format
```json
{
  "status": "error",
  "message": "Error description",
  "error_code": "ERROR_CODE",
  "error_details": {
    "field": "field_name",
    "reason": "validation_error"
  },
  "timestamp": "2023-01-01T12:00:00Z",
  "request_id": "uuid"
}
```

### Common Error Codes
- `VALIDATION_ERROR`: Request validation failed
- `NOT_FOUND`: Resource not found
- `DEVICE_NOT_FOUND`: Device not found
- `TASK_NOT_FOUND`: Task not found
- `UNAUTHORIZED`: Authentication required
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INTERNAL_ERROR`: Server error

### HTTP Status Codes
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `404`: Not Found
- `429`: Too Many Requests
- `500`: Internal Server Error
- `503`: Service Unavailable

## Rate Limiting

Default rate limits:
- 60 requests per minute per client
- 1000 requests per hour per client
- 10 request burst size

Rate limit headers:
```
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1640995200
```

## WebSocket Support (Future)

Real-time updates will be available via WebSocket:
```javascript
const ws = new WebSocket('ws://localhost:8081/ws');
ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log('Cluster update:', update);
};
```

## SDK Examples

### Python SDK
```python
import requests

class RetireClusterAPI:
    def __init__(self, base_url, api_key=None):
        self.base_url = base_url
        self.headers = {'Content-Type': 'application/json'}
        if api_key:
            self.headers['X-API-Key'] = api_key
    
    def get_cluster_status(self):
        response = requests.get(
            f"{self.base_url}/cluster/status",
            headers=self.headers
        )
        return response.json()
    
    def submit_task(self, task_type, payload, **kwargs):
        data = {
            'task_type': task_type,
            'payload': payload,
            **kwargs
        }
        response = requests.post(
            f"{self.base_url}/tasks",
            json=data,
            headers=self.headers
        )
        return response.json()

# Usage
api = RetireClusterAPI('http://localhost:8081/api/v1')
status = api.get_cluster_status()
task = api.submit_task('echo', {'message': 'Hello'})
```

### JavaScript SDK
```javascript
class RetireClusterAPI {
  constructor(baseUrl, apiKey) {
    this.baseUrl = baseUrl;
    this.headers = {'Content-Type': 'application/json'};
    if (apiKey) {
      this.headers['X-API-Key'] = apiKey;
    }
  }
  
  async getClusterStatus() {
    const response = await fetch(`${this.baseUrl}/cluster/status`, {
      headers: this.headers
    });
    return response.json();
  }
  
  async submitTask(taskType, payload, options = {}) {
    const data = {
      task_type: taskType,
      payload: payload,
      ...options
    };
    const response = await fetch(`${this.baseUrl}/tasks`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify(data)
    });
    return response.json();
  }
}

// Usage
const api = new RetireClusterAPI('http://localhost:8081/api/v1');
const status = await api.getClusterStatus();
const task = await api.submitTask('echo', {message: 'Hello'});
```

## Production Deployment

### Using Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8081 retire_cluster.api.wsgi:app
```

### Using Docker
```dockerfile
FROM python:3.11-slim

COPY . /app
WORKDIR /app

RUN pip install retire-cluster[api]
EXPOSE 8081

CMD ["retire-cluster-api", "--host", "0.0.0.0", "--port", "8081"]
```

### Environment Variables
```bash
export RETIRE_CLUSTER_API_HOST=0.0.0.0
export RETIRE_CLUSTER_API_PORT=8081
export RETIRE_CLUSTER_API_KEY=your-secret-key
export RETIRE_CLUSTER_CLUSTER_HOST=localhost
export RETIRE_CLUSTER_CLUSTER_PORT=8080
```

## Monitoring and Logging

### Prometheus Metrics (Future)
```
# HELP retire_cluster_devices_total Total number of registered devices
# TYPE retire_cluster_devices_total gauge
retire_cluster_devices_total{status="online"} 4

# HELP retire_cluster_tasks_total Total number of tasks
# TYPE retire_cluster_tasks_total counter
retire_cluster_tasks_total{status="success"} 1250
```

### Log Format
```json
{
  "timestamp": "2023-01-01T12:00:00Z",
  "level": "INFO",
  "logger": "api.requests",
  "message": "Request processed",
  "request_id": "uuid",
  "method": "GET",
  "path": "/api/v1/cluster/status",
  "status_code": 200,
  "duration_ms": 45.2
}
```

## Security Best Practices

1. **Use HTTPS in production**
2. **Enable API key authentication**
3. **Configure proper CORS settings**
4. **Implement rate limiting**
5. **Monitor API access logs**
6. **Keep API keys secure**
7. **Use least privilege principle**
8. **Regular security updates**

## Troubleshooting

### Common Issues

**API server won't start**
- Check if Flask is installed: `pip install retire-cluster[api]`
- Verify port is not in use: `netstat -an | grep 8081`
- Check cluster connectivity

**Authentication errors**
- Verify API key is correct
- Check header format: `X-API-Key: your-key`
- Ensure authentication is enabled: `--auth`

**Task submission fails**
- Verify task type is supported: `GET /api/v1/tasks/types`
- Check device requirements match available devices
- Review payload format and validation

**Rate limit exceeded**
- Reduce request frequency
- Use batch operations when possible
- Consider increasing rate limits for high-volume usage

### Debug Mode
```bash
retire-cluster-api --debug
```

Enables detailed logging and error traces.