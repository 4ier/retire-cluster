# AI Integration Guide

## Overview

This guide explains how AI agents and automation tools can effectively interact with the Retire-Cluster system through its CLI-first interface design.

## Why CLI Interface is AI-Friendly

### Comparison with Traditional Web UIs

| Aspect | Traditional Web UI | CLI Interface | AI Advantage |
|--------|-------------------|---------------|--------------|
| **Data Extraction** | Parse HTML/CSS/JS | Read plain text | 100x faster, no DOM parsing |
| **Action Execution** | Simulate clicks/forms | Send commands | Direct, deterministic |
| **State Understanding** | Interpret visual elements | Parse structured text | Unambiguous |
| **Error Handling** | Parse error modals | Read stderr | Standard error codes |
| **Batch Operations** | Complex automation | Simple scripting | Native support |
| **Resource Usage** | Heavy (browser engine) | Minimal (text only) | 10x less memory |

## Quick Start for AI Agents

### 1. Basic Connection

```bash
# Direct command execution
curl -X POST http://cluster.local/api/v1/command \
  -H "Content-Type: application/json" \
  -H "Accept: text/plain" \
  -d '{"command": "devices list --format=text"}'

# Response (plain text)
android-001|online|42|2.1|3
laptop-002|online|15|4.5|1
raspi-003|offline|0|0|0
```

### 2. Structured Data Access

```python
# Python example for AI agents
import requests

class RetireClusterClient:
    def __init__(self, base_url="http://cluster.local"):
        self.base_url = base_url
    
    def execute_command(self, command):
        response = requests.post(
            f"{self.base_url}/api/v1/command",
            json={"command": command},
            headers={"Accept": "application/json"}
        )
        return response.json()
    
    def get_devices(self, status=None):
        cmd = "devices list"
        if status:
            cmd += f" --status={status}"
        return self.execute_command(cmd)
    
    def submit_task(self, task_type, payload, device=None):
        cmd = f"tasks submit {task_type} --payload='{payload}'"
        if device:
            cmd += f" --device={device}"
        return self.execute_command(cmd)

# Usage
client = RetireClusterClient()
online_devices = client.get_devices(status="online")
result = client.submit_task("echo", '{"message": "test"}')
```

## API Endpoints for AI Access

### Text-Based Endpoints (Recommended for AI)

These endpoints return plain text, optimized for parsing:

| Endpoint | Method | Description | Response Format |
|----------|--------|-------------|-----------------|
| `/text/devices` | GET | List all devices | TSV |
| `/text/tasks` | GET | List all tasks | TSV |
| `/text/status` | GET | Cluster status | Key-value pairs |
| `/text/metrics` | GET | Current metrics | Prometheus format |
| `/text/logs` | GET | Recent logs | Plain text |

### Command Execution Endpoint

```http
POST /api/v1/command
Content-Type: application/json
Accept: text/plain | application/json

{
  "command": "devices list --status=online",
  "format": "text"
}
```

### Streaming Endpoints

For real-time monitoring:

```bash
# Server-Sent Events (SSE)
curl -N http://cluster.local/stream/devices

# WebSocket
wscat -c ws://cluster.local/ws/monitor
```

## Integration Patterns

### Pattern 1: Direct Command Execution

Best for: Simple operations, one-off tasks

```python
def execute_cluster_command(command):
    response = requests.post(
        "http://cluster.local/api/v1/command",
        json={"command": command},
        headers={"Accept": "text/plain"}
    )
    return response.text

# Example: Get online devices
devices = execute_cluster_command("devices list --status=online")
for line in devices.strip().split('\n'):
    device_id, status, cpu, memory, tasks = line.split('|')
    print(f"Device {device_id}: CPU={cpu}%")
```

### Pattern 2: Structured API Access

Best for: Complex workflows, data processing

```python
class ClusterAPI:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
    
    def get_json(self, endpoint):
        return self.session.get(f"{self.base_url}{endpoint}").json()
    
    def get_text(self, endpoint):
        return self.session.get(
            f"{self.base_url}{endpoint}",
            headers={"Accept": "text/plain"}
        ).text
    
    def post_command(self, command):
        return self.session.post(
            f"{self.base_url}/api/v1/command",
            json={"command": command}
        ).json()

# Usage
api = ClusterAPI("http://cluster.local")
devices = api.get_text("/text/devices")
status = api.get_json("/api/v1/cluster/status")
```

