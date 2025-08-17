# Web界面设计文档

## 概述

Retire-Cluster 采用 CLI 优先的 Web 界面设计，在通过终端风格美学保持出色的人机可用性的同时，优先考虑机器可读性和 AI 可访问性。

## 设计理念

### 核心原则

1. **文本优先**: 所有信息必须可以作为纯文本访问
2. **命令驱动**: 每个操作都可以通过命令执行
3. **机器可读**: 针对解析优化的输出格式
4. **渐进增强**: 在任何文本浏览器中都能工作，在现代浏览器中得到增强
5. **键盘为中心**: 完整的键盘导航支持

### 目标用户

- **主要用户**: 系统管理员、DevOps 工程师
- **次要用户**: AI 代理、自动化脚本
- **第三方用户**: 监控系统、CLI 浏览器

## 架构

### 三层访问模型

```
┌─────────────────────────────────────┐
│         展示层                       │
├─────────────┬───────────────────────┤
│  Web终端    │    CLI/文本访问       │
│   (xterm.js) │  (w3m, lynx, curl)   │
├─────────────┼───────────────────────┤
│  /web/*     │    /cli/*              │
│  (富文本UI)  │    (纯文本)           │
├─────────────┴───────────────────────┤
│         API层                        │
│    /api/v1/* (JSON)                 │
│    /text/*   (纯文本)               │
│    /stream/* (SSE/WebSocket)        │
└─────────────────────────────────────┘
```

### 端点结构

| 路径模式 | 内容类型 | 用途 | 示例 |
|----------|----------|------|------|
| `/api/v1/*` | `application/json` | 编程访问 | `/api/v1/devices` |
| `/text/*` | `text/plain` | CLI/AI访问 | `/text/devices` |
| `/cli/*` | `text/html` | 终端UI | `/cli/dashboard` |
| `/stream/*` | `text/event-stream` | 实时更新 | `/stream/logs` |

## 命令系统

### 命令语法

```
<动词> <名词> [选项] [参数]
```

示例：
- `list devices --status=online`
- `show device android-001`
- `submit task --type=echo --payload="test"`
- `monitor logs --device=laptop-002`

### 核心命令

```bash
# 帮助和导航
help [command]           # 显示命令帮助
clear                   # 清除屏幕
exit                    # 退出界面

# 集群管理
cluster status          # 显示集群状态
cluster health          # 健康检查
cluster metrics         # 性能指标
cluster config          # 配置

# 设备操作
devices list [--status=] [--role=]     # 列出设备
devices show <id>                       # 显示设备详细信息
devices ping <id>                       # ping设备
devices remove <id>                     # 移除设备
devices monitor                         # 实时监控

# 任务管理
tasks submit <type> [--payload=]        # 提交任务
tasks list [--status=] [--device=]     # 列出任务
tasks show <id>                         # 显示任务详细信息
tasks cancel <id>                       # 取消任务
tasks retry <id>                        # 重试任务
tasks monitor                           # 监控任务

# 监控
monitor devices         # 设备状态流
monitor tasks          # 任务执行流
monitor logs           # 日志流
monitor metrics        # 指标流

# 导出
export devices --format=csv            # 导出设备到CSV
export tasks --format=json             # 导出任务到JSON
export logs --since=1h                 # 导出最近1小时的日志
export config                          # 导出配置
```

## 用户界面组件

### 1. 终端模拟器 (xterm.js)

**核心功能：**
- 完整的VT100/xterm兼容性
- 命令自动补全（Tab键）
- 命令历史（上下箭头）
- 多行编辑支持
- 复制粘贴功能

**实现特性：**
```javascript
// 终端配置
const terminal = new Terminal({
  theme: {
    background: '#000000',
    foreground: '#00ff00',  // 绿色文本（Matrix主题）
  },
  fontSize: 14,
  fontFamily: 'Consolas, Monaco, monospace',
  cursorBlink: true,
  allowTransparency: true
});

// 自动补全
terminal.onData((input) => {
  if (input === '\t') {
    // 触发命令补全
    requestCompletion(currentLine);
  }
});
```

### 2. 状态仪表板

