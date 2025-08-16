# Task Execution Framework

The Retire-Cluster Task Execution Framework provides a powerful, distributed task execution system that can intelligently distribute computational work across your cluster of devices.

## Overview

The framework consists of several key components:

- **Task**: Definition of work to be executed
- **TaskQueue**: Priority-based task queue with device targeting
- **TaskScheduler**: Intelligent task distribution and load balancing
- **TaskExecutor**: Task execution engine on worker nodes
- **TaskResult**: Comprehensive result tracking and status

## Quick Start

### 1. Basic Task Submission

```python
from retire_cluster.tasks import Task, TaskRequirements, TaskPriority

# Create a simple task
task = Task(
    task_type="echo",
    payload={"message": "Hello World!"},
    priority=TaskPriority.NORMAL
)

# Submit to cluster
task_id = scheduler.submit_task(task)
```

### 2. Task with Requirements

```python
# Task that requires specific device capabilities
compute_task = Task(
    task_type="python_eval",
    payload={"expression": "sum(range(1000000))"},
    requirements=TaskRequirements(
        min_cpu_cores=4,
        min_memory_gb=8,
        required_platform="linux",
        timeout_seconds=60
    )
)
```

### 3. Mobile-Specific Task

```python
# Task targeted at mobile devices
mobile_task = Task(
    task_type="system_info",
    payload={},
    requirements=TaskRequirements(
        required_role="mobile",
        required_platform="android"
    )
)
```

## Task Types

### Built-in Task Types

The framework includes several built-in task types:

#### Echo Task
```python
Task(
    task_type="echo",
    payload={"message": "Your message here"}
)
```
Returns the payload as-is. Useful for testing connectivity.

#### Sleep Task
```python
Task(
    task_type="sleep", 
    payload={"duration": 5.0}
)
```
Sleeps for the specified duration in seconds.

#### System Info Task
```python
Task(task_type="system_info", payload={})
```
Returns device capabilities and system information.

#### Python Evaluation Task
```python
Task(
    task_type="python_eval",
    payload={"expression": "2 + 2"}
)
```
Evaluates a Python expression safely. Limited for security.

#### HTTP Request Task
```python
Task(
    task_type="http_request",
    payload={
        "url": "https://api.example.com/data",
        "method": "GET",
        "headers": {"Authorization": "Bearer token"},
        "timeout": 30
    }
)
```
Makes HTTP requests. Useful for web scraping or API calls.

#### Command Execution Task
```python
Task(
    task_type="command",
    payload={
        "command": "ls -la",
        "timeout": 10
    }
)
```
Executes shell commands. Use with caution for security.

### Custom Task Types

You can register custom task handlers on worker nodes:

```python
def my_custom_handler(payload):
    # Your custom logic here
    input_data = payload.get('input')
    result = process_data(input_data)
    return {"output": result}

# Register on worker
executor.register_handler("my_custom_task", my_custom_handler)
```

## Task Requirements

### Resource Requirements

```python
TaskRequirements(
    min_cpu_cores=4,        # Minimum CPU cores
    min_memory_gb=8,        # Minimum RAM in GB
    min_storage_gb=100,     # Minimum storage in GB
    gpu_required=True,      # Requires GPU
    internet_required=True  # Requires internet access
)
```

### Platform Requirements

```python
TaskRequirements(
    required_platform="linux",      # "windows", "linux", "android", "darwin"
    required_role="compute",         # "worker", "compute", "storage", "mobile"
    required_tags=["gpu-capable"]    # Custom device tags
)
```

### Execution Requirements

```python
TaskRequirements(
    timeout_seconds=300,    # Maximum execution time
    max_retries=3          # Maximum retry attempts
)
```

## Task Priorities

Tasks can be assigned different priority levels:

```python
TaskPriority.URGENT    # Highest priority
TaskPriority.HIGH      # High priority  
TaskPriority.NORMAL    # Normal priority (default)
TaskPriority.LOW       # Lowest priority
```

Higher priority tasks are scheduled first.

## Task Status Tracking

Tasks go through several status states:

- `PENDING`: Task created but not yet queued
- `QUEUED`: Task waiting for available device
- `ASSIGNED`: Task assigned to specific device
- `RUNNING`: Task currently executing
- `SUCCESS`: Task completed successfully
- `FAILED`: Task failed with error
- `CANCELLED`: Task was cancelled
- `TIMEOUT`: Task exceeded timeout limit

## Monitoring Tasks

### Check Task Status

```python
status = scheduler.get_task_status(task_id)
print(f"Task status: {status.value}")
```

