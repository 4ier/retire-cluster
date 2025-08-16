"""
Configuration management API routes
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional

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

from ..models import APIResponse, ErrorResponse, ResponseStatus
from ..middleware import LoggingMiddleware, AuthMiddleware


class ConfigRoutes:
    """Configuration management API routes"""
    
    def __init__(self, cluster_server, task_scheduler=None):
        self.cluster_server = cluster_server
        self.task_scheduler = task_scheduler
        self.logger = logging.getLogger("api.config")
        
        # Create blueprint
        self.blueprint = Blueprint('config', __name__, url_prefix='/api/v1/config')
        
        # Middleware - config endpoints require authentication
        self.auth = AuthMiddleware(require_auth=True)
        self.logging = LoggingMiddleware()
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self):
        """Register all configuration routes"""
        
        @self.blueprint.route('', methods=['GET'])
        @self.auth
        @self.logging
        def get_full_config():
            """Get complete configuration"""
            try:
                config_data = {
                    'server': {
                        'host': self.cluster_server.config.server.host,
                        'port': self.cluster_server.config.server.port,
                        'max_connections': self.cluster_server.config.server.max_connections
                    },
                    'database': {
                        'path': self.cluster_server.config.database.path
                    },
                    'heartbeat': {
                        'interval': self.cluster_server.config.heartbeat.interval,
                        'timeout': self.cluster_server.config.heartbeat.timeout,
                        'max_missed': self.cluster_server.config.heartbeat.max_missed
                    },
                    'logging': {
                        'level': self.cluster_server.config.logging.level,
                        'file_path': self.cluster_server.config.logging.file_path
                    }
                }
                
                # Add task scheduler config if available
                if self.task_scheduler:
                    config_data['task_scheduler'] = {
                        'max_tasks_per_device': self.task_scheduler.max_tasks_per_device,
                        'heartbeat_timeout': self.task_scheduler.heartbeat_timeout,
                        'load_balancing_enabled': self.task_scheduler.load_balancing_enabled,
                        'device_affinity_enabled': self.task_scheduler.device_affinity_enabled
                    }
                
                response = APIResponse(
                    status=ResponseStatus.SUCCESS,
                    data=config_data,
                    request_id=getattr(g, 'request_id', None)
                )
                
                return jsonify(response.to_dict())
                
            except Exception as e:
                self.logger.error(f"Error getting configuration: {e}")
                error_response = ErrorResponse(
                    message="Failed to get configuration",
                    error_code="CONFIG_GET_ERROR",
                    error_details={'error': str(e)},
                    request_id=getattr(g, 'request_id', None)
                )
                return jsonify(error_response.to_dict()), 500
        
        @self.blueprint.route('/server', methods=['GET'])
        @self.auth
        @self.logging
        def get_server_config():
            """Get server configuration"""
            try:
                server_config = {
                    'host': self.cluster_server.config.server.host,
                    'port': self.cluster_server.config.server.port,
                    'max_connections': self.cluster_server.config.server.max_connections,
                    'current_connections': len(getattr(self.cluster_server, 'active_connections', [])),
                    'server_start_time': getattr(self.cluster_server, 'start_time', datetime.now()).isoformat(),
                    'is_running': getattr(self.cluster_server, 'is_running', False)
                }
                
                response = APIResponse(
                    status=ResponseStatus.SUCCESS,
                    data=server_config,
                    request_id=getattr(g, 'request_id', None)
                )
                
                return jsonify(response.to_dict())
                
            except Exception as e:
                self.logger.error(f"Error getting server configuration: {e}")
                error_response = ErrorResponse(
                    message="Failed to get server configuration",
                    error_code="SERVER_CONFIG_ERROR",
                    error_details={'error': str(e)},
                    request_id=getattr(g, 'request_id', None)
                )
                return jsonify(error_response.to_dict()), 500
        
        @self.blueprint.route('/heartbeat', methods=['GET'])
        @self.auth
        @self.logging
        def get_heartbeat_config():
            """Get heartbeat configuration"""
            try:
                heartbeat_config = {
                    'interval': self.cluster_server.config.heartbeat.interval,
                    'timeout': self.cluster_server.config.heartbeat.timeout,
                    'max_missed': self.cluster_server.config.heartbeat.max_missed,
                    'current_active_devices': len(self.cluster_server.device_registry.get_online_devices()),
                    'total_registered_devices': len(self.cluster_server.device_registry.get_all_devices())
                }
                
                response = APIResponse(
                    status=ResponseStatus.SUCCESS,
                    data=heartbeat_config,
                    request_id=getattr(g, 'request_id', None)
                )
                
                return jsonify(response.to_dict())
                
            except Exception as e:
                self.logger.error(f"Error getting heartbeat configuration: {e}")
                error_response = ErrorResponse(
                    message="Failed to get heartbeat configuration",
                    error_code="HEARTBEAT_CONFIG_ERROR",
                    error_details={'error': str(e)},
                    request_id=getattr(g, 'request_id', None)
                )
                return jsonify(error_response.to_dict()), 500
        
        @self.blueprint.route('/scheduler', methods=['GET'])
        @self.auth
        @self.logging
        def get_scheduler_config():
            """Get task scheduler configuration"""
            try:
                if not self.task_scheduler:
                    error_response = ErrorResponse(
                        message="Task scheduler not configured",
                        error_code="SCHEDULER_NOT_AVAILABLE",
                        request_id=getattr(g, 'request_id', None)
                    )
                    return jsonify(error_response.to_dict()), 404
                
                scheduler_config = {
                    'max_tasks_per_device': self.task_scheduler.max_tasks_per_device,
                    'heartbeat_timeout': self.task_scheduler.heartbeat_timeout,
                    'load_balancing_enabled': self.task_scheduler.load_balancing_enabled,
                    'device_affinity_enabled': self.task_scheduler.device_affinity_enabled,
                    'is_running': getattr(self.task_scheduler, '_running', False),
                    'registered_devices': len(self.task_scheduler._devices),
                    'online_devices': len(self.task_scheduler.get_online_devices()),
                    'scheduler_stats': self.task_scheduler.stats
                }
                
                response = APIResponse(
                    status=ResponseStatus.SUCCESS,
                    data=scheduler_config,
                    request_id=getattr(g, 'request_id', None)
                )
                
                return jsonify(response.to_dict())
                
            except Exception as e:
                self.logger.error(f"Error getting scheduler configuration: {e}")
                error_response = ErrorResponse(
                    message="Failed to get scheduler configuration",
                    error_code="SCHEDULER_CONFIG_ERROR",
                    error_details={'error': str(e)},
                    request_id=getattr(g, 'request_id', None)
                )
                return jsonify(error_response.to_dict()), 500
        
        @self.blueprint.route('/server', methods=['PUT'])
        @self.auth
        @self.logging
        def update_server_config():
            """Update server configuration"""
            try:
                data = request.get_json()
                if not data:
                    error_response = ErrorResponse(
                        message="Request body is required",
                        error_code="MISSING_REQUEST_BODY",
                        request_id=getattr(g, 'request_id', None)
                    )
                    return jsonify(error_response.to_dict()), 400
                
                updated_fields = []
                
                # Update max_connections if provided
                if 'max_connections' in data:
                    new_max = int(data['max_connections'])
                    if new_max < 1 or new_max > 1000:
                        error_response = ErrorResponse(
                            message="max_connections must be between 1 and 1000",
                            error_code="INVALID_MAX_CONNECTIONS",
                            request_id=getattr(g, 'request_id', None)
                        )
                        return jsonify(error_response.to_dict()), 400
                    
                    self.cluster_server.config.server.max_connections = new_max
                    updated_fields.append('max_connections')
                
                # Save configuration
                if updated_fields:
                    self.cluster_server.config.save()
                
                update_info = {
                    'updated_fields': updated_fields,
                    'updated_at': datetime.now().isoformat(),
                    'current_config': {
                        'host': self.cluster_server.config.server.host,
                        'port': self.cluster_server.config.server.port,
                        'max_connections': self.cluster_server.config.server.max_connections
                    }
                }
                
                response = APIResponse(
                    status=ResponseStatus.SUCCESS,
                    data=update_info,
                    message=f"Server configuration updated: {', '.join(updated_fields)}" if updated_fields else "No changes made",
                    request_id=getattr(g, 'request_id', None)
                )
                
                return jsonify(response.to_dict())
                
            except ValueError as e:
                error_response = ErrorResponse(
                    message=f"Invalid configuration value: {str(e)}",
                    error_code="INVALID_CONFIG_VALUE",
                    request_id=getattr(g, 'request_id', None)
                )
                return jsonify(error_response.to_dict()), 400
                
            except Exception as e:
                self.logger.error(f"Error updating server configuration: {e}")
                error_response = ErrorResponse(
                    message="Failed to update server configuration",
                    error_code="SERVER_CONFIG_UPDATE_ERROR",
                    error_details={'error': str(e)},
                    request_id=getattr(g, 'request_id', None)
                )
                return jsonify(error_response.to_dict()), 500
        
        @self.blueprint.route('/heartbeat', methods=['PUT'])
        @self.auth
        @self.logging
        def update_heartbeat_config():
            """Update heartbeat configuration"""
            try:
                data = request.get_json()
                if not data:
                    error_response = ErrorResponse(
                        message="Request body is required",
                        error_code="MISSING_REQUEST_BODY",
                        request_id=getattr(g, 'request_id', None)
                    )
                    return jsonify(error_response.to_dict()), 400
                
                updated_fields = []
                
                # Update interval if provided
                if 'interval' in data:
                    new_interval = int(data['interval'])
                    if new_interval < 10 or new_interval > 300:
                        error_response = ErrorResponse(
                            message="interval must be between 10 and 300 seconds",
                            error_code="INVALID_INTERVAL",
                            request_id=getattr(g, 'request_id', None)
                        )
                        return jsonify(error_response.to_dict()), 400
                    
                    self.cluster_server.config.heartbeat.interval = new_interval
                    updated_fields.append('interval')
                
                # Update timeout if provided
                if 'timeout' in data:
                    new_timeout = int(data['timeout'])
                    if new_timeout < 30 or new_timeout > 600:
                        error_response = ErrorResponse(
                            message="timeout must be between 30 and 600 seconds",
                            error_code="INVALID_TIMEOUT",
                            request_id=getattr(g, 'request_id', None)
                        )
                        return jsonify(error_response.to_dict()), 400
                    
                    self.cluster_server.config.heartbeat.timeout = new_timeout
                    updated_fields.append('timeout')
                
                # Update max_missed if provided
                if 'max_missed' in data:
                    new_max_missed = int(data['max_missed'])
                    if new_max_missed < 1 or new_max_missed > 10:
                        error_response = ErrorResponse(
                            message="max_missed must be between 1 and 10",
                            error_code="INVALID_MAX_MISSED",
                            request_id=getattr(g, 'request_id', None)
                        )
                        return jsonify(error_response.to_dict()), 400
                    
                    self.cluster_server.config.heartbeat.max_missed = new_max_missed
                    updated_fields.append('max_missed')
                
                # Save configuration
                if updated_fields:
                    self.cluster_server.config.save()
                
                update_info = {
                    'updated_fields': updated_fields,
                    'updated_at': datetime.now().isoformat(),
                    'current_config': {
                        'interval': self.cluster_server.config.heartbeat.interval,
                        'timeout': self.cluster_server.config.heartbeat.timeout,
                        'max_missed': self.cluster_server.config.heartbeat.max_missed
                    }
                }
                
                response = APIResponse(
                    status=ResponseStatus.SUCCESS,
                    data=update_info,
                    message=f"Heartbeat configuration updated: {', '.join(updated_fields)}" if updated_fields else "No changes made",
                    request_id=getattr(g, 'request_id', None)
                )
                
                return jsonify(response.to_dict())
                
            except ValueError as e:
                error_response = ErrorResponse(
                    message=f"Invalid configuration value: {str(e)}",
                    error_code="INVALID_CONFIG_VALUE",
                    request_id=getattr(g, 'request_id', None)
                )
                return jsonify(error_response.to_dict()), 400
                
            except Exception as e:
                self.logger.error(f"Error updating heartbeat configuration: {e}")
                error_response = ErrorResponse(
                    message="Failed to update heartbeat configuration",
                    error_code="HEARTBEAT_CONFIG_UPDATE_ERROR",
                    error_details={'error': str(e)},
                    request_id=getattr(g, 'request_id', None)
                )
                return jsonify(error_response.to_dict()), 500
        
        @self.blueprint.route('/reset', methods=['POST'])
        @self.auth
        @self.logging
        def reset_config():
            """Reset configuration to defaults"""
            try:
                # Create default configuration
                from ...core.config import Config
                default_config = Config()
                
                # Backup current config file path
                config_file = self.cluster_server.config.config_file
                
                # Replace current config with defaults
                self.cluster_server.config = default_config
                self.cluster_server.config.config_file = config_file
                
                # Save default configuration
                self.cluster_server.config.save()
                
                reset_info = {
                    'reset_at': datetime.now().isoformat(),
                    'config_file': config_file,
                    'default_config': {
                        'server': {
                            'host': default_config.server.host,
                            'port': default_config.server.port,
                            'max_connections': default_config.server.max_connections
                        },
                        'heartbeat': {
                            'interval': default_config.heartbeat.interval,
                            'timeout': default_config.heartbeat.timeout,
                            'max_missed': default_config.heartbeat.max_missed
                        }
                    }
                }
                
                response = APIResponse(
                    status=ResponseStatus.SUCCESS,
                    data=reset_info,
                    message="Configuration reset to defaults",
                    request_id=getattr(g, 'request_id', None)
                )
                
                return jsonify(response.to_dict())
                
            except Exception as e:
                self.logger.error(f"Error resetting configuration: {e}")
                error_response = ErrorResponse(
                    message="Failed to reset configuration",
                    error_code="CONFIG_RESET_ERROR",
                    error_details={'error': str(e)},
                    request_id=getattr(g, 'request_id', None)
                )
                return jsonify(error_response.to_dict()), 500