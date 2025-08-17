# AI集成指南

## 概述

Retire-Cluster 专门设计为 AI 友好的系统，提供多种接口格式和访问方式，使 AI 代理和自动化脚本能够轻松集成和管理集群。

## AI友好的设计原则

### 1. 多格式支持
- **纯文本**: 管道分隔、键值对格式
- **结构化数据**: JSON、CSV、TSV
- **流式数据**: Server-Sent Events (SSE)
- **标准协议**: HTTP REST API

### 2. 可预测的接口
- 一致的URL模式
- 标准HTTP状态码
- 统一的错误格式
- 明确的内容类型

### 3. 机器可解析
- 无HTML标记的纯数据
- 标准化的字段名称
- 可预测的数据结构
- 清晰的分隔符

## API端点概览

### 文本API（AI优化）

```bash
# 设备管理
GET /text/devices                    # 管道分隔的设备列表
GET /text/devices?status=online      # 过滤在线设备
GET /text/device/{id}                # 单个设备信息

# 集群状态  
GET /text/status                     # 键值对格式
GET /text/health                     # 简单健康状态
GET /text/metrics                    # Prometheus格式指标

# 任务管理
GET /text/tasks                      # 任务列表
POST /text/tasks                     # 提交任务
GET /text/tasks/{id}                 # 任务详情

# 日志和监控
GET /text/logs                       # 纯文本日志
GET /stream/devices                  # 实时设备状态流
GET /stream/logs                     # 实时日志流
```

### JSON API（程序化访问）

```bash
# RESTful 风格
GET /api/v1/devices                  # 结构化设备数据
POST /api/v1/tasks                   # 创建任务
GET /api/v1/cluster/status           # 集群信息
POST /api/v1/command                 # 执行CLI命令
```

## 数据格式示例

### 设备列表（文本格式）

```bash
# 默认管道分隔
curl http://cluster:5000/text/devices
android-001|online|42|2.1|3|mobile
laptop-002|online|15|4.5|1|compute
raspi-003|offline|0|0|0|storage

# CSV格式（Accept头）
curl -H "Accept: text/csv" http://cluster:5000/text/devices
id,status,cpu,memory,tasks,role
android-001,online,42,2.1,3,mobile
laptop-002,online,15,4.5,1,compute
raspi-003,offline,0,0,0,storage

# TSV格式
curl -H "Accept: text/tab-separated-values" http://cluster:5000/text/devices
id	status	cpu	memory	tasks	role
android-001	online	42	2.1	3	mobile
laptop-002	online	15	4.5	1	compute
raspi-003	offline	0	0	0	storage
```

### 集群状态（键值对）

```bash
curl http://cluster:5000/text/status
STATUS: healthy
NODES: 2/3 online
CPU: 48 cores (37% utilized)
MEMORY: 128GB (42% used)
TASKS: 12 active, 45 completed
UPTIME: 15d 6h 42m
```

### JSON响应格式

```json
{
  "status": "success",
  "data": {
    "devices": [
      {
        "id": "android-001",
        "status": "online",
        "cpu_usage": 42,
        "memory_gb": 2.1,
        "active_tasks": 3,
        "role": "mobile",
        "last_seen": "2024-01-15T10:30:15Z"
      }
    ]
  },
  "meta": {
    "total": 3,
    "online": 2,
    "timestamp": "2024-01-15T10:30:15Z"
  }
}
```

## Python客户端示例

### 基础客户端类

```python
import requests
import json
from typing import List, Dict, Optional

class RetireClusterClient:
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})
    
    def get_devices(self, status: Optional[str] = None, format: str = 'json') -> List[Dict]:
        """获取设备列表"""
        url = f"{self.base_url}/api/v1/devices"
        params = {}
        if status:
            params['status'] = status
            
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        if format == 'json':
            return response.json()['data']['devices']
        else:
            return response.text
    
    def get_cluster_status(self) -> Dict:
        """获取集群状态"""
        url = f"{self.base_url}/api/v1/cluster/status"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()['data']
    
    def submit_task(self, task_type: str, payload: Dict, 
                   priority: str = 'normal', device_id: Optional[str] = None) -> str:
        """提交任务"""
        url = f"{self.base_url}/api/v1/tasks"
        data = {
            'task_type': task_type,
            'payload': payload,
            'priority': priority
        }
        if device_id:
            data['device_id'] = device_id
            
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()['data']['task_id']
    
    def get_task_status(self, task_id: str) -> Dict:
        """获取任务状态"""
        url = f"{self.base_url}/api/v1/tasks/{task_id}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()['data']
    
    def execute_command(self, command: str, format: str = 'text') -> str:
        """执行CLI命令"""
        url = f"{self.base_url}/api/v1/command"
        data = {
            'command': command,
            'format': format
        }
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()['output']
```

