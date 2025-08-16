"""
Integration modules for external task execution frameworks
"""

import asyncio
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, List
import logging

from .task import Task, TaskStatus, TaskResult, TaskRequirements


class ExternalFrameworkIntegration(ABC):
    """Base class for external framework integrations"""
    
    def __init__(self, cluster_client):
        self.cluster_client = cluster_client
        self.logger = logging.getLogger(f"integration.{self.__class__.__name__}")
    
    @abstractmethod
    def submit_task(self, task_type: str, payload: Dict[str, Any], **kwargs) -> str:
        """Submit a task to the external framework"""
        pass
    
    @abstractmethod
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get task status from external framework"""
        pass
    
    @abstractmethod
    def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """Get task result from external framework"""
        pass
    
    @abstractmethod
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task in the external framework"""
        pass


class TemporalIntegration(ExternalFrameworkIntegration):
    """
    Integration with Temporal workflow engine
    
    This allows using Temporal for complex workflow orchestration
    while using Retire-Cluster for actual task execution
    """
    
    def __init__(self, cluster_client, temporal_client=None):
        super().__init__(cluster_client)
        self.temporal_client = temporal_client
        self._workflows: Dict[str, Any] = {}
        
        # Try to import Temporal SDK
        try:
            from temporalio import client, worker, workflow, activity
            self.temporal_available = True
            self.client_module = client
            self.worker_module = worker
            self.workflow_module = workflow
            self.activity_module = activity
        except ImportError:
            self.temporal_available = False
            self.logger.warning("Temporal SDK not available. Install with: pip install temporalio")
    
    async def initialize(self, temporal_host: str = "localhost:7233", namespace: str = "default"):
        """Initialize Temporal client connection"""
        if not self.temporal_available:
            raise RuntimeError("Temporal SDK not available")
        
        try:
            self.temporal_client = await self.client_module.Client.connect(
                f"{temporal_host}",
                namespace=namespace
            )
            self.logger.info(f"Connected to Temporal at {temporal_host}")
        except Exception as e:
            self.logger.error(f"Failed to connect to Temporal: {e}")
            raise
    
    def submit_task(self, task_type: str, payload: Dict[str, Any], **kwargs) -> str:
        """Submit task via Temporal workflow"""
        if not self.temporal_available or not self.temporal_client:
            raise RuntimeError("Temporal not available or not initialized")
        
        # Create a Retire-Cluster task
        requirements = kwargs.get('requirements', TaskRequirements())
        task = Task(
            task_type=task_type,
            payload=payload,
            requirements=requirements
        )
        
        # Submit to cluster
        task_id = self.cluster_client.submit_task(task)
        
        # Start Temporal workflow for monitoring
        workflow_id = f"retire-cluster-{task_id}"
        
        # Note: This would need a proper Temporal workflow implementation
        # For now, we just track the task
        self._workflows[workflow_id] = {
            'task_id': task_id,
            'status': 'running'
        }
        
        return workflow_id
    
    def get_task_status(self, workflow_id: str) -> Optional[TaskStatus]:
        """Get task status via Temporal"""
        workflow_info = self._workflows.get(workflow_id)
        if not workflow_info:
            return None
        
        # Get status from cluster
        task_id = workflow_info['task_id']
        return self.cluster_client.get_task_status(task_id)
    
    def get_task_result(self, workflow_id: str) -> Optional[TaskResult]:
        """Get task result via Temporal"""
        workflow_info = self._workflows.get(workflow_id)
        if not workflow_info:
            return None
        
        task_id = workflow_info['task_id']
        return self.cluster_client.get_task_result(task_id)
    
    def cancel_task(self, workflow_id: str) -> bool:
        """Cancel task via Temporal"""
        workflow_info = self._workflows.get(workflow_id)
        if not workflow_info:
            return False
        
        task_id = workflow_info['task_id']
        success = self.cluster_client.cancel_task(task_id)
        
        if success:
            self._workflows[workflow_id]['status'] = 'cancelled'
        
        return success
    
    def create_retire_cluster_activity(self):
        """Create a Temporal activity that executes tasks on Retire-Cluster"""
        if not self.temporal_available:
            return None
        
        @self.activity_module.defn
        async def execute_retire_cluster_task(task_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            """Temporal activity that executes a task on Retire-Cluster"""
            task = Task(task_type=task_type, payload=payload)
            task_id = self.cluster_client.submit_task(task)
            
            # Wait for completion (in real implementation, use async polling)
            import time
            while True:
                status = self.cluster_client.get_task_status(task_id)
                if status in [TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                    break
                time.sleep(1)
            
            result = self.cluster_client.get_task_result(task_id)
            if result.status == TaskStatus.SUCCESS:
                return result.result_data
            else:
                raise Exception(result.error_message)
        
        return execute_retire_cluster_task


class CeleryIntegration(ExternalFrameworkIntegration):
    """
    Integration with Celery distributed task queue
    
    This allows using Celery as a task broker while executing
    tasks on Retire-Cluster devices
    """
    
    def __init__(self, cluster_client, celery_app=None):
        super().__init__(cluster_client)
        self.celery_app = celery_app
        self._task_mapping: Dict[str, str] = {}  # celery_task_id -> cluster_task_id
        
        # Try to import Celery
        try:
            import celery
            self.celery_available = True
            self.celery_module = celery
        except ImportError:
            self.celery_available = False
            self.logger.warning("Celery not available. Install with: pip install celery")
    
    def initialize(self, broker_url: str = "redis://localhost:6379", backend_url: str = None):
        """Initialize Celery app"""
        if not self.celery_available:
            raise RuntimeError("Celery not available")
        
        if not self.celery_app:
            self.celery_app = self.celery_module.Celery(
                'retire_cluster_integration',
                broker=broker_url,
                backend=backend_url or broker_url
            )
        
        # Register Retire-Cluster task
        self._register_cluster_task()
        self.logger.info("Celery integration initialized")
    
    def _register_cluster_task(self):
        """Register a Celery task that executes on Retire-Cluster"""
        
        @self.celery_app.task(bind=True)
        def execute_on_retire_cluster(self, task_type: str, payload: Dict[str, Any], requirements: Dict[str, Any] = None):
            """Celery task that executes on Retire-Cluster"""
            # Create cluster task
            task_requirements = TaskRequirements(**requirements) if requirements else TaskRequirements()
            task = Task(
                task_type=task_type,
                payload=payload,
                requirements=task_requirements
            )
            
            # Submit to cluster
            cluster_task_id = self.cluster_client.submit_task(task)
            
            # Store mapping
            celery_task_id = self.request.id
            self._task_mapping[celery_task_id] = cluster_task_id
            
            # Wait for completion (using Celery's retry mechanism)
            status = self.cluster_client.get_task_status(cluster_task_id)
            
            if status in [TaskStatus.PENDING, TaskStatus.QUEUED, TaskStatus.ASSIGNED, TaskStatus.RUNNING]:
                # Task still running, retry after delay
                raise self.retry(countdown=5, max_retries=None)
            
            # Task completed
            result = self.cluster_client.get_task_result(cluster_task_id)
            
            if result.status == TaskStatus.SUCCESS:
                return result.result_data
            else:
                raise Exception(result.error_message)
        
        self.execute_on_retire_cluster = execute_on_retire_cluster
    
    def submit_task(self, task_type: str, payload: Dict[str, Any], **kwargs) -> str:
        """Submit task via Celery"""
        if not self.celery_available or not self.celery_app:
            raise RuntimeError("Celery not available or not initialized")
        
        requirements = kwargs.get('requirements', {})
        if isinstance(requirements, TaskRequirements):
            requirements = {
                'min_cpu_cores': requirements.min_cpu_cores,
                'min_memory_gb': requirements.min_memory_gb,
                'min_storage_gb': requirements.min_storage_gb,
                'required_platform': requirements.required_platform,
                'required_role': requirements.required_role,
                'required_tags': requirements.required_tags,
                'gpu_required': requirements.gpu_required,
                'internet_required': requirements.internet_required,
                'timeout_seconds': requirements.timeout_seconds,
                'max_retries': requirements.max_retries
            }
        
        # Submit via Celery
        celery_task = self.execute_on_retire_cluster.delay(
            task_type=task_type,
            payload=payload,
            requirements=requirements
        )
        
        return celery_task.id
    
    def get_task_status(self, celery_task_id: str) -> Optional[TaskStatus]:
        """Get task status via Celery"""
        if not self.celery_app:
            return None
        
        try:
            celery_task = self.celery_app.AsyncResult(celery_task_id)
            
            # Map Celery states to TaskStatus
            state_mapping = {
                'PENDING': TaskStatus.PENDING,
                'STARTED': TaskStatus.RUNNING,
                'SUCCESS': TaskStatus.SUCCESS,
                'FAILURE': TaskStatus.FAILED,
                'REVOKED': TaskStatus.CANCELLED,
                'RETRY': TaskStatus.RUNNING
            }
            
            return state_mapping.get(celery_task.state, TaskStatus.PENDING)
        
        except Exception:
            return None
    
    def get_task_result(self, celery_task_id: str) -> Optional[TaskResult]:
        """Get task result via Celery"""
        if not self.celery_app:
            return None
        
        try:
            celery_task = self.celery_app.AsyncResult(celery_task_id)
            
            if celery_task.state == 'SUCCESS':
                return TaskResult(
                    task_id=celery_task_id,
                    status=TaskStatus.SUCCESS,
                    result_data=celery_task.result
                )
            elif celery_task.state == 'FAILURE':
                return TaskResult(
                    task_id=celery_task_id,
                    status=TaskStatus.FAILED,
                    error_message=str(celery_task.info)
                )
            else:
                return TaskResult(
                    task_id=celery_task_id,
                    status=self.get_task_status(celery_task_id) or TaskStatus.PENDING
                )
        
        except Exception:
            return None
    
    def cancel_task(self, celery_task_id: str) -> bool:
        """Cancel task via Celery"""
        if not self.celery_app:
            return False
        
        try:
            celery_task = self.celery_app.AsyncResult(celery_task_id)
            celery_task.revoke(terminate=True)
            
            # Also cancel in cluster if we have the mapping
            if celery_task_id in self._task_mapping:
                cluster_task_id = self._task_mapping[celery_task_id]
                self.cluster_client.cancel_task(cluster_task_id)
                del self._task_mapping[celery_task_id]
            
            return True
        
        except Exception:
            return False


class SimpleTaskBridge:
    """
    Simple bridge for external frameworks that don't need full integration
    
    This provides a simple HTTP/REST interface for submitting tasks
    """
    
    def __init__(self, cluster_client, host: str = "0.0.0.0", port: int = 8081):
        self.cluster_client = cluster_client
        self.host = host
        self.port = port
        self.logger = logging.getLogger("task_bridge")
        
        # Try to import Flask for HTTP interface
        try:
            from flask import Flask, request, jsonify
            self.flask_available = True
            self.Flask = Flask
            self.request = request
            self.jsonify = jsonify
        except ImportError:
            self.flask_available = False
            self.logger.warning("Flask not available. Install with: pip install flask")
    
    def start_http_bridge(self):
        """Start HTTP bridge for external task submission"""
        if not self.flask_available:
            raise RuntimeError("Flask not available")
        
        app = self.Flask(__name__)
        
        @app.route('/tasks', methods=['POST'])
        def submit_task():
            data = self.request.json
            
            task_type = data.get('task_type')
            payload = data.get('payload', {})
            requirements = data.get('requirements', {})
            
            if not task_type:
                return self.jsonify({'error': 'task_type is required'}), 400
            
            try:
                # Create task
                task_requirements = TaskRequirements(**requirements)
                task = Task(
                    task_type=task_type,
                    payload=payload,
                    requirements=task_requirements
                )
                
                # Submit to cluster
                task_id = self.cluster_client.submit_task(task)
                
                return self.jsonify({
                    'task_id': task_id,
                    'status': 'submitted'
                })
            
            except Exception as e:
                return self.jsonify({'error': str(e)}), 500
        
        @app.route('/tasks/<task_id>', methods=['GET'])
        def get_task_status(task_id):
            try:
                status = self.cluster_client.get_task_status(task_id)
                result = self.cluster_client.get_task_result(task_id)
                
                response = {
                    'task_id': task_id,
                    'status': status.value if status else 'not_found'
                }
                
                if result:
                    response['result'] = result.to_dict()
                
                return self.jsonify(response)
            
            except Exception as e:
                return self.jsonify({'error': str(e)}), 500
        
        @app.route('/tasks/<task_id>', methods=['DELETE'])
        def cancel_task(task_id):
            try:
                success = self.cluster_client.cancel_task(task_id)
                return self.jsonify({
                    'task_id': task_id,
                    'cancelled': success
                })
            
            except Exception as e:
                return self.jsonify({'error': str(e)}), 500
        
        self.logger.info(f"Starting HTTP task bridge on {self.host}:{self.port}")
        app.run(host=self.host, port=self.port)