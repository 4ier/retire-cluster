# Retire-Cluster 部署指南

## 概述

本指南涵盖了 Retire-Cluster 的所有部署场景，从简单的开发设置到 NAS 系统上的生产级 Docker 部署。

## 目录

1. [快速开始](#快速开始)
2. [开发环境设置](#开发环境设置)
3. [生产环境部署](#生产环境部署)
4. [Docker 部署](#docker-部署)
5. [平台特定设置](#平台特定设置)
6. [监控和维护](#监控和维护)

## 快速开始

### 基本要求

- Python 3.8+（推荐 Python 3.10+）
- 网络连接（所有设备在同一网络中）
- 至少一台设备作为主节点（推荐 NAS 或常开计算机）

### 安装

```bash
# 从 PyPI 安装（可用时）
pip install retire-cluster

# 或从源码安装
git clone https://github.com/yourusername/retire-cluster.git
cd retire-cluster
pip install -e .
```

### 简单设置

```bash
# 1. 启动主节点（在 NAS 或主计算机上）
python -m retire_cluster.main_node --host 0.0.0.0 --port 8080

# 2. 启动工作节点（在任何设备上）
python -m retire_cluster.worker_node \
    --device-id "my-device" \
    --main-host 192.168.1.100 \
    --main-port 8080

# 3. 启动 Web 仪表板（可选）
python -m retire_cluster.web.app --port 5000
```

## 开发环境设置

### 本地开发

```bash
# 克隆仓库
git clone https://github.com/yourusername/retire-cluster.git
cd retire-cluster

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
pip install -e .

# 运行测试
python -m pytest tests/

# 启动开发服务器
python examples/simple_main_server.py
```

### 多节点测试

```bash
# 终端 1: 主节点
python examples/simple_main_server.py --port 8080

# 终端 2: 工作节点 1
python examples/simple_worker_client.py \
    --device-id worker-001 \
    --main-host localhost

# 终端 3: 工作节点 2
python examples/simple_worker_client.py \
    --device-id worker-002 \
    --main-host localhost

# 终端 4: Web 仪表板
python -m retire_cluster.web.app
```

## 生产环境部署

### 主节点配置

创建 `/etc/retire-cluster/config.json`：

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8080,
    "max_connections": 100
  },
  "database": {
    "path": "/var/lib/retire-cluster/cluster.db",
    "backup_enabled": true,
    "backup_interval": 3600
  },
  "logging": {
    "level": "INFO",
    "file": "/var/log/retire-cluster/cluster.log",
    "max_size": "10MB",
    "backup_count": 5
  },
  "cluster": {
    "heartbeat_interval": 60,
    "offline_threshold": 300,
    "task_timeout": 3600
  }
}
```

### Systemd 服务（Linux）

创建 `/etc/systemd/system/retire-cluster-main.service`：

```ini
[Unit]
Description=Retire-Cluster 主节点
After=network.target

[Service]
Type=simple
User=retire-cluster
Group=retire-cluster
ExecStart=/opt/retire-cluster/venv/bin/python -m retire_cluster.main_node --config /etc/retire-cluster/config.json
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用并启动服务：

```bash
# 创建用户
sudo useradd -r -s /bin/false retire-cluster

# 创建目录
sudo mkdir -p /var/lib/retire-cluster /var/log/retire-cluster /etc/retire-cluster
sudo chown retire-cluster:retire-cluster /var/lib/retire-cluster /var/log/retire-cluster

# 启用服务
sudo systemctl enable retire-cluster-main
sudo systemctl start retire-cluster-main
```

## Docker 部署

### 为什么只对主节点使用 Docker？

**主节点优势：**
- 在 NAS/服务器上保持一致的环境
- 简化更新和回滚
- 资源隔离
- 简化备份和迁移

**工作节点考虑因素：**
- 多样化平台（Android、旧笔记本、树莓派）
- 移动设备的资源限制
- 原生性能要求
- 平台特定功能（Termux、GPIO、传感器）

### 快速 Docker 设置

```bash
# 克隆仓库
git clone https://github.com/yourusername/retire-cluster.git
cd retire-cluster

# 配置环境
cp .env.example .env
# 编辑 .env 文件配置你的设置

# 使用自动化脚本部署
chmod +x docker/deploy.sh
./docker/deploy.sh

# 或直接使用 Docker Compose
docker-compose up -d
```

### Docker Compose 配置

```yaml
version: '3.8'

services:
  retire-cluster-main:
    container_name: retire-cluster-main
    image: retire-cluster:latest
    build: .
    restart: unless-stopped
    
    ports:
      - "8080:8080"  # 主节点服务器
      - "5000:5000"  # Web 仪表板
    
    volumes:
      - ./data/config:/data/config
      - ./data/database:/data/database
      - ./data/logs:/data/logs
    
    environment:
      - TZ=Asia/Shanghai
      - LOG_LEVEL=INFO
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/api/health"]
      interval: 30s
      timeout: 5s
      retries: 3
```

### Docker 管理脚本

**部署：**
```bash
./docker/deploy.sh [选项]
  --data-path PATH    # 自定义数据目录
  --with-proxy        # 使用 Nginx 代理部署
  --skip-build        # 跳过镜像构建
```

**备份：**
```bash
./docker/backup.sh              # 创建备份
./docker/backup.sh restore file # 从备份恢复
```

**健康监控：**
```bash
./docker/health-monitor.sh                    # 交互式监控
./docker/health-monitor.sh --daemon           # 后台监控
./docker/health-monitor.sh --email admin@...  # 邮件警报
```

## 平台特定设置

### NAS 部署

#### 群晖 DSM

```bash
# SSH 登录群晖 NAS
ssh admin@synology-ip

# 启用 Docker
# 套件中心 → Docker → 安装

# 部署 Retire-Cluster
cd /volume1/docker
git clone https://github.com/yourusername/retire-cluster.git
cd retire-cluster

# 配置群晖环境
cp .env.example .env
sed -i 's|DATA_PATH=.*|DATA_PATH=/volume1/docker/retire-cluster|' .env

# 部署
./docker/deploy.sh

# 设置计划任务
# 控制面板 → 任务计划器 → 新增
# 每日备份（凌晨 2 点）：/volume1/docker/retire-cluster/docker/backup.sh
```

#### 威联通 QTS

```bash
# SSH 登录威联通 NAS
ssh admin@qnap-ip

# 使用 Container Station
# App Center → Container Station → 安装

# 通过 Container Station GUI 或 CLI 部署
cd /share/Container
git clone https://github.com/yourusername/retire-cluster.git
cd retire-cluster

# 配置威联通环境
cp .env.example .env
sed -i 's|DATA_PATH=.*|DATA_PATH=/share/Container/retire-cluster|' .env

# 部署
./docker/deploy.sh
```

### 工作节点设置

#### Android (Termux)

```bash
# 从 F-Droid 安装 Termux
# 在 Termux 终端中：

# 更新包
pkg update && pkg upgrade

# 安装 Python 和依赖
pkg install python
pip install psutil requests

# 下载工作节点脚本
curl -O https://raw.githubusercontent.com/yourusername/retire-cluster/main/examples/simple_worker_client.py

# 运行工作节点
python simple_worker_client.py \
    --device-id android-$(hostname) \
    --role mobile \
    --main-host 192.168.1.100
```

#### 树莓派

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Python 和 pip
sudo apt install python3 python3-pip python3-venv -y

# 安装工作节点
pip3 install psutil requests

# 下载并运行工作节点
wget https://raw.githubusercontent.com/yourusername/retire-cluster/main/examples/simple_worker_client.py
python3 simple_worker_client.py \
    --device-id rpi-$(hostname) \
    --role compute \
    --main-host 192.168.1.100

# 可选：创建 systemd 服务
sudo tee /etc/systemd/system/retire-cluster-worker.service << EOF
[Unit]
Description=Retire-Cluster 工作节点
After=network.target

[Service]
Type=simple
User=pi
ExecStart=/usr/bin/python3 /home/pi/simple_worker_client.py --device-id rpi-$(hostname) --role compute --main-host 192.168.1.100
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable retire-cluster-worker
sudo systemctl start retire-cluster-worker
```

#### 旧笔记本/台式机

```bash
# Linux
sudo apt install python3 python3-pip
pip3 install psutil requests

# Windows
# 从 python.org 下载 Python
pip install psutil requests

# macOS
brew install python3
pip3 install psutil requests

# 下载并运行工作节点
curl -O https://raw.githubusercontent.com/yourusername/retire-cluster/main/examples/simple_worker_client.py
python3 simple_worker_client.py \
    --device-id laptop-$(hostname) \
    --role compute \
    --main-host 192.168.1.100
```

## Web 仪表板

### CLI 风格终端界面

Web 仪表板提供终端风格界面，可通过以下方式访问：
- **Web 浏览器**: http://your-main-node:5000
- **CLI 浏览器**: w3m、lynx、links（AI 友好）
- **API 访问**: 多种格式（JSON、CSV、TSV、纯文本）

### 功能特性

- **终端仿真**: 使用 xterm.js 的完整终端和命令执行
- **实时更新**: 用于实时监控的服务器发送事件
- **多格式输出**: 支持人类和机器可读格式
- **命令自动完成**: 命令的 Tab 补全
- **历史记录**: 上下箭头键的命令历史导航

### API 端点

```bash
# 文本 API（AI 友好）
curl http://main-node:5000/text/devices              # 管道分隔
curl http://main-node:5000/text/devices -H "Accept: text/csv"  # CSV
curl http://main-node:5000/text/status               # 键值对

# JSON API
curl http://main-node:5000/api/v1/devices           # 结构化 JSON
curl http://main-node:5000/api/v1/cluster/status    # 集群信息

# 流式 API
curl http://main-node:5000/stream/devices -H "Accept: text/event-stream"
curl http://main-node:5000/stream/logs               # 实时日志
```

## 监控和维护

### 健康监控

```bash
# 检查集群状态
curl http://main-node:8080/api/health
curl http://main-node:5000/text/status

# 查看日志
tail -f /var/log/retire-cluster/cluster.log  # 原生
docker logs -f retire-cluster-main           # Docker

# 监控资源
docker stats retire-cluster-main             # Docker
systemctl status retire-cluster-main         # Systemd
```

### 备份策略

**手动备份：**
```bash
# 原生部署
tar -czf backup-$(date +%Y%m%d).tar.gz \
    /var/lib/retire-cluster \
    /etc/retire-cluster

# Docker 部署
./docker/backup.sh
```

**自动备份（Crontab）：**
```bash
# 添加到 crontab
0 2 * * * /path/to/retire-cluster/docker/backup.sh
```

### 更新和升级

**Docker 部署：**
```bash
# 拉取最新代码
git pull origin main

# 重新构建和部署
./docker/deploy.sh

# 或手动更新
docker-compose down
docker-compose build
docker-compose up -d
```

**原生部署：**
```bash
# 更新代码
git pull origin main
pip install -e .

# 重启服务
sudo systemctl restart retire-cluster-main
```

### 故障排除

**常见问题：**

1. **连接被拒绝：**
   ```bash
   # 检查服务是否运行
   systemctl status retire-cluster-main
   docker ps | grep retire-cluster
   
   # 检查端口
   netstat -tulpn | grep 8080
   
   # 检查防火墙
   sudo ufw status
   ```

2. **工作节点无法连接：**
   ```bash
   # 测试连接
   telnet main-node-ip 8080
   
   # 检查工作节点日志
   python simple_worker_client.py --test --main-host main-node-ip
   ```

3. **数据库问题：**
   ```bash
   # 检查数据库完整性
   sqlite3 /var/lib/retire-cluster/cluster.db "PRAGMA integrity_check;"
   
   # 从备份恢复
   ./docker/backup.sh restore backup_file.tar.gz
   ```

**日志分析：**
```bash
# 主节点日志
tail -f /var/log/retire-cluster/cluster.log
docker logs -f retire-cluster-main

# Web 仪表板日志
tail -f /var/log/retire-cluster/web.log

# 工作节点日志（检查工作节点输出）
```

## 安全考虑

### 网络安全

1. **防火墙配置：**
   ```bash
   # 允许集群通信
   sudo ufw allow 8080/tcp
   sudo ufw allow 5000/tcp
   
   # 限制到本地网络
   sudo ufw allow from 192.168.1.0/24 to any port 8080
   ```

2. **仅内部网络：**
   ```yaml
   # Docker Compose - 绑定到特定 IP
   ports:
     - "192.168.1.100:8080:8080"
   ```

### 应用程序安全

1. **API 认证**（未来功能）：
   ```json
   {
     "security": {
       "api_key_required": true,
       "api_keys": ["your-secret-key"],
       "rate_limiting": {
         "requests_per_minute": 60
       }
     }
   }
   ```

2. **容器安全：**
   - 以非 root 用户运行（UID 1000）
   - 强制执行资源限制
   - 只读根文件系统（可选）

### 数据保护

1. **加密备份：**
   ```bash
   # 加密备份文件
   gpg --symmetric --cipher-algo AES256 backup.tar.gz
   ```

2. **访问控制：**
   ```bash
   # 设置正确的文件权限
   chmod 600 /etc/retire-cluster/config.json
   chown retire-cluster:retire-cluster /var/lib/retire-cluster
   ```

## 性能优化

### 资源调优

**Docker 限制：**
```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
    reservations:
      cpus: '0.5'
      memory: 512M
```

**数据库优化：**
```json
{
  "database": {
    "wal_mode": true,
    "cache_size": 10000,
    "synchronous": "NORMAL"
  }
}
```

### 网络优化

```json
{
  "cluster": {
    "heartbeat_interval": 30,
    "connection_pool_size": 50,
    "tcp_keepalive": true
  }
}
```

## 生产环境检查清单

- [ ] 主节点部署在可靠硬件上（NAS/服务器）
- [ ] 配置自动备份的 Docker 部署
- [ ] 配置健康监控
- [ ] 配置防火墙规则
- [ ] 工作节点注册并在线
- [ ] Web 仪表板可访问
- [ ] 配置日志轮转
- [ ] 测试备份计划
- [ ] 记录更新程序
- [ ] 配置监控警报

## 支持和资源

- **文档**: `/docs/` 目录
- **示例**: `/examples/` 目录
- **问题**: GitHub Issues
- **社区**: GitHub Discussions

---

**下一步：**
1. 选择你的部署方式（生产环境推荐 Docker）
2. 在 NAS 或常开设备上设置主节点
3. 在闲置设备上配置工作节点
4. 访问 Web 仪表板进行管理
5. 设置监控和备份