### Pattern 3: Event-Driven Monitoring

Best for: Real-time responses, alerting

```python
import sseclient

def monitor_events(url):
    response = requests.get(url, stream=True)
    client = sseclient.SSEClient(response)
    
    for event in client.events():
        data = json.loads(event.data)
        if data['type'] == 'device_offline':
            handle_device_offline(data['device_id'])
        elif data['type'] == 'task_failed':
            handle_task_failure(data['task_id'])

# Start monitoring
monitor_events("http://cluster.local/stream/events")
```

### Pattern 4: Batch Operations

Best for: Bulk tasks, scheduled operations

```python
def batch_submit_tasks(tasks):
    results = []
    for task in tasks:
        cmd = f"tasks submit {task['type']} --payload='{json.dumps(task['payload'])}'"
        if 'device' in task:
            cmd += f" --device={task['device']}"
        
        result = execute_command(cmd)
        results.append(result)
    
    return results

# Submit multiple tasks
tasks = [
    {"type": "echo", "payload": {"msg": "test1"}, "device": "android-001"},
    {"type": "echo", "payload": {"msg": "test2"}, "device": "laptop-002"},
]
results = batch_submit_tasks(tasks)
```

## CLI Browser Access (w3m, lynx, curl)

### Using w3m

```bash
# View cluster status
w3m -dump http://cluster.local/cli/status

# Execute command via URL
w3m -dump "http://cluster.local/cli/exec?cmd=devices+list"

# Interactive session
w3m http://cluster.local/cli
```

### Using lynx

```bash
# Get device list
lynx -dump http://cluster.local/text/devices

# View formatted output
lynx -width=120 -dump http://cluster.local/cli/dashboard
```

### Using curl

```bash
# Simple text output
curl -s http://cluster.local/text/devices

# JSON output
curl -s -H "Accept: application/json" http://cluster.local/api/v1/devices

# Execute command
curl -s -X POST http://cluster.local/api/v1/command \
  -d '{"command": "devices list --format=csv"}' \
  -H "Accept: text/csv"

# Stream logs
curl -N http://cluster.local/stream/logs | while read line; do
  echo "$(date): $line"
done
```

## Output Parsing Examples

### Parsing TSV Output

```python
def parse_devices_tsv(tsv_data):
    devices = []
    for line in tsv_data.strip().split('\n'):
        if line.startswith('#') or not line:
            continue
        
        parts = line.split('\t')
        devices.append({
            'id': parts[0],
            'status': parts[1],
            'cpu': float(parts[2]),
            'memory': float(parts[3]),
            'tasks': int(parts[4])
        })
    
    return devices

# Example usage
tsv_data = requests.get("http://cluster.local/text/devices").text
devices = parse_devices_tsv(tsv_data)
```

### Parsing Pipe-Delimited Output

```python
def parse_pipe_delimited(data):
    rows = []
    for line in data.strip().split('\n'):
        rows.append(line.split('|'))
    return rows

# Example
data = "android-001|online|42|2.1|3\nlaptop-002|online|15|4.5|1"
parsed = parse_pipe_delimited(data)
```

### Parsing Key-Value Output

```python
def parse_key_value(data):
    result = {}
    for line in data.strip().split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            result[key.strip()] = value.strip()
    return result

# Example
status_data = """
STATUS: healthy
NODES: 5/7 online
CPU: 48 cores (37% utilized)
MEMORY: 128GB (42% used)
"""
status = parse_key_value(status_data)
```

## Error Handling

### Standard Error Response Format

```json
{
  "status": "error",
  "error_code": 404,
  "message": "Device not found",
  "details": "No device with ID 'android-999'",
  "suggestion": "Use 'devices list' to see available devices"
}
```

### Exit Codes

```python
import subprocess

def execute_cli_command(command):
    result = subprocess.run(
        ['retire-cluster'] + command.split(),
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        return result.stdout
    elif result.returncode == 6:
        raise ResourceNotFoundError(result.stderr)
    elif result.returncode == 5:
        raise AuthenticationError(result.stderr)
    else:
        raise CommandError(f"Exit code {result.returncode}: {result.stderr}")
```

## Best Practices for AI Integration

### 1. Use Appropriate Output Formats

