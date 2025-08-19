# 调试 NAS Web Dashboard 连接问题

## 问题描述
无法访问 http://192.168.0.116:5008/

## 可能的原因和解决方案

### 1. 容器未运行
```bash
# SSH到NAS
ssh 18617007050@192.168.0.116

# 检查容器状态
docker ps -a | grep retire-cluster

# 如果容器未运行，启动它
cd ~/docker/retire-cluster
docker-compose up -d
```

### 2. 端口配置错误
```bash
# 检查当前端口映射
docker port retire-cluster-main

# 检查.env文件配置
cat .env | grep -E "(WEB_PORT|CLUSTER_PORT)"

# 应该看到：
# WEB_PORT=5008
# CLUSTER_PORT=8081
```

### 3. 修复端口配置
```bash
# 运行修复脚本
chmod +x docker/fix-port.sh
./docker/fix-port.sh
```

### 4. 手动修复步骤
```bash
# 1. 停止容器
docker-compose down

# 2. 编辑.env文件
echo "WEB_PORT=5008" >> .env
echo "CLUSTER_PORT=8081" >> .env

# 3. 重新启动
docker-compose up -d

# 4. 检查日志
docker logs -f retire-cluster-main
```

### 5. 防火墙配置

#### Synology DSM
1. 打开控制面板 > 安全性 > 防火墙
2. 创建新规则允许端口 5008 和 8081
3. 或者临时禁用防火墙测试

#### 命令行方式
```bash
# 添加防火墙规则（Synology）
sudo iptables -I INPUT -p tcp --dport 5008 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 8081 -j ACCEPT
```

### 6. 测试连接

#### 从NAS本地测试
```bash
# 测试容器内部
docker exec retire-cluster-main curl http://localhost:5000

# 测试主机端口
curl http://localhost:5008
curl http://127.0.0.1:5008
```

#### 从其他设备测试
```bash
# 测试网络连通性
ping 192.168.0.116

# 测试端口是否开放
telnet 192.168.0.116 5008
# 或
nc -zv 192.168.0.116 5008

# 测试HTTP访问
curl http://192.168.0.116:5008
```

### 7. 查看详细日志
```bash
# 容器日志
docker logs retire-cluster-main --tail 100

# Docker Compose日志
docker-compose logs

# 系统日志（如果有权限）
dmesg | grep -i docker
journalctl -u docker
```

### 8. 容器网络检查
```bash
# 检查容器网络
docker network ls
docker network inspect retire-cluster_retire-cluster-net

# 检查容器IP
docker inspect retire-cluster-main | grep IPAddress

# 进入容器调试
docker exec -it retire-cluster-main sh
# 在容器内：
netstat -tulpn
ps aux
```

### 9. 完整重新部署
如果以上都不行，尝试完全重新部署：

```bash
# 1. 完全清理
docker-compose down -v
docker system prune -f

# 2. 创建新的.env文件
cat > .env << EOF
DATA_PATH=/volume1/docker/retire-cluster
TZ=Asia/Shanghai
LOG_LEVEL=INFO
CLUSTER_PORT=8081
WEB_PORT=5008
NETWORK_SUBNET=172.20.0.0/16
CPU_LIMIT=2.0
CPU_RESERVATION=0.5
MEMORY_LIMIT=2G
MEMORY_RESERVATION=512M
EOF

# 3. 重新部署
docker-compose up -d

# 4. 监控日志
docker-compose logs -f
```

### 10. 验证Web服务是否启动
```bash
# 检查Web服务进程
docker exec retire-cluster-main ps aux | grep -E "(python|flask|web)"

# 检查端口监听
docker exec retire-cluster-main netstat -tulpn | grep 5000
```

## 快速诊断命令
运行这个一键诊断：
```bash
echo "=== Docker容器状态 ==="
docker ps -a | grep retire-cluster
echo ""
echo "=== 端口映射 ==="
docker port retire-cluster-main 2>/dev/null || echo "容器未运行"
echo ""
echo "=== 环境变量 ==="
cat .env 2>/dev/null | grep -E "(WEB_PORT|CLUSTER_PORT)" || echo ".env文件不存在"
echo ""
echo "=== 本地测试 ==="
curl -I http://localhost:5008 2>/dev/null || echo "本地无法访问"
echo ""
echo "=== 容器日志（最后10行）==="
docker logs --tail 10 retire-cluster-main 2>/dev/null || echo "无法获取日志"
```

## 预期结果
正确配置后，应该能够：
1. 从NAS本地访问: http://localhost:5008
2. 从局域网访问: http://192.168.0.116:5008
3. 看到Web Dashboard界面

如果还是无法访问，请提供上述诊断命令的输出结果。