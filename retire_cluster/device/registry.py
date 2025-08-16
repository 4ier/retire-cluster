"""
Device registry for managing cluster devices
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from threading import Lock

from ..core.logger import get_logger
from ..core.exceptions import DeviceError, RegistrationError, DatabaseError

logger = get_logger(__name__)


class DeviceRegistry:
    """
    In-memory device registry with optional persistence
    Thread-safe device management
    """
    
    def __init__(self, persistent: bool = False, db_path: Optional[str] = None):
        self.devices: Dict[str, Dict[str, Any]] = {}
        self.heartbeat_history: List[Dict[str, Any]] = []
        self.persistent = persistent
        self.db_path = db_path
        self._lock = Lock()
        
        if persistent and db_path:
            self._init_database()
        
        logger.info(f"DeviceRegistry initialized (persistent={persistent})")
    
    def _init_database(self):
        """Initialize database if using persistent storage"""
        try:
            # For now, use JSON file as simple persistence
            # In production, this would use SQLite or another database
            if self.db_path and self.db_path.endswith('.json'):
                self._load_from_json()
            else:
                logger.warning("Database persistence not implemented for this storage type")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise DatabaseError(f"Database initialization failed: {e}")
    
    def _load_from_json(self):
        """Load devices from JSON file"""
        try:
            import os
            if os.path.exists(self.db_path):
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.devices = data.get('devices', {})
                    self.heartbeat_history = data.get('heartbeat_history', [])
                    logger.info(f"Loaded {len(self.devices)} devices from {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to load from JSON: {e}")
    
    def _save_to_json(self):
        """Save devices to JSON file"""
        try:
            import os
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            data = {
                'devices': self.devices,
                'heartbeat_history': self.heartbeat_history[-100:]  # Keep last 100
            }
            
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Failed to save to JSON: {e}")
    
    def register_device(self, device_data: Dict[str, Any]) -> bool:
        """
        Register or update device in the registry
        
        Args:
            device_data: Device information dictionary
            
        Returns:
            True if successful, False otherwise
        """
        device_id = device_data.get('device_id')
        if not device_id:
            raise RegistrationError("device_id is required")
        
        with self._lock:
            try:
                # Check if device exists
                is_new_device = device_id not in self.devices
                
                # Prepare device record
                device_record = {
                    'device_id': device_id,
                    'role': device_data.get('role', 'worker'),
                    'status': 'online',
                    'last_heartbeat': datetime.now().isoformat(),
                    'ip_address': device_data.get('ip_address'),
                    'platform': device_data.get('platform'),
                    'platform_details': device_data.get('platform_details', {}),
                    'capabilities': device_data.get('capabilities', {}),
                    'tags': device_data.get('tags', []),
                    'description': device_data.get('description', ''),
                    'hardware': {
                        'cpu_count': device_data.get('cpu_count'),
                        'memory_total_gb': device_data.get('memory_total_gb'),
                        'storage_total_gb': device_data.get('storage_total_gb'),
                        'hostname': device_data.get('hostname')
                    },
                    'last_updated': datetime.now().isoformat()
                }
                
                # Set registration time for new devices
                if is_new_device:
                    device_record['registration_time'] = datetime.now().isoformat()
                    logger.info(f"Registering new device: {device_id}")
                else:
                    device_record['registration_time'] = self.devices[device_id].get('registration_time')
                    logger.info(f"Updating existing device: {device_id}")
                
                # Store device
                self.devices[device_id] = device_record
                
                # Save to persistent storage if enabled
                if self.persistent and self.db_path:
                    self._save_to_json()
                
                logger.info(f"Device {device_id} registered successfully (role: {device_record['role']})")
                return True
                
            except Exception as e:
                logger.error(f"Failed to register device {device_id}: {e}")
                raise RegistrationError(f"Device registration failed: {e}")
    
    def update_heartbeat(self, device_id: str, metrics: Dict[str, Any]) -> bool:
        """
        Update device heartbeat and metrics
        
        Args:
            device_id: Device identifier
            metrics: Device metrics dictionary
            
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            try:
                if device_id not in self.devices:
                    logger.warning(f"Heartbeat received for unregistered device: {device_id}")
                    return False
                
                # Update device status
                self.devices[device_id]['last_heartbeat'] = datetime.now().isoformat()
                self.devices[device_id]['status'] = 'online'
                self.devices[device_id]['last_updated'] = datetime.now().isoformat()
                
                # Record heartbeat history
                heartbeat_record = {
                    'device_id': device_id,
                    'timestamp': datetime.now().isoformat(),
                    'metrics': metrics
                }
                
                self.heartbeat_history.append(heartbeat_record)
                
                # Keep only recent heartbeats (last 1000)
                if len(self.heartbeat_history) > 1000:
                    self.heartbeat_history = self.heartbeat_history[-1000:]
                
                # Save to persistent storage if enabled
                if self.persistent and self.db_path:
                    self._save_to_json()
                
                logger.debug(f"Heartbeat updated for device {device_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to update heartbeat for {device_id}: {e}")
                return False
    
    def get_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get device information by ID"""
        with self._lock:
            return self.devices.get(device_id)
    
    def get_all_devices(self) -> List[Dict[str, Any]]:
        """Get all registered devices"""
        with self._lock:
            return list(self.devices.values())
    
    def get_online_devices(self, role: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of online devices, optionally filtered by role
        
        Args:
            role: Filter by device role (optional)
            
        Returns:
            List of online device dictionaries
        """
        with self._lock:
            devices = [d for d in self.devices.values() if d['status'] == 'online']
            
            if role:
                devices = [d for d in devices if d['role'] == role]
            
            return devices
    
    def get_devices_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """Get devices that have a specific tag"""
        with self._lock:
            devices = []
            for device in self.devices.values():
                if tag in device.get('tags', []):
                    devices.append(device)
            return devices
    
    def get_devices_by_capability(self, capability_type: str, capability: str) -> List[Dict[str, Any]]:
        """Get devices that have a specific capability"""
        with self._lock:
            devices = []
            for device in self.devices.values():
                device_capabilities = device.get('capabilities', {})
                if capability in device_capabilities.get(capability_type, []):
                    devices.append(device)
            return devices
    
    def mark_offline_devices(self, timeout_seconds: int = 300) -> int:
        """
        Mark devices as offline if heartbeat timeout exceeded
        
        Args:
            timeout_seconds: Timeout threshold in seconds
            
        Returns:
            Number of devices marked offline
        """
        with self._lock:
            timeout_threshold = datetime.now() - timedelta(seconds=timeout_seconds)
            marked_offline = 0
            
            for device_id, device in self.devices.items():
                try:
                    last_heartbeat = datetime.fromisoformat(device['last_heartbeat'])
                    if last_heartbeat < timeout_threshold and device['status'] == 'online':
                        device['status'] = 'offline'
                        device['last_updated'] = datetime.now().isoformat()
                        marked_offline += 1
                        logger.warning(f"Device {device_id} marked offline (last heartbeat: {device['last_heartbeat']})")
                except (ValueError, TypeError) as e:
                    logger.error(f"Invalid heartbeat timestamp for device {device_id}: {e}")
            
            if marked_offline > 0:
                # Save to persistent storage if enabled
                if self.persistent and self.db_path:
                    self._save_to_json()
            
            return marked_offline
    
    def remove_device(self, device_id: str) -> bool:
        """Remove device from registry"""
        with self._lock:
            if device_id in self.devices:
                del self.devices[device_id]
                
                # Remove from heartbeat history
                self.heartbeat_history = [
                    h for h in self.heartbeat_history 
                    if h.get('device_id') != device_id
                ]
                
                # Save to persistent storage if enabled
                if self.persistent and self.db_path:
                    self._save_to_json()
                
                logger.info(f"Device {device_id} removed from registry")
                return True
            return False
    
    def get_cluster_stats(self) -> Dict[str, Any]:
        """Get cluster statistics"""
        with self._lock:
            online_devices = [d for d in self.devices.values() if d['status'] == 'online']
            offline_devices = [d for d in self.devices.values() if d['status'] == 'offline']
            
            # Calculate total resources
            total_cpu = sum(d.get('hardware', {}).get('cpu_count', 0) for d in online_devices if d.get('hardware', {}).get('cpu_count'))
            total_memory = sum(d.get('hardware', {}).get('memory_total_gb', 0) for d in online_devices if d.get('hardware', {}).get('memory_total_gb'))
            total_storage = sum(d.get('hardware', {}).get('storage_total_gb', 0) for d in online_devices if d.get('hardware', {}).get('storage_total_gb'))
            
            # Count by role
            role_counts = {}
            for device in online_devices:
                role = device.get('role', 'unknown')
                role_counts[role] = role_counts.get(role, 0) + 1
            
            # Count by platform
            platform_counts = {}
            for device in online_devices:
                platform = device.get('platform', 'unknown')
                platform_counts[platform] = platform_counts.get(platform, 0) + 1
            
            return {
                'total_devices': len(self.devices),
                'online_devices': len(online_devices),
                'offline_devices': len(offline_devices),
                'health_percentage': round((len(online_devices) / len(self.devices)) * 100, 1) if self.devices else 0,
                'total_resources': {
                    'cpu_cores': total_cpu,
                    'memory_gb': round(total_memory, 2),
                    'storage_gb': round(total_storage, 2)
                },
                'by_role': role_counts,
                'by_platform': platform_counts,
                'last_updated': datetime.now().isoformat()
            }
    
    def get_recent_heartbeats(self, device_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent heartbeat history"""
        with self._lock:
            heartbeats = self.heartbeat_history
            
            if device_id:
                heartbeats = [h for h in heartbeats if h.get('device_id') == device_id]
            
            # Return most recent first
            return sorted(heartbeats, key=lambda x: x['timestamp'], reverse=True)[:limit]