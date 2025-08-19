"""
Flask web application for Retire-Cluster CLI interface
"""

import json
import time
from datetime import datetime
from flask import Flask, request, jsonify, Response, render_template_string
from flask_cors import CORS
from typing import Optional, Dict, Any

from .cli_parser import CommandParser
from .cli_executor import CommandExecutor


def create_app(cluster_server=None, testing=False):
    """
    Create and configure Flask application
    
    Args:
        cluster_server: Cluster server instance
        testing: Enable testing mode
        
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    app.config['TESTING'] = testing
    
    # Enable CORS
    CORS(app, origins=['*'])
    
    # Initialize CLI components
    parser = CommandParser()
    executor = CommandExecutor(cluster_server) if cluster_server else None
    
    # Mock cluster server for testing if needed
    if not cluster_server:
        from unittest.mock import Mock
        cluster_server = Mock()
        cluster_server.get_devices.return_value = []
        cluster_server.get_cluster_status.return_value = {
            "status": "healthy",
            "nodes_online": 0,
            "nodes_total": 0,
            "cpu_cores": 0,
            "cpu_usage": 0,
            "memory_total": 0,
            "memory_usage": 0,
            "tasks_active": 0,
            "tasks_completed": 0,
            "uptime": "0h 0m"
        }
        cluster_server.get_logs.return_value = []
        executor = CommandExecutor(cluster_server)
    
    # Root route - redirect to CLI interface
    @app.route('/', methods=['GET'])
    def index():
        """Redirect root to CLI interface"""
        from flask import redirect
        return redirect('/cli')
    
    # Text API Endpoints
    
    @app.route('/text/devices', methods=['GET'])
    def text_devices():
        """Return devices in plain text format"""
        try:
            accept_header = request.headers.get('Accept', 'text/plain')
            status_filter = request.args.get('status')
            
            devices = cluster_server.get_devices()
            
            # Apply filter
            if status_filter:
                devices = [d for d in devices if d.get('status') == status_filter]
            
            # Format based on Accept header
            if 'text/csv' in accept_header:
                # CSV format
                lines = ['id,status,cpu,memory,tasks']
                for device in devices:
                    lines.append(f"{device.get('id', '')},{device.get('status', '')},{device.get('cpu', 0)},{device.get('memory', 0)},{device.get('tasks', 0)}")
                response_text = '\n'.join(lines)
                content_type = 'text/csv'
            
            elif 'text/tab-separated-values' in accept_header:
                # TSV format
                lines = ['id\tstatus\tcpu\tmemory\ttasks']
                for device in devices:
                    lines.append(f"{device.get('id', '')}\t{device.get('status', '')}\t{device.get('cpu', 0)}\t{device.get('memory', 0)}\t{device.get('tasks', 0)}")
                response_text = '\n'.join(lines)
                content_type = 'text/tab-separated-values'
            
            else:
                # Default pipe-delimited format
                lines = []
                for device in devices:
                    lines.append(f"{device.get('id', '')}|{device.get('status', '')}|{device.get('cpu', 0)}|{device.get('memory', 0)}|{device.get('tasks', 0)}")
                response_text = '\n'.join(lines)
                content_type = 'text/plain'
            
            return Response(response_text, mimetype=content_type, headers={'Content-Type': f'{content_type}; charset=utf-8'})
            
        except Exception as e:
            # Return error response 
            return Response(f"Error: {str(e)}", status=500, mimetype='text/plain')
    
    @app.route('/text/status', methods=['GET'])
    def text_status():
        """Return cluster status in plain text format"""
        status = cluster_server.get_cluster_status()
        
        lines = [
            f"STATUS: {status.get('status', 'unknown')}",
            f"NODES: {status.get('nodes_online', 0)}/{status.get('nodes_total', 0)} online",
            f"CPU: {status.get('cpu_cores', 0)} cores ({status.get('cpu_usage', 0)}% utilized)",
            f"MEMORY: {status.get('memory_total', 0)}GB ({status.get('memory_usage', 0)}% used)",
            f"TASKS: {status.get('tasks_active', 0)} active, {status.get('tasks_completed', 0)} completed today",
            f"UPTIME: {status.get('uptime', 'N/A')}"
        ]
        
        return Response('\n'.join(lines), mimetype='text/plain', headers={'Content-Type': 'text/plain; charset=utf-8'})
    
    @app.route('/text/metrics', methods=['GET'])
    def text_metrics():
        """Return metrics in Prometheus format"""
        status = cluster_server.get_cluster_status()
        devices = cluster_server.get_devices()
        
        online_devices = len([d for d in devices if d.get('status') == 'online'])
        
        lines = [
            "# HELP cluster_devices_total Total number of devices in cluster",
            "# TYPE cluster_devices_total gauge",
            f"cluster_devices_total {len(devices)}",
            "",
            "# HELP cluster_devices_online Number of online devices",
            "# TYPE cluster_devices_online gauge",
            f"cluster_devices_online {online_devices}",
            "",
            "# HELP cluster_cpu_usage_percent CPU usage percentage",
            "# TYPE cluster_cpu_usage_percent gauge",
            f"cluster_cpu_usage_percent {status.get('cpu_usage', 0)}",
            "",
            "# HELP cluster_memory_usage_percent Memory usage percentage",
            "# TYPE cluster_memory_usage_percent gauge",
            f"cluster_memory_usage_percent {status.get('memory_usage', 0)}",
            "",
            "# HELP cluster_tasks_active Number of active tasks",
            "# TYPE cluster_tasks_active gauge",
            f"cluster_tasks_active {status.get('tasks_active', 0)}",
        ]
        
        return Response('\n'.join(lines), mimetype='text/plain', headers={'Content-Type': 'text/plain; charset=utf-8'})
    
    @app.route('/text/logs', methods=['GET'])
    def text_logs():
        """Return logs in plain text format"""
        logs = cluster_server.get_logs()
        
        lines = []
        for log in logs:
            timestamp = log.get('timestamp', '')
            level = log.get('level', 'INFO')
            message = log.get('message', '')
            lines.append(f"[{timestamp}] {level}: {message}")
        
        return Response('\n'.join(lines), mimetype='text/plain', headers={'Content-Type': 'text/plain; charset=utf-8'})
    
    # JSON API Endpoints
    
    @app.route('/api/v1/devices', methods=['GET'])
    def api_devices():
        """Return devices in JSON format"""
        devices = cluster_server.get_devices()
        
        return jsonify({
            'status': 'success',
            'data': {
                'devices': devices,
                'count': len(devices),
                'timestamp': datetime.now().isoformat()
            }
        })
    
    @app.route('/api/v1/cluster/status', methods=['GET'])
    def api_cluster_status():
        """Return cluster status in JSON format"""
        status = cluster_server.get_cluster_status()
        
        return jsonify({
            'status': 'success',
            'data': {
                'cluster_status': status.get('status'),
                'nodes_online': status.get('nodes_online'),
                'nodes_total': status.get('nodes_total'),
                'cpu_cores': status.get('cpu_cores'),
                'cpu_usage': status.get('cpu_usage'),
                'memory_total': status.get('memory_total'),
                'memory_usage': status.get('memory_usage'),
                'tasks_active': status.get('tasks_active'),
                'tasks_completed': status.get('tasks_completed'),
                'uptime': status.get('uptime')
            }
        })
    
    @app.route('/api/v1/command', methods=['POST'])
    def api_command():
        """Execute a CLI command"""
        data = request.get_json()
        
        if not data or 'command' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Command required',
                'error_code': 'MISSING_COMMAND'
            }), 400
        
        command_str = data.get('command')
        format_type = data.get('format', 'text')
        
        # Parse command
        parsed = parser.parse(command_str)
        
        # Validate command
        if not parser.validate(parsed):
            return jsonify({
                'status': 'error',
                'message': f"Invalid command: {command_str}",
                'error_code': 'INVALID_COMMAND'
            }), 400
        
        # Execute command
        result = executor.execute(parsed)
        
        if result['status'] == 'error':
            return jsonify({
                'status': 'error',
                'message': result.get('error', 'Command execution failed'),
                'error_code': 'EXECUTION_ERROR'
            }), 400
        
        return jsonify({
            'status': 'success',
            'command': command_str,
            'format': format_type,
            'output': result.get('output', ''),
            'exit_code': result.get('exit_code', 0)
        })
    
    # Streaming Endpoints (SSE)
    
    @app.route('/stream/devices', methods=['GET'])
    def stream_devices():
        """Stream device updates using Server-Sent Events"""
        def generate():
            count = 0
            max_events = 1 if app.config.get('TESTING') else float('inf')
            
            while count < max_events:
                devices = cluster_server.get_devices()
                data = json.dumps({
                    'timestamp': datetime.now().isoformat(),
                    'devices': devices
                })
                yield f"event: device_update\ndata: {data}\n\n"
                count += 1
                
                if not app.config.get('TESTING'):
                    time.sleep(5)  # Update every 5 seconds
        
        return Response(generate(), mimetype='text/event-stream')
    
    @app.route('/stream/logs', methods=['GET'])
    def stream_logs():
        """Stream logs using Server-Sent Events"""
        device_filter = request.args.get('device')
        
        def generate():
            last_index = 0
            count = 0
            max_events = 1 if app.config.get('TESTING') else float('inf')
            
            while count < max_events:
                logs = cluster_server.get_logs()
                
                # Send new logs only
                if len(logs) > last_index:
                    new_logs = logs[last_index:]
                    for log in new_logs:
                        if device_filter and log.get('device') != device_filter:
                            continue
                        
                        data = json.dumps(log)
                        yield f"event: log\ndata: {data}\n\n"
                        count += 1
                    
                    last_index = len(logs)
                else:
                    # Send a heartbeat event for testing
                    yield f"event: heartbeat\ndata: {{}}\n\n"
                    count += 1
                
                if not app.config.get('TESTING'):
                    time.sleep(1)  # Check for new logs every second
        
        return Response(generate(), mimetype='text/event-stream')
    
    # CLI Terminal Interface
    
    @app.route('/cli', methods=['GET'])
    def cli_interface():
        """Render CLI terminal interface"""
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Retire-Cluster Terminal</title>
            <link rel="stylesheet" href="/static/css/terminal.css">
            <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>⚡</text></svg>">
        </head>
        <body class="theme-matrix">
            <!-- Terminal Header -->
            <div class="terminal-header">
                <div class="terminal-title">
                    <span class="icon">⚡</span>
                    <span>RETIRE-CLUSTER</span>
                    <span style="font-size: 12px; opacity: 0.7;">v1.1.0</span>
                </div>
                
                <div class="terminal-status">
                    <div>
                        <span class="status-indicator online"></span>
                        <span class="status-text">Connected</span>
                    </div>
                    <div id="currentTime"></div>
                    <div>
                        <select id="themeSelect" style="background: var(--bg-secondary); color: var(--text-primary); border: 1px solid var(--text-dim); font-size: 12px;">
                            <option value="matrix">Matrix</option>
                            <option value="amber">Amber</option>
                            <option value="blue">Blue</option>
                        </select>
                    </div>
                    <button id="sidebarToggle" style="background: none; border: 1px solid var(--text-dim); color: var(--text-primary); padding: 5px 10px; cursor: pointer; font-size: 12px;">
                        Info
                    </button>
                </div>
            </div>
            
            <!-- Terminal Main Area -->
            <div class="terminal-main">
                <div class="terminal-container">
                    <div id="terminal"></div>
                </div>
                
                <!-- Sidebar -->
                <div class="terminal-sidebar">
                    <div class="sidebar-section">
                        <h3>Quick Commands</h3>
                        <ul>
                            <li><code>help</code> - Show all commands</li>
                            <li><code>cluster status</code> - Cluster overview</li>
                            <li><code>devices list</code> - List all devices</li>
                            <li><code>tasks list</code> - Show active tasks</li>
                            <li><code>monitor devices</code> - Real-time monitoring</li>
                            <li><code>export devices --format=csv</code> - Export data</li>
                        </ul>
                    </div>
                    
                    <div class="sidebar-section">
                        <h3>Keyboard Shortcuts</h3>
                        <ul>
                            <li><strong>Tab</strong> - Auto-complete</li>
                            <li><strong>↑/↓</strong> - Command history</li>
                            <li><strong>Ctrl+C</strong> - Cancel command</li>
                            <li><strong>Ctrl+L</strong> - Clear screen</li>
                            <li><strong>Ctrl+R</strong> - Search history</li>
                        </ul>
                    </div>
                    
                    <div class="sidebar-section">
                        <h3>Output Formats</h3>
                        <ul>
                            <li><code>--format=table</code> - ASCII table</li>
                            <li><code>--format=json</code> - JSON output</li>
                            <li><code>--format=csv</code> - CSV format</li>
                            <li><code>--format=tsv</code> - Tab-separated</li>
                        </ul>
                    </div>
                    
                    <div class="sidebar-section">
                        <h3>Examples</h3>
                        <ul>
                            <li><code>devices list --status=online</code></li>
                            <li><code>tasks submit echo --payload='{"msg":"test"}'</code></li>
                            <li><code>monitor logs --device=android-001</code></li>
                        </ul>
                    </div>
                </div>
            </div>
            
            <!-- Terminal Footer -->
            <div class="terminal-footer">
                <div class="footer-shortcuts">
                    <span><span class="key">F1</span> Help</span>
                    <span><span class="key">F2</span> Devices</span>
                    <span><span class="key">F3</span> Tasks</span>
                    <span><span class="key">F4</span> Logs</span>
                    <span><span class="key">Ctrl+L</span> Clear</span>
                </div>
                
                <div class="footer-info">
                    <span id="connectionInfo">API: Ready</span>
                    <span>⚡ CLI-First Design</span>
                </div>
            </div>
            
            <!-- Load xterm.js -->
            <script src="https://cdn.jsdelivr.net/npm/xterm@5.3.0/lib/xterm.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/xterm-addon-fit@0.8.0/lib/xterm-addon-fit.js"></script>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/xterm@5.3.0/css/xterm.css" />
            
            <!-- Load our terminal implementation -->
            <script src="/static/js/terminal.js"></script>
            
            <script>
                // Update time display
                function updateTime() {
                    const now = new Date();
                    document.getElementById('currentTime').textContent = now.toLocaleTimeString();
                }
                
                updateTime();
                setInterval(updateTime, 1000);
                
                // Handle function keys
                document.addEventListener('keydown', (event) => {
                    if (event.key === 'F1') {
                        event.preventDefault();
                        if (window.terminal) {
                            window.terminal.term.write('help\\r');
                            window.terminal.executeCommand();
                        }
                    }
                });
                
                // Ensure proper sizing after page load
                window.addEventListener('load', function() {
                    setTimeout(function() {
                        if (window.terminal && window.terminal.fitAddon) {
                            window.terminal.fitAddon.fit();
                        }
                    }, 100);
                });
                
                // Handle page visibility changes
                document.addEventListener('visibilitychange', function() {
                    if (!document.hidden && window.terminal && window.terminal.fitAddon) {
                        setTimeout(function() {
                            window.terminal.fitAddon.fit();
                        }, 50);
                    }
                });
            </script>
        </body>
        </html>
        """
        return render_template_string(html)
    
    # Error handlers
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'status': 'error',
            'message': 'Endpoint not found',
            'error_code': 'NOT_FOUND'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'status': 'error',
            'message': 'Internal server error',
            'error_code': 'INTERNAL_ERROR'
        }), 500
    
    return app


def run_server(cluster_server=None, host='0.0.0.0', port=8081, debug=False):
    """
    Run the Flask web server
    
    Args:
        cluster_server: Cluster server instance
        host: Host to bind to
        port: Port to bind to
        debug: Enable debug mode
    """
    app = create_app(cluster_server)
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_server(debug=True)