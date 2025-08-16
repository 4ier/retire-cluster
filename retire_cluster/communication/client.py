"""
Worker node cluster client
"""

import socket
import time
from typing import Dict, Any, Optional
from datetime import datetime

from ..core.config import WorkerConfig
from ..core.logger import get_logger
from ..core.exceptions import NetworkError, RegistrationError
from ..device.profiler import DeviceProfiler
from .protocol import Message, MessageType, create_register_message, create_heartbeat_message, create_status_message

logger = get_logger(__name__)


class ClusterClient:
    """Worker node client for communicating with main node"""
    
    def __init__(self, config: WorkerConfig):
        self.config = config
        self.device_id = config.device_id
        self.profiler = DeviceProfiler(config.device_id, config.role)
        self.running = False
        
        logger.info(f"ClusterClient initialized for device {self.device_id}")
    
    def _send_message(self, message: Message, timeout: int = 10) -> Optional[Message]:
        """
        Send message to main node and return response
        
        Args:
            message: Message to send
            timeout: Socket timeout in seconds
            
        Returns:
            Response message or None if failed
        """
        try:
            # Create socket connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            
            # Connect to main node
            sock.connect((self.config.main_host, self.config.main_port))
            
            # Send message
            message_json = message.to_json()
            sock.send(message_json.encode('utf-8'))
            
            # Receive response
            response_data = sock.recv(8192).decode('utf-8')
            if response_data:
                response = Message.from_json(response_data)
                sock.close()
                return response
            
        except socket.timeout:
            logger.error(f"Connection to main node timed out after {timeout}s")
        except socket.error as e:
            logger.error(f"Socket error: {e}")
        except Exception as e:
            logger.error(f"Communication error: {e}")
        finally:
            try:
                sock.close()
            except:
                pass
        
        return None
    
    def register(self) -> bool:
        """
        Register with main node
        
        Returns:
            True if registration successful, False otherwise
        """
        try:
            # Get device profile
            device_profile = self.profiler.get_device_profile()
            
            # Add worker-specific configuration
            device_profile.update({
                'role': self.config.role,
                'max_concurrent_tasks': self.config.max_concurrent_tasks,
                'worker_config': {
                    'heartbeat_interval': self.config.heartbeat_interval,
                    'main_host': self.config.main_host,
                    'main_port': self.config.main_port
                }
            })
            
            # Create registration message
            message = create_register_message(self.device_id, device_profile)
            
            # Send registration
            response = self._send_message(message)
            
            if response and response.message_type == MessageType.ACK:
                result = response.data.get('result', {})
                if result.get('success'):
                    logger.info(f"Successfully registered with main node: {result.get('message')}")
                    return True
                else:
                    logger.error(f"Registration failed: {result}")
                    return False
            elif response and response.message_type == MessageType.ERROR:
                error_msg = response.data.get('error', 'Unknown error')
                logger.error(f"Registration error: {error_msg}")
                raise RegistrationError(error_msg)
            else:
                logger.error("No valid response received for registration")
                return False
                
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            raise RegistrationError(f"Registration failed: {e}")
    
    def send_heartbeat(self) -> bool:
        """
        Send heartbeat with current metrics
        
        Returns:
            True if heartbeat successful, False otherwise
        """
        try:
            # Get current metrics
            metrics = self.profiler.get_realtime_metrics()
            
            # Create heartbeat message
            message = create_heartbeat_message(self.device_id, metrics)
            
            # Send heartbeat
            response = self._send_message(message, timeout=5)
            
            if response and response.message_type == MessageType.ACK:
                result = response.data.get('result', {})
                success = result.get('success', False)
                
                if success:
                    logger.debug(f"Heartbeat sent successfully")
                else:
                    logger.warning(f"Heartbeat failed: {result.get('message')}")
                
                return success
            else:
                logger.warning("No valid response received for heartbeat")
                return False
                
        except Exception as e:
            logger.error(f"Heartbeat failed: {e}")
            return False
    
    def get_cluster_status(self, role_filter: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get cluster status from main node
        
        Args:
            role_filter: Filter devices by role (optional)
            
        Returns:
            Cluster status dictionary or None if failed
        """
        try:
            filters = {}
            if role_filter:
                filters['role'] = role_filter
            
            message = create_status_message(self.device_id, filters)
            response = self._send_message(message)
            
            if response and response.message_type == MessageType.ACK:
                return response.data.get('result')
            else:
                logger.error("Failed to get cluster status")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get cluster status: {e}")
            return None
    
    def test_connection(self) -> bool:
        """
        Test connection to main node
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            status = self.get_cluster_status()
            if status:
                logger.info("Connection test successful")
                return True
            else:
                logger.error("Connection test failed")
                return False
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def run(self) -> None:
        """
        Main worker loop - register and send periodic heartbeats
        """
        logger.info(f"Starting worker node {self.device_id}")
        logger.info(f"Role: {self.config.role}")
        logger.info(f"Main node: {self.config.main_host}:{self.config.main_port}")
        logger.info(f"Platform: {self.profiler.platform_info['system']}")
        logger.info(f"Has psutil: {self.profiler.get_device_profile().get('has_psutil', False)}")
        
        # Test connection first
        if not self.test_connection():
            logger.error("Cannot connect to main node, exiting...")
            return
        
        # Register with main node
        registered = False
        for attempt in range(5):
            try:
                if self.register():
                    registered = True
                    break
                else:
                    logger.warning(f"Registration attempt {attempt + 1}/5 failed")
                    
            except RegistrationError as e:
                logger.error(f"Registration error: {e}")
                break
            except Exception as e:
                logger.error(f"Registration attempt {attempt + 1}/5 failed: {e}")
            
            if attempt < 4:  # Don't sleep on last attempt
                time.sleep(5)
        
        if not registered:
            logger.error("Failed to register with main node after 5 attempts")
            return
        
        # Main worker loop
        logger.info("Worker node registered and running...")
        logger.info(f"Heartbeat interval: {self.config.heartbeat_interval}s")
        
        self.running = True
        last_heartbeat = 0
        
        while self.running:
            try:
                current_time = time.time()
                
                # Send heartbeat
                if current_time - last_heartbeat >= self.config.heartbeat_interval:
                    if self.send_heartbeat():
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        logger.info(f"[{timestamp}] Heartbeat sent")
                    else:
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        logger.warning(f"[{timestamp}] Heartbeat failed")
                    
                    last_heartbeat = current_time
                
                # Check for tasks (placeholder - task management not implemented yet)
                # TODO: Implement task checking and execution
                
                # Sleep briefly to avoid busy loop
                time.sleep(10)
                
            except KeyboardInterrupt:
                logger.info("Shutdown requested")
                self.running = False
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(30)  # Wait before retrying
        
        logger.info("Worker node stopped")
    
    def stop(self) -> None:
        """Stop the worker node"""
        self.running = False
        logger.info("Worker stop requested")