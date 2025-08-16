#!/usr/bin/env python3
"""
Example demonstrating the Retire-Cluster task execution framework

This example shows how to:
1. Set up a task scheduler and queue
2. Submit various types of tasks
3. Monitor task execution
4. Handle task results

Run this example after starting a main node and some worker nodes.
"""

import time
import asyncio
from pathlib import Path

from retire_cluster.tasks import (
    Task, TaskStatus, TaskResult, TaskRequirements, TaskPriority,
    TaskQueue, TaskScheduler
)
from retire_cluster.core.config import Config
from retire_cluster.core.logger import get_logger


def main():
    """Main example function"""
    print("🚀 Retire-Cluster Task Execution Framework Example")
    print("=" * 60)
    
    # Setup logging
    logger = get_logger("task_example", level="INFO")
    
    # Create task queue and scheduler
    task_queue = TaskQueue()
    scheduler = TaskScheduler(task_queue)
    
    # Register some example devices (in real usage, these come from worker nodes)
    example_devices = {
        'laptop-001': {
            'device_id': 'laptop-001',
            'role': 'compute',
            'platform': 'windows',
            'cpu_count': 8,
            'memory_total_gb': 16,
            'storage_total_gb': 500,
            'has_gpu': True,
            'tags': ['development', 'gpu-capable']
        },
        'android-001': {
            'device_id': 'android-001', 
            'role': 'mobile',
            'platform': 'android',
            'cpu_count': 4,
            'memory_total_gb': 6,
            'storage_total_gb': 128,
            'has_gpu': False,
            'tags': ['mobile', 'battery-powered']
        },
        'server-001': {
            'device_id': 'server-001',
            'role': 'compute',
            'platform': 'linux',
            'cpu_count': 32,
            'memory_total_gb': 64,
            'storage_total_gb': 2000,
            'has_gpu': True,
            'tags': ['server', 'high-performance']
        }
    }
    
    # Register devices with scheduler
    print("\n📱 Registering example devices...")
    for device_id, capabilities in example_devices.items():
        scheduler.register_device(device_id, capabilities)
        print(f"   ✓ {device_id} ({capabilities['role']}, {capabilities['platform']})")
    
    # Start scheduler
    print("\n⚙️  Starting task scheduler...")
    scheduler.start()
    
    try:
        # Submit various example tasks
        print("\n📋 Submitting example tasks...")
        
        # 1. Simple echo task
        echo_task = Task(
            task_type="echo",
            payload={"message": "Hello from Retire-Cluster!"},
            priority=TaskPriority.NORMAL
        )
        scheduler.submit_task(echo_task)
        print(f"   ✓ Submitted echo task: {echo_task.task_id}")
        
        # 2. System info task for mobile devices
        mobile_info_task = Task(
            task_type="system_info",
            payload={},
            priority=TaskPriority.HIGH,
            requirements=TaskRequirements(
                required_role="mobile",
                required_platform="android"
            )
        )
        scheduler.submit_task(mobile_info_task)
        print(f"   ✓ Submitted mobile system info task: {mobile_info_task.task_id}")
        
        # 3. CPU-intensive task for high-performance devices
        compute_task = Task(
            task_type="python_eval",
            payload={"expression": "sum(range(1000000))"},
            priority=TaskPriority.NORMAL,
            requirements=TaskRequirements(
                min_cpu_cores=8,
                min_memory_gb=8,
                required_tags=["high-performance"]
            )
        )
        scheduler.submit_task(compute_task)
        print(f"   ✓ Submitted compute task: {compute_task.task_id}")
        
        # 4. HTTP request task
        http_task = Task(
            task_type="http_request",
            payload={
                "url": "https://api.github.com/repos/4ier/retire-cluster",
                "method": "GET"
            },
            priority=TaskPriority.LOW,
            requirements=TaskRequirements(
                internet_required=True,
                timeout_seconds=30
            )
        )
        scheduler.submit_task(http_task)
        print(f"   ✓ Submitted HTTP request task: {http_task.task_id}")
        
        # 5. Sleep task with specific timing
        sleep_task = Task(
            task_type="sleep",
            payload={"duration": 3.0},
            priority=TaskPriority.URGENT
        )
        scheduler.submit_task(sleep_task)
        print(f"   ✓ Submitted sleep task: {sleep_task.task_id}")
        
        # Monitor task execution
        print("\n📊 Monitoring task execution...")
        submitted_tasks = [echo_task, mobile_info_task, compute_task, http_task, sleep_task]
        
        completed_tasks = []
        max_wait_time = 60  # 1 minute
        start_time = time.time()
        
        while len(completed_tasks) < len(submitted_tasks) and (time.time() - start_time) < max_wait_time:
            # Print queue statistics
            stats = scheduler.get_cluster_statistics()
            queue_stats = stats['queue_stats']
            
            print(f"\n   Queue Status:")
            print(f"   - Total tasks: {queue_stats['total_tasks']}")
            print(f"   - Pending: {queue_stats['by_status'].get('pending', 0)}")
            print(f"   - Queued: {queue_stats['by_status'].get('queued', 0)}")
            print(f"   - Running: {queue_stats['by_status'].get('running', 0)}")
            print(f"   - Completed: {queue_stats['by_status'].get('success', 0)}")
            print(f"   - Failed: {queue_stats['by_status'].get('failed', 0)}")
            
            # Check individual task status
            for task in submitted_tasks:
                if task not in completed_tasks:
                    current_task = task_queue.get_task(task.task_id)
                    if current_task and current_task.is_terminal_status():
                        completed_tasks.append(task)
                        status_icon = "✅" if current_task.status == TaskStatus.SUCCESS else "❌"
                        print(f"   {status_icon} Task {task.task_id[:8]} ({task.task_type}): {current_task.status.value}")
                        
                        if current_task.result:
                            if current_task.result.status == TaskStatus.SUCCESS:
                                print(f"      Result: {current_task.result.result_data}")
                            else:
                                print(f"      Error: {current_task.result.error_message}")
                            
                            if current_task.result.execution_time_seconds:
                                print(f"      Execution time: {current_task.result.execution_time_seconds:.2f}s")
            
            time.sleep(2)
        
        # Final summary
        print(f"\n📈 Final Summary:")
        print(f"   Completed: {len(completed_tasks)}/{len(submitted_tasks)} tasks")
        
        final_stats = scheduler.get_cluster_statistics()
        scheduler_stats = final_stats['scheduler_stats']
        
        print(f"   Tasks scheduled: {scheduler_stats['tasks_scheduled']}")
        print(f"   Scheduler rounds: {scheduler_stats['scheduler_rounds']}")
        
        # Show detailed results
        print(f"\n📋 Detailed Results:")
        for task in submitted_tasks:
            current_task = task_queue.get_task(task.task_id)
            if current_task:
                print(f"\n   Task: {task.task_type} ({task.task_id[:8]})")
                print(f"   Status: {current_task.status.value}")
                print(f"   Priority: {task.priority.name}")
                
                if current_task.assigned_device_id:
                    print(f"   Assigned to: {current_task.assigned_device_id}")
                
                if current_task.result:
                    print(f"   Worker: {current_task.result.worker_device_id}")
                    if current_task.result.execution_time_seconds:
                        print(f"   Execution time: {current_task.result.execution_time_seconds:.2f}s")
                    
                    if current_task.result.status == TaskStatus.SUCCESS:
                        print(f"   Result: {current_task.result.result_data}")
                    else:
                        print(f"   Error: {current_task.result.error_message}")
    
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    
    finally:
        # Clean up
        print("\n🔄 Shutting down scheduler...")
        scheduler.stop()
        print("✅ Example completed!")


