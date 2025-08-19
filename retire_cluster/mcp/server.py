"""
MCP Server implementation for Retire-Cluster.

Provides a Model Context Protocol server that exposes cluster management
capabilities through standardized tools and resources.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from ..device.registry import DeviceRegistry
from ..tasks.scheduler import TaskScheduler
from ..core.logger import get_logger

logger = get_logger(__name__)


class MCPServer:
    """
    MCP Server that exposes cluster capabilities to Claude Code.
    
    This server implements the Model Context Protocol to provide:
    - Device management tools
    - Task scheduling and execution
    - Cluster monitoring and status
    - Natural language interface for cluster operations
    """
    
    def __init__(self, 
                 registry: DeviceRegistry,
                 scheduler: Optional[TaskScheduler] = None,
                 host: str = "localhost",
                 port: int = 3000):
        """
        Initialize MCP Server.
        
        Args:
            registry: Device registry instance
            scheduler: Task scheduler instance
            host: Server host address
            port: Server port
        """
        self.registry = registry
        self.scheduler = scheduler
        self.host = host
        self.port = port
        self.server = None
        self.clients = set()
        
        # Tool definitions
        self.tools = self._initialize_tools()
        
        # Resource definitions
        self.resources = self._initialize_resources()
        
        logger.info(f"MCP Server initialized on {host}:{port}")
    
    def _initialize_tools(self) -> Dict[str, Dict[str, Any]]:
        """Initialize available MCP tools."""
        return {
            "list_devices": {
                "name": "list_devices",
                "description": "List all devices in the cluster",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": ["all", "online", "offline"],
                            "description": "Filter devices by status"
                        },
                        "role": {
                            "type": "string",
                            "enum": ["all", "worker", "storage", "compute"],
                            "description": "Filter devices by role"
                        }
                    }
                }
            },
            "get_device_info": {
                "name": "get_device_info",
                "description": "Get detailed information about a specific device",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "The ID of the device"
                        }
                    },
                    "required": ["device_id"]
                }
            },
            "execute_task": {
                "name": "execute_task",
                "description": "Execute a task on the cluster",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task_type": {
                            "type": "string",
                            "description": "Type of task to execute"
                        },
                        "command": {
                            "type": "string",
                            "description": "Command or script to execute"
                        },
                        "target_device": {
                            "type": "string",
                            "description": "Optional: specific device to execute on"
                        },
                        "requirements": {
                            "type": "object",
                            "description": "Task requirements (CPU, memory, etc.)"
                        }
                    },
                    "required": ["task_type", "command"]
                }
            },
            "get_cluster_status": {
                "name": "get_cluster_status",
                "description": "Get overall cluster status and statistics",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            "schedule_task": {
                "name": "schedule_task",
                "description": "Schedule a task for future execution",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task_type": {
                            "type": "string",
                            "description": "Type of task to schedule"
                        },
                        "command": {
                            "type": "string",
                            "description": "Command or script to execute"
                        },
                        "schedule_time": {
                            "type": "string",
                            "description": "ISO format datetime or cron expression"
                        },
                        "requirements": {
                            "type": "object",
                            "description": "Task requirements"
                        }
                    },
                    "required": ["task_type", "command", "schedule_time"]
                }
            },
            "cancel_task": {
                "name": "cancel_task",
                "description": "Cancel a running or scheduled task",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "The ID of the task to cancel"
                        }
                    },
                    "required": ["task_id"]
                }
            },
            "get_task_status": {
                "name": "get_task_status",
                "description": "Get the status of a specific task",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "The ID of the task"
                        }
                    },
                    "required": ["task_id"]
                }
            },
            "manage_device": {
                "name": "manage_device",
                "description": "Manage device state (restart, shutdown, etc.)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "The ID of the device"
                        },
                        "action": {
                            "type": "string",
                            "enum": ["restart", "shutdown", "wake", "update"],
                            "description": "Action to perform"
                        }
                    },
                    "required": ["device_id", "action"]
                }
            }
        }
    
    def _initialize_resources(self) -> Dict[str, Dict[str, Any]]:
        """Initialize available MCP resources."""
        return {
            "cluster_config": {
                "uri": "retire-cluster://config",
                "name": "Cluster Configuration",
                "description": "Current cluster configuration and settings",
                "mimeType": "application/json"
            },
            "device_registry": {
                "uri": "retire-cluster://devices",
                "name": "Device Registry",
                "description": "Complete device registry with all metadata",
                "mimeType": "application/json"
            },
            "task_queue": {
                "uri": "retire-cluster://tasks",
                "name": "Task Queue",
                "description": "Current task queue and execution history",
                "mimeType": "application/json"
            },
            "cluster_metrics": {
                "uri": "retire-cluster://metrics",
                "name": "Cluster Metrics",
                "description": "Real-time cluster performance metrics",
                "mimeType": "application/json"
            }
        }
    
    async def start(self):
        """Start the MCP server."""
        try:
            self.server = await asyncio.start_server(
                self._handle_client,
                self.host,
                self.port
            )
            
            logger.info(f"MCP Server started on {self.host}:{self.port}")
            
            async with self.server:
                await self.server.serve_forever()
                
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            raise
    
    async def stop(self):
        """Stop the MCP server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("MCP Server stopped")
    
    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle MCP client connections."""
        addr = writer.get_extra_info('peername')
        logger.info(f"MCP client connected from {addr}")
        self.clients.add(writer)
        
        try:
            # Send initial server info
            await self._send_server_info(writer)
            
            while True:
                # Read messages from client
                data = await reader.readline()
                if not data:
                    break
                
                try:
                    message = json.loads(data.decode())
                    response = await self._handle_message(message)
                    
                    # Send response
                    await self._send_message(writer, response)
                    
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from {addr}")
                    await self._send_error(writer, "Invalid JSON format")
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error handling client {addr}: {e}")
        finally:
            self.clients.discard(writer)
            writer.close()
            await writer.wait_closed()
            logger.info(f"MCP client disconnected from {addr}")
    
    async def _handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP messages."""
        msg_type = message.get("type")
        msg_id = message.get("id")
        
        if msg_type == "initialize":
            return await self._handle_initialize(msg_id, message)
        elif msg_type == "tools/list":
            return await self._handle_tools_list(msg_id)
        elif msg_type == "tools/call":
            return await self._handle_tool_call(msg_id, message)
        elif msg_type == "resources/list":
            return await self._handle_resources_list(msg_id)
        elif msg_type == "resources/read":
            return await self._handle_resource_read(msg_id, message)
        else:
            return {
                "type": "error",
                "id": msg_id,
                "error": {
                    "code": "unknown_message_type",
                    "message": f"Unknown message type: {msg_type}"
                }
            }
    
    async def _handle_initialize(self, msg_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialization request."""
        return {
            "type": "initialize/result",
            "id": msg_id,
            "result": {
                "protocolVersion": "0.1.0",
                "capabilities": {
                    "tools": True,
                    "resources": True,
                    "prompts": False,
                    "logging": True
                },
                "serverInfo": {
                    "name": "retire-cluster-mcp",
                    "version": "1.0.0",
                    "description": "MCP server for Retire-Cluster management"
                }
            }
        }
    
    async def _handle_tools_list(self, msg_id: str) -> Dict[str, Any]:
        """Handle tools list request."""
        return {
            "type": "tools/list/result",
            "id": msg_id,
            "result": {
                "tools": list(self.tools.values())
            }
        }
    
    async def _handle_tool_call(self, msg_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool call request."""
        tool_name = message.get("params", {}).get("name")
        arguments = message.get("params", {}).get("arguments", {})
        
        if tool_name not in self.tools:
            return {
                "type": "error",
                "id": msg_id,
                "error": {
                    "code": "unknown_tool",
                    "message": f"Unknown tool: {tool_name}"
                }
            }
        
        try:
            result = await self._execute_tool(tool_name, arguments)
            return {
                "type": "tools/call/result",
                "id": msg_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2)
                        }
                    ]
                }
            }
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {
                "type": "error",
                "id": msg_id,
                "error": {
                    "code": "tool_execution_error",
                    "message": str(e)
                }
            }
    
    async def _handle_resources_list(self, msg_id: str) -> Dict[str, Any]:
        """Handle resources list request."""
        return {
            "type": "resources/list/result",
            "id": msg_id,
            "result": {
                "resources": list(self.resources.values())
            }
        }
    
    async def _handle_resource_read(self, msg_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resource read request."""
        uri = message.get("params", {}).get("uri")
        
        # Find resource by URI
        resource = None
        for res in self.resources.values():
            if res["uri"] == uri:
                resource = res
                break
        
        if not resource:
            return {
                "type": "error",
                "id": msg_id,
                "error": {
                    "code": "unknown_resource",
                    "message": f"Unknown resource: {uri}"
                }
            }
        
        try:
            content = await self._read_resource(uri)
            return {
                "type": "resources/read/result",
                "id": msg_id,
                "result": {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": resource["mimeType"],
                            "text": json.dumps(content, indent=2)
                        }
                    ]
                }
            }
        except Exception as e:
            logger.error(f"Error reading resource {uri}: {e}")
            return {
                "type": "error",
                "id": msg_id,
                "error": {
                    "code": "resource_read_error",
                    "message": str(e)
                }
            }
    
    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool and return results."""
        if tool_name == "list_devices":
            return await self._tool_list_devices(arguments)
        elif tool_name == "get_device_info":
            return await self._tool_get_device_info(arguments)
        elif tool_name == "execute_task":
            return await self._tool_execute_task(arguments)
        elif tool_name == "get_cluster_status":
            return await self._tool_get_cluster_status(arguments)
        elif tool_name == "schedule_task":
            return await self._tool_schedule_task(arguments)
        elif tool_name == "cancel_task":
            return await self._tool_cancel_task(arguments)
        elif tool_name == "get_task_status":
            return await self._tool_get_task_status(arguments)
        elif tool_name == "manage_device":
            return await self._tool_manage_device(arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def _tool_list_devices(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """List devices tool implementation."""
        status_filter = arguments.get("status", "all")
        role_filter = arguments.get("role", "all")
        
        devices = []
        for device_id, device in self.registry.devices.items():
            # Apply filters
            if status_filter != "all":
                if status_filter == "online" and device.get("status") != "online":
                    continue
                elif status_filter == "offline" and device.get("status") != "offline":
                    continue
            
            if role_filter != "all" and device.get("role") != role_filter:
                continue
            
            devices.append({
                "id": device_id,
                "hostname": device.get("hostname"),
                "role": device.get("role"),
                "status": device.get("status"),
                "platform": device.get("platform"),
                "last_seen": device.get("last_heartbeat")
            })
        
        return {
            "devices": devices,
            "total": len(devices),
            "filter": {
                "status": status_filter,
                "role": role_filter
            }
        }
    
    async def _tool_get_device_info(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get device info tool implementation."""
        device_id = arguments["device_id"]
        device = self.registry.get_device(device_id)
        
        if not device:
            raise ValueError(f"Device not found: {device_id}")
        
        return device
    
    async def _tool_execute_task(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task tool implementation."""
        if not self.scheduler:
            raise RuntimeError("Task scheduler not available")
        
        task_id = await self.scheduler.submit_task(
            task_type=arguments["task_type"],
            command=arguments["command"],
            target_device=arguments.get("target_device"),
            requirements=arguments.get("requirements", {})
        )
        
        return {
            "task_id": task_id,
            "status": "submitted",
            "message": "Task submitted for execution"
        }
    
    async def _tool_get_cluster_status(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get cluster status tool implementation."""
        online_devices = sum(1 for d in self.registry.devices.values() 
                           if d.get("status") == "online")
        total_devices = len(self.registry.devices)
        
        # Calculate total resources
        total_cpu = sum(d.get("cpu_count", 0) for d in self.registry.devices.values())
        total_memory = sum(d.get("memory_total", 0) for d in self.registry.devices.values())
        
        return {
            "status": "operational",
            "devices": {
                "total": total_devices,
                "online": online_devices,
                "offline": total_devices - online_devices
            },
            "resources": {
                "total_cpu_cores": total_cpu,
                "total_memory_gb": round(total_memory / (1024**3), 2)
            },
            "tasks": {
                "running": self.scheduler.running_tasks if self.scheduler else 0,
                "queued": self.scheduler.queued_tasks if self.scheduler else 0
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def _tool_schedule_task(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule task tool implementation."""
        if not self.scheduler:
            raise RuntimeError("Task scheduler not available")
        
        task_id = await self.scheduler.schedule_task(
            task_type=arguments["task_type"],
            command=arguments["command"],
            schedule_time=arguments["schedule_time"],
            requirements=arguments.get("requirements", {})
        )
        
        return {
            "task_id": task_id,
            "status": "scheduled",
            "schedule_time": arguments["schedule_time"]
        }
    
    async def _tool_cancel_task(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Cancel task tool implementation."""
        if not self.scheduler:
            raise RuntimeError("Task scheduler not available")
        
        success = await self.scheduler.cancel_task(arguments["task_id"])
        
        return {
            "task_id": arguments["task_id"],
            "cancelled": success,
            "message": "Task cancelled" if success else "Failed to cancel task"
        }
    
    async def _tool_get_task_status(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get task status tool implementation."""
        if not self.scheduler:
            raise RuntimeError("Task scheduler not available")
        
        status = await self.scheduler.get_task_status(arguments["task_id"])
        
        if not status:
            raise ValueError(f"Task not found: {arguments['task_id']}")
        
        return status
    
    async def _tool_manage_device(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Manage device tool implementation."""
        device_id = arguments["device_id"]
        action = arguments["action"]
        
        device = self.registry.get_device(device_id)
        if not device:
            raise ValueError(f"Device not found: {device_id}")
        
        # Send management command to device
        # This would be implemented based on the actual device communication protocol
        
        return {
            "device_id": device_id,
            "action": action,
            "status": "command_sent",
            "message": f"Management command '{action}' sent to device"
        }
    
    async def _read_resource(self, uri: str) -> Dict[str, Any]:
        """Read resource content."""
        if uri == "retire-cluster://config":
            return {
                "cluster_name": "Retire-Cluster",
                "version": "1.0.0",
                "main_node": {
                    "host": self.host,
                    "port": self.port
                }
            }
        elif uri == "retire-cluster://devices":
            return {
                "devices": list(self.registry.devices.values()),
                "total": len(self.registry.devices)
            }
        elif uri == "retire-cluster://tasks":
            if self.scheduler:
                return await self.scheduler.get_all_tasks()
            return {"tasks": [], "message": "Scheduler not available"}
        elif uri == "retire-cluster://metrics":
            return await self._get_cluster_metrics()
        else:
            raise ValueError(f"Unknown resource: {uri}")
    
    async def _get_cluster_metrics(self) -> Dict[str, Any]:
        """Get cluster metrics."""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "devices": {},
            "aggregate": {
                "cpu_usage": 0,
                "memory_usage": 0,
                "disk_usage": 0
            }
        }
        
        for device_id, device in self.registry.devices.items():
            if device.get("status") == "online":
                metrics["devices"][device_id] = {
                    "cpu_percent": device.get("cpu_percent", 0),
                    "memory_percent": device.get("memory_percent", 0),
                    "disk_percent": device.get("disk_percent", 0)
                }
                
                metrics["aggregate"]["cpu_usage"] += device.get("cpu_percent", 0)
                metrics["aggregate"]["memory_usage"] += device.get("memory_percent", 0)
                metrics["aggregate"]["disk_usage"] += device.get("disk_percent", 0)
        
        # Calculate averages
        online_count = len([d for d in self.registry.devices.values() 
                          if d.get("status") == "online"])
        if online_count > 0:
            metrics["aggregate"]["cpu_usage"] /= online_count
            metrics["aggregate"]["memory_usage"] /= online_count
            metrics["aggregate"]["disk_usage"] /= online_count
        
        return metrics
    
    async def _send_server_info(self, writer: asyncio.StreamWriter):
        """Send server information to client."""
        info = {
            "type": "serverInfo",
            "serverInfo": {
                "name": "retire-cluster-mcp",
                "version": "1.0.0",
                "protocolVersion": "0.1.0"
            }
        }
        await self._send_message(writer, info)
    
    async def _send_message(self, writer: asyncio.StreamWriter, message: Dict[str, Any]):
        """Send a message to client."""
        data = json.dumps(message) + "\n"
        writer.write(data.encode())
        await writer.drain()
    
    async def _send_error(self, writer: asyncio.StreamWriter, error: str):
        """Send an error message to client."""
        message = {
            "type": "error",
            "error": {
                "code": "server_error",
                "message": error
            }
        }
        await self._send_message(writer, message)