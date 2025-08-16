# Retire-Cluster

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.7+-green.svg)
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

- Python 3.7+
- 网络连通性（所有设备需在同一网络）
- 可选：psutil用于增强系统监控

### 安装

```bash
# 克隆仓库
git clone https://github.com/4ier/retire-cluster.git
cd retire-cluster

# 安装依赖
pip install -r requirements.txt

# 或作为包安装
pip install .
```

### 启动主节点

```bash
# 使用简单示例服务器
python examples/simple_main_server.py

# 或使用包
python -m retire_cluster.main_node --host 0.0.0.0 --port 8080
```

### 启动工作节点

```bash
# 使用简单示例客户端
python examples/simple_worker_client.py --device-id worker-001 --main-host <主节点IP>

# 或使用包
python -m retire_cluster.worker_node --device-id worker-001 --main-host <主节点IP>
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
python simple_worker_client.py --device-id android-001 --role mobile --main-host <主节点IP>
```

#### 树莓派 / ARM设备

```bash
# 如果没有Python，先安装
sudo apt-get update
sudo apt-get install python3 python3-pip

# 运行工作节点
python3 simple_worker_client.py --device-id rpi-001 --role compute --main-host <主节点IP>
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

### v1.0.0 (当前版本)
- [x] 基础设备管理
- [x] TCP socket通信
- [x] 心跳监控
- [x] 跨平台支持

### v1.1.0 (计划中)
- [ ] 任务执行框架
- [ ] Web管理界面
- [ ] REST API
- [ ] Docker支持

### v2.0.0 (未来)
- [ ] 分布式存储
- [ ] 负载均衡
- [ ] 多集群支持
- [ ] 云端集成

---

**让你的闲置设备重获新生！🚀**