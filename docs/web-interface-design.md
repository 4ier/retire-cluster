# Web Interface Design Document

## Overview

Retire-Cluster adopts a CLI-first web interface design that prioritizes machine readability and AI accessibility while maintaining excellent human usability through terminal-style aesthetics.

## Design Philosophy

### Core Principles

1. **Text-First**: All information must be accessible as plain text
2. **Command-Driven**: Every action can be performed via command
3. **Machine-Readable**: Output formats optimized for parsing
4. **Progressive Enhancement**: Works in any text browser, enhanced in modern browsers
5. **Keyboard-Centric**: Full keyboard navigation support

### Target Users

- **Primary**: System administrators, DevOps engineers
- **Secondary**: AI agents, automation scripts
- **Tertiary**: Monitoring systems, CLI browsers

## Architecture

### Three-Layer Access Model

```
┌─────────────────────────────────────┐
│         Presentation Layer           │
├─────────────┬───────────────────────┤
│  Web Terminal│    CLI/Text Access    │
│   (xterm.js) │  (w3m, lynx, curl)   │
├─────────────┼───────────────────────┤
│  /web/*     │    /cli/*              │
│  (Rich TUI)  │    (Plain Text)       │
├─────────────┴───────────────────────┤
│         API Layer                    │
│    /api/v1/* (JSON)                 │
│    /text/*   (Plain Text)           │
│    /stream/* (SSE/WebSocket)        │
└─────────────────────────────────────┘
```

### Endpoint Structure

| Path Pattern | Content Type | Purpose | Example |
|--------------|--------------|---------|---------|
| `/api/v1/*` | `application/json` | Programmatic access | `/api/v1/devices` |
| `/text/*` | `text/plain` | CLI/AI access | `/text/devices` |
| `/cli/*` | `text/html` | Terminal UI | `/cli/dashboard` |
| `/stream/*` | `text/event-stream` | Real-time updates | `/stream/logs` |

## Command System

### Command Syntax

```
<verb> <noun> [options] [arguments]
```

Examples:
- `list devices --status=online`
- `show device android-001`
- `submit task --type=echo --payload="test"`
- `monitor logs --device=laptop-002`

### Core Commands

```bash
# Help & Navigation
help [command]           # Show help for command
clear                   # Clear screen
exit                    # Exit interface

# Cluster Management
cluster status          # Show cluster status
cluster health          # Health check
cluster metrics         # Performance metrics
cluster config          # Configuration

# Device Operations
devices list [--status=] [--role=]     # List devices
devices show <id>                       # Show device details
devices ping <id>                       # Ping device
devices remove <id>                     # Remove device
devices monitor                         # Real-time monitoring

# Task Management
tasks submit <type> [--payload=]        # Submit task
tasks list [--status=] [--device=]     # List tasks
tasks show <id>                         # Show task details
tasks cancel <id>                       # Cancel task
tasks retry <id>                        # Retry task
tasks monitor                           # Monitor tasks

# Monitoring
monitor devices         # Device status stream
monitor tasks          # Task execution stream
monitor logs           # Log stream
monitor metrics        # Metrics stream

# Data Export
export devices [--format=csv|json|tsv]
export tasks [--format=csv|json|tsv]
export logs [--from=] [--to=]
```

## User Interface Design

### Terminal Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ RETIRE-CLUSTER v1.1.0 | 192.168.0.116 | Connected              │
├─────────────────────────────────────────────────────────────────┤
│ [F1]Help [F2]Devices [F3]Tasks [F4]Logs [F5]Metrics    00:42:15│
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ cluster@main:~$ devices list --status=online                   │
│                                                                 │
│ ID           STATUS   CPU    MEM     TASKS  UPTIME            │
│ ─────────────────────────────────────────────────────────────  │
│ android-001  ONLINE   42%    2.1GB   3      2d 14h 32m        │
│ laptop-002   ONLINE   15%    4.5GB   1      5d 08h 15m        │
│ tablet-004   ONLINE   68%    1.8GB   5      1d 02h 45m        │
│                                                                 │
│ Total: 3 devices online, 4 offline                             │
│                                                                 │
│ cluster@main:~$ _                                              │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ [Tab]Complete [↑↓]History [Ctrl+C]Cancel [Ctrl+L]Clear        │
└─────────────────────────────────────────────────────────────────┘
```

### Color Scheme

```css
/* Default Theme: Classic Terminal */
--bg-primary: #0c0c0c;
--bg-secondary: #1a1a1a;
--text-primary: #00ff00;
--text-secondary: #00cc00;
--text-dim: #008800;
--prompt: #00ffff;
--error: #ff0000;
--warning: #ffff00;
--success: #00ff00;
--info: #0088ff;

/* Alternative Themes */
- Matrix (black/green)
- Amber (black/amber)
- Solarized Dark
- Dracula
- High Contrast
```

### ASCII Visualizations

#### Resource Usage Bar
```
CPU  [████████████░░░░░░░░] 62%
MEM  [██████████░░░░░░░░░░] 48%
DISK [███░░░░░░░░░░░░░░░░░] 15%
NET  [█████████████████░░░] 85%
```

#### Time Series Chart
```
CPU Usage (last 30 min)
100│
 80│    ╭─╮
 60│   ╱  ╰─╮    ╭───╮
 40│  ╱     ╰────╯   ╰───
 20│ ╱
  0└──────────────────────
   0    10    20    30