**ASCII艺术界面：**
```
┌─────────────────────────────────────────────────────────────┐
│                     RETIRE-CLUSTER v1.1.0                   │
├─────────────────────────────────────────────────────────────┤
│ 集群状态: HEALTHY    │ 在线设备: 5/7      │ 活动任务: 12     │
│ 运行时间: 15d 6h     │ CPU使用: 37%       │ 内存使用: 42%    │
├─────────────────────────────────────────────────────────────┤
│                        设备网格                              │
│ ┌─────┬─────┬─────┬─────┐                                    │
│ │ ✓01 │ ✓02 │ ✗03 │ ✓04 │  ✓ 在线  ✗ 离线  ⚠ 警告        │
│ │ ✓05 │ ⚠06 │ ✓07 │ --- │                                 │
│ └─────┴─────┴─────┴─────┘                                    │
├─────────────────────────────────────────────────────────────┤
│                      最近活动                                │
│ [10:30:15] INFO: 设备 android-001 已连接                    │
│ [10:30:16] ERROR: 任务 task-abc123 执行失败                 │
│ [10:30:17] WARNING: 设备 raspi-003 心跳超时                 │
└─────────────────────────────────────────────────────────────┘
```

### 3. 设备列表

**表格格式（人类可读）：**
```
设备ID        状态    CPU   内存   任务  角色      平台     运行时间
─────────────────────────────────────────────────────────────────
android-001   在线    42%   2.1GB   3    mobile    android  2d 14h 32m
laptop-002    在线    15%   4.5GB   1    compute   linux    5d 08h 15m
raspi-003     离线    0%    0GB     0    storage   linux    0m
```

**管道分隔格式（机器可读）：**
```
android-001|online|42|2.1|3|mobile|android|2d14h32m
laptop-002|online|15|4.5|1|compute|linux|5d08h15m
raspi-003|offline|0|0|0|storage|linux|0m
```

### 4. 任务监控

**实时任务流：**
```
任务ID         状态      设备          类型        进度      运行时间
─────────────────────────────────────────────────────────────────
task-abc123    运行中    android-001   python_eval [████████░░] 80%  00:02:15
task-def456    排队      -             echo        [░░░░░░░░░░]  0%  00:00:00
task-ghi789    完成      laptop-002    system_info [██████████] 100% 00:00:03
```

### 5. 日志查看器

**彩色日志输出：**
```bash
# 实时日志流
logs follow

# 输出示例
[2024-01-15 10:30:15] INFO  主节点启动成功 (端口: 8080)
[2024-01-15 10:30:16] DEBUG 等待设备连接...
[2024-01-15 10:30:17] INFO  设备注册: android-001 (8核, 8GB内存)
[2024-01-15 10:30:18] WARN  设备 raspi-003 心跳延迟 (延迟: 120s)
[2024-01-15 10:30:19] ERROR 任务执行失败: task-abc123 (原因: 超时)
```

## 响应式设计

### 桌面布局 (>1200px)

```
┌─────────────────────────────────────────────────────────────┐
│ Retire-Cluster Dashboard                      [≡] [◐] [✕]  │
├─────────────────────────────────────────────────────────────┤
│ ┌───────────────┐ ┌─────────────────────────────────────────┐ │
│ │    侧边栏      │ │              主终端区域                  │ │
│ │               │ │                                         │ │
│ │ • 仪表板      │ │  cluster@main:~$ devices list          │ │
│ │ • 设备管理    │ │  设备ID        状态    CPU    内存      │ │
│ │ • 任务管理    │ │  ─────────────────────────────────────  │ │
│ │ • 监控        │ │  android-001   在线    42%    2.1GB    │ │
│ │ • 日志        │ │  laptop-002    在线    15%    4.5GB    │ │
│ │ • 设置        │ │  raspi-003     离线    0%     0GB      │ │
│ │               │ │                                         │ │
│ │               │ │  cluster@main:~$ █                     │ │
│ └───────────────┘ └─────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ 状态栏: 5设备在线 | 12个活动任务 | CPU: 37% | 内存: 42%        │
└─────────────────────────────────────────────────────────────┘
```

### 移动布局 (<768px)

```
┌─────────────────────────────┐
│ [☰] Retire-Cluster    [⚙]  │
├─────────────────────────────┤
│                             │
│  cluster@main:~$ devices    │
│                             │
│  android-001  在线  42%     │
│  laptop-002   在线  15%     │
│  raspi-003    离线   0%     │
│                             │
│  cluster@main:~$ █         │
│                             │
├─────────────────────────────┤
│ [仪表板] [设备] [任务] [日志] │
└─────────────────────────────┘
```

## 主题系统

### Matrix主题（默认）
```css
:root {
  --bg-primary: #000000;
  --bg-secondary: #001100;
  --text-primary: #00ff00;
  --text-secondary: #00aa00;
  --accent: #00ff41;
  --warning: #ffff00;
  --error: #ff0000;
  --border: #004400;
}
```