def create_integration_example():
    """Example showing integration with external frameworks"""
    print("\n🔗 Framework Integration Examples")
    print("=" * 40)
    
    # Example of using task execution with external frameworks
    from retire_cluster.tasks.integrations import (
        TemporalIntegration, CeleryIntegration, SimpleTaskBridge
    )
    
    # Mock cluster client for demonstration
    class MockClusterClient:
        def submit_task(self, task):
            print(f"   📤 Submitted task: {task.task_id}")
            return task.task_id
        
        def get_task_status(self, task_id):
            return TaskStatus.SUCCESS
        
        def get_task_result(self, task_id):
            return TaskResult(
                task_id=task_id,
                status=TaskStatus.SUCCESS,
                result_data={"message": "Task completed via integration"}
            )
        
        def cancel_task(self, task_id):
            return True
    
    mock_client = MockClusterClient()
    
    # Temporal Integration Example
    print("\n📅 Temporal Integration:")
    temporal_integration = TemporalIntegration(mock_client)
    if temporal_integration.temporal_available:
        print("   ✅ Temporal SDK available")
        print("   📝 Example: Use Temporal workflows to orchestrate complex task sequences")
        print("   📝 Each workflow step can be executed on different cluster devices")
    else:
        print("   ⚠️  Temporal SDK not available (install with: pip install temporalio)")
    
    # Celery Integration Example
    print("\n🌾 Celery Integration:")
    celery_integration = CeleryIntegration(mock_client)
    if celery_integration.celery_available:
        print("   ✅ Celery available")
        print("   📝 Example: Use Celery as task broker with Retire-Cluster execution")
        print("   📝 Submit tasks via Celery, execute on cluster devices")
    else:
        print("   ⚠️  Celery not available (install with: pip install celery)")
    
    # Simple HTTP Bridge Example
    print("\n🌐 HTTP Bridge:")
    http_bridge = SimpleTaskBridge(mock_client)
    if http_bridge.flask_available:
        print("   ✅ Flask available")
        print("   📝 Example: HTTP API for task submission")
        print("   📝 POST /tasks - Submit new task")
        print("   📝 GET /tasks/<id> - Check task status")
        print("   📝 DELETE /tasks/<id> - Cancel task")
    else:
        print("   ⚠️  Flask not available (install with: pip install flask)")


if __name__ == "__main__":
    try:
        main()
        create_integration_example()
    except Exception as e:
        print(f"❌ Error running example: {e}")
        import traceback
        traceback.print_exc()