#!/usr/bin/env python3
"""
Example demonstrating Retire-Cluster REST API usage

This example shows how to interact with the Retire-Cluster system via REST API:
1. Connect to the API server
2. Check cluster status and health
3. List and monitor devices
4. Submit and manage tasks
5. Monitor task execution

Prerequisites:
- Start main node: retire-cluster-main
- Start API server: retire-cluster-api
- Have some worker nodes connected
"""

import requests
import time
import json
from datetime import datetime
from typing import Dict, Any, Optional, List


class RetireClusterAPI:
    """Python client for Retire-Cluster REST API"""
    
    def __init__(self, base_url: str = "http://localhost:8081/api/v1", api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
        # Set headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'retire-cluster-python-client/1.0.0'
        })
        
        if api_key:
            self.session.headers['X-API-Key'] = api_key
    
    def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make GET request"""
        response = self.session.get(f"{self.base_url}{endpoint}", **kwargs)
        response.raise_for_status()
        return response.json()
    
    def post(self, endpoint: str, data: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """Make POST request"""
        response = self.session.post(f"{self.base_url}{endpoint}", json=data, **kwargs)
        response.raise_for_status()
        return response.json()
    
    def put(self, endpoint: str, data: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """Make PUT request"""
        response = self.session.put(f"{self.base_url}{endpoint}", json=data, **kwargs)
        response.raise_for_status()
        return response.json()
    
    def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make DELETE request"""
        response = self.session.delete(f"{self.base_url}{endpoint}", **kwargs)
        response.raise_for_status()
        return response.json()
    
    # Cluster management
    def get_cluster_status(self) -> Dict[str, Any]:
        """Get cluster status and statistics"""
        return self.get('/cluster/status')
    
    def get_health(self) -> Dict[str, Any]:
        """Get health check"""
        response = self.session.get(f"{self.base_url.replace('/api/v1', '')}/health")
        response.raise_for_status()
        return response.json()
    
    def get_cluster_metrics(self) -> Dict[str, Any]:
        """Get detailed cluster metrics"""
        return self.get('/cluster/metrics')
    
    # Device management
    def list_devices(self, **filters) -> Dict[str, Any]:
        """List devices with optional filtering"""
        return self.get('/devices', params=filters)
    
    def get_device(self, device_id: str) -> Dict[str, Any]:
        """Get detailed device information"""
        return self.get(f'/devices/{device_id}')
    
    def get_device_status(self, device_id: str) -> Dict[str, Any]:
        """Get device status"""
        return self.get(f'/devices/{device_id}/status')
    
    def ping_device(self, device_id: str) -> Dict[str, Any]:
        """Ping a device"""
        return self.post(f'/devices/{device_id}/ping')
    
    def get_devices_summary(self) -> Dict[str, Any]:
        """Get devices summary statistics"""
        return self.get('/devices/summary')
    
    # Task management
    def submit_task(self, task_type: str, payload: Dict[str, Any], 
                   priority: str = "normal", requirements: Dict[str, Any] = None,
                   metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Submit a new task"""
        data = {
            'task_type': task_type,
            'payload': payload,
            'priority': priority
        }
        if requirements:
            data['requirements'] = requirements
        if metadata:
            data['metadata'] = metadata
        
        return self.post('/tasks', data)
    
    def list_tasks(self, **filters) -> Dict[str, Any]:
        """List tasks with optional filtering"""
        return self.get('/tasks', params=filters)
    
    def get_task(self, task_id: str) -> Dict[str, Any]:
        """Get detailed task information"""
        return self.get(f'/tasks/{task_id}')
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status"""
        return self.get(f'/tasks/{task_id}/status')
    
    def get_task_result(self, task_id: str) -> Dict[str, Any]:
        """Get task result"""
        return self.get(f'/tasks/{task_id}/result')
    
    def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """Cancel a task"""
        return self.post(f'/tasks/{task_id}/cancel')
    
    def retry_task(self, task_id: str) -> Dict[str, Any]:
        """Retry a failed task"""
        return self.post(f'/tasks/{task_id}/retry')
    
    def get_task_statistics(self) -> Dict[str, Any]:
        """Get task execution statistics"""
        return self.get('/tasks/statistics')
    
    def get_supported_task_types(self) -> Dict[str, Any]:
        """Get supported task types"""
        return self.get('/tasks/types')


def main():
    """Main example function"""
    print("🚀 Retire-Cluster REST API Example")
    print("=" * 50)
    
    # Initialize API client
    api = RetireClusterAPI()
    
    try:
        # 1. Health check
        print("\n❤️  Checking API health...")
        health = api.get_health()
        print(f"   Status: {health['status']}")
        print(f"   Components: {health.get('components', {})}")
        
        # 2. Get cluster status
        print("\n📊 Getting cluster status...")
        cluster_status = api.get_cluster_status()
        cluster_stats = cluster_status['data']['cluster_stats']
        
        print(f"   Total devices: {cluster_stats['total_devices']}")
        print(f"   Online devices: {cluster_stats['online_devices']}")
        print(f"   Health: {cluster_stats['health_percentage']}%")
        print(f"   Total CPU cores: {cluster_stats['total_resources'].get('cpu_cores', 0)}")
        print(f"   Total memory: {cluster_stats['total_resources'].get('memory_gb', 0)} GB")
        
        # 3. List devices
        print("\n📱 Listing devices...")
        devices_response = api.list_devices(status="online", page_size=10)
        devices = devices_response['data']
        
        if devices:
            print(f"   Found {len(devices)} online devices:")
            for device in devices:
                print(f"   - {device['device_id']} ({device['role']}, {device['platform']})")
                print(f"     CPU: {device['capabilities'].get('cpu_count', 'unknown')} cores, "
                      f"RAM: {device['capabilities'].get('memory_total_gb', 'unknown')} GB")
        else:
            print("   No online devices found")
            print("   Start worker nodes with: retire-cluster-worker --join localhost:8080")
            return
        
        # 4. Get device details
        if devices:
            device_id = devices[0]['device_id']
            print(f"\n🔍 Getting details for device: {device_id}")
            device_details = api.get_device(device_id)
            device_data = device_details['data']
            
            print(f"   Device ID: {device_data['device_id']}")
            print(f"   Role: {device_data['role']}")
            print(f"   Platform: {device_data['platform']}")
            print(f"   Status: {device_data['status']}")
            print(f"   Last heartbeat: {device_data['last_heartbeat']}")
            print(f"   Uptime: {device_data.get('uptime', 'unknown')}")
        
        # 5. Get supported task types
        print("\n📋 Getting supported task types...")
        task_types_response = api.get_supported_task_types()
        supported_types = task_types_response['data']['supported_types']
        print(f"   Supported task types: {', '.join(supported_types)}")
        
        # 6. Submit example tasks
        print("\n📤 Submitting example tasks...")
        
        submitted_tasks = []
        
        # Echo task
        echo_task = api.submit_task(
            task_type="echo",
            payload={"message": "Hello from REST API!"},
            priority="normal",
            metadata={"source": "api_example"}
        )
        task_id = echo_task['data']['task_id']
        submitted_tasks.append(task_id)
        print(f"   ✓ Submitted echo task: {task_id[:8]}...")
        
        # System info task
        if any(d['role'] in ['mobile', 'compute'] for d in devices):
            sysinfo_task = api.submit_task(
                task_type="system_info",
                payload={},
                priority="high",
                requirements={
                    "required_role": "mobile" if any(d['role'] == 'mobile' for d in devices) else "compute"
                }
            )
            task_id = sysinfo_task['data']['task_id']
            submitted_tasks.append(task_id)
            print(f"   ✓ Submitted system info task: {task_id[:8]}...")
        
        # Sleep task
        sleep_task = api.submit_task(
            task_type="sleep",
            payload={"duration": 2.0},
            priority="low"
        )
        task_id = sleep_task['data']['task_id']
        submitted_tasks.append(task_id)
        print(f"   ✓ Submitted sleep task: {task_id[:8]}...")
        
        # 7. Monitor task execution
        print(f"\n⏳ Monitoring {len(submitted_tasks)} tasks...")
        completed_tasks = []
        max_wait_time = 30  # 30 seconds
        start_time = time.time()
        
        while len(completed_tasks) < len(submitted_tasks) and (time.time() - start_time) < max_wait_time:
            for task_id in submitted_tasks:
                if task_id not in completed_tasks:
                    status_response = api.get_task_status(task_id)
                    status_data = status_response['data']
                    status = status_data['status']
                    
                    if status in ['success', 'failed', 'cancelled', 'timeout']:
                        completed_tasks.append(task_id)
                        status_icon = "✅" if status == 'success' else "❌"
                        print(f"   {status_icon} Task {task_id[:8]} completed with status: {status}")
                        
                        # Get result if successful
                        if status == 'success':
                            try:
                                result_response = api.get_task_result(task_id)
                                result_data = result_response['data']
                                print(f"      Result: {result_data.get('result_data', {})}")
                                print(f"      Execution time: {result_data.get('execution_time_seconds', 0):.2f}s")
                                print(f"      Worker: {result_data.get('worker_device_id', 'unknown')}")
                            except Exception as e:
                                print(f"      Could not get result: {e}")
            
            if len(completed_tasks) < len(submitted_tasks):
                time.sleep(1)
        
        # 8. Get task statistics
        print("\n📈 Getting task statistics...")
        try:
            task_stats = api.get_task_statistics()
            stats_data = task_stats['data']
            queue_stats = stats_data['queue_stats']
            
            print(f"   Total tasks: {queue_stats['total_tasks']}")
            print(f"   By status: {queue_stats.get('by_status', {})}")
            print(f"   By priority: {queue_stats.get('by_priority', {})}")
        except Exception as e:
            print(f"   Could not get task statistics: {e}")
        
        # 9. List recent tasks
        print("\n📋 Listing recent tasks...")
        recent_tasks = api.list_tasks(page=1, page_size=5)
        tasks_data = recent_tasks['data']
        
        if tasks_data:
            print(f"   Recent tasks:")
            for task in tasks_data:
                print(f"   - {task['task_id'][:8]} ({task['task_type']}) - {task['status']}")
                print(f"     Created: {task['created_at']}")
                if task.get('assigned_device_id'):
                    print(f"     Assigned to: {task['assigned_device_id']}")
        
        # 10. Device summary
        print("\n📊 Getting devices summary...")
        devices_summary = api.get_devices_summary()
        summary_data = devices_summary['data']
        
        print(f"   Total devices: {summary_data['total_devices']}")
        print(f"   Online: {summary_data['online_devices']}")
        print(f"   Offline: {summary_data['offline_devices']}")
        print(f"   By role: {summary_data['by_role']}")
        print(f"   By platform: {summary_data['by_platform']}")
        print(f"   Total resources:")
        print(f"     CPU cores: {summary_data['resource_totals']['cpu_cores']}")
        print(f"     Memory: {summary_data['resource_totals']['memory_gb']} GB")
        print(f"     Storage: {summary_data['resource_totals']['storage_gb']} GB")
        
        print("\n✅ API example completed successfully!")
        print("\n💡 Next steps:")
        print("   - Explore more endpoints in the API documentation")
        print("   - Try submitting custom tasks with specific requirements")
        print("   - Monitor cluster performance using the metrics endpoints")
        print("   - Build your own applications using the API")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API server")
        print("   Make sure the API server is running:")
        print("   retire-cluster-api --host localhost --port 8081")
    
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP error: {e}")
        print(f"   Response: {e.response.text if e.response else 'No response'}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def demo_advanced_usage():
    """Demonstrate advanced API usage patterns"""
    print("\n🔧 Advanced API Usage Examples")
    print("=" * 40)
    
    api = RetireClusterAPI()
    
    try:
        # Batch task submission
        print("\n📦 Batch task submission...")
        batch_tasks = []
        
        for i in range(5):
            task = api.submit_task(
                task_type="python_eval",
                payload={"expression": f"2 ** {i}"},
                priority="normal",
                metadata={"batch_id": "demo_batch", "task_number": i}
            )
            batch_tasks.append(task['data']['task_id'])
        
        print(f"   Submitted {len(batch_tasks)} tasks in batch")
        
        # Wait for batch completion
        print("   Waiting for batch completion...")
        while True:
            completed = 0
            for task_id in batch_tasks:
                status = api.get_task_status(task_id)
                if status['data']['is_terminal']:
                    completed += 1
            
            if completed == len(batch_tasks):
                break
            
            print(f"   Progress: {completed}/{len(batch_tasks)} completed")
            time.sleep(2)
        
        # Collect results
        print("   Collecting results...")
        for i, task_id in enumerate(batch_tasks):
            try:
                result = api.get_task_result(task_id)
                result_data = result['data']['result_data']
                print(f"   Task {i}: 2^{i} = {result_data}")
            except:
                print(f"   Task {i}: Failed or no result")
        
        # Device filtering example
        print("\n🔍 Device filtering examples...")
        
        # Get only mobile devices
        mobile_devices = api.list_devices(role="mobile", status="online")
        print(f"   Mobile devices: {len(mobile_devices['data'])}")
        
        # Get devices with GPU
        gpu_devices = api.list_devices(tags=["gpu-capable"])
        print(f"   GPU-capable devices: {len(gpu_devices['data'])}")
        
        # Task with specific requirements
        print("\n⚙️  Task with specific requirements...")
        specialized_task = api.submit_task(
            task_type="system_info",
            payload={},
            requirements={
                "min_cpu_cores": 4,
                "min_memory_gb": 8,
                "required_platform": "linux"
            },
            metadata={"purpose": "specialized_workload"}
        )
        print(f"   Submitted specialized task: {specialized_task['data']['task_id'][:8]}...")
        
    except Exception as e:
        print(f"❌ Advanced demo error: {e}")


if __name__ == "__main__":
    try:
        main()
        
        # Run advanced demo if basic demo succeeded
        response = input("\nRun advanced usage demo? (y/N): ")
        if response.lower() == 'y':
            demo_advanced_usage()
            
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted")
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()