### Get Task Result

```python
result = scheduler.get_task_result(task_id)
if result:
    if result.status == TaskStatus.SUCCESS:
        print(f"Result: {result.result_data}")
    else:
        print(f"Error: {result.error_message}")
```

### Get Cluster Statistics

```python
stats = scheduler.get_cluster_statistics()
print(f"Online devices: {stats['cluster_stats']['online_devices']}")
print(f"Queue size: {stats['queue_stats']['total_tasks']}")
```

## Advanced Features

### Load Balancing

The scheduler automatically balances tasks across available devices based on:
- Current device load
- Device capabilities
- Task requirements
- Device affinity (tasks of same type prefer same device)

### Fault Tolerance

- Automatic retry of failed tasks (up to `max_retries`)
- Offline device detection and task reassignment
- Timeout handling for stuck tasks

### Device Affinity

Tasks of the same type are preferentially assigned to the same device to improve:
- Cache locality
- Initialization overhead
- Resource utilization

## Integration with External Frameworks

### Temporal Integration

Use Temporal for complex workflow orchestration:

```python
from retire_cluster.tasks.integrations import TemporalIntegration

temporal = TemporalIntegration(cluster_client)
await temporal.initialize("localhost:7233")

# Submit task via Temporal workflow
workflow_id = temporal.submit_task("data_processing", {"input": "data"})
```

### Celery Integration

Use Celery as a task broker:

```python
from retire_cluster.tasks.integrations import CeleryIntegration

celery = CeleryIntegration(cluster_client)
celery.initialize("redis://localhost:6379")

# Submit via Celery
task_id = celery.submit_task("analysis", {"dataset": "data.csv"})
```

### HTTP API Bridge

Expose task submission via HTTP:

```python
from retire_cluster.tasks.integrations import SimpleTaskBridge

bridge = SimpleTaskBridge(cluster_client)
bridge.start_http_bridge()  # Starts HTTP server on port 8081

# Submit via HTTP POST
# curl -X POST http://localhost:8081/tasks \
#   -H "Content-Type: application/json" \
#   -d '{"task_type": "echo", "payload": {"message": "Hello"}}'
```

## CLI Integration

The task framework integrates with the Retire-Cluster CLI:

```bash
# Start main node with task scheduling
retire-cluster-main --port 8080

# Start worker that can execute tasks  
retire-cluster-worker --join 192.168.1.100:8080 --role compute

# Monitor cluster and tasks
retire-cluster-status 192.168.1.100:8080
```

## Security Considerations

### Safe Task Types
- `echo`: Always safe
- `sleep`: Safe
- `system_info`: Safe (read-only)
- `http_request`: Generally safe, but review URLs

### Potentially Dangerous Task Types
- `python_eval`: Limited expression evaluation, but still potentially risky
- `command`: Can execute arbitrary commands - use with extreme caution

### Best Practices
1. Only allow trusted task types in production
2. Validate all task payloads
3. Use resource limits and timeouts
4. Run workers in sandboxed environments
5. Monitor task execution logs

## Performance Optimization

### Task Design
- Keep tasks stateless when possible
- Minimize data transfer in payloads
- Use appropriate timeout values
- Consider task granularity (not too small, not too large)

### Device Utilization
- Use device tags to optimize task placement
- Monitor device performance and adjust requirements
- Balance compute vs. I/O intensive tasks

### Network Optimization
- Minimize task payload size
- Use local data when possible
- Consider task result caching

## Troubleshooting

### Common Issues

**Tasks stuck in QUEUED status**
- Check if any devices meet task requirements
- Verify devices are online and responding
- Review task requirements vs. device capabilities

**Tasks failing immediately**
- Check device logs for error details
- Verify task handler is registered for task type
- Review task payload format

**Poor performance**
- Monitor device load and capacity
- Check network latency between nodes
- Review task size and complexity

### Debugging

Enable debug logging:
```python
logger = get_logger("scheduler", level="DEBUG")
```

Check queue statistics:
```python
stats = task_queue.get_queue_statistics()
print(stats)
```

Monitor device status:
```python
online_devices = scheduler.get_online_devices()
for device_id in online_devices:
    capabilities = scheduler.get_device_capabilities(device_id)
    print(f"{device_id}: {capabilities}")
```

## Examples

See `examples/task_execution_example.py` for a comprehensive demonstration of the task execution framework in action.

The example shows:
- Setting up the scheduler
- Submitting various task types
- Monitoring execution
- Handling results
- Integration patterns