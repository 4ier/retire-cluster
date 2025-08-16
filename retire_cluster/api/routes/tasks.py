"""
Task management API routes
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

try:
    from flask import Blueprint, request, jsonify, g
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    class Blueprint:
        def __init__(self, *args, **kwargs):
            pass
        def route(self, *args, **kwargs):
            def decorator(f):
                return f
            return decorator

from ..models import (
    APIResponse, ErrorResponse, PaginatedResponse, TaskInfo, TaskSubmissionRequest,
    ResponseStatus, TASK_SUBMISSION_SCHEMA, TASK_FILTER_SCHEMA
)
from ..middleware import LoggingMiddleware, AuthMiddleware, ValidationMiddleware
from ...tasks import Task, TaskStatus, TaskPriority, TaskRequirements


class TaskRoutes:
    """Task management API routes"""
    
    def __init__(self, task_scheduler):
        self.task_scheduler = task_scheduler
        self.logger = logging.getLogger("api.tasks")
        
        # Create blueprint
        self.blueprint = Blueprint('tasks', __name__, url_prefix='/api/v1/tasks')
        
        # Middleware
        self.auth = AuthMiddleware()
        self.logging = LoggingMiddleware()
        self.validation = ValidationMiddleware()
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self):
        """Register all task routes"""
        
        @self.blueprint.route('', methods=['POST'])
        @self.validation.validate_json(TASK_SUBMISSION_SCHEMA)
        @self.logging
        def submit_task():
            """Submit a new task for execution"""
            try:
                data = request.get_json()
                
                # Parse task requirements
                requirements_data = data.get('requirements', {})
                requirements = TaskRequirements(
                    min_cpu_cores=requirements_data.get('min_cpu_cores'),
                    min_memory_gb=requirements_data.get('min_memory_gb'),
                    min_storage_gb=requirements_data.get('min_storage_gb'),
                    required_platform=requirements_data.get('required_platform'),
                    required_role=requirements_data.get('required_role'),
                    required_tags=requirements_data.get('required_tags'),
                    gpu_required=requirements_data.get('gpu_required', False),
                    internet_required=requirements_data.get('internet_required', False),
                    timeout_seconds=requirements_data.get('timeout_seconds', 300),
                    max_retries=requirements_data.get('max_retries', 3)
                )
                
                # Parse priority
                priority_str = data.get('priority', 'normal').upper()
                try:
                    priority = TaskPriority[priority_str]
                except KeyError:
                    priority = TaskPriority.NORMAL
                
                # Create task
                task = Task(
                    task_type=data['task_type'],
                    payload=data['payload'],
                    priority=priority,
                    requirements=requirements,
                    metadata=data.get('metadata', {})
                )
                
                # Submit to scheduler
                task_id = self.task_scheduler.submit_task(task)
                
                # Convert task to API format
                task_info = self._task_to_api_format(task)
                
                response = APIResponse(
                    status=ResponseStatus.SUCCESS,
                    data={
                        'task_id': task_id,
                        'task': task_info,
                        'submitted_at': datetime.now().isoformat()
                    },
                    message="Task submitted successfully",
                    request_id=getattr(g, 'request_id', None)
                )
                
                return jsonify(response.to_dict()), 201
                
            except Exception as e:
                self.logger.error(f"Error submitting task: {e}")
                error_response = ErrorResponse(
                    message="Failed to submit task",
                    error_code="TASK_SUBMISSION_ERROR",
                    error_details={'error': str(e)},
                    request_id=getattr(g, 'request_id', None)
                )
                return jsonify(error_response.to_dict()), 500
        
        @self.blueprint.route('', methods=['GET'])
        @self.logging
        def list_tasks():
            """List tasks with optional filtering and pagination"""
            try:
                # Parse query parameters
                page = int(request.args.get('page', 1))
                page_size = min(int(request.args.get('page_size', 20)), 100)
                status_filter = request.args.get('status')
                task_type_filter = request.args.get('task_type')
                priority_filter = request.args.get('priority')
                device_id_filter = request.args.get('device_id')
                
                # Get tasks from scheduler
                if status_filter:
                    try:
                        status_enum = TaskStatus[status_filter.upper()]
                        tasks = self.task_scheduler.task_queue.get_tasks_by_status(status_enum)
                    except KeyError:
                        error_response = ErrorResponse(
                            message=f"Invalid status filter: {status_filter}",
                            error_code="INVALID_STATUS_FILTER",
                            request_id=getattr(g, 'request_id', None)
                        )
                        return jsonify(error_response.to_dict()), 400
                else:
                    # Get all tasks
                    tasks = list(self.task_scheduler.task_queue._tasks.values())
                
                # Apply additional filters
                filtered_tasks = self._filter_tasks(
                    tasks, task_type_filter, priority_filter, device_id_filter
                )
                
                # Sort by creation time (newest first)
                filtered_tasks.sort(key=lambda t: t.created_at, reverse=True)
                
                # Apply pagination
                total_items = len(filtered_tasks)
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                paginated_tasks = filtered_tasks[start_idx:end_idx]
                
                # Convert to API format
                task_infos = [self._task_to_api_format(task) for task in paginated_tasks]
                
                response = PaginatedResponse(
                    status=ResponseStatus.SUCCESS,
                    data=task_infos,
                    page=page,
                    page_size=page_size,
                    total_items=total_items,
                    request_id=getattr(g, 'request_id', None)
                )
                
                return jsonify(response.to_dict())
                
            except ValueError as e:
                error_response = ErrorResponse(
                    message=f"Invalid query parameter: {str(e)}",
                    error_code="INVALID_PARAMETER",
                    request_id=getattr(g, 'request_id', None)
                )
                return jsonify(error_response.to_dict()), 400
                
            except Exception as e:
                self.logger.error(f"Error listing tasks: {e}")
                error_response = ErrorResponse(
                    message="Failed to list tasks",
                    error_code="LIST_TASKS_ERROR",
                    error_details={'error': str(e)},
                    request_id=getattr(g, 'request_id', None)
                )
                return jsonify(error_response.to_dict()), 500
        
        @self.blueprint.route('/<task_id>', methods=['GET'])
        @self.logging
        def get_task(task_id: str):
            """Get detailed information about a specific task"""
            try:
                task = self.task_scheduler.task_queue.get_task(task_id)
                
                if not task:
                    error_response = ErrorResponse(
                        message=f"Task '{task_id}' not found",
                        error_code="TASK_NOT_FOUND",
                        request_id=getattr(g, 'request_id', None)
                    )
                    return jsonify(error_response.to_dict()), 404
                
                # Convert to detailed API format
                task_info = self._task_to_api_format(task, detailed=True)
                
                response = APIResponse(
                    status=ResponseStatus.SUCCESS,
                    data=task_info,
                    request_id=getattr(g, 'request_id', None)
                )
                
                return jsonify(response.to_dict())
                
            except Exception as e:
                self.logger.error(f"Error getting task {task_id}: {e}")
                error_response = ErrorResponse(
                    message=f"Failed to get task '{task_id}'",
                    error_code="GET_TASK_ERROR",
                    error_details={'error': str(e)},
                    request_id=getattr(g, 'request_id', None)
                )
                return jsonify(error_response.to_dict()), 500
        
        @self.blueprint.route('/<task_id>/status', methods=['GET'])
        @self.logging
        def get_task_status(task_id: str):
            """Get current status of a specific task"""
            try:
                task = self.task_scheduler.task_queue.get_task(task_id)
                
                if not task:
                    error_response = ErrorResponse(
                        message=f"Task '{task_id}' not found",
                        error_code="TASK_NOT_FOUND",
                        request_id=getattr(g, 'request_id', None)
                    )
                    return jsonify(error_response.to_dict()), 404
                
                status_info = {
                    'task_id': task_id,
                    'status': task.status.value,
                    'created_at': task.created_at.isoformat(),
                    'assigned_device_id': task.assigned_device_id,
                    'assigned_at': task.assigned_at.isoformat() if task.assigned_at else None,
                    'started_at': task.started_at.isoformat() if task.started_at else None,
                    'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                    'execution_time_seconds': task.get_execution_time(),
                    'retry_count': task.retry_count,
                    'is_terminal': task.is_terminal_status(),
                    'can_retry': task.can_retry(),
                    'timestamp': datetime.now().isoformat()
                }
                
                response = APIResponse(
                    status=ResponseStatus.SUCCESS,
                    data=status_info,
                    request_id=getattr(g, 'request_id', None)
                )
                
                return jsonify(response.to_dict())
                
            except Exception as e:
                self.logger.error(f"Error getting task status {task_id}: {e}")
                error_response = ErrorResponse(
                    message=f"Failed to get task status for '{task_id}'",
                    error_code="GET_TASK_STATUS_ERROR",
                    error_details={'error': str(e)},
                    request_id=getattr(g, 'request_id', None)
                )
                return jsonify(error_response.to_dict()), 500
        
        @self.blueprint.route('/<task_id>/result', methods=['GET'])
        @self.logging
        def get_task_result(task_id: str):
            """Get result of a completed task"""
            try:
                task = self.task_scheduler.task_queue.get_task(task_id)
                
                if not task:
                    error_response = ErrorResponse(
                        message=f"Task '{task_id}' not found",
                        error_code="TASK_NOT_FOUND",
                        request_id=getattr(g, 'request_id', None)
                    )
                    return jsonify(error_response.to_dict()), 404
                
                if not task.result:
                    error_response = ErrorResponse(
                        message=f"Task '{task_id}' has no result yet",
                        error_code="NO_TASK_RESULT",
                        request_id=getattr(g, 'request_id', None)
                    )
                    return jsonify(error_response.to_dict()), 404
                
                result_info = {
                    'task_id': task_id,
                    'status': task.result.status.value,
                    'result_data': task.result.result_data,
                    'error_message': task.result.error_message,
                    'error_traceback': task.result.error_traceback,
                    'execution_time_seconds': task.result.execution_time_seconds,
                    'worker_device_id': task.result.worker_device_id,
                    'started_at': task.result.started_at.isoformat() if task.result.started_at else None,
                    'completed_at': task.result.completed_at.isoformat() if task.result.completed_at else None,
                    'logs': task.result.logs
                }
                
                response = APIResponse(
                    status=ResponseStatus.SUCCESS,
                    data=result_info,
                    request_id=getattr(g, 'request_id', None)
                )
                
                return jsonify(response.to_dict())
                
            except Exception as e:
                self.logger.error(f"Error getting task result {task_id}: {e}")
                error_response = ErrorResponse(
                    message=f"Failed to get task result for '{task_id}'",
                    error_code="GET_TASK_RESULT_ERROR",
                    error_details={'error': str(e)},
                    request_id=getattr(g, 'request_id', None)
                )
                return jsonify(error_response.to_dict()), 500
        
        @self.blueprint.route('/<task_id>/cancel', methods=['POST'])
        @self.auth
        @self.logging
        def cancel_task(task_id: str):
            """Cancel a running or queued task"""
            try:
                success = self.task_scheduler.cancel_task(task_id)
                
                if not success:
                    error_response = ErrorResponse(
                        message=f"Cannot cancel task '{task_id}' - task not found or already completed",
                        error_code="CANNOT_CANCEL_TASK",
                        request_id=getattr(g, 'request_id', None)
                    )
                    return jsonify(error_response.to_dict()), 400
                
                cancellation_info = {
                    'task_id': task_id,
                    'cancelled_at': datetime.now().isoformat(),
                    'cancelled_by': 'api_request'
                }
                
                response = APIResponse(
                    status=ResponseStatus.SUCCESS,
                    data=cancellation_info,
                    message=f"Task '{task_id}' cancelled successfully",
                    request_id=getattr(g, 'request_id', None)
                )
                
                return jsonify(response.to_dict())
                
            except Exception as e:
                self.logger.error(f"Error cancelling task {task_id}: {e}")
                error_response = ErrorResponse(
                    message=f"Failed to cancel task '{task_id}'",
                    error_code="CANCEL_TASK_ERROR",
                    error_details={'error': str(e)},
                    request_id=getattr(g, 'request_id', None)
                )
                return jsonify(error_response.to_dict()), 500
        
        @self.blueprint.route('/<task_id>/retry', methods=['POST'])
        @self.auth
        @self.logging
        def retry_task(task_id: str):
            """Retry a failed task"""
            try:
                success = self.task_scheduler.task_queue.retry_failed_task(task_id)
                
                if not success:
                    error_response = ErrorResponse(
                        message=f"Cannot retry task '{task_id}' - task not found, not failed, or max retries exceeded",
                        error_code="CANNOT_RETRY_TASK",
                        request_id=getattr(g, 'request_id', None)
                    )
                    return jsonify(error_response.to_dict()), 400
                
                retry_info = {
                    'task_id': task_id,
                    'retried_at': datetime.now().isoformat(),
                    'retried_by': 'api_request'
                }
                
                response = APIResponse(
                    status=ResponseStatus.SUCCESS,
                    data=retry_info,
                    message=f"Task '{task_id}' queued for retry",
                    request_id=getattr(g, 'request_id', None)
                )
                
                return jsonify(response.to_dict())
                
            except Exception as e:
                self.logger.error(f"Error retrying task {task_id}: {e}")
                error_response = ErrorResponse(
                    message=f"Failed to retry task '{task_id}'",
                    error_code="RETRY_TASK_ERROR",
                    error_details={'error': str(e)},
                    request_id=getattr(g, 'request_id', None)
                )
                return jsonify(error_response.to_dict()), 500
        
        @self.blueprint.route('/statistics', methods=['GET'])
        @self.logging
        def get_task_statistics():
            """Get task execution statistics"""
            try:
                stats = self.task_scheduler.task_queue.get_queue_statistics()
                
                # Add additional computed statistics
                enhanced_stats = {
                    'queue_stats': stats,
                    'performance_metrics': {
                        'success_rate': self._calculate_success_rate(stats),
                        'average_execution_time': self._calculate_average_execution_time(),
                        'tasks_per_hour': self._calculate_tasks_per_hour(),
                        'device_utilization': self._calculate_device_utilization()
                    },
                    'current_load': {
                        'pending_tasks': stats['by_status'].get('pending', 0) + stats['by_status'].get('queued', 0),
                        'running_tasks': stats['by_status'].get('running', 0),
                        'capacity_utilization': self._calculate_capacity_utilization()
                    },
                    'timestamp': datetime.now().isoformat()
                }
                
                response = APIResponse(
                    status=ResponseStatus.SUCCESS,
                    data=enhanced_stats,
                    request_id=getattr(g, 'request_id', None)
                )
                
                return jsonify(response.to_dict())
                
            except Exception as e:
                self.logger.error(f"Error getting task statistics: {e}")
                error_response = ErrorResponse(
                    message="Failed to get task statistics",
                    error_code="TASK_STATISTICS_ERROR",
                    error_details={'error': str(e)},
                    request_id=getattr(g, 'request_id', None)
                )
                return jsonify(error_response.to_dict()), 500
        
        @self.blueprint.route('/types', methods=['GET'])
        @self.logging
        def get_supported_task_types():
            """Get list of supported task types"""
            try:
                # Get supported task types from devices
                online_devices = self.task_scheduler.get_online_devices()
                supported_types = set()
                
                for device_id in online_devices:
                    capabilities = self.task_scheduler.get_device_capabilities(device_id)
                    if capabilities and 'supported_task_types' in capabilities:
                        supported_types.update(capabilities['supported_task_types'])
                
                # Add built-in task types
                builtin_types = ['echo', 'sleep', 'system_info', 'python_eval', 'http_request', 'command']
                supported_types.update(builtin_types)
                
                task_types_info = {
                    'supported_types': sorted(list(supported_types)),
                    'builtin_types': builtin_types,
                    'custom_types': sorted(list(supported_types - set(builtin_types))),
                    'total_count': len(supported_types),
                    'online_devices': len(online_devices)
                }
                
                response = APIResponse(
                    status=ResponseStatus.SUCCESS,
                    data=task_types_info,
                    request_id=getattr(g, 'request_id', None)
                )
                
                return jsonify(response.to_dict())
                
            except Exception as e:
                self.logger.error(f"Error getting supported task types: {e}")
                error_response = ErrorResponse(
                    message="Failed to get supported task types",
                    error_code="TASK_TYPES_ERROR",
                    error_details={'error': str(e)},
                    request_id=getattr(g, 'request_id', None)
                )
                return jsonify(error_response.to_dict()), 500
    
    def _task_to_api_format(self, task: Task, detailed: bool = False) -> Dict[str, Any]:
        """Convert task object to API format"""
        task_info = {
            'task_id': task.task_id,
            'task_type': task.task_type,
            'status': task.status.value,
            'priority': task.priority.name.lower(),
            'created_at': task.created_at.isoformat(),
            'assigned_device_id': task.assigned_device_id,
            'assigned_at': task.assigned_at.isoformat() if task.assigned_at else None,
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'execution_time_seconds': task.get_execution_time(),
            'retry_count': task.retry_count
        }
        
        if detailed:
            task_info.update({
                'payload': task.payload,
                'requirements': {
                    'min_cpu_cores': task.requirements.min_cpu_cores,
                    'min_memory_gb': task.requirements.min_memory_gb,
                    'min_storage_gb': task.requirements.min_storage_gb,
                    'required_platform': task.requirements.required_platform,
                    'required_role': task.requirements.required_role,
                    'required_tags': task.requirements.required_tags,
                    'gpu_required': task.requirements.gpu_required,
                    'internet_required': task.requirements.internet_required,
                    'timeout_seconds': task.requirements.timeout_seconds,
                    'max_retries': task.requirements.max_retries
                },
                'metadata': task.metadata,
                'error_history': task.error_history,
                'result': task.result.to_dict() if task.result else None
            })
        
        return task_info
    
    def _filter_tasks(self, tasks: List[Task], task_type_filter: Optional[str], 
                     priority_filter: Optional[str], device_id_filter: Optional[str]) -> List[Task]:
        """Filter tasks based on criteria"""
        filtered = tasks
        
        if task_type_filter:
            filtered = [t for t in filtered if t.task_type == task_type_filter]
        
        if priority_filter:
            try:
                priority_enum = TaskPriority[priority_filter.upper()]
                filtered = [t for t in filtered if t.priority == priority_enum]
            except KeyError:
                pass  # Invalid priority filter, ignore
        
        if device_id_filter:
            filtered = [t for t in filtered if t.assigned_device_id == device_id_filter]
        
        return filtered
    
    def _calculate_success_rate(self, stats: Dict[str, Any]) -> float:
        """Calculate task success rate"""
        total_completed = stats['by_status'].get('success', 0) + stats['by_status'].get('failed', 0)
        if total_completed == 0:
            return 0.0
        return (stats['by_status'].get('success', 0) / total_completed) * 100
    
    def _calculate_average_execution_time(self) -> float:
        """Calculate average task execution time"""
        # This would require tracking execution times in the scheduler
        return 0.0  # Placeholder
    
    def _calculate_tasks_per_hour(self) -> float:
        """Calculate tasks per hour rate"""
        # This would require time-based metrics
        return 0.0  # Placeholder
    
    def _calculate_device_utilization(self) -> Dict[str, float]:
        """Calculate device utilization metrics"""
        return {}  # Placeholder
    
    def _calculate_capacity_utilization(self) -> float:
        """Calculate overall cluster capacity utilization"""
        return 0.0  # Placeholder