"""
Communication protocol definitions
"""

import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

from ..core.exceptions import NetworkError


class MessageType(Enum):
    """Message types for cluster communication"""
    REGISTER = "register"
    HEARTBEAT = "heartbeat"
    STATUS = "status"
    LIST_DEVICES = "list_devices"
    DEVICE_INFO = "device_info"
    TASK_ASSIGN = "task_assign"
    TASK_RESULT = "task_result"
    TASK_STATUS = "task_status"
    TASK_CANCEL = "task_cancel"
    TASK_REQUEST = "task_request"
    TASK_SUBMIT = "task_submit"
    ERROR = "error"
    ACK = "ack"


@dataclass
class Message:
    """Standard message format for cluster communication"""
    message_type: MessageType
    sender_id: str
    receiver_id: Optional[str] = None
    message_id: Optional[str] = None
    timestamp: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.message_id is None:
            self.message_id = str(uuid.uuid4())
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if self.data is None:
            self.data = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            'message_type': self.message_type.value,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'message_id': self.message_id,
            'timestamp': self.timestamp,
            'data': self.data
        }
    
    def to_json(self) -> str:
        """Convert message to JSON string"""
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary"""
        try:
            message_type = MessageType(data['message_type'])
            return cls(
                message_type=message_type,
                sender_id=data['sender_id'],
                receiver_id=data.get('receiver_id'),
                message_id=data.get('message_id'),
                timestamp=data.get('timestamp'),
                data=data.get('data', {})
            )
        except (KeyError, ValueError) as e:
            raise NetworkError(f"Invalid message format: {e}")
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """Create message from JSON string"""
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            raise NetworkError(f"Invalid JSON message: {e}")


def create_register_message(sender_id: str, device_data: Dict[str, Any]) -> Message:
    """Create device registration message"""
    return Message(
        message_type=MessageType.REGISTER,
        sender_id=sender_id,
        data=device_data
    )


def create_heartbeat_message(sender_id: str, metrics: Dict[str, Any]) -> Message:
    """Create heartbeat message"""
    return Message(
        message_type=MessageType.HEARTBEAT,
        sender_id=sender_id,
        data={'metrics': metrics}
    )


def create_status_message(sender_id: str, filters: Optional[Dict[str, Any]] = None) -> Message:
    """Create status request message"""
    return Message(
        message_type=MessageType.STATUS,
        sender_id=sender_id,
        data=filters or {}
    )


def create_error_message(sender_id: str, error: str, original_message_id: Optional[str] = None) -> Message:
    """Create error response message"""
    data = {'error': error}
    if original_message_id:
        data['original_message_id'] = original_message_id
    
    return Message(
        message_type=MessageType.ERROR,
        sender_id=sender_id,
        data=data
    )


def create_ack_message(sender_id: str, original_message_id: str, result: Optional[Dict[str, Any]] = None) -> Message:
    """Create acknowledgment message"""
    data = {'original_message_id': original_message_id}
    if result:
        data['result'] = result
    
    return Message(
        message_type=MessageType.ACK,
        sender_id=sender_id,
        data=data
    )


def create_task_submit_message(sender_id: str, task_data: Dict[str, Any]) -> Message:
    """Create task submission message"""
    return Message(
        message_type=MessageType.TASK_SUBMIT,
        sender_id=sender_id,
        data={'task': task_data}
    )


def create_task_assign_message(sender_id: str, receiver_id: str, task_data: Dict[str, Any]) -> Message:
    """Create task assignment message"""
    return Message(
        message_type=MessageType.TASK_ASSIGN,
        sender_id=sender_id,
        receiver_id=receiver_id,
        data={'task': task_data}
    )


def create_task_result_message(sender_id: str, task_result: Dict[str, Any]) -> Message:
    """Create task result message"""
    return Message(
        message_type=MessageType.TASK_RESULT,
        sender_id=sender_id,
        data={'result': task_result}
    )


def create_task_status_message(sender_id: str, task_id: str) -> Message:
    """Create task status query message"""
    return Message(
        message_type=MessageType.TASK_STATUS,
        sender_id=sender_id,
        data={'task_id': task_id}
    )


def create_task_cancel_message(sender_id: str, task_id: str, receiver_id: Optional[str] = None) -> Message:
    """Create task cancellation message"""
    return Message(
        message_type=MessageType.TASK_CANCEL,
        sender_id=sender_id,
        receiver_id=receiver_id,
        data={'task_id': task_id}
    )


def create_task_request_message(sender_id: str, capabilities: Dict[str, Any]) -> Message:
    """Create task request message (worker requesting tasks)"""
    return Message(
        message_type=MessageType.TASK_REQUEST,
        sender_id=sender_id,
        data={'capabilities': capabilities}
    )