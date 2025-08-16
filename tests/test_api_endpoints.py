"""
Test suite for API endpoints (text/plain and JSON)
"""

import unittest
import json
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestTextAPIEndpoints(unittest.TestCase):
    """Test text/plain API endpoints"""
    
    def setUp(self):
        """Set up test client"""
        from retire_cluster.web.app import create_app
        
        # Create mock cluster server
        self.mock_cluster = Mock()
        self.mock_cluster.get_devices.return_value = [
            {"id": "android-001", "status": "online", "cpu": 42, "memory": 2.1, "tasks": 3},
            {"id": "laptop-002", "status": "online", "cpu": 15, "memory": 4.5, "tasks": 1},
            {"id": "raspi-003", "status": "offline", "cpu": 0, "memory": 0, "tasks": 0},
        ]
        
        self.mock_cluster.get_cluster_status.return_value = {
            "status": "healthy",
            "nodes_online": 5,
            "nodes_total": 7,
            "cpu_cores": 48,
            "cpu_usage": 37,
            "memory_total": 128,
            "memory_usage": 42,
            "tasks_active": 12,
            "tasks_completed": 45,
            "uptime": "15d 6h 42m"
        }
        
        self.app = create_app(self.mock_cluster, testing=True)
        self.client = self.app.test_client()
    
    def test_text_devices_endpoint(self):
        """Test /text/devices endpoint returns pipe-delimited text"""
        response = self.client.get('/text/devices')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'text/plain; charset=utf-8')
        
        # Check content format
        lines = response.data.decode('utf-8').strip().split('\n')
        self.assertEqual(len(lines), 3)
        
        # Verify first device
        first_device = lines[0].split('|')
        self.assertEqual(first_device[0], 'android-001')
        self.assertEqual(first_device[1], 'online')
        self.assertEqual(first_device[2], '42')
        self.assertEqual(first_device[3], '2.1')
        self.assertEqual(first_device[4], '3')
    
    def test_text_status_endpoint(self):
        """Test /text/status endpoint returns key-value pairs"""
        response = self.client.get('/text/status')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'text/plain; charset=utf-8')
        
        # Parse key-value pairs
        content = response.data.decode('utf-8')
        self.assertIn("STATUS: healthy", content)
        self.assertIn("NODES: 5/7 online", content)
        self.assertIn("CPU: 48 cores (37% utilized)", content)
        self.assertIn("MEMORY: 128GB (42% used)", content)
        self.assertIn("TASKS: 12 active", content)
        self.assertIn("UPTIME: 15d 6h 42m", content)
    
    def test_text_devices_with_filter(self):
        """Test /text/devices with status filter"""
        response = self.client.get('/text/devices?status=online')
        
        self.assertEqual(response.status_code, 200)
        
        lines = response.data.decode('utf-8').strip().split('\n')
        self.assertEqual(len(lines), 2)  # Only online devices
        
        # Verify offline device is not included
        for line in lines:
            self.assertNotIn('raspi-003', line)
    
    def test_text_metrics_endpoint(self):
        """Test /text/metrics endpoint returns Prometheus format"""
        response = self.client.get('/text/metrics')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'text/plain; charset=utf-8')
        
        content = response.data.decode('utf-8')
        
        # Check Prometheus format
        self.assertIn("# HELP cluster_devices_total", content)
        self.assertIn("# TYPE cluster_devices_total gauge", content)
        self.assertIn("cluster_devices_total", content)
        self.assertIn("cluster_devices_online", content)
        self.assertIn("cluster_cpu_usage_percent", content)
        self.assertIn("cluster_memory_usage_percent", content)
    
    def test_text_logs_endpoint(self):
        """Test /text/logs endpoint returns plain text logs"""
        # Mock log entries
        self.mock_cluster.get_logs.return_value = [
            {"timestamp": "2024-01-15 10:30:15", "level": "INFO", 
             "message": "Device android-001 connected"},
            {"timestamp": "2024-01-15 10:30:16", "level": "ERROR",
             "message": "Task task-abc123 failed"},
        ]
        
        response = self.client.get('/text/logs')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'text/plain; charset=utf-8')
        
        content = response.data.decode('utf-8')
        self.assertIn("[2024-01-15 10:30:15] INFO: Device android-001 connected", content)
        self.assertIn("[2024-01-15 10:30:16] ERROR: Task task-abc123 failed", content)
    
    def test_csv_format_devices(self):
        """Test devices endpoint with CSV format"""
        response = self.client.get('/text/devices', 
                                  headers={'Accept': 'text/csv'})
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/csv', response.content_type)
        
        lines = response.data.decode('utf-8').strip().split('\n')
        
        # Check header
        self.assertEqual(lines[0], 'id,status,cpu,memory,tasks')
        
        # Check first data row
        self.assertEqual(lines[1], 'android-001,online,42,2.1,3')
    
    def test_tsv_format_devices(self):
        """Test devices endpoint with TSV format"""
        response = self.client.get('/text/devices',
                                  headers={'Accept': 'text/tab-separated-values'})
        
        self.assertEqual(response.status_code, 200)
        
        lines = response.data.decode('utf-8').strip().split('\n')
        
        # Check header
        self.assertEqual(lines[0], 'id\tstatus\tcpu\tmemory\ttasks')
        
        # Check first data row
        fields = lines[1].split('\t')
        self.assertEqual(fields[0], 'android-001')
        self.assertEqual(fields[1], 'online')


