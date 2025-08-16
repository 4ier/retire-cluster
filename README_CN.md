# Retire-Cluster

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS%20%7C%20Android-lightgrey.svg)

> 让闲置设备重获新生！基于TCP Socket通信的分布式系统，将你的旧手机、平板、笔记本等闲置设备组织成一个统一的AI工作集群。

[English Documentation](README.md)

## 🎯 项目概述

Retire-Cluster是一个创新的闲置设备复用解决方案，专为拥有多台旧设备的用户设计。通过将闲置的手机、平板、老笔记本等设备组织成一个统一的工作集群，让这些"退休"的设备重新发挥价值。

系统支持设备自动发现、实时状态监控、智能任务调度，并提供自然语言接口进行集群管理。

### ✨ 核心特性

- **♻️ 闲置设备复用**: 让旧手机、平板、老笔记本重新发挥价值
- **🤖 智能设备调度**: 基于设备能力和状态自动选择最适合的执行节点
- **📊 实时监控**: 心跳机制确保设备状态实时更新，支持故障自动检测
- **🔧 自动发现**: 设备自感知系统，自动收集和上报硬件软件信息
- **🔄 动态扩展**: 支持设备热插拔，无需重启服务即可添加新设备
- **🛡️ 故障容错**: 自动故障检测和任务重新分配机制
- **🌍 跨平台支持**: 支持Windows、Linux、macOS、Android (Termux)
- **⚡ 任务执行**: 分布式任务执行，支持优先级队列和需求匹配
- **🌐 REST API**: 完整的HTTP API，支持程序化集群管理
- **🔐 安全性**: API认证、限流和输入验证
- **🔗 框架集成**: 支持Temporal、Celery等主流框架集成
- **📦 简单安装**: 单一pip命令安装，自动配置

## 🏗️ 系统架构

```
┌─────────────────────┐         ┌─────────────────────┐
│   主节点            │         │   工作节点           │
│                     │◄────────┤                     │
│ ┌─────────────────┐ │         │ ┌─────────────────┐ │
│ │设备注册表       │ │         │ │设备分析器       │ │
│ │任务调度器       │ │         │ │系统监控器       │ │
│ │心跳监控器       │ │         │ │任务执行器       │ │
│ └─────────────────┘ │         │ └─────────────────┘ │
└─────────────────────┘         └─────────────────────┘
        TCP Socket                    TCP Socket
```

### 节点类型

- **主节点 (Main Node)**: 集群协调器和管理中心
- **工作节点 (Worker Node)**: 任务执行单元，支持多种平台
- **存储节点 (Storage Node)**: 数据存储和文件服务（计划中）

## 🚀 快速开始

### 系统要求

- Python 3.10+
- 网络连通性（所有设备需在同一网络）
- 可选：psutil用于增强系统监控

### 安装

```bash
# 基础安装
pip install retire-cluster

# 包含REST API支持
pip install retire-cluster[api]

# 包含框架集成
pip install retire-cluster[integrations]

# 完整安装（包含所有功能）
pip install retire-cluster[all]

# 或从源码安装
git clone https://github.com/4ier/retire-cluster.git
cd retire-cluster
pip install .[all]
```

### 启动主节点

```bash
# 使用默认设置启动主节点
retire-cluster-main

# 使用自定义端口和数据目录
retire-cluster-main --port 9090 --data-dir /opt/retire-cluster

# 初始化配置文件
retire-cluster-main --init-config
```

### 启动工作节点

```bash
# 使用自动检测加入集群
retire-cluster-worker --join 192.168.1.100

# 使用自定义设备ID和角色
retire-cluster-worker --join 192.168.1.100:8080 --device-id my-laptop --role compute

# 仅测试连接
retire-cluster-worker --test 192.168.1.100
```

### 监控集群状态

```bash
# 查看集群概况
retire-cluster-status 192.168.1.100

# 列出所有设备
retire-cluster-status 192.168.1.100 --devices

# 查看特定设备详情
retire-cluster-status 192.168.1.100 --device worker-001

# 按角色筛选设备
retire-cluster-status 192.168.1.100 --devices --role mobile

# JSON格式输出
retire-cluster-status 192.168.1.100 --json
```

### 启动REST API服务器

```bash
# 使用默认设置启动API服务器
retire-cluster-api

# 启用认证和自定义端口
retire-cluster-api --port 8081 --auth --api-key your-secret-key

# 连接到指定集群节点
retire-cluster-api --cluster-host 192.168.1.100 --cluster-port 8080
```

### 使用REST API

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
  -d '{"task_type": "echo", "payload": {"message": "Hello API!"}}'

# 检查任务状态
curl http://localhost:8081/api/v1/tasks/{task_id}/status
```

### 任务执行

```python
# 程序化提交任务
from retire_cluster.tasks import Task, TaskRequirements, TaskPriority

# 简单任务
task = Task(
    task_type="echo",
    payload={"message": "Hello World!"},
    priority=TaskPriority.NORMAL
)

