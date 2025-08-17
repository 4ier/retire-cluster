# CLI界面规范

## 1. 命令行界面协议

### 1.1 命令结构

```ebnf
command     ::= verb noun [options] [arguments]
verb        ::= "list" | "show" | "create" | "update" | "delete" | 
                "start" | "stop" | "monitor" | "export" | "help"
noun        ::= "cluster" | "device" | "devices" | "task" | "tasks" | 
                "log" | "logs" | "metric" | "metrics" | "config"
options     ::= "--" option-name ["=" option-value]
arguments   ::= string | number | json
```

### 1.2 标准选项

所有命令都支持这些标准选项：

| 选项 | 简写 | 描述 | 默认值 |
|------|------|------|--------|
| `--format` | `-f` | 输出格式 (json\|text\|csv\|tsv\|table) | table |
| `--output` | `-o` | 输出文件路径 | stdout |
| `--quiet` | `-q` | 抑制非错误输出 | false |
| `--verbose` | `-v` | 详细输出 | false |
| `--help` | `-h` | 显示命令帮助 | - |
| `--no-color` | - | 禁用彩色输出 | false |
| `--api-key` | `-k` | API认证密钥 | - |

## 2. 命令参考

### 2.1 集群命令

#### cluster status
```bash
cluster status [--format=json|text|table]

# 示例
cluster status                    # 表格格式（默认）
cluster status --format=json      # JSON输出
cluster status -f text            # 纯文本
```

**输出（文本格式）：**
```
状态: healthy
节点: 5/7 在线
CPU: 48核心 (37% 使用率)
内存: 128GB (42% 已用)
任务: 12个活动，今天完成45个
运行时间: 15天 6小时 42分钟
```

#### cluster health
```bash
cluster health [--check=all|api|database|network]

# 示例
cluster health                    # 所有检查
cluster health --check=network    # 仅网络检查
```

#### cluster metrics
```bash
cluster metrics [--period=1h|24h|7d|30d] [--type=cpu|memory|network|disk]

# 示例
cluster metrics --period=24h --type=cpu
cluster metrics -p 1h              # 最近一小时，所有指标
```

### 2.2 设备命令

#### devices list
```bash
devices list [--status=online|offline|all] 
             [--role=worker|storage|compute]
             [--sort=name|cpu|memory|tasks]
             [--limit=N]

# 示例
devices list --status=online
devices list --role=worker --sort=cpu
devices list --limit=10 --format=csv
```

**输出（表格格式）：**
```
设备ID       状态    角色     CPU   内存    任务  运行时间
─────────────────────────────────────────────────────────
android-001  在线   worker   42%   2.1GB   3     2天 14小时
laptop-002   在线   compute  15%   4.5GB   1     5天 08小时
raspi-003    离线   storage  -     -       0     -
tablet-004   在线   worker   68%   1.8GB   5     1天 02小时
```

#### devices show
```bash
devices show <device-id> [--format=json|yaml|text]

# 示例
devices show android-001
devices show laptop-002 --format=json
```

#### devices ping
```bash
devices ping <device-id> [--count=N] [--timeout=seconds]

# 示例
devices ping android-001
devices ping all --timeout=5
```

#### devices remove
```bash
devices remove <device-id> [--force]

# 示例
devices remove android-001
devices remove offline --force    # 删除所有离线设备
```

### 2.3 任务命令

#### tasks submit
```bash
tasks submit <task-type> [--payload=json] 
                         [--device=id]
                         [--priority=low|normal|high|urgent]
                         [--requirements=json]

# 示例
tasks submit echo --payload='{"message":"test"}'
tasks submit compute --payload=@task.json --priority=high
tasks submit system_info --device=android-001
```

#### tasks list
```bash
tasks list [--status=pending|running|completed|failed|all]
           [--device=id]
           [--type=task-type]
           [--since=timestamp]
           [--limit=N]

# 示例
tasks list --status=running
tasks list --device=laptop-002 --since="2024-01-15"
tasks list --type=echo --limit=20
```

**输出（表格格式）：**
```
任务ID        状态     设备          类型         优先级  创建时间
─────────────────────────────────────────────────────────────────
task-abc123   运行中   android-001   python_eval  normal  10:30:15
task-def456   排队     -             echo         high    10:30:16
task-ghi789   完成     laptop-002    system_info  normal  10:30:17
task-jkl012   失败     raspi-003     backup       low     10:30:18
```

#### tasks show
```bash
tasks show <task-id> [--format=json|yaml|text]

# 示例
tasks show task-abc123
tasks show task-def456 --format=json
```

#### tasks cancel
```bash
tasks cancel <task-id> [--force]

# 示例
tasks cancel task-abc123
tasks cancel running --force      # 取消所有运行中的任务
```

#### tasks retry
```bash
tasks retry <task-id> [--priority=low|normal|high|urgent]

# 示例
tasks retry task-abc123
tasks retry failed --priority=high  # 重试所有失败的任务
```

### 2.4 监控命令

