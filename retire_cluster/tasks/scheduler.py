"""
Task scheduler for intelligent task distribution across the cluster
"""

import threading
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Set, Callable, Any
import logging

from .task import Task, TaskStatus, TaskResult, TaskRequirements
from .queue import TaskQueue


class TaskScheduler:
    """
    Intelligent task scheduler that distributes tasks across cluster devices
    """
    
    def __init__(self, task_queue: TaskQueue):
        self.task_queue = task_queue
        self.logger = logging.getLogger("scheduler")
        
        # Device registry
        self._devices: Dict[str, Dict[str, Any]] = {}  # device_id -> capabilities
        self._device_heartbeats: Dict[str, datetime] = {}  # device_id -> last_heartbeat
        self._device_loads: Dict[str, int] = {}  # device_id -> current_task_count
        
        # Scheduling configuration
        self.heartbeat_timeout = 300  # 5 minutes
        self.max_tasks_per_device = 5
        self.load_balancing_enabled = True
        self.device_affinity_enabled = True
        
        # Scheduling thread
        self._scheduler_thread: Optional[threading.Thread] = None
        self._shutdown_event = threading.Event()
        self._running = False
        
        # Statistics
        self.stats = {
            'tasks_scheduled': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'scheduler_rounds': 0,
            'last_schedule_time': None
        }
        
        # Task placement history for affinity
        self._task_device_history: Dict[str, str] = {}  # task_type -> preferred_device_id
        
    def start(self) -> None:
        """Start the scheduler"""
        if self._running:
            return
        
        self._running = True
        self._shutdown_event.clear()
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()
        self.logger.info("Task scheduler started")

    def stop(self, timeout: float = 10.0) -> None:
        """Stop the scheduler"""
        if not self._running:
            return
        
        self.logger.info("Stopping task scheduler...")
        self._running = False
        self._shutdown_event.set()
        
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=timeout)
            if self._scheduler_thread.is_alive():
                self.logger.warning("Scheduler thread did not stop within timeout")
            else:
                self.logger.info("Task scheduler stopped")

    def register_device(self, device_id: str, capabilities: Dict[str, Any]) -> None:
        """Register a device with the scheduler"""
        self._devices[device_id] = capabilities.copy()
        self._device_heartbeats[device_id] = datetime.now(timezone.utc)
        self._device_loads[device_id] = 0
        self.logger.info(f"Registered device: {device_id}")

    def unregister_device(self, device_id: str) -> None:
        """Unregister a device"""
        if device_id in self._devices:
            del self._devices[device_id]
        if device_id in self._device_heartbeats:
            del self._device_heartbeats[device_id]
        if device_id in self._device_loads:
            del self._device_loads[device_id]
        self.logger.info(f"Unregistered device: {device_id}")

    def update_device_heartbeat(self, device_id: str, task_count: Optional[int] = None) -> None:
        """Update device heartbeat and optionally task count"""
        if device_id in self._devices:
            self._device_heartbeats[device_id] = datetime.now(timezone.utc)
            if task_count is not None:
                self._device_loads[device_id] = task_count

    def submit_task(self, task: Task) -> str:
        """Submit a task for scheduling"""
        self.task_queue.add_task(task)
        self.logger.info(f"Submitted task {task.task_id} ({task.task_type}) with priority {task.priority.name}")
        return task.task_id

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task"""
        return self.task_queue.cancel_task(task_id)

    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get task status"""
        task = self.task_queue.get_task(task_id)
        return task.status if task else None

    def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """Get task result"""
        task = self.task_queue.get_task(task_id)
        return task.result if task else None

    def get_online_devices(self) -> List[str]:
        """Get list of online devices"""
        current_time = datetime.now(timezone.utc)
        online_devices = []
        
        for device_id, last_heartbeat in self._device_heartbeats.items():
            if (current_time - last_heartbeat).total_seconds() < self.heartbeat_timeout:
                online_devices.append(device_id)
        
        return online_devices

    def get_device_capabilities(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get device capabilities"""
        return self._devices.get(device_id)

    def get_cluster_statistics(self) -> Dict[str, Any]:
        """Get cluster and scheduling statistics"""
        online_devices = self.get_online_devices()
        queue_stats = self.task_queue.get_queue_statistics()
        
        total_capacity = 0
        total_load = 0
        device_stats = {}
        
        for device_id in online_devices:
            capacity = self.max_tasks_per_device
            load = self._device_loads.get(device_id, 0)
            total_capacity += capacity
            total_load += load
            
            device_stats[device_id] = {
                'capacity': capacity,
                'load': load,
                'utilization': (load / capacity) * 100 if capacity > 0 else 0,
                'capabilities': self._devices.get(device_id, {})
            }
        
        return {
            'scheduler_stats': self.stats.copy(),
            'queue_stats': queue_stats,
            'cluster_stats': {
                'online_devices': len(online_devices),
                'total_devices': len(self._devices),
                'total_capacity': total_capacity,
                'total_load': total_load,
                'cluster_utilization': (total_load / total_capacity) * 100 if total_capacity > 0 else 0
            },
            'device_stats': device_stats
        }

    def _scheduler_loop(self) -> None:
        """Main scheduler loop"""
        while self._running and not self._shutdown_event.is_set():
            try:
                self._schedule_tasks()
                self._cleanup_offline_devices()
                self._update_device_loads()
                
                self.stats['scheduler_rounds'] += 1
                self.stats['last_schedule_time'] = datetime.now(timezone.utc).isoformat()
                
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}")
            
            # Sleep for a short interval
            self._shutdown_event.wait(1.0)

    def _schedule_tasks(self) -> None:
        """Schedule pending tasks to available devices"""
        online_devices = self.get_online_devices()
        if not online_devices:
            return
        
        # Get pending tasks
        pending_tasks = self.task_queue.get_tasks_by_status(TaskStatus.QUEUED)
        if not pending_tasks:
            return
        
        # Sort tasks by priority
        pending_tasks.sort(key=lambda t: (-t.priority.value, t.created_at))
        
        for task in pending_tasks:
            best_device = self._find_best_device_for_task(task, online_devices)
            if best_device:
                if self.task_queue.assign_task_to_device(task.task_id, best_device):
                    self.stats['tasks_scheduled'] += 1
                    self.logger.info(f"Scheduled task {task.task_id} to device {best_device}")
                    
                    # Update device affinity
                    if self.device_affinity_enabled:
                        self._task_device_history[task.task_type] = best_device

    def _find_best_device_for_task(self, task: Task, online_devices: List[str]) -> Optional[str]:
        """Find the best device for executing a task"""
        suitable_devices = []
        
        # Filter devices that can handle the task
        for device_id in online_devices:
            if self._can_device_handle_task(device_id, task):
                # Check device load
                current_load = self._device_loads.get(device_id, 0)
                if current_load < self.max_tasks_per_device:
                    suitable_devices.append(device_id)
        
        if not suitable_devices:
            return None
        
        # Apply device affinity if enabled
        if self.device_affinity_enabled and task.task_type in self._task_device_history:
            preferred_device = self._task_device_history[task.task_type]
            if preferred_device in suitable_devices:
                suitable_devices = [preferred_device] + [d for d in suitable_devices if d != preferred_device]
        
        # Apply load balancing if enabled
        if self.load_balancing_enabled and len(suitable_devices) > 1:
            # Sort by current load (ascending)
            suitable_devices.sort(key=lambda d: self._device_loads.get(d, 0))
        
        return suitable_devices[0]

    def _can_device_handle_task(self, device_id: str, task: Task) -> bool:
        """Check if a device can handle a specific task"""
        capabilities = self._devices.get(device_id)
        if not capabilities:
            return False
        
        requirements = task.requirements
        
        # CPU cores check
        if requirements.min_cpu_cores:
            device_cores = capabilities.get('cpu_count', 0)
            if device_cores < requirements.min_cpu_cores:
                return False
        
        # Memory check
        if requirements.min_memory_gb:
            device_memory = capabilities.get('memory_total_gb', 0)
            if device_memory < requirements.min_memory_gb:
                return False
        
        # Storage check
        if requirements.min_storage_gb:
            device_storage = capabilities.get('storage_total_gb', 0)
            if device_storage < requirements.min_storage_gb:
                return False
        
        # Platform check
        if requirements.required_platform:
            device_platform = capabilities.get('platform', '').lower()
            if device_platform != requirements.required_platform.lower():
                return False
        
        # Role check
        if requirements.required_role:
            device_role = capabilities.get('role', '')
            if device_role != requirements.required_role:
                return False
        
        # Tags check
        if requirements.required_tags:
            device_tags = set(capabilities.get('tags', []))
            required_tags = set(requirements.required_tags)
            if not required_tags.issubset(device_tags):
                return False
        
        # GPU check
        if requirements.gpu_required:
            if not capabilities.get('has_gpu', False):
                return False
        
        return True

    def _cleanup_offline_devices(self) -> None:
        """Remove offline devices from consideration"""
        current_time = datetime.now(timezone.utc)
        offline_devices = []
        
        for device_id, last_heartbeat in self._device_heartbeats.items():
            if (current_time - last_heartbeat).total_seconds() > self.heartbeat_timeout:
                offline_devices.append(device_id)
        
        for device_id in offline_devices:
            self.logger.warning(f"Device {device_id} went offline")
            # Note: We don't remove the device entirely, just mark it as offline
            # The device can come back online with a heartbeat

    def _update_device_loads(self) -> None:
        """Update device load information from task queue"""
        for device_id in self._devices:
            running_tasks = self.task_queue.get_tasks_by_device(device_id)
            active_count = len([t for t in running_tasks if t.status in [TaskStatus.ASSIGNED, TaskStatus.RUNNING]])
            self._device_loads[device_id] = active_count