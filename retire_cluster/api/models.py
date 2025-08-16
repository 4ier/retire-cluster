"""
API response models and data structures
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum


class ResponseStatus(Enum):
    """API response status"""
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"


@dataclass
class APIResponse:
    """Standard API response format"""
    status: ResponseStatus
    data: Optional[Any] = None
    message: Optional[str] = None
    timestamp: Optional[str] = None
    request_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {
            'status': self.status.value,
            'timestamp': self.timestamp,
            'data': self.data
        }
        
        if self.message:
            result['message'] = self.message
        if self.request_id:
            result['request_id'] = self.request_id
            
        return result


@dataclass 
class ErrorResponse(APIResponse):
    """Error response format"""
    error_code: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        super().__post_init__()
        self.status = ResponseStatus.ERROR
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        
        if self.error_code:
            result['error_code'] = self.error_code
        if self.error_details:
            result['error_details'] = self.error_details
            
        return result


@dataclass
class PaginatedResponse(APIResponse):
    """Paginated response format"""
    page: int = 1
    page_size: int = 20
    total_items: int = 0
    total_pages: int = 0
    has_next: bool = False
    has_previous: bool = False
    
    def __post_init__(self):
        super().__post_init__()
        if self.total_items > 0 and self.page_size > 0:
            self.total_pages = (self.total_items + self.page_size - 1) // self.page_size
            self.has_next = self.page < self.total_pages
            self.has_previous = self.page > 1
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result['pagination'] = {
            'page': self.page,
            'page_size': self.page_size,
            'total_items': self.total_items,
            'total_pages': self.total_pages,
            'has_next': self.has_next,
            'has_previous': self.has_previous
        }
        return result


@dataclass
class DeviceInfo:
    """Device information model"""
    device_id: str
    role: str
    platform: str
    status: str
    ip_address: Optional[str] = None
    last_heartbeat: Optional[str] = None
    capabilities: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    uptime: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ClusterStats:
    """Cluster statistics model"""
    total_devices: int
    online_devices: int
    offline_devices: int
    health_percentage: float
    total_resources: Dict[str, Any]
    by_role: Dict[str, int]
    by_platform: Dict[str, int]
    by_status: Dict[str, int]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TaskInfo:
    """Task information model"""
    task_id: str
    task_type: str
    status: str
    priority: str
    created_at: str
    assigned_device_id: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    execution_time_seconds: Optional[float] = None
    worker_device_id: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TaskSubmissionRequest:
    """Task submission request model"""
    task_type: str
    payload: Dict[str, Any]
    priority: str = "normal"
    requirements: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ConfigUpdate:
    """Configuration update model"""
    section: str
    key: str
    value: Any
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Request validation schemas
TASK_SUBMISSION_SCHEMA = {
    "type": "object",
    "required": ["task_type", "payload"],
    "properties": {
        "task_type": {
            "type": "string",
            "minLength": 1,
            "maxLength": 100
        },
        "payload": {
            "type": "object"
        },
        "priority": {
            "type": "string",
            "enum": ["low", "normal", "high", "urgent"]
        },
        "requirements": {
            "type": "object",
            "properties": {
                "min_cpu_cores": {"type": "integer", "minimum": 1},
                "min_memory_gb": {"type": "number", "minimum": 0.1},
                "min_storage_gb": {"type": "number", "minimum": 0.1},
                "required_platform": {"type": "string"},
                "required_role": {"type": "string"},
                "required_tags": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "gpu_required": {"type": "boolean"},
                "internet_required": {"type": "boolean"},
                "timeout_seconds": {"type": "integer", "minimum": 1, "maximum": 3600},
                "max_retries": {"type": "integer", "minimum": 0, "maximum": 10}
            }
        },
        "metadata": {"type": "object"}
    }
}

DEVICE_FILTER_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["online", "offline", "all"]
        },
        "role": {"type": "string"},
        "platform": {"type": "string"},
        "tags": {
            "type": "array",
            "items": {"type": "string"}
        }
    }
}

TASK_FILTER_SCHEMA = {
    "type": "object", 
    "properties": {
        "status": {
            "type": "string",
            "enum": ["pending", "queued", "assigned", "running", "success", "failed", "cancelled", "timeout"]
        },
        "task_type": {"type": "string"},
        "priority": {
            "type": "string",
            "enum": ["low", "normal", "high", "urgent"]
        },
        "device_id": {"type": "string"},
        "created_after": {"type": "string", "format": "date-time"},
        "created_before": {"type": "string", "format": "date-time"}
    }
}