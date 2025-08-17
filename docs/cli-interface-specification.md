# CLI Interface Specification

## 1. Command Line Interface Protocol

### 1.1 Command Structure

```ebnf
command     ::= verb noun [options] [arguments]
verb        ::= "list" | "show" | "create" | "update" | "delete" | 
                "start" | "stop" | "monitor" | "export" | "help"
noun        ::= "cluster" | "device" | "devices" | "task" | "tasks" | 
                "log" | "logs" | "metric" | "metrics" | "config"
options     ::= "--" option-name ["=" option-value]
arguments   ::= string | number | json
```

### 1.2 Standard Options

All commands support these standard options:

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--format` | `-f` | Output format (json\|text\|csv\|tsv\|table) | table |
| `--output` | `-o` | Output file path | stdout |
| `--quiet` | `-q` | Suppress non-error output | false |
| `--verbose` | `-v` | Verbose output | false |
| `--help` | `-h` | Show command help | - |
| `--no-color` | - | Disable colored output | false |
| `--api-key` | `-k` | API authentication key | - |

## 2. Command Reference

### 2.1 Cluster Commands

#### cluster status
```bash
cluster status [--format=json|text|table]

# Examples
cluster status                    # Table format (default)
cluster status --format=json      # JSON output
cluster status -f text            # Plain text
```

**Output (text format):**
```
STATUS: healthy
NODES: 5/7 online
CPU: 48 cores (37% utilized)
MEMORY: 128GB (42% used)
TASKS: 12 active, 45 completed today
UPTIME: 15d 6h 42m
```

#### cluster health
```bash
cluster health [--check=all|api|database|network]

# Examples
cluster health                    # All checks
cluster health --check=network    # Network only
```

#### cluster metrics
```bash
cluster metrics [--period=1h|24h|7d|30d] [--type=cpu|memory|network|disk]

# Examples
cluster metrics --period=24h --type=cpu
cluster metrics -p 1h              # Last hour, all metrics
```

### 2.2 Device Commands

#### devices list
```bash
devices list [--status=online|offline|all] 
             [--role=worker|storage|compute]
             [--sort=name|cpu|memory|tasks]
             [--limit=N]

# Examples
devices list --status=online
devices list --role=worker --sort=cpu
devices list --limit=10 --format=csv
```

**Output (table format):**
```
ID           STATUS   ROLE     CPU   MEM    TASKS  UPTIME
─────────────────────────────────────────────────────────
android-001  online   worker   42%   2.1GB  3      2d 14h
laptop-002   online   compute  15%   4.5GB  1      5d 08h
raspi-003    offline  storage  -     -      0      -
tablet-004   online   worker   68%   1.8GB  5      1d 02h
```

#### devices show
```bash
devices show <device-id> [--format=json|yaml|text]

# Examples
devices show android-001
devices show laptop-002 --format=json
```

#### devices ping
```bash
devices ping <device-id> [--count=N] [--timeout=seconds]

# Examples
devices ping android-001
devices ping all --timeout=5
```

#### devices remove
```bash
devices remove <device-id> [--force]

# Examples
devices remove android-001
devices remove offline --force    # Remove all offline devices
```

### 2.3 Task Commands

#### tasks submit
```bash
tasks submit <task-type> [--payload=json] 
                         [--device=id]
                         [--priority=low|normal|high|urgent]
                         [--requirements=json]

# Examples
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

# Examples
tasks list --status=running
tasks list --device=laptop-002 --since="2024-01-15"
tasks list --type=compute --limit=20
```

#### tasks show
```bash
tasks show <task-id> [--format=json|yaml|text]

# Examples
tasks show task-abc123
tasks show task-abc123 --format=json
```

#### tasks cancel
```bash
tasks cancel <task-id> [--force]

# Examples
tasks cancel task-abc123
tasks cancel all --status=pending    # Cancel all pending
```

#### tasks retry
```bash
tasks retry <task-id> [--max-attempts=N]

# Examples
tasks retry task-abc123
tasks retry failed --max-attempts=3  # Retry all failed
```

### 2.4 Monitoring Commands

#### monitor devices
```bash
monitor devices [--interval=seconds] [--filter=expression]