#### monitor devices
```bash
monitor devices [--device=id] [--interval=seconds] [--output=file]

# 示例
monitor devices                   # 监控所有设备
monitor devices --device=android-001
monitor devices --interval=5 --output=devices.log
```

**输出：**
```
[10:30:15] android-001: CPU 42% | 内存 2.1GB/8GB | 任务 3
[10:30:15] laptop-002:  CPU 15% | 内存 4.5GB/16GB | 任务 1
[10:30:16] android-001: CPU 45% | 内存 2.2GB/8GB | 任务 3
[10:30:16] laptop-002:  CPU 18% | 内存 4.6GB/16GB | 任务 2
```

#### monitor tasks
```bash
monitor tasks [--status=all|running|pending] [--device=id]

# 示例
monitor tasks --status=running
monitor tasks --device=android-001
```

#### monitor logs
```bash
monitor logs [--level=debug|info|warning|error] 
             [--device=id] 
             [--follow]
             [--tail=N]

# 示例
monitor logs --level=error --follow
monitor logs --device=android-001 --tail=100
```

**输出：**
```
[2024-01-15 10:30:15] INFO  主节点启动成功 (端口: 8080)
[2024-01-15 10:30:16] DEBUG 等待设备连接...
[2024-01-15 10:30:17] INFO  设备注册: android-001 (8核, 8GB内存)
[2024-01-15 10:30:18] WARN  设备 raspi-003 心跳延迟 (延迟: 120s)
[2024-01-15 10:30:19] ERROR 任务执行失败: task-abc123 (原因: 超时)
```

### 2.5 导出命令

#### export devices
```bash
export devices [--format=csv|json|xml] 
               [--fields=field1,field2,...]
               [--output=file]

# 示例
export devices --format=csv --output=devices.csv
export devices --fields=id,status,cpu,memory --format=json
```

#### export tasks
```bash
export tasks [--since=timestamp] 
             [--status=all|completed|failed]
             [--format=csv|json]

# 示例
export tasks --since="2024-01-01" --format=csv
export tasks --status=completed --output=completed_tasks.json
```

#### export logs
```bash
export logs [--since=timestamp] 
            [--until=timestamp]
            [--level=debug|info|warning|error]
            [--format=text|json]

# 示例
export logs --since="2024-01-15" --level=error
export logs --since="-1h" --format=json  # 最近1小时
```

#### export config
```bash
export config [--format=json|yaml] [--include-secrets]

# 示例
export config --format=yaml
export config --include-secrets --output=config_backup.json
```

### 2.6 配置命令

#### config show
```bash
config show [--section=server|database|logging|cluster]

# 示例
config show
config show --section=server
```

#### config set
```bash
config set <key> <value> [--section=section]

# 示例
config set server.port 8081
config set cluster.heartbeat_interval 30 --section=cluster
```

#### config get
```bash
config get <key> [--section=section]

# 示例
config get server.port
config get heartbeat_interval --section=cluster
```

### 2.7 帮助命令

#### help
```bash
help [command]

# 示例
help                    # 显示所有命令
help devices            # 显示设备相关命令
help devices list       # 显示 devices list 命令详细帮助
```

## 3. 输出格式规范

### 3.1 表格格式 (table)

```
标题1      标题2      标题3
─────────────────────────────
值1        值2        值3
值4        值5        值6
```

特点：
- 自动列宽调整
- 标题行分隔符
- 左对齐文本，右对齐数字

### 3.2 CSV格式

```
标题1,标题2,标题3
值1,值2,值3
值4,值5,值6
```

特点：
- 标准RFC 4180格式
- 引号转义特殊字符
- UTF-8编码

### 3.3 TSV格式

```
标题1	标题2	标题3
值1	值2	值3
值4	值5	值6
```

特点：
- Tab分隔
- 无引号转义
- 适合程序处理

### 3.4 JSON格式

```json
{
  "status": "success",
  "data": [
    {"标题1": "值1", "标题2": "值2", "标题3": "值3"},
    {"标题1": "值4", "标题2": "值5", "标题3": "值6"}
  ],
  "meta": {
    "total": 2,
    "timestamp": "2024-01-15T10:30:15Z"
  }
}
```

### 3.5 纯文本格式

```
设备ID: android-001
状态: 在线
CPU使用率: 42%
内存使用: 2.1GB / 8GB
活动任务: 3
运行时间: 2天 14小时 32分钟

设备ID: laptop-002
状态: 在线
CPU使用率: 15%
内存使用: 4.5GB / 16GB
活动任务: 1
运行时间: 5天 8小时 15分钟
```

## 4. 交互模式

### 4.1 进入交互模式

```bash
# 启动交互式shell
cluster-cli

# 或者使用别名
retire-cluster-cli
```

### 4.2 交互式提示符

```bash
cluster@main:~$ devices list
cluster@main:~$ tasks submit echo --payload='{"test": true}'
cluster@worker:android-001$ # 连接到特定设备时
```

### 4.3 自动补全

- Tab键触发命令补全
- 支持命令、选项、参数补全
- 智能上下文感知