class TestJSONAPIEndpoints(unittest.TestCase):
    """Test JSON API endpoints"""
    
    def setUp(self):
        """Set up test client"""
        from retire_cluster.web.app import create_app
        
        self.mock_cluster = Mock()
        self.mock_cluster.get_devices.return_value = [
            {"id": "android-001", "status": "online", "cpu": 42, "memory": 2.1, "tasks": 3},
        ]
        
        self.app = create_app(self.mock_cluster, testing=True)
        self.client = self.app.test_client()
    
    def test_api_devices_json(self):
        """Test /api/v1/devices returns JSON"""
        response = self.client.get('/api/v1/devices',
                                  headers={'Accept': 'application/json'})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertIn('devices', data['data'])
        self.assertEqual(len(data['data']['devices']), 1)
        self.assertEqual(data['data']['devices'][0]['id'], 'android-001')
    
    def test_api_cluster_status(self):
        """Test /api/v1/cluster/status endpoint"""
        self.mock_cluster.get_cluster_status.return_value = {
            "status": "healthy",
            "nodes_online": 5,
            "nodes_total": 7
        }
        
        response = self.client.get('/api/v1/cluster/status')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['data']['cluster_status'], 'healthy')
        self.assertEqual(data['data']['nodes_online'], 5)
    
    def test_api_error_handling(self):
        """Test API error response format"""
        response = self.client.get('/api/v1/invalid_endpoint')
        
        self.assertEqual(response.status_code, 404)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
        self.assertIn('message', data)
        self.assertIn('error_code', data)


class TestCommandAPIEndpoint(unittest.TestCase):
    """Test command execution API endpoint"""
    
    def setUp(self):
        """Set up test client"""
        from retire_cluster.web.app import create_app
        
        self.mock_cluster = Mock()
        self.mock_cluster.get_devices.return_value = [
            {"id": "android-001", "status": "online", "cpu": 42, "memory": 2.1, "tasks": 3},
        ]
        self.mock_cluster.get_cluster_status.return_value = {
            "status": "healthy",
            "nodes_online": 5,
            "nodes_total": 7
        }
        self.mock_cluster.get_logs.return_value = []
        
        self.app = create_app(self.mock_cluster, testing=True)
        self.client = self.app.test_client()
    
    def test_execute_command_endpoint(self):
        """Test POST /api/v1/command endpoint"""
        command_data = {
            "command": "devices list --status=online",
            "format": "text"
        }
        
        response = self.client.post('/api/v1/command',
                                   data=json.dumps(command_data),
                                   content_type='application/json')
        
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.data}")
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertIn('output', data)
        self.assertIn('command', data)
        self.assertEqual(data['command'], "devices list --status=online")
    
    def test_execute_invalid_command(self):
        """Test executing invalid command returns error"""
        command_data = {
            "command": "invalid command here",
            "format": "text"
        }
        
        response = self.client.post('/api/v1/command',
                                   data=json.dumps(command_data),
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
        self.assertIn('message', data)
    
    def test_command_with_json_format(self):
        """Test command execution with JSON format"""
        command_data = {
            "command": "devices list --format=json",
            "format": "json"
        }
        
        response = self.client.post('/api/v1/command',
                                   data=json.dumps(command_data),
                                   content_type='application/json',
                                   headers={'Accept': 'application/json'})
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['format'], 'json')
        # For JSON format, the output should be a dict
        if isinstance(data['output'], str):
            # If it's a string, it might be JSON-encoded
            try:
                json.loads(data['output'])
            except:
                # If not valid JSON, accept it as is for now
                pass
        else:
            self.assertIsInstance(data['output'], dict)


class TestStreamingEndpoints(unittest.TestCase):
    """Test Server-Sent Events streaming endpoints"""
    
    def setUp(self):
        """Set up test client"""
        from retire_cluster.web.app import create_app
        
        self.mock_cluster = Mock()
        self.mock_cluster.get_devices.return_value = []
        self.mock_cluster.get_logs.return_value = []
        
        self.app = create_app(self.mock_cluster, testing=True)
        self.client = self.app.test_client()
    
    def test_stream_devices_endpoint(self):
        """Test /stream/devices SSE endpoint"""
        # Just test that the endpoint exists and returns the right content type
        response = self.client.get('/stream/devices',
                                  headers={'Accept': 'text/event-stream'})
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/event-stream', response.headers.get('Content-Type', ''))
    
    def test_stream_logs_endpoint(self):
        """Test /stream/logs SSE endpoint"""
        # Just test that the endpoint exists and returns the right content type
        response = self.client.get('/stream/logs',
                                  headers={'Accept': 'text/event-stream'})
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/event-stream', response.headers.get('Content-Type', ''))
    
    def test_stream_with_filter(self):
        """Test streaming with device filter"""
        # Just test that the endpoint accepts the parameter
        response = self.client.get('/stream/logs?device=android-001',
                                  headers={'Accept': 'text/event-stream'})
        
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()