# 带特定需求的任务
compute_task = Task(
    task_type="python_eval",
    payload={"expression": "sum(range(1000000))"},
    requirements=TaskRequirements(
        min_cpu_cores=4,
        min_memory_gb=8,
        required_platform="linux"
    )
)

# 提交到调度器
task_id = scheduler.submit_task(task)
```

### 测试连接

```bash
# 测试工作节点到主节点的连接
python examples/simple_worker_client.py --device-id test-001 --test --main-host <主节点IP>
```

## 📖 使用文档

### 基础用法

```python
# 启动主节点服务器
from retire_cluster.communication.server import ClusterServer
from retire_cluster.core.config import Config

config = Config()
server = ClusterServer(config)
server.start()
```

```python
# 启动工作节点客户端
from retire_cluster.communication.client import ClusterClient
from retire_cluster.core.config import WorkerConfig

config = WorkerConfig()
config.device_id = "worker-001"
config.main_host = "192.168.1.100"

client = ClusterClient(config)
client.run()
```

### 配置文件

配置文件位于 `configs/` 目录：

- `main_config_example.json`: 主节点配置模板
- `worker_config_example.json`: 工作节点配置模板

### 平台特定设置

#### Android (Termux)

```bash
# 从F-Droid或Google Play安装Termux
# 在Termux中：
pkg update
pkg install python
pip install psutil

# 运行工作节点
retire-cluster-worker --join <主节点IP> --role mobile
```

#### 树莓派 / ARM设备

```bash
# 如果没有Python，先安装
sudo apt-get update
sudo apt-get install python3 python3-pip

# 运行工作节点
retire-cluster-worker --join <主节点IP> --role compute
```

## 🔧 高级功能

### 自定义设备角色

为特殊设备定义自定义角色：

```python
# 在工作节点配置中
config.role = "gpu-compute"  # GPU设备
config.role = "storage"      # NAS或存储服务器
config.role = "mobile"       # 移动设备
```

### 设备能力

系统自动检测设备能力：

- **计算能力**: CPU核心数、GPU可用性
- **存储能力**: 可用磁盘空间
- **服务能力**: 网络服务、自动化能力

### 监控与管理

实时监控集群状态：

```python
# 获取集群统计信息
stats = registry.get_cluster_stats()
print(f"在线设备: {stats['online_devices']}")
print(f"总资源: {stats['total_resources']}")
```

## 📊 API参考

### 消息协议

系统使用基于JSON的TCP Socket通信：

```json
{
  "message_type": "register|heartbeat|status|task_assign|task_result",
  "sender_id": "device-id",
  "data": {
    // 消息特定数据
  }
}
```

### REST API端点

- **集群管理**: `/api/v1/cluster/*` - 状态、健康检查、指标
- **设备管理**: `/api/v1/devices/*` - 列表、详情、状态、删除
- **任务管理**: `/api/v1/tasks/*` - 提交、查询、取消、重试
- **配置管理**: `/api/v1/config/*` - 读取、更新、重置

详细API文档请参考 [REST API文档](docs/rest_api.md)

## 📚 文档资源

- **任务执行框架**: [任务执行文档](docs/task_execution_framework.md)
- **REST API**: [API完整文档](docs/rest_api.md)
- **示例代码**: 
  - [任务执行示例](examples/task_execution_example.py)
  - [API使用示例](examples/api_usage_example.py)

## 🤝 贡献

欢迎贡献代码！详情请查看 [CONTRIBUTING.md](CONTRIBUTING.md)。

1. Fork 仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🗺️ 发展路线图

### v1.0.0 (已发布)
- [x] 基础设备管理
- [x] TCP socket通信
- [x] 心跳监控
- [x] 跨平台支持
- [x] CLI包管理安装
- [x] 设备分析和自动检测
- [x] 简化的工作节点部署

### v1.1.0 (当前版本)
- [x] 任务执行框架
- [x] 智能任务调度和队列管理
- [x] 内置任务类型（echo、sleep、system_info等）
- [x] 任务需求与设备能力匹配
- [x] REST API完整端点实现
- [x] API认证和安全中间件
- [x] 完整的API文档和示例
- [ ] Web管理界面
- [ ] Docker支持

### v1.2.0 (计划中)
- [ ] Web管理仪表板
- [ ] 实时集群监控界面
- [ ] 交互式任务提交界面
- [ ] 设备管理Web界面
- [ ] Docker容器化支持
- [ ] Docker Compose部署模板

### v2.0.0 (未来)
- [ ] 分布式存储系统
- [ ] 高级负载均衡算法
- [ ] 多集群联邦
- [ ] 云服务商集成（AWS、Azure、GCP）
- [ ] 自动扩缩容能力
- [ ] 机器学习工作负载优化
- [ ] WebSocket实时更新
- [ ] 监控指标集成（Prometheus、Grafana）

### 框架集成（进行中）
- [x] Temporal工作流集成支持
- [x] Celery任务队列集成
- [x] HTTP桥接外部框架
- [ ] Kubernetes操作器
- [ ] Apache Airflow集成
- [ ] Ray分布式计算集成

---

**让你的闲置设备重获新生！🚀**