```bash
cluster@main:~$ dev<TAB>
devices

cluster@main:~$ devices <TAB>
list    show    ping    remove

cluster@main:~$ devices list --st<TAB>
--status=

cluster@main:~$ devices list --status=<TAB>
online    offline    all
```

### 4.4 命令历史

- 上下箭头浏览历史
- Ctrl+R 反向搜索
- !! 重复上一个命令
- !n 执行历史中第n个命令

```bash
cluster@main:~$ history
1  devices list
2  tasks submit echo --payload='{"test": true}'
3  monitor logs --follow

cluster@main:~$ !2  # 重复执行第2个命令
```

### 4.5 管道和重定向

```bash
# 管道操作
devices list | grep online
tasks list --status=running | wc -l

# 输出重定向
devices list > devices.txt
monitor logs --tail=100 >> system.log

# 错误重定向
tasks submit invalid_task 2> errors.log
```

## 5. 脚本集成

### 5.1 退出代码

| 代码 | 含义 |
|------|------|
| 0 | 成功 |
| 1 | 一般错误 |
| 2 | 命令语法错误 |
| 3 | 连接错误 |
| 4 | 认证错误 |
| 5 | 权限错误 |
| 6 | 资源不存在 |
| 7 | 资源冲突 |

### 5.2 环境变量

```bash
# 设置默认连接
export CLUSTER_HOST=192.168.1.100
export CLUSTER_PORT=8080
export CLUSTER_API_KEY=your-secret-key

# 设置默认格式
export CLUSTER_DEFAULT_FORMAT=json

# 禁用颜色输出
export CLUSTER_NO_COLOR=1
```

### 5.3 配置文件

```yaml
# ~/.cluster/config.yml
default:
  host: 192.168.1.100
  port: 8080
  format: table
  
profiles:
  production:
    host: prod-cluster.company.com
    port: 8080
    api_key: ${PROD_API_KEY}
    
  development:
    host: localhost
    port: 8080
    format: json
```

使用配置文件：
```bash
cluster-cli --profile production devices list
```

### 5.4 批处理脚本示例

```bash
#!/bin/bash
# 集群健康检查脚本

set -e

echo "检查集群状态..."
cluster status --format=text

echo "检查离线设备..."
OFFLINE=$(devices list --status=offline --format=csv | wc -l)
if [ $OFFLINE -gt 1 ]; then  # 减1因为有头行
  echo "警告: 发现 $((OFFLINE-1)) 个离线设备"
  devices list --status=offline
fi

echo "检查失败任务..."
FAILED=$(tasks list --status=failed --since="-24h" --format=csv | wc -l)
if [ $FAILED -gt 1 ]; then
  echo "警告: 过去24小时有 $((FAILED-1)) 个任务失败"
  tasks list --status=failed --since="-24h"
fi

echo "健康检查完成"
```

## 6. 高级功能

### 6.1 监视模式

```bash
# 持续监控设备状态
monitor devices --watch --interval=5

# 监控任务队列
monitor tasks --watch --status=running

# 实时日志跟踪
monitor logs --follow --level=error
```

### 6.2 过滤和查询

```bash
# 使用JQ风格查询（JSON输出）
devices list --format=json --query='.data[] | select(.cpu > 50)'

# 使用SQL风格查询
devices list --sql="SELECT id, cpu FROM devices WHERE cpu > 50"

# 复杂过滤
tasks list --filter="status=running AND device=android-001"
```

### 6.3 批量操作

```bash
# 批量重启设备
devices list --status=online --format=csv | tail -n +2 | cut -d',' -f1 | xargs -I{} devices restart {}

# 批量取消任务
tasks list --status=pending --device=android-001 --format=csv | tail -n +2 | cut -d',' -f1 | xargs -I{} tasks cancel {}
```

### 6.4 模板和变量

```bash
# 使用模板提交任务
tasks submit compute --template=fibonacci --vars='{"n": 100}'

# 从文件读取变量
tasks submit ml_training --template=@training.json --vars=@params.json
```

## 7. 错误处理

### 7.1 错误消息格式

```bash
Error: 设备 'invalid-device' 不存在
建议: 使用 'devices list' 查看可用设备

Error: 任务 'task-123' 已在运行中
提示: 使用 'tasks cancel task-123' 先取消任务

Warning: 设备 'android-001' 响应缓慢 (延迟: 2.5s)
```

### 7.2 调试模式

```bash
# 启用详细调试输出
cluster-cli --debug devices list

# 启用API调用跟踪
cluster-cli --trace tasks submit echo --payload='{"test": true}'
```

### 7.3 恢复建议

命令失败时自动提供恢复建议：

```bash
cluster@main:~$ devices ping offline-device
Error: 设备 'offline-device' 不可达

建议的操作:
1. 检查设备是否在线: devices list --status=offline
2. 重新启动设备服务
3. 检查网络连接: ping <device-ip>
4. 查看设备日志: monitor logs --device=offline-device
```

这个CLI规范为Retire-Cluster提供了完整的命令行界面定义，确保一致性、可用性和强大的脚本集成能力。