"""
Task definition and management for Retire-Cluster
"""

import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    QUEUED = "queued"
    ASSIGNED = "assigned"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class TaskRequirements:
    """Task execution requirements"""
    min_cpu_cores: Optional[int] = None
    min_memory_gb: Optional[float] = None
    min_storage_gb: Optional[float] = None
    required_platform: Optional[str] = None  # "linux", "windows", "android", etc.
    required_role: Optional[str] = None      # "compute", "mobile", "storage", etc.
    required_tags: Optional[List[str]] = None
    gpu_required: bool = False
    internet_required: bool = False
    timeout_seconds: int = 300
    max_retries: int = 3


@dataclass
class TaskResult:
    """Task execution result"""
    task_id: str
    status: TaskStatus
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None
    execution_time_seconds: Optional[float] = None
    worker_device_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    logs: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['status'] = self.status.value
        
        # Convert datetime objects to ISO format
        for field in ['started_at', 'completed_at']:
            if data[field]:
                data[field] = data[field].isoformat()
        
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskResult':
        """Create from dictionary"""
        data = data.copy()
        data['status'] = TaskStatus(data['status'])
        
        # Convert ISO format back to datetime
        for field in ['started_at', 'completed_at']:
            if data[field]:
                data[field] = datetime.fromisoformat(data[field])
        
        return cls(**data)


class Task:
    """
    Distributed task for execution across the cluster
    """

    def __init__(
        self,
        task_type: str,
        payload: Dict[str, Any],
        task_id: Optional[str] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        requirements: Optional[TaskRequirements] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.task_id = task_id or str(uuid.uuid4())
        self.task_type = task_type
        self.payload = payload
        self.priority = priority
        self.requirements = requirements or TaskRequirements()
        self.metadata = metadata or {}
        
        # Status tracking
        self.status = TaskStatus.PENDING
        self.created_at = datetime.now(timezone.utc)
        self.assigned_device_id: Optional[str] = None
        self.assigned_at: Optional[datetime] = None
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        
        # Execution tracking
        self.retry_count = 0
        self.error_history: List[str] = []
        
        # Result
        self.result: Optional[TaskResult] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for serialization"""
        return {
            'task_id': self.task_id,
            'task_type': self.task_type,
            'payload': self.payload,
            'priority': self.priority.value,
            'requirements': asdict(self.requirements),
            'metadata': self.metadata,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'assigned_device_id': self.assigned_device_id,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'retry_count': self.retry_count,
            'error_history': self.error_history,
            'result': self.result.to_dict() if self.result else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create task from dictionary"""
        # Create requirements object
        requirements_data = data.get('requirements', {})
        requirements = TaskRequirements(**requirements_data)
        
        # Create task
        task = cls(
            task_type=data['task_type'],
            payload=data['payload'],
            task_id=data['task_id'],
            priority=TaskPriority(data['priority']),
            requirements=requirements,
            metadata=data.get('metadata', {})
        )
        
        # Set status tracking
        task.status = TaskStatus(data['status'])
        task.created_at = datetime.fromisoformat(data['created_at'])
        task.assigned_device_id = data.get('assigned_device_id')
        task.retry_count = data.get('retry_count', 0)
        task.error_history = data.get('error_history', [])
        
        # Set timestamps
        if data.get('assigned_at'):
            task.assigned_at = datetime.fromisoformat(data['assigned_at'])
        if data.get('started_at'):
            task.started_at = datetime.fromisoformat(data['started_at'])
        if data.get('completed_at'):
            task.completed_at = datetime.fromisoformat(data['completed_at'])
        
        # Set result
        if data.get('result'):
            task.result = TaskResult.from_dict(data['result'])
        
        return task

    def to_json(self) -> str:
        """Convert task to JSON string"""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'Task':
        """Create task from JSON string"""
        return cls.from_dict(json.loads(json_str))

    def assign_to_device(self, device_id: str) -> None:
        """Assign task to a specific device"""
        self.assigned_device_id = device_id
        self.assigned_at = datetime.now(timezone.utc)
        self.status = TaskStatus.ASSIGNED

    def start_execution(self) -> None:
        """Mark task as started"""
        self.started_at = datetime.now(timezone.utc)
        self.status = TaskStatus.RUNNING

    def complete_success(self, result: TaskResult) -> None:
        """Mark task as successfully completed"""
        self.completed_at = datetime.now(timezone.utc)
        self.status = TaskStatus.SUCCESS
        self.result = result

    def complete_failure(self, result: TaskResult) -> None:
        """Mark task as failed"""
        self.completed_at = datetime.now(timezone.utc)
        self.status = TaskStatus.FAILED
        self.result = result
        self.retry_count += 1
        
        if result.error_message:
            self.error_history.append(result.error_message)

    def can_retry(self) -> bool:
        """Check if task can be retried"""
        return (
            self.status == TaskStatus.FAILED and
            self.retry_count < self.requirements.max_retries
        )

    def reset_for_retry(self) -> None:
        """Reset task for retry"""
        if not self.can_retry():
            raise ValueError("Task cannot be retried")
        
        self.status = TaskStatus.PENDING
        self.assigned_device_id = None
        self.assigned_at = None
        self.started_at = None
        self.completed_at = None
        self.result = None

    def cancel(self) -> None:
        """Cancel the task"""
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.now(timezone.utc)

    def is_terminal_status(self) -> bool:
        """Check if task is in a terminal status"""
        return self.status in [
            TaskStatus.SUCCESS,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.TIMEOUT
        ]

    def get_execution_time(self) -> Optional[float]:
        """Get task execution time in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def __str__(self) -> str:
        return f"Task({self.task_id}, {self.task_type}, {self.status.value})"

    def __repr__(self) -> str:
        return (
            f"Task(task_id='{self.task_id}', task_type='{self.task_type}', "
            f"status={self.status.value}, priority={self.priority.value})"
        )