"""
Task queue management for distributed task execution
"""

import heapq
import threading
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Callable, Any
from collections import defaultdict

from .task import Task, TaskStatus, TaskPriority


class TaskQueue:
    """
    Thread-safe task queue with priority support and device targeting
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        self._priority_queue: List[tuple] = []  # (priority, timestamp, task)
        self._tasks: Dict[str, Task] = {}  # task_id -> Task
        self._device_assignments: Dict[str, str] = {}  # task_id -> device_id
        self._device_queues: Dict[str, Set[str]] = defaultdict(set)  # device_id -> set of task_ids
        self._listeners: List[Callable[[str, Task], None]] = []  # Event listeners
        self._counter = 0  # For unique timestamps

    def add_task(self, task: Task) -> None:
        """Add a task to the queue"""
        with self._lock:
            if task.task_id in self._tasks:
                raise ValueError(f"Task {task.task_id} already exists in queue")
            
            # Add to storage
            self._tasks[task.task_id] = task
            
            # Add to priority queue if not assigned to a specific device
            if task.status == TaskStatus.PENDING:
                priority_value = -task.priority.value  # Negative for max-heap behavior
                timestamp = self._counter
                self._counter += 1
                heapq.heappush(self._priority_queue, (priority_value, timestamp, task.task_id))
                task.status = TaskStatus.QUEUED
            
            self._notify_listeners('task_added', task)

    def get_next_task(self, device_id: str, device_capabilities: Dict[str, Any]) -> Optional[Task]:
        """Get the next suitable task for a device"""
        with self._lock:
            # First check device-specific assignments
            if device_id in self._device_queues:
                for task_id in list(self._device_queues[device_id]):
                    task = self._tasks.get(task_id)
                    if task and task.status == TaskStatus.QUEUED:
                        self._device_queues[device_id].remove(task_id)
                        task.assign_to_device(device_id)
                        self._device_assignments[task_id] = device_id
                        self._notify_listeners('task_assigned', task)
                        return task
            
            # Then check general priority queue
            while self._priority_queue:
                priority, timestamp, task_id = heapq.heappop(self._priority_queue)
                task = self._tasks.get(task_id)
                
                if not task or task.status != TaskStatus.QUEUED:
                    continue
                
                # Check if device meets task requirements
                if self._device_meets_requirements(device_capabilities, task.requirements):
                    task.assign_to_device(device_id)
                    self._device_assignments[task_id] = device_id
                    self._notify_listeners('task_assigned', task)
                    return task
                else:
                    # Put task back if device doesn't meet requirements
                    heapq.heappush(self._priority_queue, (priority, timestamp, task_id))
                    break
            
            return None

    def assign_task_to_device(self, task_id: str, device_id: str) -> bool:
        """Assign a specific task to a specific device"""
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            
            if task.status != TaskStatus.QUEUED:
                return False
            
            # Remove from priority queue if present
            self._remove_from_priority_queue(task_id)
            
            # Add to device-specific queue
            self._device_queues[device_id].add(task_id)
            task.status = TaskStatus.QUEUED  # Keep queued until device picks it up
            
            return True

    def update_task_status(self, task_id: str, status: TaskStatus, result_data: Optional[Dict] = None) -> bool:
        """Update task status"""
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            
            old_status = task.status
            task.status = status
            
            if status == TaskStatus.RUNNING:
                task.start_execution()
            elif status in [TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.CANCELLED, TaskStatus.TIMEOUT]:
                task.completed_at = datetime.now(timezone.utc)
                
                # Clean up assignments
                if task_id in self._device_assignments:
                    device_id = self._device_assignments[task_id]
                    if device_id in self._device_queues:
                        self._device_queues[device_id].discard(task_id)
                    del self._device_assignments[task_id]
            
            self._notify_listeners('task_status_changed', task)
            return True

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        with self._lock:
            return self._tasks.get(task_id)

    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """Get all tasks with a specific status"""
        with self._lock:
            return [task for task in self._tasks.values() if task.status == status]

    def get_tasks_by_device(self, device_id: str) -> List[Task]:
        """Get all tasks assigned to a device"""
        with self._lock:
            return [
                self._tasks[task_id] 
                for task_id in self._device_assignments 
                if self._device_assignments[task_id] == device_id and task_id in self._tasks
            ]

    def get_pending_tasks_count(self) -> int:
        """Get number of pending/queued tasks"""
        with self._lock:
            return len([t for t in self._tasks.values() if t.status in [TaskStatus.PENDING, TaskStatus.QUEUED]])

    def get_running_tasks_count(self) -> int:
        """Get number of running tasks"""
        with self._lock:
            return len([t for t in self._tasks.values() if t.status == TaskStatus.RUNNING])

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task"""
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            
            if task.is_terminal_status():
                return False
            
            # Remove from queues
            self._remove_from_priority_queue(task_id)
            if task_id in self._device_assignments:
                device_id = self._device_assignments[task_id]
                if device_id in self._device_queues:
                    self._device_queues[device_id].discard(task_id)
                del self._device_assignments[task_id]
            
            task.cancel()
            self._notify_listeners('task_cancelled', task)
            return True

    def retry_failed_task(self, task_id: str) -> bool:
        """Retry a failed task"""
        with self._lock:
            task = self._tasks.get(task_id)
            if not task or not task.can_retry():
                return False
            
            task.reset_for_retry()
            
            # Add back to priority queue
            priority_value = -task.priority.value
            timestamp = self._counter
            self._counter += 1
            heapq.heappush(self._priority_queue, (priority_value, timestamp, task.task_id))
            task.status = TaskStatus.QUEUED
            
            self._notify_listeners('task_retried', task)
            return True

    def cleanup_completed_tasks(self, max_age_seconds: int = 3600) -> int:
        """Remove completed tasks older than max_age_seconds"""
        with self._lock:
            current_time = datetime.now(timezone.utc)
            removed_count = 0
            
            tasks_to_remove = []
            for task_id, task in self._tasks.items():
                if (task.is_terminal_status() and 
                    task.completed_at and 
                    (current_time - task.completed_at).total_seconds() > max_age_seconds):
                    tasks_to_remove.append(task_id)
            
            for task_id in tasks_to_remove:
                del self._tasks[task_id]
                if task_id in self._device_assignments:
                    del self._device_assignments[task_id]
                removed_count += 1
            
            return removed_count

    def get_queue_statistics(self) -> Dict[str, Any]:
        """Get queue statistics"""
        with self._lock:
            status_counts = defaultdict(int)
            priority_counts = defaultdict(int)
            device_counts = defaultdict(int)
            
            for task in self._tasks.values():
                status_counts[task.status.value] += 1
                priority_counts[task.priority.value] += 1
                if task.assigned_device_id:
                    device_counts[task.assigned_device_id] += 1
            
            return {
                'total_tasks': len(self._tasks),
                'by_status': dict(status_counts),
                'by_priority': dict(priority_counts),
                'by_device': dict(device_counts),
                'priority_queue_size': len(self._priority_queue),
                'device_queues': {k: len(v) for k, v in self._device_queues.items()}
            }

    def add_listener(self, listener: Callable[[str, Task], None]) -> None:
        """Add event listener"""
        with self._lock:
            self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[str, Task], None]) -> None:
        """Remove event listener"""
        with self._lock:
            if listener in self._listeners:
                self._listeners.remove(listener)

    def _notify_listeners(self, event_type: str, task: Task) -> None:
        """Notify all listeners of an event"""
        for listener in self._listeners:
            try:
                listener(event_type, task)
            except Exception:
                # Continue notifying other listeners even if one fails
                pass

    def _remove_from_priority_queue(self, task_id: str) -> None:
        """Remove task from priority queue (mark as removed)"""
        # Note: We don't actually remove from heapq here as it's expensive
        # Instead, we check task status when popping from queue
        pass

    def _device_meets_requirements(self, capabilities: Dict[str, Any], requirements) -> bool:
        """Check if device capabilities meet task requirements"""
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