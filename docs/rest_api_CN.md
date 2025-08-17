# Retire-Cluster REST API

Retire-Cluster REST API 通过 HTTP 端点为分布式计算集群提供全面的管理和监控功能。

## 快速开始

### 安装

安装API支持：
```bash
pip install retire-cluster[api]
```

### 启动API服务器

```bash
# 使用默认设置启动
retire-cluster-api

# 使用自定义配置启动
retire-cluster-api --host 0.0.0.0 --port 8081 --auth --api-key your-secret-key

# 连接到特定集群节点
retire-cluster-api --cluster-host 192.168.1.100 --cluster-port 8080
```

### 基本用法

```bash
# 检查API健康状态
curl http://localhost:8081/health

# 获取集群状态
curl http://localhost:8081/api/v1/cluster/status

# 列出设备
curl http://localhost:8081/api/v1/devices

# 提交任务
curl -X POST http://localhost:8081/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"task_type": "echo", "payload": {"message": "Hello World"}}'
```

## API概览

### 基础URL
```
http://localhost:8081/api/v1
```

### 认证
API支持可选的API密钥认证：
```bash
# 在头部包含API密钥
curl -H "X-API-Key: your-secret-key" http://localhost:8081/api/v1/cluster/config

# 或使用Authorization头部
curl -H "Authorization: Bearer your-secret-key" http://localhost:8081/api/v1/cluster/config
```

### 响应格式
所有API响应都遵循一致的格式：
```json
{
  "status": "success|error",
  "data": {},
  "message": "可选消息",
  "timestamp": "2023-01-01T12:00:00Z",
  "request_id": "uuid"
}
```

## 集群管理

### 获取集群状态
```http
GET /api/v1/cluster/status
```

返回包括设备数量、健康百分比和资源总量在内的综合集群统计信息。

