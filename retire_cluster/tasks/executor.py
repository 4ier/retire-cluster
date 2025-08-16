"""
Task executor for worker nodes
"""

import asyncio
import json
import threading
import time
import traceback
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable, List
import logging

from .task import Task, TaskStatus, TaskResult


class TaskExecutor:
    """
    Executes tasks on worker nodes with proper isolation and monitoring
    """
    
    def __init__(self, device_id: str, capabilities: Dict[str, Any]):
        self.device_id = device_id
        self.capabilities = capabilities
        self.logger = logging.getLogger(f"executor.{device_id}")
        
        # Task handlers registry
        self._handlers: Dict[str, Callable[[Dict[str, Any]], Any]] = {}
        
        # Execution tracking
        self._running_tasks: Dict[str, threading.Thread] = {}
        self._task_locks: Dict[str, threading.Lock] = {}
        self._shutdown_event = threading.Event()
        
        # Statistics
        self.stats = {
            'tasks_executed': 0,
            'tasks_succeeded': 0,
            'tasks_failed': 0,
            'total_execution_time': 0.0,
            'last_task_time': None
        }
        
        # Default handlers
        self._register_builtin_handlers()

    def register_handler(self, task_type: str, handler: Callable[[Dict[str, Any]], Any]) -> None:
        """Register a task handler for a specific task type"""
        self._handlers[task_type] = handler
        self.logger.info(f"Registered handler for task type: {task_type}")

    def unregister_handler(self, task_type: str) -> None:
        """Unregister a task handler"""
        if task_type in self._handlers:
            del self._handlers[task_type]
            self.logger.info(f"Unregistered handler for task type: {task_type}")

    def get_supported_task_types(self) -> List[str]:
        """Get list of supported task types"""
        return list(self._handlers.keys())

    def can_execute_task(self, task: Task) -> bool:
        """Check if this executor can handle the task"""
        # Check if we have a handler for this task type
        if task.task_type not in self._handlers:
            return False
        
        # Check basic requirements
        requirements = task.requirements
        
        # CPU cores check
        if requirements.min_cpu_cores:
            if self.capabilities.get('cpu_count', 0) < requirements.min_cpu_cores:
                return False
        
        # Memory check
        if requirements.min_memory_gb:
            if self.capabilities.get('memory_total_gb', 0) < requirements.min_memory_gb:
                return False
        
        # Storage check
        if requirements.min_storage_gb:
            if self.capabilities.get('storage_total_gb', 0) < requirements.min_storage_gb:
                return False
        
        # Platform check
        if requirements.required_platform:
            device_platform = self.capabilities.get('platform', '').lower()
            if device_platform != requirements.required_platform.lower():
                return False
        
        # Role check
        if requirements.required_role:
            device_role = self.capabilities.get('role', '')
            if device_role != requirements.required_role:
                return False
        
        # Tags check
        if requirements.required_tags:
            device_tags = set(self.capabilities.get('tags', []))
            required_tags = set(requirements.required_tags)
            if not required_tags.issubset(device_tags):
                return False
        
        return True

    def execute_task(self, task: Task) -> TaskResult:
        """Execute a task and return the result"""
        if not self.can_execute_task(task):
            return TaskResult(
                task_id=task.task_id,
                status=TaskStatus.FAILED,
                error_message=f"Device {self.device_id} cannot execute task type {task.task_type}",
                worker_device_id=self.device_id
            )
        
        # Check if task is already running
        if task.task_id in self._running_tasks:
            return TaskResult(
                task_id=task.task_id,
                status=TaskStatus.FAILED,
                error_message="Task is already running",
                worker_device_id=self.device_id
            )
        
        # Execute in separate thread for timeout support
        result_container = {}
        execution_thread = threading.Thread(
            target=self._execute_task_thread,
            args=(task, result_container)
        )
        
        self._running_tasks[task.task_id] = execution_thread
        self._task_locks[task.task_id] = threading.Lock()
        
        try:
            execution_thread.start()
            execution_thread.join(timeout=task.requirements.timeout_seconds)
            
            if execution_thread.is_alive():
                # Task timed out
                self.logger.warning(f"Task {task.task_id} timed out after {task.requirements.timeout_seconds}s")
                return TaskResult(
                    task_id=task.task_id,
                    status=TaskStatus.TIMEOUT,
                    error_message=f"Task timed out after {task.requirements.timeout_seconds} seconds",
                    worker_device_id=self.device_id
                )
            
            return result_container.get('result', TaskResult(
                task_id=task.task_id,
                status=TaskStatus.FAILED,
                error_message="Task execution failed without result",
                worker_device_id=self.device_id
            ))
        
        finally:
            # Cleanup
            if task.task_id in self._running_tasks:
                del self._running_tasks[task.task_id]
            if task.task_id in self._task_locks:
                del self._task_locks[task.task_id]

    def _execute_task_thread(self, task: Task, result_container: Dict) -> None:
        """Execute task in a separate thread"""
        start_time = time.time()
        logs = []
        
        try:
            self.logger.info(f"Starting execution of task {task.task_id} ({task.task_type})")
            
            # Get handler
            handler = self._handlers.get(task.task_type)
            if not handler:
                raise ValueError(f"No handler registered for task type: {task.task_type}")
            
            # Execute the task
            result_data = handler(task.payload)
            
            execution_time = time.time() - start_time
            
            # Create success result
            result = TaskResult(
                task_id=task.task_id,
                status=TaskStatus.SUCCESS,
                result_data=result_data,
                execution_time_seconds=execution_time,
                worker_device_id=self.device_id,
                started_at=datetime.fromtimestamp(start_time, timezone.utc),
                completed_at=datetime.now(timezone.utc),
                logs=logs
            )
            
            # Update statistics
            self.stats['tasks_executed'] += 1
            self.stats['tasks_succeeded'] += 1
            self.stats['total_execution_time'] += execution_time
            self.stats['last_task_time'] = datetime.now(timezone.utc).isoformat()
            
            self.logger.info(f"Task {task.task_id} completed successfully in {execution_time:.2f}s")
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_message = str(e)
            error_traceback = traceback.format_exc()
            
            self.logger.error(f"Task {task.task_id} failed: {error_message}")
            self.logger.debug(f"Task {task.task_id} traceback: {error_traceback}")
            
            # Create failure result
            result = TaskResult(
                task_id=task.task_id,
                status=TaskStatus.FAILED,
                error_message=error_message,
                error_traceback=error_traceback,
                execution_time_seconds=execution_time,
                worker_device_id=self.device_id,
                started_at=datetime.fromtimestamp(start_time, timezone.utc),
                completed_at=datetime.now(timezone.utc),
                logs=logs
            )
            
            # Update statistics
            self.stats['tasks_executed'] += 1
            self.stats['tasks_failed'] += 1
            self.stats['total_execution_time'] += execution_time
            self.stats['last_task_time'] = datetime.now(timezone.utc).isoformat()
        
        result_container['result'] = result

    def get_running_tasks(self) -> List[str]:
        """Get list of currently running task IDs"""
        return list(self._running_tasks.keys())

    def is_busy(self) -> bool:
        """Check if executor is currently running tasks"""
        return len(self._running_tasks) > 0

    def get_statistics(self) -> Dict[str, Any]:
        """Get executor statistics"""
        return {
            'device_id': self.device_id,
            'supported_task_types': self.get_supported_task_types(),
            'running_tasks': len(self._running_tasks),
            'stats': self.stats.copy()
        }

    def shutdown(self, timeout: float = 30.0) -> bool:
        """Shutdown executor and wait for running tasks to complete"""
        self.logger.info("Shutting down task executor...")
        self._shutdown_event.set()
        
        # Wait for running tasks to complete
        start_time = time.time()
        while self._running_tasks and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        if self._running_tasks:
            self.logger.warning(f"Timeout waiting for tasks to complete: {list(self._running_tasks.keys())}")
            return False
        
        self.logger.info("Task executor shutdown completed")
        return True

    def _register_builtin_handlers(self) -> None:
        """Register built-in task handlers"""
        
        # Echo task - returns the payload as-is
        def echo_handler(payload: Dict[str, Any]) -> Dict[str, Any]:
            return {'echo': payload}
        
        # Sleep task - sleeps for specified duration
        def sleep_handler(payload: Dict[str, Any]) -> Dict[str, Any]:
            duration = payload.get('duration', 1.0)
            time.sleep(duration)
            return {'slept_for': duration}
        
        # System info task - returns device capabilities
        def system_info_handler(payload: Dict[str, Any]) -> Dict[str, Any]:
            return self.capabilities.copy()
        
        # Python eval task - evaluates Python expression (DANGEROUS - use with caution)
        def python_eval_handler(payload: Dict[str, Any]) -> Dict[str, Any]:
            expression = payload.get('expression', '')
            if not expression:
                raise ValueError("No expression provided")
            
            # Basic safety check
            dangerous_keywords = ['import', 'exec', 'eval', 'open', 'file', '__']
            if any(keyword in expression for keyword in dangerous_keywords):
                raise ValueError("Expression contains dangerous keywords")
            
            try:
                result = eval(expression)
                return {'result': result, 'expression': expression}
            except Exception as e:
                raise ValueError(f"Expression evaluation failed: {str(e)}")
        
        # HTTP request task - makes HTTP requests
        def http_request_handler(payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                import requests
            except ImportError:
                raise ValueError("requests library not available")
            
            url = payload.get('url')
            method = payload.get('method', 'GET').upper()
            headers = payload.get('headers', {})
            data = payload.get('data')
            timeout = payload.get('timeout', 30)
            
            if not url:
                raise ValueError("No URL provided")
            
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data if isinstance(data, dict) else None,
                data=data if not isinstance(data, dict) else None,
                timeout=timeout
            )
            
            return {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'content': response.text,
                'url': response.url
            }
        
        # Command execution task - runs shell commands (DANGEROUS)
        def command_handler(payload: Dict[str, Any]) -> Dict[str, Any]:
            import subprocess
            
            command = payload.get('command')
            if not command:
                raise ValueError("No command provided")
            
            # Basic safety check
            dangerous_commands = ['rm', 'del', 'format', 'sudo', 'su']
            if any(cmd in command.lower() for cmd in dangerous_commands):
                raise ValueError("Command contains dangerous keywords")
            
            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=payload.get('timeout', 30)
                )
                
                return {
                    'return_code': result.returncode,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'command': command
                }
            except subprocess.TimeoutExpired:
                raise ValueError("Command execution timed out")
        
        # Register handlers
        self.register_handler('echo', echo_handler)
        self.register_handler('sleep', sleep_handler)
        self.register_handler('system_info', system_info_handler)
        self.register_handler('python_eval', python_eval_handler)
        self.register_handler('http_request', http_request_handler)
        self.register_handler('command', command_handler)