"""
Integration tests for complete web interface functionality
"""

import unittest
import json
import time
import threading
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestWebInterfaceIntegration(unittest.TestCase):
    """Test complete web interface integration"""
    
    def setUp(self):
        """Set up test environment"""
        from retire_cluster.web.app import create_app
        from retire_cluster.web.cli_parser import CommandParser
        from retire_cluster.web.cli_executor import CommandExecutor
        from retire_cluster.web.terminal_renderer import TerminalRenderer
        
        # Create mock cluster server
        self.mock_cluster = Mock()
        self.setup_mock_data()
        
        # Create app and test client
        self.app = create_app(self.mock_cluster, testing=True)
        self.client = self.app.test_client()
        
        # Create individual components for testing
        self.parser = CommandParser()
        self.executor = CommandExecutor(self.mock_cluster)
        self.renderer = TerminalRenderer()
    
    def setup_mock_data(self):
        """Set up mock cluster data"""
        self.mock_devices = [
            {
                "id": "android-001",
                "status": "online",
                "cpu": 42,
                "memory": 2.1,
                "tasks": 3,
                "role": "worker",
                "platform": "android",
                "uptime": "2d 14h 32m"
            },
            {
                "id": "laptop-002", 
                "status": "online",
                "cpu": 15,
                "memory": 4.5,
                "tasks": 1,
                "role": "compute",
                "platform": "linux",
                "uptime": "5d 08h 15m"
            },
            {
                "id": "raspi-003",
                "status": "offline",
                "cpu": 0,
                "memory": 0,
                "tasks": 0,
                "role": "storage",
                "platform": "linux",
                "uptime": "0m"
            }
        ]
        
        self.mock_cluster_status = {
            "status": "healthy",
            "nodes_online": 2,
            "nodes_total": 3,
            "cpu_cores": 48,
            "cpu_usage": 37,
            "memory_total": 128,
            "memory_usage": 42,
            "tasks_active": 4,
            "tasks_completed": 45,
            "uptime": "15d 6h 42m"
        }
        
        self.mock_logs = [
            {
                "timestamp": "2024-01-15 10:30:15",
                "level": "INFO",
                "device": "android-001",
                "message": "Device connected successfully"
            },
            {
                "timestamp": "2024-01-15 10:30:16",
                "level": "ERROR",
                "device": "laptop-002", 
                "message": "Task execution failed: timeout"
            },
            {
                "timestamp": "2024-01-15 10:30:17",
                "level": "WARNING",
                "device": "raspi-003",
                "message": "Device heartbeat timeout"
            }
        ]
        
        # Configure mock returns
        self.mock_cluster.get_devices.return_value = self.mock_devices
        self.mock_cluster.get_cluster_status.return_value = self.mock_cluster_status
        self.mock_cluster.get_logs.return_value = self.mock_logs
    
    def test_complete_command_flow(self):
        """Test complete command execution flow"""
        # Test command parsing
        command = "devices list --status=online --format=table"
        parsed = self.parser.parse(command)
        
        expected_parsed = {
            "verb": "devices",
            "noun": "list",
            "options": {"status": "online", "format": "table"},
            "arguments": []
        }
        
        self.assertEqual(parsed, expected_parsed)
        
        # Test command validation
        self.assertTrue(self.parser.validate(parsed))
        
        # Test command execution
        result = self.executor.execute(parsed)
        self.assertEqual(result["status"], "success")
        self.assertIn("android-001", result["output"])
        self.assertIn("laptop-002", result["output"])
        self.assertNotIn("raspi-003", result["output"])  # Offline device filtered out
    
    def test_api_to_cli_integration(self):
        """Test API endpoint calling CLI components"""
        # Test command API endpoint
        command_data = {
            "command": "cluster status",
            "format": "text"
        }
        
        response = self.client.post('/api/v1/command',
                                   data=json.dumps(command_data),
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertIn('CLUSTER STATUS', data['output'])
        self.assertIn('HEALTHY', data['output'])  # Output is uppercase
        self.assertIn('2/3', data['output'])
    
    def test_text_api_consistency(self):
        """Test consistency between text API endpoints"""
        # Test devices endpoint
        response = self.client.get('/text/devices')
        self.assertEqual(response.status_code, 200)
        
        content = response.data.decode('utf-8')
        lines = content.strip().split('\n')
        self.assertEqual(len(lines), 3)  # Three devices
        
        # Check format consistency
        for line in lines:
            parts = line.split('|')
            self.assertEqual(len(parts), 5)  # id|status|cpu|memory|tasks
    
    def test_format_conversions(self):
        """Test different output format conversions"""
        formats = ['text', 'csv', 'tsv']
        
        for format_type in formats:
            if format_type == 'text':
                response = self.client.get('/text/devices')
            elif format_type == 'csv':
                response = self.client.get('/text/devices', 
                                          headers={'Accept': 'text/csv'})
            elif format_type == 'tsv':
                response = self.client.get('/text/devices',
                                          headers={'Accept': 'text/tab-separated-values'})
            
            self.assertEqual(response.status_code, 200)
            
            content = response.data.decode('utf-8')
            lines = content.strip().split('\n')
            
            if format_type == 'csv':
                # Check CSV header
                self.assertEqual(lines[0], 'id,status,cpu,memory,tasks')
            elif format_type == 'tsv':
                # Check TSV header
                self.assertEqual(lines[0], 'id\tstatus\tcpu\tmemory\ttasks')
    
    def test_cli_parser_edge_cases(self):
        """Test CLI parser with edge cases"""
        edge_cases = [
            ("", {"verb": None, "noun": None, "options": {}, "arguments": []}),
            ("   ", {"verb": None, "noun": None, "options": {}, "arguments": []}),
            ("help", {"verb": "help", "noun": None, "options": {}, "arguments": []}),
            ("devices list --", {"verb": "devices", "noun": "list", "options": {"": True}, "arguments": []}),
            ('echo "hello world"', {"verb": "echo", "noun": None, "options": {}, "arguments": ["hello world"]}),
        ]
        
        for command, expected in edge_cases:
            with self.subTest(command=command):
                result = self.parser.parse(command)
                self.assertEqual(result, expected)
    
    def test_terminal_rendering_integration(self):
        """Test terminal rendering with real data"""
        # Test table rendering
        table = self.renderer.render_table(
            self.mock_devices,
            headers=["ID", "STATUS", "CPU", "MEM", "TASKS"],
            fields=["id", "status", "cpu", "memory", "tasks"]
        )
        
        # Check table structure
        lines = table.split('\n')
        self.assertGreater(len(lines), 4)  # Header + separator + 3 devices
        
        # Check data presence
        self.assertIn("android-001", table)
        self.assertIn("laptop-002", table)
        self.assertIn("raspi-003", table)
        
        # Test metrics panel
        metrics = {
            "cpu_usage": self.mock_cluster_status["cpu_usage"],
            "memory_usage": self.mock_cluster_status["memory_usage"]
        }
        panel = self.renderer.render_metrics_panel(metrics)
        
        self.assertIn("CPU", panel)
        self.assertIn("37%", panel)
        self.assertIn("MEM", panel)
        self.assertIn("42%", panel)
    
    def test_error_handling_flow(self):
        """Test error handling throughout the system"""
        # Test invalid command
        invalid_command = {
            "command": "invalid_verb invalid_noun",
            "format": "text"
        }
        
        response = self.client.post('/api/v1/command',
                                   data=json.dumps(invalid_command),
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
        self.assertIn('message', data)
    
    def test_streaming_endpoints_basic(self):
        """Test streaming endpoints basic functionality"""
        # Test device stream
        response = self.client.get('/stream/devices',
                                  headers={'Accept': 'text/event-stream'})
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/event-stream', response.headers.get('Content-Type', ''))
        
        # Test log stream
        response = self.client.get('/stream/logs',
                                  headers={'Accept': 'text/event-stream'})
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/event-stream', response.headers.get('Content-Type', ''))
    
    def test_cli_interface_endpoint(self):
        """Test CLI interface HTML endpoint"""
        response = self.client.get('/cli')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/html', response.headers.get('Content-Type', ''))
        
        content = response.data.decode('utf-8')
        self.assertIn('RETIRE-CLUSTER', content)
        self.assertIn('terminal', content)
        self.assertIn('xterm.js', content)  # Updated to check for xterm.js instead
    
    def test_metrics_prometheus_format(self):
        """Test Prometheus metrics format"""
        response = self.client.get('/text/metrics')
        
        self.assertEqual(response.status_code, 200)
        
        content = response.data.decode('utf-8')
        
        # Check Prometheus format elements
        self.assertIn('# HELP', content)
        self.assertIn('# TYPE', content)
        self.assertIn('cluster_devices_total', content)
        self.assertIn('cluster_devices_online', content)
        self.assertIn('cluster_cpu_usage_percent', content)
        self.assertIn('cluster_memory_usage_percent', content)
    
    def test_command_suggestions(self):
        """Test command auto-completion suggestions"""
        test_cases = [
            ("dev", ["devices"]),
            ("devices l", ["devices list"]),
            ("cluster s", ["cluster status"]),
        ]
        
        for partial, expected_suggestions in test_cases:
            with self.subTest(partial=partial):
                suggestions = self.parser.suggest(partial)
                for expected in expected_suggestions:
                    self.assertIn(expected, suggestions)
    
    def test_data_filtering_integration(self):
        """Test data filtering across different components"""
        # Test device filtering via API
        response = self.client.get('/text/devices?status=online')
        
        content = response.data.decode('utf-8')
        lines = content.strip().split('\n')
        
        # Should only have online devices
        self.assertEqual(len(lines), 2)
        self.assertIn('android-001', content)
        self.assertIn('laptop-002', content)
        self.assertNotIn('raspi-003', content)
        
        # Test same filtering via command
        parsed = self.parser.parse("devices list --status=online")
        result = self.executor.execute(parsed)
        
        self.assertEqual(result["status"], "success")
        self.assertIn('android-001', result['output'])
        self.assertIn('laptop-002', result['output'])
        self.assertNotIn('raspi-003', result['output'])


class TestPerformanceIntegration(unittest.TestCase):
    """Test performance characteristics"""
    
    def setUp(self):
        """Set up performance test environment"""
        from retire_cluster.web.app import create_app
        
        # Create large dataset for performance testing
        self.large_device_list = []
        for i in range(1000):
            self.large_device_list.append({
                "id": f"device-{i:04d}",
                "status": "online" if i % 3 != 0 else "offline",
                "cpu": (i % 100),
                "memory": (i % 16) + 1,
                "tasks": i % 10
            })
        
        self.mock_cluster = Mock()
        self.mock_cluster.get_devices.return_value = self.large_device_list
        self.mock_cluster.get_cluster_status.return_value = {"status": "healthy"}
        self.mock_cluster.get_logs.return_value = []
        
        self.app = create_app(self.mock_cluster, testing=True)
        self.client = self.app.test_client()
    
    def test_large_device_list_performance(self):
        """Test performance with large device lists"""
        start_time = time.time()
        
        response = self.client.get('/text/devices')
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete within reasonable time (< 1 second)
        self.assertLess(duration, 1.0)
        self.assertEqual(response.status_code, 200)
        
        # Check content
        content = response.data.decode('utf-8')
        lines = content.strip().split('\n')
        self.assertEqual(len(lines), 1000)
    
    def test_csv_export_performance(self):
        """Test CSV export performance with large datasets"""
        start_time = time.time()
        
        response = self.client.get('/text/devices',
                                  headers={'Accept': 'text/csv'})
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete within reasonable time
        self.assertLess(duration, 2.0)
        self.assertEqual(response.status_code, 200)
        
        # Check CSV format
        content = response.data.decode('utf-8')
        lines = content.strip().split('\n')
        
        # Header + 1000 devices
        self.assertEqual(len(lines), 1001)
        self.assertEqual(lines[0], 'id,status,cpu,memory,tasks')


class TestErrorRecoveryIntegration(unittest.TestCase):
    """Test error recovery and resilience"""
    
    def setUp(self):
        """Set up error testing environment"""
        from retire_cluster.web.app import create_app
        
        self.mock_cluster = Mock()
        self.app = create_app(self.mock_cluster, testing=True)
        self.client = self.app.test_client()
    
    def test_cluster_server_failure_recovery(self):
        """Test behavior when cluster server fails"""
        # Simulate cluster server failure
        self.mock_cluster.get_devices.side_effect = Exception("Connection failed")
        
        # API should handle gracefully
        response = self.client.get('/text/devices')
        
        # Should return error but not crash
        self.assertEqual(response.status_code, 500)
    
    def test_malformed_request_handling(self):
        """Test handling of malformed requests"""
        # Test malformed JSON
        response = self.client.post('/api/v1/command',
                                   data='{"invalid": json}',
                                   content_type='application/json')
        
        # Should return error
        self.assertEqual(response.status_code, 400)
        
        # Test missing required fields
        response = self.client.post('/api/v1/command',
                                   data='{}',
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
    
    def test_resource_limits(self):
        """Test resource limit handling"""
        # Test very long command
        long_command = "echo " + "a" * 10000
        
        command_data = {
            "command": long_command,
            "format": "text"
        }
        
        response = self.client.post('/api/v1/command',
                                   data=json.dumps(command_data),
                                   content_type='application/json')
        
        # Should handle gracefully (either process or reject cleanly)
        self.assertIn(response.status_code, [200, 400, 413])


if __name__ == "__main__":
    unittest.main()