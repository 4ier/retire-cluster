# Retire-Cluster 中文文档

## 概述

此目录包含 Retire-Cluster 分布式计算系统的完整中文文档。

## 文档索引

### 核心指南

- **[系统架构](architecture_CN.md)** - 完整的系统架构、组件和设计模式
- **[部署指南](deployment-guide_CN.md)** - 所有场景的综合部署说明

### Web界面文档

- **[Web界面设计](web-interface-design_CN.md)** - 终端风格Web仪表板设计和架构
- **[CLI界面规范](cli-interface-specification_CN.md)** - 完整的命令参考和使用说明
- **[AI集成指南](ai-integration-guide_CN.md)** - AI友好的接口模式和示例

### API文档

- **[REST API](rest_api_CN.md)** - HTTP API端点和使用示例
- **[任务执行框架](task_execution_framework_CN.md)** - 任务调度和执行系统

## 快速参考

### 部署方式

1. **Docker（生产环境推荐）**
   ```bash
   git clone https://github.com/yourusername/retire-cluster.git
   cd retire-cluster
   ./docker/deploy.sh
   ```

2. **原生安装**
   ```bash
   pip install retire-cluster
   retire-cluster-main --init-config
   ```

### 关键端点

- **主节点**: `http://main-node:8080` (TCP套接字服务器)
- **Web仪表板**: `http://main-node:5000` (HTTP界面)
- **健康检查**: `http://main-node:8080/api/health`

### 常用命令

```bash
# CLI风格命令（通过Web界面）
devices list --status=online
cluster status
tasks submit echo --payload='{"message":"hello"}'
monitor logs --tail=100

# REST API调用
curl http://main-node:5000/text/devices
curl http://main-node:5000/api/v1/cluster/status
```

## 架构概览

```
主节点 (NAS/服务器)              工作节点 (分布式设备)
┌─────────────────────┐         ┌──────────────────────────┐
│ ┌─────────────────┐ │         │ Android │ 笔记本 │ 树莓派 │
│ │   核心系统      │ │◄───────►│ Termux  │ 原生   │ ARM  │
│ │ 设备注册表      │ │         │         │        │      │
│ │ 任务调度器      │ │         │ ┌─────────────────────┐ │
│ │ 心跳监控器      │ │         │ │ 设备分析器          │ │
│ └─────────────────┘ │         │ │ 系统监控器          │ │
│                     │         │ │ 任务执行器          │ │
│ ┌─────────────────┐ │         │ └─────────────────────┘ │
│ │  Web仪表板      │ │         └──────────────────────────┘
│ │ 终端UI          │ │
│ │ REST API        │ │
│ │ 实时SSE         │ │
│ └─────────────────┘ │
└─────────────────────┘
```

## 入门指南

1. **阅读[系统架构指南](architecture_CN.md)** 了解系统设计
2. **按照[部署指南](deployment-guide_CN.md)** 进行特定场景的部署
3. **探索[Web界面](web-interface-design_CN.md)** 文档了解仪表板使用
4. **查看[CLI规范](cli-interface-specification_CN.md)** 获取命令参考

## 贡献

添加新文档时：

1. 遵循现有结构和风格
2. 包含实用示例和代码片段
3. 添加新文件时更新此索引
4. 保持文档与代码变更同步

## 支持

- **GitHub Issues**: 报告错误或请求功能
- **GitHub Discussions**: 提问和分享想法
- **主要文档**: 查看项目 README.md 获取概览