**响应：**
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
      "uptime": "15d 6h 42m"
    }
  }
}
```

### 获取集群健康状态
```http
GET /api/v1/cluster/health
```

执行健康检查并返回集群各组件的状态。

**响应：**
```json
{
  "status": "success",
  "data": {
    "overall_health": "healthy",
    "checks": {
      "database": {
        "status": "healthy",
        "response_time_ms": 5
      },
      "network": {
        "status": "healthy",
        "connected_devices": 4
      },
      "resources": {
        "status": "warning",
        "cpu_usage": 85,
        "memory_usage": 70
      }
    }
  }
}
```

### 获取集群指标
```http
GET /api/v1/cluster/metrics
```

返回详细的性能指标和统计信息。

**查询参数：**
- `period`: 时间周期 (1h, 24h, 7d, 30d) - 默认: 1h
- `type`: 指标类型 (cpu, memory, network, disk) - 默认: all

**响应：**
```json
{
  "status": "success",
  "data": {
    "metrics": {
      "cpu": {
        "average_usage": 45.2,
        "peak_usage": 89.1,
        "total_cores": 32
      },
      "memory": {
        "average_usage": 62.8,
        "peak_usage": 87.3,
        "total_gb": 128
      },
      "tasks": {
        "completed": 156,
        "failed": 3,
        "average_duration_seconds": 42.5
      }
    },
    "period": "1h"
  }
}
```

## 设备管理

### 列出设备
```http
GET /api/v1/devices
```

返回集群中所有注册设备的列表。

**查询参数：**
- `status`: 过滤状态 (online, offline, all) - 默认: all
- `role`: 过滤角色 (compute, mobile, storage) - 默认: all
- `sort`: 排序字段 (name, cpu, memory, last_seen) - 默认: name
- `limit`: 限制结果数量 - 默认: 100

**响应：**
```json
{
  "status": "success",
  "data": {
    "devices": [
      {
        "id": "android-001",
        "hostname": "pixel-phone",
        "status": "online",
        "role": "mobile",
        "platform": {
          "os": "android",
          "arch": "aarch64",
          "python_version": "3.11.0"
        },
        "resources": {
          "cpu_cores": 8,
          "cpu_usage": 42.5,
          "memory_total_gb": 8,
          "memory_used_gb": 3.2,
          "storage_total_gb": 128,
          "storage_used_gb": 45.6
        },
        "tasks": {
          "active": 2,
          "completed": 15,
          "failed": 0
        },
        "last_seen": "2023-01-01T12:00:00Z",
        "uptime_seconds": 86400
      }
    ],
    "total": 5,
    "online": 4,
    "offline": 1
  }
}
```

### 获取设备详情
```http
GET /api/v1/devices/{device_id}
```

返回特定设备的详细信息。

**响应：**
```json
{
  "status": "success",
  "data": {
    "device": {
      "id": "android-001",
      "detailed_info": {
        "capabilities": ["computational", "network_services"],
        "network_interfaces": ["wlan0"],
        "sensors": ["accelerometer", "gyroscope"],
        "battery": {
          "level": 85,
          "charging": false
        }
      },
      "performance_history": {
        "cpu_usage_24h": [45, 52, 38, 41],
        "memory_usage_24h": [38, 42, 35, 40],
        "task_count_24h": [2, 3, 1, 2]
      }
    }
  }
}
```

### Ping设备
```http
POST /api/v1/devices/{device_id}/ping
```

向特定设备发送ping请求。

**请求体：**
```json
{
  "timeout": 5,
  "count": 3
}
```

**响应：**
```json
{
  "status": "success",
  "data": {
    "ping_results": {
      "device_id": "android-001",
      "reachable": true,
      "average_latency_ms": 15.2,
      "packet_loss": 0.0,
      "results": [
        {"seq": 1, "time_ms": 14.8},
        {"seq": 2, "time_ms": 15.1},
        {"seq": 3, "time_ms": 15.7}
      ]
    }
  }
}
```

### 移除设备
```http
DELETE /api/v1/devices/{device_id}
```

从集群中移除设备。

**查询参数：**
- `force`: 强制移除（即使有活动任务） - 默认: false

**响应：**
```json
{
  "status": "success",
  "data": {
    "removed_device": "android-001",
    "cancelled_tasks": 2
  }
}
```

## 任务管理

### 提交任务
```http
POST /api/v1/tasks
```

向集群提交新任务。

**请求体：**
```json
{
  "task_type": "echo",
  "payload": {
    "message": "Hello World",
    "repeat": 3
  },
  "priority": "normal",
  "device_id": "android-001",
  "requirements": {
    "min_cpu_cores": 2,
    "min_memory_gb": 1,
    "platform": "android"
  },
  "timeout": 300
}
```

**响应：**
```json
{
  "status": "success",
  "data": {
    "task_id": "task-abc123",
    "assigned_device": "android-001",
    "estimated_completion": "2023-01-01T12:05:00Z"
  }
}
```

### 列出任务
```http
GET /api/v1/tasks
```

返回任务列表。

**查询参数：**
- `status`: 过滤状态 (pending, running, completed, failed, all) - 默认: all
- `device_id`: 过滤设备ID
- `task_type`: 过滤任务类型
- `since`: 起始时间戳
- `limit`: 限制结果数量 - 默认: 50

**响应：**
```json
{
  "status": "success",
  "data": {
    "tasks": [
      {
        "task_id": "task-abc123",
        "task_type": "echo",
        "status": "completed",
        "device_id": "android-001",
        "priority": "normal",
        "created_at": "2023-01-01T12:00:00Z",
        "started_at": "2023-01-01T12:00:05Z",
        "completed_at": "2023-01-01T12:00:10Z",
        "execution_time_seconds": 5.2,
        "result": {
          "output": "Hello World\nHello World\nHello World",
          "exit_code": 0
        }
      }
    ],
    "total": 156,
    "pending": 3,
    "running": 2,
    "completed": 148,
    "failed": 3
  }
}
```

### 获取任务详情
```http
GET /api/v1/tasks/{task_id}
```

返回特定任务的详细信息。

**响应：**
```json
{
  "status": "success",
  "data": {
    "task": {
      "task_id": "task-abc123",
      "detailed_log": [
        "2023-01-01T12:00:05Z: 任务开始执行",
        "2023-01-01T12:00:06Z: 初始化环境",
        "2023-01-01T12:00:10Z: 任务完成"
      ],
      "resource_usage": {
        "peak_cpu_percent": 25.6,
        "peak_memory_mb": 128,
        "total_cpu_time_seconds": 4.8
      },
      "payload": {
        "message": "Hello World",
        "repeat": 3
      }
    }
  }
}
```

### 取消任务
```http
DELETE /api/v1/tasks/{task_id}
```

取消正在执行或待执行的任务。

**响应：**
```json
{
  "status": "success",
  "data": {
    "cancelled_task": "task-abc123",
    "was_running": true
  }
}
```

### 重试任务
```http
POST /api/v1/tasks/{task_id}/retry
```

重新提交失败的任务。

**请求体：**
```json
{
  "priority": "high"
}
```

**响应：**
```json
{
  "status": "success",
  "data": {
    "new_task_id": "task-def456",
    "original_task_id": "task-abc123"
  }
}
```

## 监控和日志

### 获取日志
```http
GET /api/v1/logs
```

获取系统日志。

**查询参数：**
- `level`: 日志级别 (debug, info, warning, error) - 默认: info
- `device_id`: 过滤设备ID
- `since`: 起始时间戳
- `limit`: 限制结果数量 - 默认: 100

**响应：**
```json
{
  "status": "success",
  "data": {
    "logs": [
      {
        "timestamp": "2023-01-01T12:00:00Z",
        "level": "info",
        "device_id": "android-001",
        "component": "task_executor",
        "message": "任务 task-abc123 开始执行",
        "details": {
          "task_type": "echo",
          "estimated_duration": 5
        }
      }
    ],
    "total": 1024
  }
}
```

### 实时监控
```http
GET /api/v1/monitor/stream
```

建立实时监控流（Server-Sent Events）。

**查询参数：**
- `types`: 监控类型 (devices, tasks, logs) - 默认: all
- `device_id`: 过滤设备ID

**响应（SSE流）：**
```
data: {"type": "device_update", "device_id": "android-001", "cpu_usage": 45.2}

