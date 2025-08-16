"""
Device management API routes
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

try:
    from flask import Blueprint, request, jsonify, g
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    class Blueprint:
        def __init__(self, *args, **kwargs):
            pass
        def route(self, *args, **kwargs):
            def decorator(f):
                return f
            return decorator

from ..models import (
    APIResponse, ErrorResponse, PaginatedResponse, DeviceInfo, 
    ResponseStatus, DEVICE_FILTER_SCHEMA
)
from ..middleware import LoggingMiddleware, AuthMiddleware, ValidationMiddleware


class DeviceRoutes:
    """Device management API routes"""
    
    def __init__(self, cluster_server):
        self.cluster_server = cluster_server
        self.logger = logging.getLogger("api.devices")
        
        # Create blueprint
        self.blueprint = Blueprint('devices', __name__, url_prefix='/api/v1/devices')
        
        # Middleware
        self.auth = AuthMiddleware()
        self.logging = LoggingMiddleware()
        self.validation = ValidationMiddleware()
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self):
        """Register all device routes"""
        
        @self.blueprint.route('', methods=['GET'])
        @self.logging
        def list_devices():
            """List all devices with optional filtering and pagination"""
            try:
                # Parse query parameters
                page = int(request.args.get('page', 1))
                page_size = min(int(request.args.get('page_size', 20)), 100)  # Max 100 items per page
                status_filter = request.args.get('status', 'all')
                role_filter = request.args.get('role')
                platform_filter = request.args.get('platform')
                tags_filter = request.args.getlist('tags')
                
                # Get devices from registry
                registry = self.cluster_server.device_registry
                all_devices = registry.get_all_devices()
                
                # Apply filters
                filtered_devices = self._filter_devices(
                    all_devices, status_filter, role_filter, platform_filter, tags_filter
                )
                
                # Apply pagination
                total_items = len(filtered_devices)
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                paginated_devices = filtered_devices[start_idx:end_idx]
                
                # Convert to DeviceInfo objects
                device_infos = []
                for device in paginated_devices:
                    device_info = DeviceInfo(
                        device_id=device['device_id'],
                        role=device.get('role', 'unknown'),
                        platform=device.get('platform', 'unknown'),
                        status=device.get('status', 'unknown'),
                        ip_address=device.get('ip_address'),
                        last_heartbeat=device.get('last_heartbeat'),
                        capabilities=device.get('capabilities', {}),
                        tags=device.get('tags', []),
                        uptime=self._calculate_uptime(device.get('last_heartbeat'))
                    )
                    device_infos.append(device_info.to_dict())
                
                response = PaginatedResponse(
                    status=ResponseStatus.SUCCESS,
                    data=device_infos,
                    page=page,
                    page_size=page_size,
                    total_items=total_items,
                    request_id=getattr(g, 'request_id', None)
                )
                
                return jsonify(response.to_dict())
                
            except ValueError as e:
                error_response = ErrorResponse(
                    message=f"Invalid query parameter: {str(e)}",
                    error_code="INVALID_PARAMETER",
                    request_id=getattr(g, 'request_id', None)
                )
                return jsonify(error_response.to_dict()), 400
                
            except Exception as e:
                self.logger.error(f"Error listing devices: {e}")
                error_response = ErrorResponse(
                    message="Failed to list devices",
                    error_code="LIST_DEVICES_ERROR",
                    error_details={'error': str(e)},
                    request_id=getattr(g, 'request_id', None)
                )
                return jsonify(error_response.to_dict()), 500
        
        @self.blueprint.route('/<device_id>', methods=['GET'])
        @self.logging
        def get_device(device_id: str):
            """Get detailed information about a specific device"""
            try:
                registry = self.cluster_server.device_registry
                device = registry.get_device(device_id)
                
                if not device:
                    error_response = ErrorResponse(
                        message=f"Device '{device_id}' not found",
                        error_code="DEVICE_NOT_FOUND",
                        request_id=getattr(g, 'request_id', None)
                    )
                    return jsonify(error_response.to_dict()), 404
                
                # Get detailed device information
                device_info = DeviceInfo(
                    device_id=device['device_id'],
                    role=device.get('role', 'unknown'),
                    platform=device.get('platform', 'unknown'),
                    status=device.get('status', 'unknown'),
                    ip_address=device.get('ip_address'),
                    last_heartbeat=device.get('last_heartbeat'),
                    capabilities=device.get('capabilities', {}),
                    tags=device.get('tags', []),
                    uptime=self._calculate_uptime(device.get('last_heartbeat'))
                )
                
                # Add additional details
                detailed_info = device_info.to_dict()
                detailed_info.update({
                    'registration_time': device.get('registration_time'),
                    'total_heartbeats': device.get('total_heartbeats', 0),
                    'last_error': device.get('last_error'),
                    'metrics_history': device.get('metrics_history', []),
                    'full_capabilities': device.get('full_capabilities', {})
                })
                
                response = APIResponse(
                    status=ResponseStatus.SUCCESS,
                    data=detailed_info,
                    request_id=getattr(g, 'request_id', None)
                )
                
                return jsonify(response.to_dict())
                
            except Exception as e:
                self.logger.error(f"Error getting device {device_id}: {e}")
                error_response = ErrorResponse(
                    message=f"Failed to get device '{device_id}'",
                    error_code="GET_DEVICE_ERROR",
                    error_details={'error': str(e)},
                    request_id=getattr(g, 'request_id', None)
                )
                return jsonify(error_response.to_dict()), 500
        
        @self.blueprint.route('/<device_id>/status', methods=['GET'])
        @self.logging
        def get_device_status(device_id: str):
            """Get current status of a specific device"""
            try:
                registry = self.cluster_server.device_registry
                device = registry.get_device(device_id)
                
                if not device:
                    error_response = ErrorResponse(
                        message=f"Device '{device_id}' not found",
                        error_code="DEVICE_NOT_FOUND",
                        request_id=getattr(g, 'request_id', None)
                    )
                    return jsonify(error_response.to_dict()), 404
                
                status_info = {
                    'device_id': device_id,
                    'status': device.get('status', 'unknown'),
                    'last_heartbeat': device.get('last_heartbeat'),
                    'uptime': self._calculate_uptime(device.get('last_heartbeat')),
                    'is_online': device.get('status') == 'online',
                    'response_time_ms': device.get('response_time_ms'),
                    'current_load': device.get('current_load', {}),
                    'last_metrics': device.get('last_metrics', {}),
                    'timestamp': datetime.now().isoformat()
                }
                
                response = APIResponse(
                    status=ResponseStatus.SUCCESS,
                    data=status_info,
                    request_id=getattr(g, 'request_id', None)
                )
                
                return jsonify(response.to_dict())
                
            except Exception as e:
                self.logger.error(f"Error getting device status {device_id}: {e}")
                error_response = ErrorResponse(
                    message=f"Failed to get device status for '{device_id}'",
                    error_code="GET_DEVICE_STATUS_ERROR",
                    error_details={'error': str(e)},
                    request_id=getattr(g, 'request_id', None)
                )
                return jsonify(error_response.to_dict()), 500
        
        @self.blueprint.route('/<device_id>/ping', methods=['POST'])
        @self.auth
        @self.logging
        def ping_device(device_id: str):
            """Send ping to a specific device to test connectivity"""
            try:
                registry = self.cluster_server.device_registry
                device = registry.get_device(device_id)
                
                if not device:
                    error_response = ErrorResponse(
                        message=f"Device '{device_id}' not found",
                        error_code="DEVICE_NOT_FOUND",
                        request_id=getattr(g, 'request_id', None)
                    )
                    return jsonify(error_response.to_dict()), 404
                
                # Attempt to ping the device (would need implementation in server)
                ping_start = datetime.now()
                
                # For now, simulate ping based on device status
                if device.get('status') == 'online':
                    ping_success = True
                    response_time = 50  # Simulated response time
                else:
                    ping_success = False
                    response_time = None
                
                ping_end = datetime.now()
                
                ping_result = {
                    'device_id': device_id,
                    'ping_successful': ping_success,
                    'response_time_ms': response_time,
                    'ping_timestamp': ping_start.isoformat(),
                    'duration_ms': (ping_end - ping_start).total_seconds() * 1000
                }
                
                response = APIResponse(
                    status=ResponseStatus.SUCCESS,
                    data=ping_result,
                    message="Ping completed" if ping_success else "Ping failed",
                    request_id=getattr(g, 'request_id', None)
                )
                
                return jsonify(response.to_dict())
                
            except Exception as e:
                self.logger.error(f"Error pinging device {device_id}: {e}")
                error_response = ErrorResponse(
                    message=f"Failed to ping device '{device_id}'",
                    error_code="PING_DEVICE_ERROR",
                    error_details={'error': str(e)},
                    request_id=getattr(g, 'request_id', None)
                )
                return jsonify(error_response.to_dict()), 500
        
        @self.blueprint.route('/<device_id>', methods=['DELETE'])
        @self.auth
        @self.logging
        def remove_device(device_id: str):
            """Remove a device from the cluster (requires authentication)"""
            try:
                registry = self.cluster_server.device_registry
                device = registry.get_device(device_id)
                
                if not device:
                    error_response = ErrorResponse(
                        message=f"Device '{device_id}' not found",
                        error_code="DEVICE_NOT_FOUND",
                        request_id=getattr(g, 'request_id', None)
                    )
                    return jsonify(error_response.to_dict()), 404
                
                # Remove device from registry
                registry.remove_device(device_id)
                
                removal_info = {
                    'device_id': device_id,
                    'removed_at': datetime.now().isoformat(),
                    'was_online': device.get('status') == 'online',
                    'removal_reason': 'manual_removal_via_api'
                }
                
                response = APIResponse(
                    status=ResponseStatus.SUCCESS,
                    data=removal_info,
                    message=f"Device '{device_id}' removed from cluster",
                    request_id=getattr(g, 'request_id', None)
                )
                
                return jsonify(response.to_dict())
                
            except Exception as e:
                self.logger.error(f"Error removing device {device_id}: {e}")
                error_response = ErrorResponse(
                    message=f"Failed to remove device '{device_id}'",
                    error_code="REMOVE_DEVICE_ERROR",
                    error_details={'error': str(e)},
                    request_id=getattr(g, 'request_id', None)
                )
                return jsonify(error_response.to_dict()), 500
        
        @self.blueprint.route('/summary', methods=['GET'])
        @self.logging
        def get_devices_summary():
            """Get summary statistics of all devices"""
            try:
                registry = self.cluster_server.device_registry
                all_devices = registry.get_all_devices()
                
                summary = {
                    'total_devices': len(all_devices),
                    'online_devices': len([d for d in all_devices if d.get('status') == 'online']),
                    'offline_devices': len([d for d in all_devices if d.get('status') != 'online']),
                    'by_role': {},
                    'by_platform': {},
                    'by_status': {},
                    'resource_totals': {
                        'cpu_cores': 0,
                        'memory_gb': 0,
                        'storage_gb': 0
                    },
                    'capabilities': {
                        'gpu_enabled': 0,
                        'mobile_devices': 0,
                        'server_grade': 0
                    }
                }
                
                for device in all_devices:
                    # Count by categories
                    role = device.get('role', 'unknown')
                    platform = device.get('platform', 'unknown')
                    status = device.get('status', 'unknown')
                    
                    summary['by_role'][role] = summary['by_role'].get(role, 0) + 1
                    summary['by_platform'][platform] = summary['by_platform'].get(platform, 0) + 1
                    summary['by_status'][status] = summary['by_status'].get(status, 0) + 1
                    
                    # Aggregate resources for online devices
                    if status == 'online':
                        summary['resource_totals']['cpu_cores'] += device.get('cpu_count', 0)
                        summary['resource_totals']['memory_gb'] += device.get('memory_total_gb', 0)
                        summary['resource_totals']['storage_gb'] += device.get('storage_total_gb', 0)
                        
                        # Count capabilities
                        if device.get('has_gpu'):
                            summary['capabilities']['gpu_enabled'] += 1
                        if device.get('role') == 'mobile':
                            summary['capabilities']['mobile_devices'] += 1
                        if device.get('cpu_count', 0) >= 8 and device.get('memory_total_gb', 0) >= 16:
                            summary['capabilities']['server_grade'] += 1
                
                response = APIResponse(
                    status=ResponseStatus.SUCCESS,
                    data=summary,
                    request_id=getattr(g, 'request_id', None)
                )
                
                return jsonify(response.to_dict())
                
            except Exception as e:
                self.logger.error(f"Error getting devices summary: {e}")
                error_response = ErrorResponse(
                    message="Failed to get devices summary",
                    error_code="DEVICES_SUMMARY_ERROR",
                    error_details={'error': str(e)},
                    request_id=getattr(g, 'request_id', None)
                )
                return jsonify(error_response.to_dict()), 500
    
    def _filter_devices(self, devices: List[Dict], status_filter: str, role_filter: Optional[str], 
                       platform_filter: Optional[str], tags_filter: List[str]) -> List[Dict]:
        """Filter devices based on criteria"""
        filtered = devices
        
        # Status filter
        if status_filter != 'all':
            if status_filter == 'online':
                filtered = [d for d in filtered if d.get('status') == 'online']
            elif status_filter == 'offline':
                filtered = [d for d in filtered if d.get('status') != 'online']
        
        # Role filter
        if role_filter:
            filtered = [d for d in filtered if d.get('role') == role_filter]
        
        # Platform filter
        if platform_filter:
            filtered = [d for d in filtered if d.get('platform') == platform_filter]
        
        # Tags filter
        if tags_filter:
            filtered = [d for d in filtered 
                       if all(tag in d.get('tags', []) for tag in tags_filter)]
        
        return filtered
    
    def _calculate_uptime(self, last_heartbeat: Optional[str]) -> Optional[str]:
        """Calculate device uptime from last heartbeat"""
        if not last_heartbeat:
            return None
        
        try:
            from datetime import datetime
            heartbeat_time = datetime.fromisoformat(last_heartbeat.replace('Z', '+00:00'))
            uptime_delta = datetime.now(heartbeat_time.tzinfo) - heartbeat_time
            
            days = uptime_delta.days
            hours, remainder = divmod(uptime_delta.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            if days > 0:
                return f"{days}d {hours}h {minutes}m"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
        except Exception:
            return None