# Examples
monitor devices --interval=5
monitor devices --filter="cpu>50"
```

**Output (streaming):**
```
[2024-01-15 10:30:15] android-001: CPU 45% → 52% ↑
[2024-01-15 10:30:16] laptop-002: TASK COMPLETED (task-xyz)
[2024-01-15 10:30:18] tablet-004: STATUS online → offline
```

#### monitor tasks
```bash
monitor tasks [--device=id] [--follow]

# Examples
monitor tasks --follow
monitor tasks --device=android-001
```

#### monitor logs
```bash
monitor logs [--device=id] 
             [--level=debug|info|warning|error]
             [--grep=pattern]
             [--tail=N]

# Examples
monitor logs --level=error
monitor logs --device=laptop-002 --grep="ERROR"
monitor logs --tail=100 --follow
```

### 2.5 Data Export Commands

#### export devices
```bash
export devices [--format=csv|json|tsv|xlsx] 
               [--output=file]
               [--columns=col1,col2,...]

# Examples
export devices --format=csv --output=devices.csv
export devices --columns=id,status,cpu,memory
```

#### export tasks
```bash
export tasks [--format=csv|json|tsv] 
             [--from=date] 
             [--to=date]
             [--status=completed|failed|all]

# Examples
export tasks --from="2024-01-01" --to="2024-01-31"
export tasks --status=completed --format=json
```

#### export logs
```bash
export logs [--from=timestamp] 
            [--to=timestamp]
            [--device=id]
            [--format=text|json]
            [--compress]

# Examples
export logs --from="2024-01-15 00:00" --compress
export logs --device=android-001 --format=json
```

## 3. Interactive Mode

### 3.1 Starting Interactive Mode

```bash
# Direct connection
retire-cluster

# With specific server
retire-cluster --server=192.168.0.116:8081

# With authentication
retire-cluster --api-key=your-key-here
```

### 3.2 Interactive Commands

In interactive mode, additional commands are available:

| Command | Shortcut | Description |
|---------|----------|-------------|
| `help` | `?` | Show help |
| `clear` | `Ctrl+L` | Clear screen |
| `history` | `!` | Show command history |
| `alias` | - | Create command alias |
| `set` | - | Set configuration |
| `exit` | `Ctrl+D` | Exit interactive mode |

### 3.3 Auto-completion

Tab completion is available for:
- Command names
- Device IDs
- Task IDs
- Option names
- File paths

### 3.4 Command History

- `↑/↓`: Navigate through history
- `Ctrl+R`: Reverse search
- `!!`: Repeat last command
- `!n`: Execute command number n
- `!prefix`: Execute last command starting with prefix

## 4. Output Formats

### 4.1 Table Format (Default)

```
┌────────────┬─────────┬───────┬────────┐
│ DEVICE ID  │ STATUS  │ CPU % │ MEMORY │
├────────────┼─────────┼───────┼────────┤
│ android-01 │ online  │ 42    │ 2.1GB  │
│ laptop-02  │ online  │ 15    │ 4.5GB  │
│ raspi-03   │ offline │ -     │ -      │
└────────────┴─────────┴───────┴────────┘
```

### 4.2 Plain Text Format

```
android-001|online|42|2.1
laptop-002|online|15|4.5
raspi-003|offline|0|0
```

### 4.3 JSON Format

```json
{
  "devices": [
    {
      "id": "android-001",
      "status": "online",
      "cpu_percent": 42,
      "memory_gb": 2.1
    }
  ],
  "timestamp": "2024-01-15T10:30:00Z",
  "count": 3
}
```

### 4.4 CSV Format

```csv
id,status,cpu_percent,memory_gb
android-001,online,42,2.1
laptop-002,online,15,4.5
raspi-003,offline,0,0
```

### 4.5 TSV Format

```tsv
id	status	cpu_percent	memory_gb
android-001	online	42	2.1
laptop-002	online	15	4.5
raspi-003	offline	0	0
```

## 5. Error Handling

### 5.1 Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Command line syntax error |
| 3 | Configuration error |
| 4 | Network/Connection error |
| 5 | Authentication error |
| 6 | Resource not found |
| 7 | Operation not permitted |
| 8 | Timeout |

### 5.2 Error Output Format

```
ERROR: <error-message>
  Code: <error-code>
  Details: <additional-details>
  Suggestion: <how-to-fix>

