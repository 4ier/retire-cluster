#!/usr/bin/env python3
"""
Legacy-compatible worker node for Python 3.7
"""

import json
import socket
import time
import platform
import os
import argparse
from datetime import datetime


# Try to import psutil, fallback if not available
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class SimpleProfiler:
    def __init__(self, device_id, role):
        self.device_id = device_id
        self.role = role
        self.platform_info = self.detect_platform()
    
    def detect_platform(self):
        info = {
            'system': platform.system(),
            'release': platform.release(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'is_android': False
        }
        
        # Check for Android/Termux
        android_indicators = ['ANDROID_ROOT', 'ANDROID_DATA', 'PREFIX']
        if any(indicator in os.environ for indicator in android_indicators):
            info['is_android'] = True
            info['environment'] = 'termux'
        
        return info
    
    def get_device_profile(self):
        profile = {
            'device_id': self.device_id,
            'role': self.role,
            'platform': self.platform_info['system'].lower(),
            'platform_details': self.platform_info,
            'timestamp': datetime.now().isoformat(),
            'has_psutil': HAS_PSUTIL
        }
        
        # Get network info
        try:
            hostname = socket.gethostname()
            profile['hostname'] = hostname
            
            # Get IP address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(5)
            s.connect(("8.8.8.8", 80))
            profile['ip_address'] = s.getsockname()[0]
            s.close()
        except Exception:
            profile['hostname'] = 'unknown'
            profile['ip_address'] = '127.0.0.1'
        
        # Get hardware info
        if HAS_PSUTIL:
            try:
                profile['cpu_count'] = psutil.cpu_count()
                mem = psutil.virtual_memory()
                profile['memory_total_gb'] = round(mem.total / (1024**3), 2)
                disk = psutil.disk_usage('/')
                profile['storage_total_gb'] = round(disk.total / (1024**3), 2)
            except Exception:
                pass
        else:
            profile['cpu_count'] = os.cpu_count() or 1
        
        # Capabilities
        capabilities = {
            'computational': ['general_compute'],
            'services': ['network_tasks'],
            'automation': ['file_operations']
        }
        
        if self.platform_info.get('is_android'):
            capabilities['computational'].append('mobile_compute')
            capabilities['automation'].append('android_automation')
        
        profile['capabilities'] = capabilities
        
        # Tags
        tags = [self.platform_info['system'].lower(), self.role]
        if self.platform_info.get('is_android'):
            tags.extend(['android', 'mobile', 'termux'])
        
        profile['tags'] = tags
        
        return profile
    
    def get_metrics(self):
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'device_id': self.device_id
        }
        
        if HAS_PSUTIL:
            try:
                metrics['cpu_usage'] = psutil.cpu_percent(interval=1)
                mem = psutil.virtual_memory()
                metrics['memory_usage'] = mem.percent
                metrics['memory_available_gb'] = round(mem.available / (1024**3), 2)
                disk = psutil.disk_usage('/')
                metrics['storage_usage'] = round((disk.used / disk.total) * 100, 1)
                metrics['storage_free_gb'] = round(disk.free / (1024**3), 2)
            except Exception as e:
                metrics['error'] = str(e)
        else:
            metrics['note'] = 'psutil not available - limited metrics'
        
        return metrics


