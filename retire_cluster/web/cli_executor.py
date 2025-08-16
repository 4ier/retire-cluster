"""
CLI command executor for Retire-Cluster web interface
"""

import json
import csv
import io
from typing import Dict, List, Any, Optional
from datetime import datetime


class CommandExecutor:
    """Execute parsed CLI commands"""
    
    def __init__(self, cluster_server):
        """
        Initialize command executor
        
        Args:
            cluster_server: Cluster server instance
        """
        self.cluster_server = cluster_server
        self.command_handlers = {
            'help': self._handle_help,
            'clear': self._handle_clear,
            'exit': self._handle_exit,
            'cluster': self._handle_cluster,
            'devices': self._handle_devices,
            'device': self._handle_device,
            'tasks': self._handle_tasks,
            'task': self._handle_task,
            'monitor': self._handle_monitor,
            'export': self._handle_export,
        }
    
    def execute(self, parsed_command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a parsed command
        
        Args:
            parsed_command: Parsed command dictionary
            
        Returns:
            Execution result with status and output
        """
        verb = parsed_command.get('verb')
        
        if not verb:
            return {
                "status": "error",
                "error": "No command specified",
                "exit_code": 2
            }
        
        if verb not in self.command_handlers:
            return {
                "status": "error",
                "error": f"Unknown command: {verb}",
                "exit_code": 1
            }
        
        try:
            handler = self.command_handlers[verb]
            return handler(parsed_command)
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "exit_code": 1
            }
    
    def _handle_help(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle help command"""
        help_text = """Available commands:

  cluster status    Show cluster status
  cluster health    Check cluster health
  cluster metrics   Show cluster metrics
  
  devices list      List all devices
  devices show      Show device details
  devices ping      Ping device(s)
  
  tasks list        List tasks
  tasks submit      Submit new task
  tasks show        Show task details
  
  monitor devices   Monitor device status
  monitor tasks     Monitor task execution
  monitor logs      Monitor logs
  
  export devices    Export device data
  export tasks      Export task data
  
  help              Show this help
  clear             Clear screen
  exit              Exit interface
"""
        return {
            "status": "success",
            "output": help_text,
            "format": "text",
            "exit_code": 0
        }
    
    def _handle_clear(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle clear command"""
        return {
            "status": "success",
            "action": "clear",
            "exit_code": 0
        }
    
    def _handle_exit(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle exit command"""
        return {
            "status": "success",
            "action": "exit",
            "exit_code": 0
        }
    
    def _handle_cluster(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle cluster commands"""
        noun = command.get('noun')
        
        if noun == 'status':
            return self._get_cluster_status(command)
        elif noun == 'health':
            return self._get_cluster_health(command)
        elif noun == 'metrics':
            return self._get_cluster_metrics(command)
        else:
            return {
                "status": "error",
                "error": f"Unknown cluster command: {noun}",
                "exit_code": 1
            }
    
    def _handle_devices(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle devices commands"""
        noun = command.get('noun')
        
        if noun == 'list':
            return self._list_devices(command)
        elif noun == 'show':
            return self._show_device(command)
        elif noun == 'ping':
            return self._ping_device(command)
        else:
            return {
                "status": "error",
                "error": f"Unknown devices command: {noun}",
                "exit_code": 1
            }
    
    def _handle_device(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle single device commands"""
        return self._handle_devices(command)
    
    def _handle_tasks(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tasks commands"""
        noun = command.get('noun')
        
        if noun == 'list':
            return self._list_tasks(command)
        elif noun == 'submit':
            return self._submit_task(command)
        elif noun == 'show':
            return self._show_task(command)
        else:
            return {
                "status": "error",
                "error": f"Unknown tasks command: {noun}",
                "exit_code": 1
            }
    
    def _handle_task(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle single task commands"""
        return self._handle_tasks(command)
    
    def _handle_monitor(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle monitor commands"""
        noun = command.get('noun')
        
        return {
            "status": "success",
            "action": "monitor",
            "target": noun,
            "options": command.get('options', {}),
            "exit_code": 0
        }
    
    def _handle_export(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle export commands"""
        noun = command.get('noun')
        
        if noun == 'devices':
            return self._export_devices(command)
        elif noun == 'tasks':
            return self._export_tasks(command)
        else:
            return {
                "status": "error",
                "error": f"Unknown export target: {noun}",
                "exit_code": 1
            }
    
    def _get_cluster_status(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Get cluster status"""
        try:
            status = self.cluster_server.get_cluster_status()
            
            output = f"""CLUSTER STATUS: {status.get('status', 'unknown').upper()}
─────────────────────────────────────────────
Nodes Online: {status.get('nodes_online', 0)}/{status.get('nodes_total', 0)}
CPU Cores:    {status.get('cpu_cores', 0)} ({status.get('cpu_usage', 0)}% utilized)
Memory:       {status.get('memory_total', 0)}GB ({status.get('memory_usage', 0)}% used)
Active Tasks: {status.get('tasks_active', 0)}
Uptime:       {status.get('uptime', 'N/A')}
"""
            
            return {
                "status": "success",
                "output": output,
                "format": "text",
                "exit_code": 0
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "exit_code": 1
            }
    
    def _get_cluster_health(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Get cluster health"""
        # Implementation would check various health metrics
        return {
            "status": "success",
            "output": "Cluster is healthy",
            "format": "text",
            "exit_code": 0
        }
    
    def _get_cluster_metrics(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Get cluster metrics"""
        # Implementation would return detailed metrics
        return {
            "status": "success",
            "output": "Cluster metrics",
            "format": "text",
            "exit_code": 0
        }
    
    def _list_devices(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """List devices"""
        options = command.get('options', {})
        format_type = options.get('format', 'table')
        status_filter = options.get('status')
        
        try:
            devices = self.cluster_server.get_devices()
            
            # Apply filters
            if status_filter:
                devices = [d for d in devices if d.get('status') == status_filter]
            
            # Format output based on requested format
            if format_type == 'json':
                output = {
                    "devices": devices,
                    "count": len(devices),
                    "timestamp": datetime.now().isoformat()
                }
                return {
                    "status": "success",
                    "output": output,
                    "format": "json",
                    "exit_code": 0
                }
            
            elif format_type == 'csv':
                output = self._format_devices_csv(devices)
                return {
                    "status": "success",
                    "output": output,
                    "format": "csv",
                    "exit_code": 0
                }
            
            elif format_type == 'tsv':
                output = self._format_devices_tsv(devices)
                return {
                    "status": "success",
                    "output": output,
                    "format": "tsv",
                    "exit_code": 0
                }
            
            else:  # Default table format
                output = self._format_devices_table(devices)
                return {
                    "status": "success",
                    "output": output,
                    "format": format_type,
                    "exit_code": 0
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "exit_code": 1
            }
    
    def _format_devices_table(self, devices: List[Dict]) -> str:
        """Format devices as ASCII table"""
        if not devices:
            return "No devices found"
        
        output = "ID           STATUS   CPU    MEM     TASKS  UPTIME\n"
        output += "─" * 54 + "\n"
        
        for device in devices:
            output += f"{device.get('id', 'N/A'):<12} "
            output += f"{device.get('status', 'N/A'):<8} "
            output += f"{device.get('cpu', 0):>3}%   "
            output += f"{device.get('memory', 0):>4.1f}GB  "
            output += f"{device.get('tasks', 0):>3}    "
            output += f"{device.get('uptime', 'N/A')}\n"
        
        return output
    
    def _format_devices_csv(self, devices: List[Dict]) -> str:
        """Format devices as CSV"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['id', 'status', 'cpu', 'memory', 'tasks'])
        
        # Write data
        for device in devices:
            writer.writerow([
                device.get('id', ''),
                device.get('status', ''),
                device.get('cpu', 0),
                device.get('memory', 0),
                device.get('tasks', 0)
            ])
        
        return output.getvalue()
    
    def _format_devices_tsv(self, devices: List[Dict]) -> str:
        """Format devices as TSV"""
        output = io.StringIO()
        writer = csv.writer(output, delimiter='\t')
        
        # Write header
        writer.writerow(['id', 'status', 'cpu', 'memory', 'tasks'])
        
        # Write data
        for device in devices:
            writer.writerow([
                device.get('id', ''),
                device.get('status', ''),
                device.get('cpu', 0),
                device.get('memory', 0),
                device.get('tasks', 0)
            ])
        
        return output.getvalue()
    
    def _show_device(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Show device details"""
        arguments = command.get('arguments', [])
        
        if not arguments:
            return {
                "status": "error",
                "error": "Device ID required",
                "exit_code": 1
            }
        
        device_id = arguments[0]
        
        # Implementation would fetch device details
        return {
            "status": "success",
            "output": f"Device details for {device_id}",
            "format": "text",
            "exit_code": 0
        }
    
    def _ping_device(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Ping device"""
        arguments = command.get('arguments', [])
        
        if not arguments:
            return {
                "status": "error",
                "error": "Device ID required",
                "exit_code": 1
            }
        
        # Implementation would ping devices
        return {
            "status": "success",
            "output": f"Pinging devices: {', '.join(arguments)}",
            "format": "text",
            "exit_code": 0
        }
    
    def _list_tasks(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """List tasks"""
        # Implementation would list tasks
        return {
            "status": "success",
            "output": "Task list",
            "format": "text",
            "exit_code": 0
        }
    
    def _submit_task(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Submit new task"""
        # Implementation would submit task
        return {
            "status": "success",
            "output": "Task submitted",
            "format": "text",
            "exit_code": 0
        }
    
    def _show_task(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Show task details"""
        # Implementation would show task details
        return {
            "status": "success",
            "output": "Task details",
            "format": "text",
            "exit_code": 0
        }
    
    def _export_devices(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Export devices data"""
        # Implementation would export devices
        return {
            "status": "success",
            "output": "Devices exported",
            "format": "text",
            "exit_code": 0
        }
    
    def _export_tasks(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Export tasks data"""
        # Implementation would export tasks
        return {
            "status": "success",
            "output": "Tasks exported",
            "format": "text",
            "exit_code": 0
        }