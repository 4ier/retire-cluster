"""
MCP Tools implementation for cluster management.

Provides high-level tools that can be used by Claude Code to manage
the Retire-Cluster through natural language commands.
"""

import json
from typing import Any, Dict, List, Optional
from datetime import datetime

from ..device.registry import DeviceRegistry
from ..tasks.scheduler import TaskScheduler
from ..core.logger import get_logger

logger = get_logger(__name__)


class ClusterTools:
    """
    High-level cluster management tools for MCP clients.
    
    These tools provide simplified interfaces for common cluster operations
    that can be easily invoked through natural language commands.
    """
    
    def __init__(self, registry: DeviceRegistry, scheduler: Optional[TaskScheduler] = None):
        """
        Initialize cluster tools.
        
        Args:
            registry: Device registry instance
            scheduler: Optional task scheduler instance
        """
        self.registry = registry
        self.scheduler = scheduler
    
    async def analyze_cluster_health(self) -> Dict[str, Any]:
        """
        Analyze overall cluster health and provide recommendations.
        
        Returns:
            Health analysis with status, issues, and recommendations
        """
        health = {
            "status": "healthy",
            "score": 100,
            "issues": [],
            "recommendations": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Check device availability
        total_devices = len(self.registry.devices)
        online_devices = sum(1 for d in self.registry.devices.values() 
                           if d.get("status") == "online")
        
        if total_devices == 0:
            health["status"] = "critical"
            health["score"] = 0
            health["issues"].append("No devices registered in cluster")
            health["recommendations"].append("Add worker nodes to the cluster")
        else:
            availability_ratio = online_devices / total_devices
            
            if availability_ratio < 0.5:
                health["status"] = "degraded"
                health["score"] -= 50
                health["issues"].append(f"Low device availability: {online_devices}/{total_devices} online")
                health["recommendations"].append("Check network connectivity and device power")
            elif availability_ratio < 0.8:
                health["status"] = "warning"
                health["score"] -= 20
                health["issues"].append(f"Some devices offline: {total_devices - online_devices} devices")
            
            # Check resource utilization
            avg_cpu = 0
            avg_memory = 0
            high_util_devices = []
            
            for device_id, device in self.registry.devices.items():
                if device.get("status") == "online":
                    cpu_percent = device.get("cpu_percent", 0)
                    mem_percent = device.get("memory_percent", 0)
                    
                    avg_cpu += cpu_percent
                    avg_memory += mem_percent
                    
                    if cpu_percent > 90 or mem_percent > 90:
                        high_util_devices.append(device_id)
            
            if online_devices > 0:
                avg_cpu /= online_devices
                avg_memory /= online_devices
                
                if avg_cpu > 80:
                    health["score"] -= 10
                    health["issues"].append(f"High average CPU usage: {avg_cpu:.1f}%")
                    health["recommendations"].append("Consider adding more compute nodes")
                
                if avg_memory > 80:
                    health["score"] -= 10
                    health["issues"].append(f"High average memory usage: {avg_memory:.1f}%")
                    health["recommendations"].append("Consider adding more memory or nodes")
                
                if high_util_devices:
                    health["issues"].append(f"High utilization on devices: {', '.join(high_util_devices)}")
                    health["recommendations"].append("Redistribute workload or upgrade hardware")
        
        # Update overall status based on score
        if health["score"] >= 90:
            health["status"] = "healthy"
        elif health["score"] >= 70:
            health["status"] = "warning"
        elif health["score"] >= 50:
            health["status"] = "degraded"
        else:
            health["status"] = "critical"
        
        return health
    
    async def optimize_task_distribution(self) -> Dict[str, Any]:
        """
        Analyze and optimize task distribution across the cluster.
        
        Returns:
            Optimization report with current state and recommendations
        """
        report = {
            "current_distribution": {},
            "recommended_changes": [],
            "expected_improvement": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        if not self.scheduler:
            report["error"] = "Task scheduler not available"
            return report
        
        # Analyze current task distribution
        for device_id, device in self.registry.devices.items():
            if device.get("status") == "online":
                report["current_distribution"][device_id] = {
                    "running_tasks": device.get("running_tasks", 0),
                    "cpu_usage": device.get("cpu_percent", 0),
                    "memory_usage": device.get("memory_percent", 0),
                    "capacity_score": self._calculate_capacity_score(device)
                }
        
        # Find imbalances
        if report["current_distribution"]:
            avg_load = sum(d["running_tasks"] for d in report["current_distribution"].values()) / len(report["current_distribution"])
            
            for device_id, stats in report["current_distribution"].items():
                if stats["running_tasks"] > avg_load * 1.5 and stats["cpu_usage"] > 70:
                    # Overloaded device
                    report["recommended_changes"].append({
                        "action": "redistribute",
                        "device": device_id,
                        "reason": "Device overloaded",
                        "target_reduction": int(stats["running_tasks"] - avg_load)
                    })
                elif stats["running_tasks"] < avg_load * 0.5 and stats["capacity_score"] > 50:
                    # Underutilized device
                    report["recommended_changes"].append({
                        "action": "increase_load",
                        "device": device_id,
                        "reason": "Device underutilized",
                        "additional_capacity": int(avg_load - stats["running_tasks"])
                    })
        
        # Calculate expected improvement
        if report["recommended_changes"]:
            report["expected_improvement"] = min(len(report["recommended_changes"]) * 10, 50)
        
        return report
    
    async def execute_batch_tasks(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute multiple tasks in batch with optimal distribution.
        
        Args:
            tasks: List of task definitions
            
        Returns:
            Batch execution result with task IDs and status
        """
        if not self.scheduler:
            return {
                "error": "Task scheduler not available",
                "tasks_submitted": 0
            }
        
        result = {
            "batch_id": f"batch_{datetime.now().timestamp()}",
            "tasks_submitted": 0,
            "tasks_failed": 0,
            "task_ids": [],
            "errors": [],
            "timestamp": datetime.now().isoformat()
        }
        
        for task in tasks:
            try:
                task_id = await self.scheduler.submit_task(
                    task_type=task.get("type", "general"),
                    command=task.get("command", ""),
                    target_device=task.get("target_device"),
                    requirements=task.get("requirements", {})
                )
                result["task_ids"].append(task_id)
                result["tasks_submitted"] += 1
            except Exception as e:
                result["tasks_failed"] += 1
                result["errors"].append({
                    "task": task.get("command", "unknown"),
                    "error": str(e)
                })
                logger.error(f"Failed to submit batch task: {e}")
        
        return result
    
    async def get_device_recommendations(self) -> Dict[str, Any]:
        """
        Provide recommendations for device management and optimization.
        
        Returns:
            Recommendations for each device and overall cluster
        """
        recommendations = {
            "devices": {},
            "cluster": [],
            "priority_actions": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Analyze each device
        for device_id, device in self.registry.devices.items():
            device_rec = {
                "status": device.get("status", "unknown"),
                "recommendations": []
            }
            
            if device.get("status") == "offline":
                device_rec["recommendations"].append("Check device connectivity and power")
                recommendations["priority_actions"].append({
                    "device": device_id,
                    "action": "reconnect",
                    "priority": "high"
                })
            else:
                # Check resource usage
                cpu_percent = device.get("cpu_percent", 0)
                mem_percent = device.get("memory_percent", 0)
                disk_percent = device.get("disk_percent", 0)
                
                if cpu_percent > 90:
                    device_rec["recommendations"].append("High CPU usage - consider reducing workload")
                if mem_percent > 90:
                    device_rec["recommendations"].append("High memory usage - consider freeing memory")
                if disk_percent > 90:
                    device_rec["recommendations"].append("Low disk space - clean up unnecessary files")
                
                # Check for outdated software
                if device.get("needs_update"):
                    device_rec["recommendations"].append("Software update available")
                    recommendations["priority_actions"].append({
                        "device": device_id,
                        "action": "update",
                        "priority": "medium"
                    })
            
            if device_rec["recommendations"]:
                recommendations["devices"][device_id] = device_rec
        
        # Cluster-wide recommendations
        total_devices = len(self.registry.devices)
        online_devices = sum(1 for d in self.registry.devices.values() 
                           if d.get("status") == "online")
        
        if total_devices < 3:
            recommendations["cluster"].append("Consider adding more devices for better redundancy")
        
        if online_devices < total_devices * 0.8:
            recommendations["cluster"].append("Multiple devices offline - check network infrastructure")
        
        # Check for device diversity
        platforms = set(d.get("platform") for d in self.registry.devices.values())
        if len(platforms) < 2:
            recommendations["cluster"].append("Consider diversifying device platforms for better compatibility")
        
        return recommendations
    
    async def generate_cluster_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive cluster status report.
        
        Returns:
            Detailed report with all cluster metrics and statistics
        """
        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": {},
            "devices": {},
            "performance": {},
            "tasks": {},
            "recommendations": []
        }
        
        # Summary statistics
        total_devices = len(self.registry.devices)
        online_devices = sum(1 for d in self.registry.devices.values() 
                           if d.get("status") == "online")
        
        report["summary"] = {
            "total_devices": total_devices,
            "online_devices": online_devices,
            "offline_devices": total_devices - online_devices,
            "availability_percentage": (online_devices / total_devices * 100) if total_devices > 0 else 0,
            "cluster_status": "operational" if online_devices > 0 else "offline"
        }
        
        # Device details
        for device_id, device in self.registry.devices.items():
            report["devices"][device_id] = {
                "hostname": device.get("hostname"),
                "platform": device.get("platform"),
                "status": device.get("status"),
                "role": device.get("role"),
                "cpu_cores": device.get("cpu_count"),
                "memory_gb": round(device.get("memory_total", 0) / (1024**3), 2),
                "last_seen": device.get("last_heartbeat"),
                "uptime_hours": device.get("uptime", 0) / 3600 if device.get("uptime") else 0
            }
        
        # Performance metrics
        if online_devices > 0:
            total_cpu = sum(d.get("cpu_count", 0) for d in self.registry.devices.values() 
                          if d.get("status") == "online")
            total_memory = sum(d.get("memory_total", 0) for d in self.registry.devices.values() 
                             if d.get("status") == "online")
            avg_cpu_usage = sum(d.get("cpu_percent", 0) for d in self.registry.devices.values() 
                              if d.get("status") == "online") / online_devices
            avg_mem_usage = sum(d.get("memory_percent", 0) for d in self.registry.devices.values() 
                              if d.get("status") == "online") / online_devices
            
            report["performance"] = {
                "total_cpu_cores": total_cpu,
                "total_memory_gb": round(total_memory / (1024**3), 2),
                "average_cpu_usage": round(avg_cpu_usage, 2),
                "average_memory_usage": round(avg_mem_usage, 2),
                "cluster_efficiency": round((100 - avg_cpu_usage) * (online_devices / total_devices), 2) if total_devices > 0 else 0
            }
        
        # Task statistics
        if self.scheduler:
            report["tasks"] = {
                "total_executed": self.scheduler.total_executed,
                "currently_running": self.scheduler.running_tasks,
                "queued": self.scheduler.queued_tasks,
                "success_rate": self.scheduler.success_rate
            }
        
        # Generate recommendations
        health = await self.analyze_cluster_health()
        report["recommendations"] = health.get("recommendations", [])
        
        return report
    
    def _calculate_capacity_score(self, device: Dict[str, Any]) -> float:
        """
        Calculate device capacity score based on available resources.
        
        Args:
            device: Device information
            
        Returns:
            Capacity score (0-100)
        """
        cpu_available = 100 - device.get("cpu_percent", 100)
        mem_available = 100 - device.get("memory_percent", 100)
        
        # Weight CPU and memory equally
        score = (cpu_available + mem_available) / 2
        
        # Adjust for device capabilities
        if device.get("cpu_count", 1) > 4:
            score *= 1.2  # Bonus for multi-core devices
        
        if device.get("memory_total", 0) > 8 * (1024**3):
            score *= 1.1  # Bonus for high-memory devices
        
        return min(score, 100)