```python
# For data processing: JSON
response = api.get("/api/v1/devices", headers={"Accept": "application/json"})
devices = response.json()

# For simple parsing: TSV/CSV
response = api.get("/text/devices", headers={"Accept": "text/tab-separated-values"})
devices = csv.DictReader(io.StringIO(response.text), delimiter='\t')

# For logging: Plain text
response = api.get("/text/logs", headers={"Accept": "text/plain"})
print(response.text)
```

### 2. Implement Retry Logic

```python
import time
from functools import wraps

def retry(max_attempts=3, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts >= max_attempts:
                        raise
                    time.sleep(delay * attempts)
            return None
        return wrapper
    return decorator

@retry(max_attempts=3, delay=2)
def get_device_status(device_id):
    return api.get(f"/api/v1/devices/{device_id}")
```

### 3. Use Streaming for Real-time Data

```python
def stream_logs(device_id=None):
    url = "http://cluster.local/stream/logs"
    if device_id:
        url += f"?device={device_id}"
    
    with requests.get(url, stream=True) as response:
        for line in response.iter_lines():
            if line:
                process_log_line(line.decode('utf-8'))
```

### 4. Batch Operations for Efficiency

```python
def batch_device_check(device_ids):
    # Instead of multiple API calls
    # devices = [api.get(f"/api/v1/devices/{id}") for id in device_ids]
    
    # Use single command with filtering
    all_devices = api.get("/text/devices")
    return [d for d in parse_devices(all_devices) if d['id'] in device_ids]
```

### 5. Cache Frequently Accessed Data

```python
from functools import lru_cache
from datetime import datetime, timedelta

class CachedAPI:
    def __init__(self, base_url, cache_ttl=60):
        self.base_url = base_url
        self.cache_ttl = cache_ttl
        self._cache = {}
    
    def get_cached(self, endpoint):
        now = datetime.now()
        if endpoint in self._cache:
            data, timestamp = self._cache[endpoint]
            if now - timestamp < timedelta(seconds=self.cache_ttl):
                return data
        
        data = requests.get(f"{self.base_url}{endpoint}").text
        self._cache[endpoint] = (data, now)
        return data
```

## Example AI Agent Implementation

### Complete AI Agent for Cluster Management

```python
import requests
import json
import time
from typing import List, Dict, Optional
from enum import Enum

class TaskPriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class RetireClusterAgent:
    """AI Agent for managing Retire-Cluster"""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url
        self.session = requests.Session()
        if api_key:
            self.session.headers['X-API-Key'] = api_key
    
    def execute_command(self, command: str, format: str = "json") -> Dict:
        """Execute a CLI command"""
        response = self.session.post(
            f"{self.base_url}/api/v1/command",
            json={"command": command, "format": format}
        )
        response.raise_for_status()
        return response.json() if format == "json" else response.text
    
    def get_healthy_devices(self) -> List[Dict]:
        """Get list of healthy devices"""
        devices = self.execute_command("devices list --status=online")
        return [d for d in devices['data']['devices'] if d['cpu'] < 80]
    
    def distribute_task(self, task_type: str, payload: Dict) -> List[str]:
        """Distribute task across available devices"""
        devices = self.get_healthy_devices()
        task_ids = []
        
        for device in devices:
            result = self.execute_command(
                f"tasks submit {task_type} "
                f"--payload='{json.dumps(payload)}' "
                f"--device={device['id']}"
            )
            task_ids.append(result['data']['task_id'])
        
        return task_ids
    
    def monitor_tasks(self, task_ids: List[str]) -> Dict[str, str]:
        """Monitor task completion"""
        statuses = {}
        
        for task_id in task_ids:
            result = self.execute_command(f"tasks show {task_id}")
            statuses[task_id] = result['data']['status']
        
        return statuses
    
    def auto_scale(self, threshold: int = 80):
        """Auto-scale based on cluster load"""
        status = self.execute_command("cluster metrics")
        avg_cpu = status['data']['metrics']['avg_cpu_percent']
        
        if avg_cpu > threshold:
            # Find idle devices and activate them
            idle_devices = self.execute_command(
                "devices list --status=idle --format=json"
            )
            for device in idle_devices['data']['devices'][:2]:  # Activate up to 2
                self.execute_command(f"devices activate {device['id']}")
                print(f"Activated device {device['id']} due to high load")
    
    def health_check_routine(self):
        """Perform routine health checks"""
        # Check cluster health
        health = self.execute_command("cluster health")
        
        if health['data']['status'] != 'healthy':
            # Perform recovery actions
            self.execute_command("cluster recover")
        
        # Check for offline devices
        offline = self.execute_command("devices list --status=offline")
        for device in offline['data']['devices']:
            print(f"Device {device['id']} is offline, attempting recovery...")
            self.execute_command(f"devices ping {device['id']}")
    
    def run_automation_loop(self, interval: int = 60):
        """Main automation loop"""
        while True:
            try:
                # Perform health checks
                self.health_check_routine()
                
                # Auto-scale if needed
                self.auto_scale()
                
                # Process pending tasks
                pending = self.execute_command("tasks list --status=pending")
                if pending['data']['count'] > 10:
                    print(f"High task queue ({pending['data']['count']} pending)")
                    # Activate more workers or redistribute tasks
                
                time.sleep(interval)
                
            except Exception as e:
                print(f"Error in automation loop: {e}")
                time.sleep(interval)

# Usage
if __name__ == "__main__":
    agent = RetireClusterAgent("http://cluster.local")
    
    # Distribute a task
    task_ids = agent.distribute_task(
        "data_processing",
        {"input": "data.csv", "operation": "analyze"}
    )
    
    # Monitor completion
    while True:
        statuses = agent.monitor_tasks(task_ids)
        if all(s == "completed" for s in statuses.values()):
            print("All tasks completed!")
            break
        time.sleep(5)
    
    # Start automation
    agent.run_automation_loop()
```