# Example
ERROR: Device not found
  Code: 404
  Details: No device with ID 'android-999'
  Suggestion: Use 'devices list' to see available devices
```

## 6. Scripting Support

### 6.1 Batch Mode

```bash
# Execute commands from file
retire-cluster --batch commands.txt

# Pipe commands
echo "devices list" | retire-cluster

# Command chaining
retire-cluster -c "devices list" -c "tasks list"
```

### 6.2 Script Examples

```bash
#!/bin/bash
# Monitor and alert on high CPU usage

while true; do
  retire-cluster devices list --format=json | \
  jq '.devices[] | select(.cpu_percent > 80)' | \
  while read device; do
    echo "Alert: High CPU on $(echo $device | jq -r .id)"
    # Send notification
  done
  sleep 60
done
```

### 6.3 Environment Variables

| Variable | Description |
|----------|-------------|
| `RETIRE_CLUSTER_SERVER` | Default server address |
| `RETIRE_CLUSTER_API_KEY` | Default API key |
| `RETIRE_CLUSTER_FORMAT` | Default output format |
| `RETIRE_CLUSTER_NO_COLOR` | Disable colored output |
| `RETIRE_CLUSTER_TIMEOUT` | Command timeout (seconds) |

## 7. Advanced Features

### 7.1 Filtering and Queries

```bash
# JQ-style filtering
devices list --filter='.cpu_percent > 50'

# SQL-like queries
tasks query "SELECT * FROM tasks WHERE status='running'"

# Regular expressions
logs search --regex='ERROR.*timeout'
```

### 7.2 Aggregations

```bash
# Device statistics
devices stats --group-by=role

# Task metrics
tasks metrics --aggregate=sum --period=1h
```

### 7.3 Webhooks and Notifications

```bash
# Set up webhook
monitor events --webhook=https://example.com/hook

# Email notifications
monitor alerts --email=admin@example.com --threshold="cpu>90"
```

## 8. CLI Browser Compatibility

### 8.1 w3m Access

```bash
# View dashboard
w3m http://cluster.local/cli/dashboard

# Direct command execution
w3m -dump "http://cluster.local/cli/exec?cmd=devices+list"
```

### 8.2 curl Examples

```bash
# Get device list
curl -s http://cluster.local/text/devices

# Submit task
curl -X POST http://cluster.local/api/v1/command \
  -d '{"command": "tasks submit echo --payload={\"msg\":\"test\"}"}'

# Stream logs
curl -N http://cluster.local/stream/logs
```

### 8.3 lynx Support

```bash
# Interactive session
lynx http://cluster.local/cli

# Dump mode
lynx -dump http://cluster.local/text/status
```

## 9. Performance Guidelines

### 9.1 Response Time Targets

| Operation | Target | Maximum |
|-----------|--------|---------|
| Command execution | <100ms | 500ms |
| List operations | <200ms | 1s |
| Search operations | <500ms | 2s |
| Export operations | <1s/MB | 5s/MB |

### 9.2 Resource Limits

- Maximum output size: 10MB (configurable)
- Maximum concurrent connections: 100
- Command history: 1000 entries
- Rate limiting: 100 requests/minute

## 10. Security

### 10.1 Authentication

```bash
# API key authentication
retire-cluster --api-key=your-key-here

# Interactive authentication
retire-cluster --auth
Username: admin
Password: ****
```

### 10.2 Authorization Levels

| Level | Permissions |
|-------|------------|
| read | View cluster status, list devices/tasks |
| write | Submit tasks, modify device settings |
| admin | Remove devices, cancel tasks, change config |

### 10.3 Audit Logging

All commands are logged with:
- Timestamp
- User/API key
- Command executed
- Result (success/failure)
- Response time