data: {"type": "task_completed", "task_id": "task-abc123", "device_id": "android-001"}

data: {"type": "log_entry", "level": "error", "message": "设备连接丢失"}
```

## 配置管理

### 获取配置
```http
GET /api/v1/config
```

获取集群配置信息。

**响应：**
```json
{
  "status": "success",
  "data": {
    "config": {
      "server": {
        "host": "0.0.0.0",
        "port": 8080,
        "max_connections": 100
      },
      "cluster": {
        "heartbeat_interval": 60,
        "offline_threshold": 300,
        "task_timeout": 3600
      },
      "logging": {
        "level": "info",
        "max_size": "10MB"
      }
    }
  }
}
```

### 更新配置
```http
PUT /api/v1/config
```

更新集群配置。

**请求体：**
```json
{
  "cluster": {
    "heartbeat_interval": 30,
    "offline_threshold": 180
  }
}
```

**响应：**
```json
{
  "status": "success",
  "data": {
    "updated_fields": ["cluster.heartbeat_interval", "cluster.offline_threshold"],
    "restart_required": false
  }
}
```

## 统计和分析

### 获取任务统计
```http
GET /api/v1/stats/tasks
```

获取任务执行统计信息。

**查询参数：**
- `period`: 时间周期 (1h, 24h, 7d, 30d) - 默认: 24h
- `group_by`: 分组方式 (device, task_type, hour) - 默认: device

**响应：**
```json
{
  "status": "success",
  "data": {
    "task_stats": {
      "period": "24h",
      "total_tasks": 156,
      "by_status": {
        "completed": 148,
        "failed": 3,
        "cancelled": 5
      },
      "by_device": {
        "android-001": {"completed": 45, "failed": 1},
        "laptop-002": {"completed": 38, "failed": 0}
      },
      "average_execution_time": 42.5,
      "success_rate": 94.9
    }
  }
}
```

### 获取设备统计
```http
GET /api/v1/stats/devices
```

获取设备使用统计信息。

**响应：**
```json
{
  "status": "success",
  "data": {
    "device_stats": {
      "utilization": {
        "android-001": {
          "cpu_avg": 42.5,
          "memory_avg": 38.2,
          "uptime_percent": 98.5
        }
      },
      "performance_ranking": [
        {"device_id": "laptop-002", "score": 95.2},
        {"device_id": "android-001", "score": 87.1}
      ]
    }
  }
}
```

## 错误处理

### 错误响应格式

所有错误响应都遵循标准格式：

```json
{
  "status": "error",
  "error": {
    "code": "DEVICE_NOT_FOUND",
    "message": "设备 'invalid-device' 不存在",
    "details": {
      "device_id": "invalid-device",
      "available_devices": ["android-001", "laptop-002"]
    }
  },
  "timestamp": "2023-01-01T12:00:00Z",
  "request_id": "uuid"
}
```

### 常见错误代码

| 错误代码 | HTTP状态 | 描述 |
|----------|----------|------|
| `DEVICE_NOT_FOUND` | 404 | 设备不存在 |
| `TASK_NOT_FOUND` | 404 | 任务不存在 |
| `INVALID_TASK_TYPE` | 400 | 无效的任务类型 |
| `DEVICE_OFFLINE` | 400 | 设备离线 |
| `INSUFFICIENT_RESOURCES` | 400 | 资源不足 |
| `AUTHENTICATION_REQUIRED` | 401 | 需要认证 |
| `PERMISSION_DENIED` | 403 | 权限不足 |
| `RATE_LIMIT_EXCEEDED` | 429 | 超过速率限制 |
| `INTERNAL_ERROR` | 500 | 内部服务器错误 |

## 速率限制

API实施速率限制以防止滥用：

| 端点类型 | 限制 | 时间窗口 |
|----------|------|----------|
| 只读操作 | 1000次请求 | 15分钟 |
| 写操作 | 100次请求 | 15分钟 |
| 监控流 | 10个连接 | 同时 |

当超过限制时，API返回429状态码和以下头部：
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1640995200
```

## SDK和客户端库

### Python客户端
```bash
pip install retire-cluster-client
```

```python
from retire_cluster_client import ClusterClient

client = ClusterClient('http://localhost:8081', api_key='your-key')

# 获取设备列表
devices = client.devices.list(status='online')

# 提交任务
task_id = client.tasks.submit('echo', {'message': 'Hello'})

# 监控任务
for event in client.monitor.stream(['tasks']):
    print(f"任务更新: {event}")
```

### 命令行工具
```bash
# 安装CLI工具
pip install retire-cluster-cli

# 配置连接
retire-cluster config set api_url http://localhost:8081
retire-cluster config set api_key your-secret-key

# 使用CLI
retire-cluster devices list
retire-cluster tasks submit echo --payload '{"message": "test"}'
```

这个REST API为Retire-Cluster提供了完整的HTTP接口，支持所有主要的集群管理功能，并且设计为易于集成和自动化。