## Performance Considerations

### Response Time Expectations

| Operation | CLI/Text | JSON API | HTML/GUI |
|-----------|----------|----------|----------|
| List devices | <50ms | <100ms | >500ms |
| Execute command | <100ms | <150ms | N/A |
| Parse response | <10ms | <20ms | >100ms |
| Total round-trip | <200ms | <300ms | >1000ms |

### Bandwidth Usage

```
# Text format: ~50 bytes per device
android-001|online|42|2.1|3

# JSON format: ~150 bytes per device
{"id":"android-001","status":"online","cpu":42,"memory":2.1,"tasks":3}

# HTML format: ~500+ bytes per device
<div class="device-card">...</div>
```

### Recommendations

1. **Use text format for high-frequency polling** (<1s intervals)
2. **Use JSON for complex data structures**
3. **Implement client-side caching for static data**
4. **Use streaming endpoints for real-time monitoring**
5. **Batch commands when possible**

## Security Considerations

### API Key Authentication

```python
# Include API key in headers
headers = {
    'X-API-Key': 'your-api-key-here',
    'Accept': 'application/json'
}

response = requests.get(
    "http://cluster.local/api/v1/devices",
    headers=headers
)
```

### Rate Limiting

The API implements rate limiting:
- Default: 100 requests per minute
- Burst: 10 requests per second

Handle rate limit errors:

```python
def handle_rate_limit(response):
    if response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', 60))
        time.sleep(retry_after)
        return True
    return False
```

### Input Validation

Always validate and sanitize inputs:

```python
import shlex

def safe_command(command: str, args: Dict[str, str]) -> str:
    """Build safe command with escaped arguments"""
    cmd_parts = [command]
    
    for key, value in args.items():
        # Escape shell arguments
        safe_value = shlex.quote(str(value))
        cmd_parts.append(f"--{key}={safe_value}")
    
    return ' '.join(cmd_parts)

# Usage
command = safe_command("devices list", {"status": "online", "format": "json"})
```

## Troubleshooting

### Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Empty responses | Wrong Accept header | Use `Accept: text/plain` or `application/json` |
| Parsing errors | Format mismatch | Check response content-type |
| Timeout errors | Long operations | Use async endpoints or increase timeout |
| 401 Unauthorized | Missing API key | Include API key in headers |
| 429 Too Many Requests | Rate limit exceeded | Implement exponential backoff |

### Debug Mode

Enable debug output:

```python
import logging

logging.basicConfig(level=logging.DEBUG)

# See all HTTP requests
import http.client
http.client.HTTPConnection.debuglevel = 1
```

## Additional Resources

- [CLI Command Reference](./cli-interface-specification.md)
- [API Documentation](./api-documentation.md)
- [Web Interface Design](./web-interface-design.md)
- [Example Scripts](../examples/ai-scripts/)
- [Performance Benchmarks](./performance-benchmarks.md)