### 使用示例

```python
# 初始化客户端
client = RetireClusterClient('http://192.168.1.100:5000')

# 获取在线设备
online_devices = client.get_devices(status='online')
print(f"在线设备数量: {len(online_devices)}")

# 检查集群状态
status = client.get_cluster_status()
print(f"集群状态: {status['status']}")
print(f"CPU使用率: {status['cpu_usage']}%")

# 提交任务
task_id = client.submit_task(
    task_type='echo',
    payload={'message': 'Hello from AI!'},
    priority='high'
)
print(f"任务已提交: {task_id}")

# 检查任务状态
task_status = client.get_task_status(task_id)
print(f"任务状态: {task_status['status']}")

# 执行CLI命令
result = client.execute_command('devices list --status=online')
print("设备列表:")
print(result)
```

## 流式数据处理

### Server-Sent Events (SSE)

```python
import requests
import json

def monitor_devices(base_url: str):
    """监控设备状态变化"""
    url = f"{base_url}/stream/devices"
    headers = {'Accept': 'text/event-stream'}
    
    with requests.get(url, headers=headers, stream=True) as response:
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = json.loads(line[6:])  # 移除 'data: ' 前缀
                    print(f"设备更新: {data}")

def monitor_logs(base_url: str, device_id: Optional[str] = None):
    """监控实时日志"""
    url = f"{base_url}/stream/logs"
    if device_id:
        url += f"?device={device_id}"
        
    headers = {'Accept': 'text/event-stream'}
    
    with requests.get(url, headers=headers, stream=True) as response:
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    log_entry = json.loads(line[6:])
                    print(f"[{log_entry['timestamp']}] {log_entry['level']}: {log_entry['message']}")

# 使用示例
monitor_devices('http://192.168.1.100:5000')
```

## CLI浏览器集成

### w3m浏览器支持

```bash
# 纯文本访问，无JavaScript依赖
w3m http://192.168.1.100:5000/text/devices

# 通过w3m查看集群状态
w3m http://192.168.1.100:5000/text/status

# 使用lynx浏览器
lynx http://192.168.1.100:5000/text/devices
```

### curl脚本集成

```bash
#!/bin/bash
# AI友好的集群管理脚本

CLUSTER_URL="http://192.168.1.100:5000"

# 检查集群健康状态
check_health() {
    echo "=== 集群健康检查 ==="
    curl -s "$CLUSTER_URL/text/status"
    echo -e "\n"
}

# 列出离线设备
check_offline_devices() {
    echo "=== 离线设备检查 ==="
    offline=$(curl -s "$CLUSTER_URL/text/devices?status=offline")
    if [ -n "$offline" ]; then
        echo "发现离线设备:"
        echo "$offline"
    else
        echo "所有设备在线"
    fi
    echo -e "\n"
}

# 获取任务统计
get_task_stats() {
    echo "=== 任务统计 ==="
    # 使用JSON API获取详细统计
    curl -s "$CLUSTER_URL/api/v1/tasks/stats" | \
        jq -r '. | "活动任务: \(.active), 完成任务: \(.completed), 失败任务: \(.failed)"'
    echo -e "\n"
}

# 执行检查
check_health
check_offline_devices
get_task_stats
```

## 自动化脚本示例

### 设备监控脚本

