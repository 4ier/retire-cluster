"""
Device profiling and system information collection
"""

import platform
import socket
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from ..core.logger import get_logger
from ..core.exceptions import DeviceError


logger = get_logger(__name__)


class DeviceProfiler:
    """Collects device hardware and software information"""
    
    def __init__(self, device_id: str, role: str = "worker"):
        self.device_id = device_id
        self.role = role
        self.platform_info = self._detect_platform()
        logger.info(f"DeviceProfiler initialized for {device_id} ({role})")
    
    def _detect_platform(self) -> Dict[str, Any]:
        """Detect platform and environment details"""
        info = {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'is_android': False,
            'is_virtual': False
        }
        
        # Check for Android/Termux
        android_indicators = ['ANDROID_ROOT', 'ANDROID_DATA', 'PREFIX']
        if any(indicator in os.environ for indicator in android_indicators):
            info['is_android'] = True
            info['environment'] = 'termux'
            logger.info("Detected Android/Termux environment")
            
            # Try to get Android version
            try:
                if os.path.exists('/system/build.prop'):
                    with open('/system/build.prop', 'r') as f:
                        for line in f:
                            if 'ro.build.version.release' in line:
                                info['android_version'] = line.split('=')[1].strip()
                                break
            except Exception as e:
                logger.debug(f"Could not read Android version: {e}")
        
        # Check for virtualization
        try:
            if HAS_PSUTIL:
                # Simple virtualization detection
                hostname = socket.gethostname().lower()
                virtual_indicators = ['vm', 'virtual', 'docker', 'container']
                if any(indicator in hostname for indicator in virtual_indicators):
                    info['is_virtual'] = True
        except Exception:
            pass
        
        return info
    
    def get_device_profile(self) -> Dict[str, Any]:
        """Collect comprehensive device profile"""
        logger.debug(f"Collecting device profile for {self.device_id}")
        
        profile = {
            'device_id': self.device_id,
            'role': self.role,
            'platform': self.platform_info['system'].lower(),
            'platform_details': self.platform_info,
            'timestamp': datetime.now().isoformat(),
            'has_psutil': HAS_PSUTIL
        }
        
        # Hardware information
        try:
            profile.update(self._get_hardware_info())
        except Exception as e:
            logger.warning(f"Could not get hardware info: {e}")
        
        # Network information
        try:
            profile.update(self._get_network_info())
        except Exception as e:
            logger.warning(f"Could not get network info: {e}")
        
        # Capabilities and tags
        profile['capabilities'] = self._detect_capabilities()
        profile['tags'] = self._generate_tags()
        
        logger.info(f"Device profile collected for {self.device_id}")
        return profile
    
    def _get_hardware_info(self) -> Dict[str, Any]:
        """Get hardware information"""
        info = {}
        
        # CPU information
        try:
            if HAS_PSUTIL:
                info['cpu_count'] = psutil.cpu_count(logical=False) or psutil.cpu_count()
                info['cpu_count_logical'] = psutil.cpu_count()
                
                cpu_freq = psutil.cpu_freq()
                if cpu_freq:
                    info['cpu_freq_mhz'] = cpu_freq.current
            else:
                info['cpu_count'] = os.cpu_count() or 1
                
        except Exception as e:
            logger.debug(f"CPU info error: {e}")
            info['cpu_count'] = os.cpu_count() or 1
        
        # Memory information
        try:
            if HAS_PSUTIL:
                mem = psutil.virtual_memory()
                info['memory_total_gb'] = round(mem.total / (1024**3), 2)
                info['memory_available_gb'] = round(mem.available / (1024**3), 2)
            else:
                # Fallback method for systems without psutil
                info['memory_total_gb'] = None
                
        except Exception as e:
            logger.debug(f"Memory info error: {e}")
        
        # Storage information
        try:
            if HAS_PSUTIL:
                disk = psutil.disk_usage('/')
                info['storage_total_gb'] = round(disk.total / (1024**3), 2)
                info['storage_free_gb'] = round(disk.free / (1024**3), 2)
            else:
                # Basic fallback
                try:
                    stat = os.statvfs('/')
                    total = stat.f_frsize * stat.f_blocks
                    free = stat.f_frsize * stat.f_available
                    info['storage_total_gb'] = round(total / (1024**3), 2)
                    info['storage_free_gb'] = round(free / (1024**3), 2)
                except AttributeError:
                    # Windows fallback
                    info['storage_total_gb'] = None
                    
        except Exception as e:
            logger.debug(f"Storage info error: {e}")
        
        return info
    
    def _get_network_info(self) -> Dict[str, Any]:
        """Get network information"""
        info = {}
        
        try:
            # Hostname
            info['hostname'] = socket.gethostname()
            
            # IP address
            try:
                # Try to get primary IP by connecting to external host
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.settimeout(5)
                s.connect(("8.8.8.8", 80))
                info['ip_address'] = s.getsockname()[0]
                s.close()
            except Exception:
                # Fallback to hostname resolution
                try:
                    info['ip_address'] = socket.gethostbyname(info['hostname'])
                except Exception:
                    info['ip_address'] = '127.0.0.1'
            
            # Network interfaces (if psutil available)
            if HAS_PSUTIL:
                try:
                    interfaces = psutil.net_if_addrs()
                    info['network_interfaces'] = list(interfaces.keys())
                except Exception:
                    pass
                    
        except Exception as e:
            logger.debug(f"Network info error: {e}")
            info['hostname'] = 'unknown'
            info['ip_address'] = '127.0.0.1'
        
        return info
    
    def _detect_capabilities(self) -> Dict[str, List[str]]:
        """Detect device capabilities"""
        capabilities = {
            'computational': [],
            'services': [],
            'automation': []
        }
        
        # Basic computational capabilities
        if self.platform_info.get('is_android'):
            capabilities['computational'].extend(['mobile_compute', 'low_power'])
            capabilities['automation'].append('android_automation')
        else:
            capabilities['computational'].append('general_compute')
        
        # Check for GPU capabilities (simplified)
        try:
            if HAS_PSUTIL and not self.platform_info.get('is_android'):
                # Try to detect NVIDIA GPU
                import subprocess
                result = subprocess.run(['nvidia-smi'], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=5)
                if result.returncode == 0:
                    capabilities['computational'].append('gpu_compute')
        except Exception:
            pass
        
        # Storage capabilities
        if HAS_PSUTIL:
            try:
                disk = psutil.disk_usage('/')
                if disk.total > 100 * (1024**3):  # More than 100GB
                    capabilities['services'].append('storage')
                if disk.total > 1 * (1024**4):  # More than 1TB
                    capabilities['services'].append('large_storage')
            except Exception:
                pass
        
        # Network capabilities
        capabilities['services'].extend(['network_tasks', 'http_server'])
        
        # Automation capabilities
        capabilities['automation'].extend(['file_operations', 'script_execution'])
        
        # Add role-specific capabilities
        if self.role in ['storage', 'nas']:
            capabilities['services'].extend(['backup', 'file_sync'])
        elif self.role in ['compute', 'gpu']:
            capabilities['computational'].extend(['parallel_processing'])
        
        return capabilities
    
    def _generate_tags(self) -> List[str]:
        """Generate descriptive tags for the device"""
        tags = []
        
        # Platform tags
        tags.append(self.platform_info['system'].lower())
        if self.platform_info.get('is_android'):
            tags.extend(['android', 'mobile', 'termux'])
        
        # Architecture tags
        machine = self.platform_info.get('machine', '').lower()
        if 'arm' in machine or 'aarch' in machine:
            tags.append('arm')
        elif 'x86' in machine or 'amd64' in machine:
            tags.append('x86')
        
        # Resource tags
        if HAS_PSUTIL:
            try:
                mem = psutil.virtual_memory()
                if mem.total < 2 * (1024**3):
                    tags.append('low_memory')
                elif mem.total > 8 * (1024**3):
                    tags.append('high_memory')
                
                cpu_count = psutil.cpu_count()
                if cpu_count and cpu_count <= 2:
                    tags.append('low_cpu')
                elif cpu_count and cpu_count >= 8:
                    tags.append('high_cpu')
            except Exception:
                pass
        
        # Virtualization tag
        if self.platform_info.get('is_virtual'):
            tags.append('virtual')
        
        # Role tag
        tags.append(self.role)
        
        return tags
    
    def get_realtime_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        logger.debug(f"Collecting real-time metrics for {self.device_id}")
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'device_id': self.device_id
        }
        
        if not HAS_PSUTIL:
            metrics['note'] = 'psutil not available - limited metrics'
            return metrics
        
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics['cpu_usage'] = cpu_percent
            
            # Memory metrics
            mem = psutil.virtual_memory()
            metrics['memory_usage'] = mem.percent
            metrics['memory_available_gb'] = round(mem.available / (1024**3), 2)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            metrics['storage_usage'] = round((disk.used / disk.total) * 100, 1)
            metrics['storage_free_gb'] = round(disk.free / (1024**3), 2)
            
            # Network metrics (basic)
            net_io = psutil.net_io_counters()
            if net_io:
                metrics['network_bytes_sent'] = net_io.bytes_sent
                metrics['network_bytes_recv'] = net_io.bytes_recv
            
            # Load average (Unix-like systems)
            try:
                load_avg = psutil.getloadavg()
                metrics['load_average_1m'] = round(load_avg[0], 2)
                metrics['load_average_5m'] = round(load_avg[1], 2)
                metrics['load_average_15m'] = round(load_avg[2], 2)
            except (AttributeError, OSError):
                # Not available on Windows
                pass
            
            # Temperature (if available)
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    all_temps = []
                    for name, entries in temps.items():
                        for entry in entries:
                            if entry.current and entry.current > 0:
                                all_temps.append(entry.current)
                    if all_temps:
                        metrics['temperature_avg'] = round(sum(all_temps) / len(all_temps), 1)
                        metrics['temperature_max'] = round(max(all_temps), 1)
            except Exception:
                pass
            
            # Battery (for mobile devices)
            if self.platform_info.get('is_android'):
                try:
                    battery = psutil.sensors_battery()
                    if battery:
                        metrics['battery_percent'] = battery.percent
                        metrics['battery_charging'] = battery.power_plugged
                except Exception:
                    pass
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            raise DeviceError(f"Failed to collect metrics: {e}")
        
        logger.debug(f"Metrics collected for {self.device_id}")
        return metrics