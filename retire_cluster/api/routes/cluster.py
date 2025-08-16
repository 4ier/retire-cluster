"""
Cluster management API routes
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any

try:
    from flask import Blueprint, request, jsonify, g
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    # Mock Blueprint for when Flask is not available
    class Blueprint:
        def __init__(self, *args, **kwargs):
            pass
        def route(self, *args, **kwargs):
            def decorator(f):
                return f
            return decorator

from ..models import APIResponse, ErrorResponse, ClusterStats, ResponseStatus
from ..middleware import LoggingMiddleware, AuthMiddleware


class ClusterRoutes:
    """Cluster management API routes"""
    
    def __init__(self, cluster_server, task_scheduler=None):
        self.cluster_server = cluster_server
        self.task_scheduler = task_scheduler
        self.logger = logging.getLogger("api.cluster")
        
        # Create blueprint
        self.blueprint = Blueprint('cluster', __name__, url_prefix='/api/v1/cluster')
        
        # Middleware
        self.auth = AuthMiddleware()
        self.logging = LoggingMiddleware()
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self):
        """Register all cluster routes"""
        
        @self.blueprint.route('/status', methods=['GET'])
        @self.logging
        def get_cluster_status():
            """Get overall cluster status and statistics"""
            try:
                # Get cluster statistics from registry
                registry = self.cluster_server.device_registry
                stats = registry.get_cluster_stats()
                
                # Add scheduler statistics if available
                if self.task_scheduler:
                    scheduler_stats = self.task_scheduler.get_cluster_statistics()
                    stats.update(scheduler_stats)
                
                cluster_stats = ClusterStats(
                    total_devices=stats.get('total_devices', 0),
                    online_devices=stats.get('online_devices', 0),
                    offline_devices=stats.get('offline_devices', 0),
                    health_percentage=stats.get('health_percentage', 0),
                    total_resources=stats.get('total_resources', {}),
                    by_role=stats.get('by_role', {}),
                    by_platform=stats.get('by_platform', {}),
                    by_status=stats.get('by_status', {})
                )
                
                response = APIResponse(
                    status=ResponseStatus.SUCCESS,
                    data={
                        'cluster_stats': cluster_stats.to_dict(),
                        'server_info': {
                            'version': '1.0.0',
                            'uptime': self._get_server_uptime(),
                            'host': self.cluster_server.config.server.host,
                            'port': self.cluster_server.config.server.port
                        },
                        'timestamp': datetime.now().isoformat()
                    },
                    request_id=getattr(g, 'request_id', None)
                )
                
                return jsonify(response.to_dict())
                
            except Exception as e:
                self.logger.error(f"Error getting cluster status: {e}")
                error_response = ErrorResponse(
                    message="Failed to get cluster status",
                    error_code="CLUSTER_STATUS_ERROR",
                    error_details={'error': str(e)},
                    request_id=getattr(g, 'request_id', None)
                )
                return jsonify(error_response.to_dict()), 500
        
        @self.blueprint.route('/health', methods=['GET'])
        def get_health_check():
            """Simple health check endpoint"""
            try:
                # Basic health checks
                health_status = {
                    'api': 'healthy',
                    'cluster_server': 'healthy' if self.cluster_server else 'unhealthy',
                    'task_scheduler': 'healthy' if self.task_scheduler else 'not_configured',
                    'timestamp': datetime.now().isoformat()
                }
                
                # Check if we can access the device registry
                try:
                    registry = self.cluster_server.device_registry
                    device_count = len(registry.get_all_devices())
                    health_status['device_registry'] = 'healthy'
                    health_status['device_count'] = device_count
                except Exception:
                    health_status['device_registry'] = 'unhealthy'
                
                # Determine overall health
                unhealthy_components = [k for k, v in health_status.items() 
                                     if isinstance(v, str) and 'unhealthy' in v]
                
                overall_status = 'healthy' if not unhealthy_components else 'degraded'
                
                response = APIResponse(
                    status=ResponseStatus.SUCCESS,
                    data={
                        'status': overall_status,
                        'components': health_status,
                        'unhealthy_components': unhealthy_components
                    }
                )
                
                status_code = 200 if overall_status == 'healthy' else 503
                return jsonify(response.to_dict()), status_code
                
            except Exception as e:
                error_response = ErrorResponse(
                    message="Health check failed",
                    error_code="HEALTH_CHECK_ERROR",
                    error_details={'error': str(e)}
                )
                return jsonify(error_response.to_dict()), 500
        
        @self.blueprint.route('/metrics', methods=['GET'])
        @self.logging
        def get_cluster_metrics():
            """Get detailed cluster metrics"""
            try:
                registry = self.cluster_server.device_registry
                devices = registry.get_all_devices()
                
                # Calculate detailed metrics
                metrics = {
                    'devices': {
                        'total': len(devices),
                        'online': len([d for d in devices if d.get('status') == 'online']),
                        'by_role': {},
                        'by_platform': {},
                        'resource_utilization': {}
                    },
                    'resources': {
                        'total_cpu_cores': 0,
                        'total_memory_gb': 0,
                        'total_storage_gb': 0,
                        'average_utilization': 0
                    },
                    'performance': {
                        'average_response_time': 0,
                        'request_rate': 0,
                        'error_rate': 0
                    }
                }
                
                # Aggregate device metrics
                for device in devices:
                    role = device.get('role', 'unknown')
                    platform = device.get('platform', 'unknown')
                    
                    metrics['devices']['by_role'][role] = metrics['devices']['by_role'].get(role, 0) + 1
                    metrics['devices']['by_platform'][platform] = metrics['devices']['by_platform'].get(platform, 0) + 1
                    
                    # Aggregate resources
                    if device.get('status') == 'online':
                        metrics['resources']['total_cpu_cores'] += device.get('cpu_count', 0)
                        metrics['resources']['total_memory_gb'] += device.get('memory_total_gb', 0)
                        metrics['resources']['total_storage_gb'] += device.get('storage_total_gb', 0)
                
                # Add task metrics if scheduler is available
                if self.task_scheduler:
                    scheduler_stats = self.task_scheduler.get_cluster_statistics()
                    metrics['tasks'] = scheduler_stats.get('queue_stats', {})
                
                response = APIResponse(
                    status=ResponseStatus.SUCCESS,
                    data=metrics,
                    request_id=getattr(g, 'request_id', None)
                )
                
                return jsonify(response.to_dict())
                
            except Exception as e:
                self.logger.error(f"Error getting cluster metrics: {e}")
                error_response = ErrorResponse(
                    message="Failed to get cluster metrics",
                    error_code="METRICS_ERROR",
                    error_details={'error': str(e)},
                    request_id=getattr(g, 'request_id', None)
                )
                return jsonify(error_response.to_dict()), 500
        
        @self.blueprint.route('/config', methods=['GET'])
        @self.auth
        @self.logging
        def get_cluster_config():
            """Get cluster configuration (requires authentication)"""
            try:
                config_data = {
                    'server': {
                        'host': self.cluster_server.config.server.host,
                        'port': self.cluster_server.config.server.port,
                        'max_connections': self.cluster_server.config.server.max_connections
                    },
                    'heartbeat': {
                        'interval': self.cluster_server.config.heartbeat.interval,
                        'timeout': self.cluster_server.config.heartbeat.timeout,
                        'max_missed': self.cluster_server.config.heartbeat.max_missed
                    },
                    'features': {
                        'task_scheduling': self.task_scheduler is not None,
                        'api_enabled': True,
                        'auth_required': self.auth.require_auth
                    }
                }
                
                response = APIResponse(
                    status=ResponseStatus.SUCCESS,
                    data=config_data,
                    request_id=getattr(g, 'request_id', None)
                )
                
                return jsonify(response.to_dict())
                
            except Exception as e:
                self.logger.error(f"Error getting cluster config: {e}")
                error_response = ErrorResponse(
                    message="Failed to get cluster configuration",
                    error_code="CONFIG_ERROR",
                    error_details={'error': str(e)},
                    request_id=getattr(g, 'request_id', None)
                )
                return jsonify(error_response.to_dict()), 500
        
        @self.blueprint.route('/shutdown', methods=['POST'])
        @self.auth
        @self.logging  
        def shutdown_cluster():
            """Shutdown the cluster (requires authentication)"""
            try:
                # Graceful shutdown process
                shutdown_status = {
                    'initiated_at': datetime.now().isoformat(),
                    'estimated_completion': None,
                    'steps': []
                }
                
                # Stop task scheduler if available
                if self.task_scheduler:
                    self.task_scheduler.stop()
                    shutdown_status['steps'].append({
                        'component': 'task_scheduler',
                        'status': 'stopped',
                        'timestamp': datetime.now().isoformat()
                    })
                
                # Notify all devices about shutdown
                registry = self.cluster_server.device_registry
                devices = registry.get_all_devices()
                for device in devices:
                    if device.get('status') == 'online':
                        # Send shutdown notification (would need implementation in server)
                        pass
                
                shutdown_status['steps'].append({
                    'component': 'device_notifications',
                    'status': 'sent',
                    'device_count': len(devices),
                    'timestamp': datetime.now().isoformat()
                })
                
                response = APIResponse(
                    status=ResponseStatus.SUCCESS,
                    data=shutdown_status,
                    message="Cluster shutdown initiated",
                    request_id=getattr(g, 'request_id', None)
                )
                
                return jsonify(response.to_dict())
                
            except Exception as e:
                self.logger.error(f"Error initiating cluster shutdown: {e}")
                error_response = ErrorResponse(
                    message="Failed to initiate cluster shutdown",
                    error_code="SHUTDOWN_ERROR", 
                    error_details={'error': str(e)},
                    request_id=getattr(g, 'request_id', None)
                )
                return jsonify(error_response.to_dict()), 500
    
    def _get_server_uptime(self) -> str:
        """Get server uptime in human readable format"""
        if hasattr(self.cluster_server, 'start_time'):
            uptime_seconds = (datetime.now() - self.cluster_server.start_time).total_seconds()
            
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            
            if days > 0:
                return f"{days}d {hours}h {minutes}m"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
        
        return "unknown"