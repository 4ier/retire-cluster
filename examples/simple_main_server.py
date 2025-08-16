#!/usr/bin/env python3
"""
Legacy-compatible main node for Python 3.7
"""

import json
import socket
import threading
import time
import os
from datetime import datetime, timedelta


# Simple configuration
class Config:
    def __init__(self):
        self.host = "0.0.0.0"
        self.port = 8080
        self.timeout = 10
        self.heartbeat_timeout = 300


# Simple device registry
class DeviceRegistry:
    def __init__(self):
        self.devices = {}
        self.heartbeat_history = []
        self.lock = threading.Lock()
    
    def register_device(self, device_data):
        with self.lock:
            device_id = device_data.get('device_id')
            if not device_id:
                return False
            
            self.devices[device_id] = {
                'device_id': device_id,
                'role': device_data.get('role', 'worker'),
                'status': 'online',
                'last_heartbeat': datetime.now().isoformat(),
                'registration_time': datetime.now().isoformat(),
                'ip_address': device_data.get('ip_address'),
                'platform': device_data.get('platform'),
                'capabilities': device_data.get('capabilities', {}),
                'tags': device_data.get('tags', []),
                'hardware': {
                    'cpu_count': device_data.get('cpu_count'),
                    'memory_total_gb': device_data.get('memory_total_gb'),
                    'storage_total_gb': device_data.get('storage_total_gb')
                }
            }
            print(f"[REGISTER] Device {device_id} registered from {device_data.get('ip_address')}")
            return True
    
    def update_heartbeat(self, device_id, metrics):
        with self.lock:
            if device_id not in self.devices:
                return False
            
            self.devices[device_id]['last_heartbeat'] = datetime.now().isoformat()
            self.devices[device_id]['status'] = 'online'
            
            self.heartbeat_history.append({
                'device_id': device_id,
                'timestamp': datetime.now().isoformat(),
                'metrics': metrics
            })
            
            # Keep only last 100 heartbeats
            if len(self.heartbeat_history) > 100:
                self.heartbeat_history = self.heartbeat_history[-100:]
            
            print(f"[HEARTBEAT] {device_id} - CPU: {metrics.get('cpu_usage', 'N/A')}%")
            return True
    
    def get_cluster_stats(self):
        with self.lock:
            online_devices = [d for d in self.devices.values() if d['status'] == 'online']
            
            # Count by role
            role_counts = {}
            for device in online_devices:
                role = device.get('role', 'unknown')
                role_counts[role] = role_counts.get(role, 0) + 1
            
            return {
                'total_devices': len(self.devices),
                'online_devices': len(online_devices),
                'health_percentage': round((len(online_devices) / len(self.devices)) * 100, 1) if self.devices else 0,
                'by_role': role_counts,
                'timestamp': datetime.now().isoformat()
            }
    
    def mark_offline_devices(self, timeout_seconds):
        with self.lock:
            timeout_threshold = datetime.now() - timedelta(seconds=timeout_seconds)
            marked_offline = 0
            
            for device_id, device in self.devices.items():
                try:
                    last_heartbeat = datetime.fromisoformat(device['last_heartbeat'])
                    if last_heartbeat < timeout_threshold and device['status'] == 'online':
                        device['status'] = 'offline'
                        marked_offline += 1
                        print(f"[MONITOR] Device {device_id} marked offline")
                except Exception:
                    pass
            
            return marked_offline


# Message processing
def process_message(data, client_address, registry):
    try:
        message = json.loads(data)
        message_type = message.get('message_type')
        sender_id = message.get('sender_id')
        message_data = message.get('data', {})
        
        if message_type == 'register':
            message_data['ip_address'] = client_address[0]
            message_data['device_id'] = sender_id
            success = registry.register_device(message_data)
            
            return {
                'message_type': 'ack',
                'sender_id': 'main_server',
                'data': {
                    'result': {
                        'success': success,
                        'device_id': sender_id,
                        'message': 'Device registered successfully' if success else 'Registration failed'
                    }
                }
            }
        
        elif message_type == 'heartbeat':
            metrics = message_data.get('metrics', {})
            success = registry.update_heartbeat(sender_id, metrics)
            
            return {
                'message_type': 'ack',
                'sender_id': 'main_server',
                'data': {
                    'result': {
                        'success': success,
                        'message': 'Heartbeat recorded' if success else 'Device not registered'
                    }
                }
            }
        
        elif message_type == 'status':
            stats = registry.get_cluster_stats()
            online_devices = [d['device_id'] for d in registry.devices.values() if d['status'] == 'online']
            
            return {
                'message_type': 'ack',
                'sender_id': 'main_server',
                'data': {
                    'result': {
                        'cluster_stats': stats,
                        'online_devices': len(online_devices),
                        'device_list': online_devices,
                        'timestamp': datetime.now().isoformat()
                    }
                }
            }
        
        else:
            return {
                'message_type': 'error',
                'sender_id': 'main_server',
                'data': {
                    'error': f'Unknown message type: {message_type}'
                }
            }
    
    except Exception as e:
        return {
            'message_type': 'error',
            'sender_id': 'main_server',
            'data': {
                'error': str(e)
            }
        }


# Client handler
def handle_client(client_socket, client_address, registry, config):
    try:
        client_socket.settimeout(config.timeout)
        
        # Receive message
        data = client_socket.recv(8192).decode('utf-8')
        if not data:
            return
        
        # Process message
        response = process_message(data, client_address, registry)
        
        # Send response
        if response:
            client_socket.send(json.dumps(response).encode('utf-8'))
    
    except Exception as e:
        print(f"Error handling client {client_address}: {e}")
    finally:
        try:
            client_socket.close()
        except:
            pass


# Heartbeat monitor
def heartbeat_monitor(registry, config):
    while True:
        try:
            marked_offline = registry.mark_offline_devices(config.heartbeat_timeout)
            if marked_offline > 0:
                print(f"[MONITOR] Marked {marked_offline} devices as offline")
            time.sleep(60)
        except Exception as e:
            print(f"Monitor error: {e}")
            time.sleep(60)


def main():
    print("Starting Retire-Cluster Main Node (Legacy Mode)...")
    
    config = Config()
    registry = DeviceRegistry()
    
    # Create directories
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Start heartbeat monitor
    monitor_thread = threading.Thread(target=heartbeat_monitor, args=(registry, config), daemon=True)
    monitor_thread.start()
    
    # Create server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((config.host, config.port))
        server_socket.listen(50)
        
        print(f"Retire-Cluster Main Node Server")
        print(f"Listening on {config.host}:{config.port}")
        print(f"Python version: {os.sys.version}")
        print(f"Supported messages: register, heartbeat, status")
        print("-" * 50)
        
        while True:
            try:
                client_socket, client_address = server_socket.accept()
                
                # Handle client in separate thread
                client_thread = threading.Thread(
                    target=handle_client,
                    args=(client_socket, client_address, registry, config),
                    daemon=True
                )
                client_thread.start()
                
            except socket.error as e:
                print(f"Socket error: {e}")
                break
    
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        server_socket.close()
        print("Server stopped")


if __name__ == "__main__":
    main()