```python
#!/usr/bin/env python3
"""
AI驱动的设备监控脚本
自动检测异常并采取行动
"""

import time
import requests
import json
from datetime import datetime
from typing import Dict, List

class ClusterMonitor:
    def __init__(self, cluster_url: str):
        self.cluster_url = cluster_url.rstrip('/')
        self.last_check = {}
        
    def get_devices_status(self) -> List[Dict]:
        """获取所有设备状态"""
        response = requests.get(f"{self.cluster_url}/api/v1/devices")
        return response.json()['data']['devices']
    
    def check_device_health(self, device: Dict) -> Dict:
        """检查单个设备健康状态"""
        issues = []
        
        # CPU使用率检查
        if device['cpu_usage'] > 90:
            issues.append(f"CPU使用率过高: {device['cpu_usage']}%")
        
        # 内存使用检查
        memory_usage = (device['memory_used'] / device['memory_total']) * 100
        if memory_usage > 85:
            issues.append(f"内存使用率过高: {memory_usage:.1f}%")
        
        # 心跳检查
        last_seen = datetime.fromisoformat(device['last_seen'].replace('Z', '+00:00'))
        elapsed = (datetime.now(last_seen.tzinfo) - last_seen).total_seconds()
        if elapsed > 300:  # 5分钟无心跳
            issues.append(f"心跳超时: {elapsed:.0f}秒")
        
        return {
            'device_id': device['id'],
            'healthy': len(issues) == 0,
            'issues': issues
        }
    
    def auto_restart_device(self, device_id: str) -> bool:
        """自动重启设备"""
        try:
            response = requests.post(
                f"{self.cluster_url}/api/v1/command",
                json={
                    'command': f'devices restart {device_id}',
                    'format': 'json'
                }
            )
            return response.status_code == 200
        except:
            return False
    
    def send_alert(self, message: str):
        """发送警报（可集成多种通知方式）"""
        timestamp = datetime.now().isoformat()
        print(f"[{timestamp}] ALERT: {message}")
        
        # 这里可以集成:
        # - Slack/Discord Webhook
        # - 邮件通知
        # - 短信接口
        # - 企业微信/钉钉
    
    def monitor_loop(self, interval: int = 60):
        """主监控循环"""
        print(f"开始监控集群，检查间隔: {interval}秒")
        
        while True:
            try:
                devices = self.get_devices_status()
                print(f"检查 {len(devices)} 个设备...")
                
                for device in devices:
                    health = self.check_device_health(device)
                    
                    if not health['healthy']:
                        device_id = health['device_id']
                        issues = ', '.join(health['issues'])
                        
                        self.send_alert(f"设备 {device_id} 异常: {issues}")
                        
                        # 自动修复逻辑
                        if '心跳超时' in issues:
                            print(f"尝试重启设备 {device_id}...")
                            if self.auto_restart_device(device_id):
                                print(f"设备 {device_id} 重启命令已发送")
                            else:
                                print(f"设备 {device_id} 重启失败")
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                print("监控已停止")
                break
            except Exception as e:
                print(f"监控错误: {e}")
                time.sleep(interval)

if __name__ == "__main__":
    monitor = ClusterMonitor("http://192.168.1.100:5000")
    monitor.monitor_loop(60)
```

### 智能任务调度器