```

#### Device Status Grid
```
┌─────┬─────┬─────┬─────┐
│ ✓01 │ ✓02 │ ✗03 │ ✓04 │
├─────┼─────┼─────┼─────┤
│ ✓05 │ ⚠06 │ ✓07 │ ✗08 │
└─────┴─────┴─────┴─────┘

Legend: ✓ Online  ✗ Offline  ⚠ Warning
```

## API Design

### Content Negotiation

```python
@app.route('/devices')
def devices():
    accept = request.headers.get('Accept', 'text/html')
    
    if 'application/json' in accept:
        return jsonify(devices_data)
    elif 'text/plain' in accept:
        return plain_text_response(devices_data)
    elif 'text/csv' in accept:
        return csv_response(devices_data)
    else:
        return render_template('cli_devices.html', devices=devices_data)
```

### Response Formats

#### JSON Format
```json
{
  "status": "success",
  "data": {
    "devices": [
      {
        "id": "android-001",
        "status": "online",
        "cpu_usage": 42,
        "memory_gb": 2.1
      }
    ]
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Plain Text Format
```
android-001|online|42|2.1|3
laptop-002|online|15|4.5|1
raspi-003|offline|0|0|0
```

#### CSV Format
```csv
id,status,cpu,memory,tasks
android-001,online,42,2.1,3
laptop-002,online,15,4.5,1
raspi-003,offline,0,0,0
```

## AI Integration

### Machine-Readable Features

1. **Structured Output**: Consistent delimiter-separated values
2. **Standard Exit Codes**: 0 for success, non-zero for errors
3. **Predictable Paths**: RESTful resource naming
4. **Semantic HTML**: Proper use of `<pre>`, `<code>`, `<output>`
5. **ARIA Labels**: Screen reader and parser friendly

### AI Access Patterns

#### Direct Command Execution
```bash
curl -X POST http://cluster.local/api/v1/command \
  -d '{"command": "devices list --status=online"}' \
  -H "Accept: text/plain"
```

#### Streaming Updates
```bash
curl -N http://cluster.local/stream/devices \
  | while read -r line; do
      echo "Device update: $line"
    done
```

#### Batch Operations
```bash
# Submit multiple tasks
cat tasks.txt | while read task; do
  curl -X POST http://cluster.local/api/v1/tasks -d "$task"
done
```

## Accessibility

### Keyboard Navigation

| Key | Action |
|-----|--------|
| `Tab` | Auto-complete command |
| `↑/↓` | Navigate command history |
| `Ctrl+C` | Cancel current command |
| `Ctrl+L` | Clear screen |
| `Ctrl+R` | Reverse search history |
| `F1-F10` | Quick navigation |
| `Alt+[1-9]` | Switch to tab N |
| `/` | Start search |
| `n/N` | Next/Previous search result |

### Screen Reader Support

- Semantic HTML5 elements
- ARIA labels and descriptions
- Skip navigation links
- Keyboard-only navigation
- High contrast mode

## Performance Optimization

### Strategies

1. **Virtual Scrolling**: For large log outputs
2. **Incremental Rendering**: Update only changed portions
3. **Web Workers**: Command parsing and processing
4. **Lazy Loading**: Load historical data on demand
5. **Response Caching**: Cache frequently accessed data
6. **Compression**: gzip for text responses

### Target Metrics

- Initial load: < 1 second
- Command response: < 100ms
- Real-time update latency: < 50ms
- Memory usage: < 50MB for 10k log lines

## Testing Strategy

### CLI Browser Compatibility

Test with:
- `w3m`
- `lynx`
- `links`
- `elinks`
- `curl`
- `wget`
- `httpie`

### Automated Testing

```bash
# Test CLI access
curl -s http://localhost:8081/text/devices | grep -q "online"

# Test command execution
echo "devices list" | nc localhost 8081

# Test streaming
timeout 5 curl -N http://localhost:8081/stream/logs
```

## Implementation Phases

### Phase 1: Core CLI Interface (MVP)
- Basic command parser
- Text-only endpoints
- Device listing and status

### Phase 2: Enhanced Terminal UI
- xterm.js integration
- ASCII visualizations
- Command history and autocomplete

### Phase 3: Real-time Features
- WebSocket/SSE streaming
- Live monitoring dashboards
- Push notifications

### Phase 4: Advanced Features
- Custom commands/plugins
- Batch operations
- Scripting support

## Security Considerations

1. **Input Sanitization**: Escape all user input
2. **Command Injection**: Whitelist allowed commands
3. **Rate Limiting**: Prevent abuse
4. **Authentication**: Optional API key support
5. **Audit Logging**: Log all commands
6. **CORS**: Configurable origins

## Appendix

### Example Sessions

#### Human User Session
```bash
$ telnet cluster.local 8081
RETIRE-CLUSTER v1.1.0
cluster@main:~$ devices list
3 devices online, 4 offline
cluster@main:~$ monitor logs --device=android-001
[2024-01-15 10:30:15] Task started: echo_test
[2024-01-15 10:30:16] Task completed successfully
^C
cluster@main:~$ exit
```

#### AI/Bot Session
```bash
$ curl -s http://cluster.local/text/devices \
  | awk -F'|' '$2=="online" {print $1}' \
  | xargs -I{} curl -X POST \
    http://cluster.local/api/v1/tasks \
    -d '{"device_id": "{}", "type": "health_check"}'
```

### References

- [ANSI Escape Codes](https://en.wikipedia.org/wiki/ANSI_escape_code)
- [ASCII Art Libraries](https://github.com/topics/ascii-art)
- [Terminal UI Best Practices](https://github.com/rothgar/awesome-tuis)
- [CLI Design Guidelines](https://clig.dev/)