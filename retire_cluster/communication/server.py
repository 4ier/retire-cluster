"""
Main node cluster server
"""

import socket
import threading
import time
from typing import Dict, Any, Optional, Callable
from datetime import datetime

from ..core.config import Config
from ..core.logger import get_logger
from ..core.exceptions import NetworkError, RegistrationError
from ..device.registry import DeviceRegistry
from .protocol import Message, MessageType, create_ack_message, create_error_message

logger = get_logger(__name__)


class ClusterServer:
    """Main node server for cluster management"""
    
    def __init__(self, config: Config):
        self.config = config
        self.registry = DeviceRegistry(
            persistent=True,
            db_path=config.database.path.replace('.db', '.json')  # Use JSON for simplicity
        )
        self.running = False
        self.server_socket: Optional[socket.socket] = None
        self.client_handlers: Dict[str, threading.Thread] = {}
        
        # Message handlers
        self.message_handlers = {
            MessageType.REGISTER: self._handle_register,
            MessageType.HEARTBEAT: self._handle_heartbeat,
            MessageType.STATUS: self._handle_status,
            MessageType.LIST_DEVICES: self._handle_list_devices,
            MessageType.DEVICE_INFO: self._handle_device_info,
        }
        
        logger.info(f"ClusterServer initialized on {config.server.host}:{config.server.port}")
    
    def start(self) -> None:
        """Start the cluster server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.config.server.host, self.config.server.port))
            self.server_socket.listen(self.config.server.max_connections)
            
            self.running = True
            
            # Start heartbeat monitor thread
            monitor_thread = threading.Thread(target=self._heartbeat_monitor, daemon=True)
            monitor_thread.start()
            
            logger.info(f"Cluster server listening on {self.config.server.host}:{self.config.server.port}")
            logger.info("Available message types: register, heartbeat, status, list_devices, device_info")
            
            # Main server loop
            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    
                    # Handle client in separate thread
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, client_address),
                        daemon=True
                    )
                    client_thread.start()
                    
                    # Clean up finished threads
                    self._cleanup_handlers()
                    
                except socket.error as e:
                    if self.running:
                        logger.error(f"Socket error: {e}")
                        break
                    
        except Exception as e:
            logger.error(f"Server startup failed: {e}")
            raise NetworkError(f"Failed to start server: {e}")
        finally:
            self.stop()
    
    def stop(self) -> None:
        """Stop the cluster server"""
        self.running = False
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception as e:
                logger.error(f"Error closing server socket: {e}")
        
        logger.info("Cluster server stopped")
    
    def _handle_client(self, client_socket: socket.socket, client_address: tuple) -> None:
        """Handle individual client connection"""
        client_id = f"{client_address[0]}:{client_address[1]}"
        logger.debug(f"Client connected: {client_id}")
        
        try:
            # Set socket timeout
            client_socket.settimeout(self.config.server.timeout)
            
            # Receive message
            data = client_socket.recv(4096).decode('utf-8')
            if not data:
                return
            
            try:
                message = Message.from_json(data)
                logger.debug(f"Received message from {client_id}: {message.message_type.value}")
                
                # Process message
                response = self._process_message(message, client_address)
                
                # Send response
                if response:
                    client_socket.send(response.to_json().encode('utf-8'))
                
            except Exception as e:
                logger.error(f"Error processing message from {client_id}: {e}")
                error_response = create_error_message("main_server", str(e))
                try:
                    client_socket.send(error_response.to_json().encode('utf-8'))
                except:
                    pass
                
        except socket.timeout:
            logger.warning(f"Client {client_id} timed out")
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass
            logger.debug(f"Client {client_id} disconnected")
    
    def _process_message(self, message: Message, client_address: tuple) -> Optional[Message]:
        """Process incoming message and return response"""
        handler = self.message_handlers.get(message.message_type)
        
        if not handler:
            error_msg = f"Unknown message type: {message.message_type.value}"
            logger.warning(error_msg)
            return create_error_message("main_server", error_msg, message.message_id)
        
        try:
            # Add client IP to message data for registration
            if message.message_type == MessageType.REGISTER:
                message.data['ip_address'] = client_address[0]
            
            result = handler(message)
            
            # Create acknowledgment response
            return create_ack_message("main_server", message.message_id, result)
            
        except Exception as e:
            logger.error(f"Handler error for {message.message_type.value}: {e}")
            return create_error_message("main_server", str(e), message.message_id)
    
    def _handle_register(self, message: Message) -> Dict[str, Any]:
        """Handle device registration"""
        device_data = message.data
        device_id = message.sender_id
        
        if not device_id:
            raise RegistrationError("sender_id is required for registration")
        
        # Add device_id to data if not present
        device_data['device_id'] = device_id
        
        success = self.registry.register_device(device_data)
        
        if success:
            logger.info(f"Device registered: {device_id} from {device_data.get('ip_address')}")
            return {
                'success': True,
                'device_id': device_id,
                'message': 'Device registered successfully'
            }
        else:
            raise RegistrationError("Failed to register device")
    
    def _handle_heartbeat(self, message: Message) -> Dict[str, Any]:
        """Handle device heartbeat"""
        device_id = message.sender_id
        metrics = message.data.get('metrics', {})
        
        success = self.registry.update_heartbeat(device_id, metrics)
        
        if success:
            logger.debug(f"Heartbeat received from {device_id}")
            return {'success': True, 'message': 'Heartbeat recorded'}
        else:
            logger.warning(f"Heartbeat failed for unregistered device: {device_id}")
            return {'success': False, 'message': 'Device not registered'}
    
    def _handle_status(self, message: Message) -> Dict[str, Any]:
        """Handle cluster status request"""
        filters = message.data
        role_filter = filters.get('role')
        
        if role_filter:
            devices = self.registry.get_online_devices(role=role_filter)
        else:
            devices = self.registry.get_online_devices()
        
        stats = self.registry.get_cluster_stats()
        
        return {
            'cluster_stats': stats,
            'online_devices': len(devices),
            'device_list': [d['device_id'] for d in devices],
            'timestamp': datetime.now().isoformat()
        }
    
    def _handle_list_devices(self, message: Message) -> Dict[str, Any]:
        """Handle list devices request"""
        filters = message.data
        status_filter = filters.get('status', 'all')
        role_filter = filters.get('role')
        
        if status_filter == 'online':
            devices = self.registry.get_online_devices(role=role_filter)
        elif status_filter == 'offline':
            all_devices = self.registry.get_all_devices()
            devices = [d for d in all_devices if d['status'] == 'offline']
            if role_filter:
                devices = [d for d in devices if d['role'] == role_filter]
        else:  # all
            devices = self.registry.get_all_devices()
            if role_filter:
                devices = [d for d in devices if d['role'] == role_filter]
        
        return {
            'devices': devices,
            'count': len(devices),
            'filters_applied': filters
        }
    
    def _handle_device_info(self, message: Message) -> Dict[str, Any]:
        """Handle device info request"""
        device_id = message.data.get('device_id')
        
        if not device_id:
            raise ValueError("device_id required for device info request")
        
        device = self.registry.get_device(device_id)
        
        if device:
            # Get recent heartbeats for this device
            recent_heartbeats = self.registry.get_recent_heartbeats(device_id, limit=10)
            
            return {
                'device': device,
                'recent_heartbeats': recent_heartbeats
            }
        else:
            return {
                'device': None,
                'error': f'Device {device_id} not found'
            }
    
    def _heartbeat_monitor(self) -> None:
        """Background thread to monitor device heartbeats"""
        logger.info("Heartbeat monitor started")
        
        while self.running:
            try:
                marked_offline = self.registry.mark_offline_devices(
                    self.config.heartbeat.timeout_threshold
                )
                
                if marked_offline > 0:
                    logger.warning(f"Marked {marked_offline} devices as offline")
                
                time.sleep(self.config.heartbeat.cleanup_interval)
                
            except Exception as e:
                logger.error(f"Heartbeat monitor error: {e}")
                time.sleep(60)
        
        logger.info("Heartbeat monitor stopped")
    
    def _cleanup_handlers(self) -> None:
        """Clean up finished client handler threads"""
        finished_handlers = [
            client_id for client_id, thread in self.client_handlers.items()
            if not thread.is_alive()
        ]
        
        for client_id in finished_handlers:
            del self.client_handlers[client_id]