```python
#!/usr/bin/env python3
"""
AI驱动的智能任务调度器
根据设备性能和负载自动优化任务分配
"""

import requests
import json
from typing import List, Dict, Optional
import math

class IntelligentScheduler:
    def __init__(self, cluster_url: str):
        self.cluster_url = cluster_url.rstrip('/')
    
    def get_available_devices(self) -> List[Dict]:
        """获取可用设备列表"""
        response = requests.get(f"{self.cluster_url}/api/v1/devices?status=online")
        return response.json()['data']['devices']
    
    def calculate_device_score(self, device: Dict, task_requirements: Dict) -> float:
        """计算设备适合度评分"""
        score = 0.0
        
        # CPU评分（50%权重）
        cpu_available = 100 - device['cpu_usage']
        required_cpu = task_requirements.get('min_cpu_percent', 10)
        if cpu_available >= required_cpu:
            score += 0.5 * (cpu_available / 100)
        else:
            return 0.0  # 不满足最低要求
        
        # 内存评分（30%权重）
        memory_available = device['memory_total'] - device['memory_used']
        required_memory = task_requirements.get('min_memory_gb', 0.5)
        if memory_available >= required_memory:
            score += 0.3 * min(1.0, memory_available / (required_memory * 2))
        else:
            return 0.0
        
        # 负载评分（20%权重）
        task_load = device.get('active_tasks', 0)
        max_tasks = device.get('max_concurrent_tasks', 5)
        if task_load < max_tasks:
            score += 0.2 * (1 - task_load / max_tasks)
        else:
            return 0.0
        
        return score
    
    def select_best_device(self, task_requirements: Dict) -> Optional[str]:
        """选择最适合的设备"""
        devices = self.get_available_devices()
        best_device = None
        best_score = 0.0
        
        for device in devices:
            score = self.calculate_device_score(device, task_requirements)
            if score > best_score:
                best_score = score
                best_device = device['id']
        
        return best_device
    
    def submit_optimized_task(self, task_type: str, payload: Dict, 
                            requirements: Dict = None) -> str:
        """提交优化调度的任务"""
        if not requirements:
            requirements = {}
        
        # 选择最佳设备
        best_device = self.select_best_device(requirements)
        
        if not best_device:
            raise Exception("没有可用的设备满足任务要求")
        
        # 提交任务到选定设备
        response = requests.post(
            f"{self.cluster_url}/api/v1/tasks",
            json={
                'task_type': task_type,
                'payload': payload,
                'device_id': best_device,
                'requirements': requirements
            }
        )
        
        if response.status_code == 200:
            task_id = response.json()['data']['task_id']
            print(f"任务 {task_id} 已调度到设备 {best_device}")
            return task_id
        else:
            raise Exception(f"任务提交失败: {response.text}")

# 使用示例
if __name__ == "__main__":
    scheduler = IntelligentScheduler("http://192.168.1.100:5000")
    
    # 提交计算密集型任务
    task_id = scheduler.submit_optimized_task(
        task_type='fibonacci',
        payload={'n': 1000000},
        requirements={
            'min_cpu_percent': 30,
            'min_memory_gb': 2.0
        }
    )
    
    print(f"计算任务已提交: {task_id}")
```

## 集成最佳实践

### 1. 错误处理
```python
def robust_api_call(url, **kwargs):
    """带重试的API调用"""
    for attempt in range(3):
        try:
            response = requests.get(url, timeout=10, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)  # 指数退避
```

### 2. 数据缓存
```python
from functools import lru_cache
import time

@lru_cache(maxsize=1)
def get_cached_devices(timestamp):
    """缓存设备列表（每30秒刷新）"""
    response = requests.get(f"{CLUSTER_URL}/api/v1/devices")
    return response.json()['data']['devices']

def get_devices():
    # 每30秒的时间戳
    cache_key = int(time.time()) // 30
    return get_cached_devices(cache_key)
```

### 3. 异步处理
```python
import asyncio
import aiohttp

async def async_cluster_client():
    """异步集群客户端"""
    async with aiohttp.ClientSession() as session:
        # 并发获取多个API端点
        tasks = [
            session.get(f"{CLUSTER_URL}/api/v1/devices"),
            session.get(f"{CLUSTER_URL}/api/v1/tasks"),
            session.get(f"{CLUSTER_URL}/api/v1/cluster/status")
        ]
        
        responses = await asyncio.gather(*tasks)
        return [await r.json() for r in responses]
```

## 性能对比

### 传统GUI vs CLI友好接口

| 特性 | 传统Web GUI | CLI友好接口 | AI访问优势 |
|------|-------------|-------------|------------|
| 数据获取 | 需要解析HTML | 直接JSON/文本 | 🚀 快速 |
| 带宽使用 | 高（CSS/JS/图片） | 低（纯数据） | 💾 节省 |
| 解析复杂度 | 复杂DOM解析 | 简单文本/JSON | ⚡ 高效 |
| 实时监控 | WebSocket复杂 | SSE简单 | 📡 稳定 |
| 脚本集成 | 困难（需要浏览器） | 简单（curl/Python） | 🔧 便捷 |
| 错误处理 | 需要截图识别 | 结构化错误消息 | 🎯 精确 |

通过这些AI友好的设计，Retire-Cluster为各种自动化场景提供了强大的集成能力，让AI代理能够高效地管理和监控分布式设备集群。