class SimpleClient:
    def __init__(self, device_id, role, main_host, main_port):
        self.device_id = device_id
        self.role = role
        self.main_host = main_host
        self.main_port = main_port
        self.profiler = SimpleProfiler(device_id, role)
        self.running = False
    
    def send_message(self, message, timeout=10):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((self.main_host, self.main_port))
            
            # Send message
            message_json = json.dumps(message)
            sock.send(message_json.encode('utf-8'))
            
            # Receive response
            response_data = sock.recv(8192).decode('utf-8')
            if response_data:
                response = json.loads(response_data)
                sock.close()
                return response
            
        except Exception as e:
            print(f"Communication error: {e}")
        finally:
            try:
                sock.close()
            except:
                pass
        
        return None
    
    def register(self):
        device_profile = self.profiler.get_device_profile()
        
        message = {
            'message_type': 'register',
            'sender_id': self.device_id,
            'data': device_profile
        }
        
        response = self.send_message(message)
        
        if response and response.get('message_type') == 'ack':
            result = response.get('data', {}).get('result', {})
            if result.get('success'):
                print(f"+ Successfully registered with main node")
                return True
            else:
                print(f"- Registration failed: {result}")
                return False
        else:
            print("- No valid response received for registration")
            return False
    
    def send_heartbeat(self):
        metrics = self.profiler.get_metrics()
        
        message = {
            'message_type': 'heartbeat',
            'sender_id': self.device_id,
            'data': {'metrics': metrics}
        }
        
        response = self.send_message(message, timeout=5)
        
        if response and response.get('message_type') == 'ack':
            result = response.get('data', {}).get('result', {})
            return result.get('success', False)
        
        return False
    
    def get_cluster_status(self):
        message = {
            'message_type': 'status',
            'sender_id': self.device_id,
            'data': {}
        }
        
        response = self.send_message(message)
        
        if response and response.get('message_type') == 'ack':
            return response.get('data', {}).get('result')
        
        return None
    
    def test_connection(self):
        try:
            status = self.get_cluster_status()
            if status:
                print("+ Connection test successful")
                return True
            else:
                print("- Connection test failed")
                return False
        except Exception as e:
            print(f"- Connection test failed: {e}")
            return False
    
    def run(self):
        print(f"Starting Worker Node: {self.device_id}")
        print(f"Role: {self.role}")
        print(f"Platform: {self.profiler.platform_info['system']}")
        print(f"Main Node: {self.main_host}:{self.main_port}")
        print(f"Has psutil: {HAS_PSUTIL}")
        print("-" * 50)
        
        # Test connection
        if not self.test_connection():
            print("Cannot connect to main node, exiting...")
            return
        
        # Register
        registered = False
        for attempt in range(3):
            if self.register():
                registered = True
                break
            print(f"Registration attempt {attempt + 1}/3 failed")
            time.sleep(5)
        
        if not registered:
            print("Failed to register after 3 attempts")
            return
        
        # Main loop
        print("Worker running... (Ctrl+C to stop)")
        self.running = True
        last_heartbeat = 0
        heartbeat_interval = 60
        
        while self.running:
            try:
                current_time = time.time()
                
                if current_time - last_heartbeat >= heartbeat_interval:
                    if self.send_heartbeat():
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        print(f"[{timestamp}] + Heartbeat sent")
                    else:
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        print(f"[{timestamp}] - Heartbeat failed")
                    last_heartbeat = current_time
                
                time.sleep(10)
                
            except KeyboardInterrupt:
                print("\nShutdown requested")
                self.running = False
            except Exception as e:
                print(f"Error in main loop: {e}")
                time.sleep(30)
        
        print("Worker stopped")


def main():
    parser = argparse.ArgumentParser(description='Simple Worker Node (Legacy)')
    parser.add_argument('--device-id', required=True, help='Device ID')
    parser.add_argument('--role', default='worker', help='Device role')
    parser.add_argument('--main-host', default='localhost', help='Main node host')
    parser.add_argument('--main-port', type=int, default=8080, help='Main node port')
    parser.add_argument('--test', action='store_true', help='Test mode only')
    
    args = parser.parse_args()
    
    client = SimpleClient(args.device_id, args.role, args.main_host, args.main_port)
    
    if args.test:
        print("=== Test Mode ===")
        profile = client.profiler.get_device_profile()
        print(f"Device ID: {profile['device_id']}")
        print(f"Platform: {profile['platform']}")
        print(f"Role: {profile['role']}")
        print(f"IP: {profile.get('ip_address', 'unknown')}")
        print(f"CPU cores: {profile.get('cpu_count', 'unknown')}")
        print(f"Memory: {profile.get('memory_total_gb', 'unknown')} GB")
        print(f"Storage: {profile.get('storage_total_gb', 'unknown')} GB")
        print(f"Tags: {', '.join(profile.get('tags', []))}")
        
        print("\nTesting connection...")
        if client.test_connection():
            status = client.get_cluster_status()
            if status:
                stats = status.get('cluster_stats', {})
                print(f"Cluster health: {stats.get('health_percentage', 0)}%")
                print(f"Online devices: {stats.get('online_devices', 0)}")
                print(f"Total devices: {stats.get('total_devices', 0)}")
                
                by_role = stats.get('by_role', {})
                if by_role:
                    print("Devices by role:")
                    for role, count in by_role.items():
                        print(f"  {role}: {count}")
    else:
        client.run()


if __name__ == "__main__":
    main()