### 琥珀主题
```css
:root {
  --bg-primary: #1a0f00;
  --bg-secondary: #2a1500;
  --text-primary: #ffb000;
  --text-secondary: #cc8800;
  --accent: #ffd700;
  --warning: #ff8800;
  --error: #ff4400;
  --border: #664400;
}
```

### 蓝色主题
```css
:root {
  --bg-primary: #001122;
  --bg-secondary: #002244;
  --text-primary: #00aaff;
  --text-secondary: #0088cc;
  --accent: #00ccff;
  --warning: #ffaa00;
  --error: #ff4444;
  --border: #004466;
}
```

## API集成

### 文本API端点

**设备列表：**
```bash
# 默认格式（管道分隔）
GET /text/devices
Content-Type: text/plain

android-001|online|42|2.1|3
laptop-002|online|15|4.5|1
raspi-003|offline|0|0|0

# CSV格式
GET /text/devices
Accept: text/csv

id,status,cpu,memory,tasks
android-001,online,42,2.1,3
laptop-002,online,15,4.5,1
raspi-003,offline,0,0,0

# TSV格式
GET /text/devices
Accept: text/tab-separated-values

id	status	cpu	memory	tasks
android-001	online	42	2.1	3
laptop-002	online	15	4.5	1
raspi-003	offline	0	0	0
```

**集群状态：**
```bash
GET /text/status
Content-Type: text/plain

STATUS: healthy
NODES: 2/3 online
CPU: 48 cores (37% utilized)
MEMORY: 128GB (42% used)
TASKS: 12 active, 45 completed
UPTIME: 15d 6h 42m
```

**Prometheus指标：**
```bash
GET /text/metrics
Content-Type: text/plain

# HELP cluster_devices_total 集群中的总设备数
# TYPE cluster_devices_total gauge
cluster_devices_total 3

# HELP cluster_devices_online 在线设备数
# TYPE cluster_devices_online gauge
cluster_devices_online 2

# HELP cluster_cpu_usage_percent CPU使用率百分比
# TYPE cluster_cpu_usage_percent gauge
cluster_cpu_usage_percent 37

# HELP cluster_memory_usage_percent 内存使用率百分比
# TYPE cluster_memory_usage_percent gauge
cluster_memory_usage_percent 42
```

### 流式端点

**设备状态流：**
```bash
GET /stream/devices
Accept: text/event-stream

data: {"event": "device_update", "device_id": "android-001", "status": "online", "cpu": 42}

data: {"event": "device_offline", "device_id": "raspi-003", "timestamp": "2024-01-15T10:30:17Z"}

data: {"event": "device_online", "device_id": "raspi-003", "timestamp": "2024-01-15T10:35:22Z"}
```

**日志流：**
```bash
GET /stream/logs
Accept: text/event-stream

data: {"timestamp": "2024-01-15T10:30:15Z", "level": "INFO", "message": "设备 android-001 已连接"}

data: {"timestamp": "2024-01-15T10:30:16Z", "level": "ERROR", "message": "任务 task-abc123 执行失败"}
```

## 可访问性特性

### 键盘导航

**全局快捷键：**
- `Ctrl+/`: 显示帮助
- `Ctrl+K`: 命令面板
- `Ctrl+L`: 清除屏幕
- `Esc`: 取消当前操作
- `Tab`: 命令补全
- `↑/↓`: 命令历史

**导航快捷键：**
- `Alt+1`: 仪表板
- `Alt+2`: 设备管理
- `Alt+3`: 任务管理
- `Alt+4`: 监控
- `Alt+5`: 日志

### 屏幕阅读器支持

```html
<!-- 语义化HTML结构 -->
<main role="main" aria-label="集群管理控制台">
  <section aria-label="设备状态">
    <h2>设备状态</h2>
    <table role="grid" aria-label="设备列表">
      <thead>
        <tr role="row">
          <th role="columnheader">设备ID</th>
          <th role="columnheader">状态</th>
        </tr>
      </thead>
      <tbody>
        <tr role="row" aria-describedby="device-android-001-status">
          <td role="gridcell">android-001</td>
          <td role="gridcell" id="device-android-001-status">在线</td>
        </tr>
      </tbody>
    </table>
  </section>
</main>
```

### 高对比度模式

```css
@media (prefers-contrast: high) {
  :root {
    --bg-primary: #000000;
    --text-primary: #ffffff;
    --accent: #ffff00;
    --border: #ffffff;
  }
}
```

## 性能优化

### 虚拟滚动

对于大型数据集（>1000项），实现虚拟滚动：

```javascript
class VirtualScrollList {
  constructor(container, itemHeight, data) {
    this.container = container;
    this.itemHeight = itemHeight;
    this.data = data;
    this.visibleStart = 0;
    this.visibleEnd = 0;
    this.init();
  }
  
  init() {
    this.container.style.height = `${this.data.length * this.itemHeight}px`;
    this.container.addEventListener('scroll', this.onScroll.bind(this));
    this.render();
  }
  
  onScroll() {
    const scrollTop = this.container.scrollTop;
    this.visibleStart = Math.floor(scrollTop / this.itemHeight);
    this.visibleEnd = Math.min(
      this.visibleStart + Math.ceil(this.container.clientHeight / this.itemHeight),
      this.data.length
    );
    this.render();
  }
  
  render() {
    // 只渲染可见项目
    const visibleItems = this.data.slice(this.visibleStart, this.visibleEnd);
    // 渲染逻辑...
  }
}
```

### 数据缓存

```javascript
class DataCache {
  constructor(ttl = 30000) { // 30秒TTL
    this.cache = new Map();
    this.ttl = ttl;
  }
  
  set(key, data) {
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
  }
  
  get(key) {
    const item = this.cache.get(key);
    if (!item) return null;
    
    if (Date.now() - item.timestamp > this.ttl) {
      this.cache.delete(key);
      return null;
    }
    
    return item.data;
  }
}
```

## 测试策略

### 单元测试

```javascript
// 命令解析器测试
describe('CommandParser', () => {
  test('解析简单命令', () => {
    const parser = new CommandParser();
    const result = parser.parse('devices list');
    expect(result).toEqual({
      verb: 'devices',
      noun: 'list',
      options: {},
      arguments: []
    });
  });
  
  test('解析带选项的命令', () => {
    const parser = new CommandParser();
    const result = parser.parse('devices list --status=online');
    expect(result.options).toEqual({ status: 'online' });
  });
});
```

### 集成测试

```javascript
// API集成测试
describe('API Integration', () => {
  test('设备列表端点', async () => {
    const response = await fetch('/text/devices');
    expect(response.status).toBe(200);
    expect(response.headers.get('content-type')).toBe('text/plain');
    
    const text = await response.text();
    const lines = text.trim().split('\n');
    expect(lines.length).toBeGreaterThan(0);
  });
});
```

### 端到端测试

```javascript
// Playwright E2E测试
test('完整工作流程', async ({ page }) => {
  await page.goto('/cli');
  
  // 等待终端加载
  await page.waitForSelector('.xterm-screen');
  
  // 输入命令
  await page.keyboard.type('devices list');
  await page.keyboard.press('Enter');
  
  // 验证输出
  await expect(page.locator('.xterm-screen')).toContainText('android-001');
});
```

## 安全考虑

### 输入验证

```javascript
class CommandValidator {
  static validate(command) {
    // 防止命令注入
    const dangerous = /[;&|`$(){}[\]]/;
    if (dangerous.test(command)) {
      throw new Error('不安全的命令字符');
    }
    
    // 限制命令长度
    if (command.length > 1000) {
      throw new Error('命令过长');
    }
    
    return true;
  }
}
```

### CSRF保护

```javascript
// CSRF令牌验证
app.use((req, res, next) => {
  if (req.method === 'POST') {
    const token = req.headers['x-csrf-token'];
    if (!validateCSRFToken(token)) {
      return res.status(403).json({ error: 'CSRF令牌无效' });
    }
  }
  next();
});
```

### 速率限制

```javascript
const rateLimit = require('express-rate-limit');

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15分钟
  max: 100, // 限制每个IP 100次请求
  message: '请求过于频繁，请稍后再试'
});

app.use('/api/', limiter);
```

## 部署注意事项

### 静态资源

```nginx
# Nginx配置示例
location /static/ {
  expires 1y;
  add_header Cache-Control "public, immutable";
  gzip_static on;
}

location /cli/ {
  try_files $uri $uri/ /cli/index.html;
}
```

### CDN集成

```html
<!-- 使用CDN加速静态资源 -->
<script src="https://cdn.jsdelivr.net/npm/xterm@5.0.0/lib/xterm.min.js"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/xterm@5.0.0/css/xterm.css">
```

### 监控集成

```javascript
// 性能监控
const observer = new PerformanceObserver((list) => {
  list.getEntries().forEach((entry) => {
    if (entry.entryType === 'navigation') {
      console.log('页面加载时间:', entry.loadEventEnd - entry.loadEventStart);
    }
  });
});

observer.observe({ entryTypes: ['navigation', 'resource'] });
```

这个设计文档为Retire-Cluster的Web界面提供了全面的指导，确保既满足人类用户的需求，又对AI和自动化系统友好。通过CLI优先的方法，我们创建了一个真正通用的管理界面。