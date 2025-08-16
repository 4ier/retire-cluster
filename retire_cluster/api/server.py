"""
REST API server for Retire-Cluster
"""

import logging
import threading
from datetime import datetime
from typing import Optional, Dict, Any, List

try:
    from flask import Flask, jsonify, request
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    Flask = None
    CORS = None

from .routes import ClusterRoutes, DeviceRoutes, TaskRoutes
from .middleware import (
    AuthMiddleware, CORSMiddleware, LoggingMiddleware, 
    RateLimitMiddleware, ValidationMiddleware, create_error_handler
)
from .models import ErrorResponse, ResponseStatus
from ..core.logger import get_logger


class APIServer:
    """REST API server for Retire-Cluster"""
    
    def __init__(self, 
                 cluster_server,
                 task_scheduler=None,
                 host: str = "0.0.0.0",
                 port: int = 8081,
                 debug: bool = False,
                 api_keys: Optional[List[str]] = None,
                 require_auth: bool = False,
                 enable_cors: bool = True,
                 enable_rate_limiting: bool = True):
        
        if not FLASK_AVAILABLE:
            raise RuntimeError("Flask is required for API server. Install with: pip install flask flask-cors")
        
        self.cluster_server = cluster_server
        self.task_scheduler = task_scheduler
        self.host = host
        self.port = port
        self.debug = debug
        self.logger = get_logger("api.server", level="DEBUG" if debug else "INFO")
        
        # Create Flask app
        self.app = Flask(__name__)
        self.app.config['JSON_SORT_KEYS'] = False
        
        # Initialize middleware
        self.auth = AuthMiddleware(api_keys=api_keys, require_auth=require_auth)
        self.cors = CORSMiddleware()
        self.logging_middleware = LoggingMiddleware(include_body=debug)
        self.rate_limit = RateLimitMiddleware() if enable_rate_limiting else None
        self.validation = ValidationMiddleware()
        
        # Server state
        self.start_time = datetime.now()
        self.is_running = False
        self.server_thread: Optional[threading.Thread] = None
        
        # Setup Flask app
        self._setup_app(enable_cors)
        self._register_routes()
        self._register_error_handlers()
        
        self.logger.info(f"API server initialized on {host}:{port}")
    
    def _setup_app(self, enable_cors: bool) -> None:
        """Setup Flask application configuration"""
        
        # Enable CORS if requested
        if enable_cors and CORS:
            CORS(self.app, 
                 origins=['*'],
                 methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
                 allow_headers=['Content-Type', 'Authorization', 'X-API-Key'])
        
        # Add before_request handler
        @self.app.before_request
        def before_request():
            # Handle CORS preflight
            if request.method == 'OPTIONS':
                return self.cors.handle_preflight()
        
        # Add after_request handler
        @self.app.after_request
        def after_request(response):
            return self.cors.apply_cors_headers(response)
    
    def _register_routes(self) -> None:
        """Register API routes"""
        
        # Create route handlers
        cluster_routes = ClusterRoutes(self.cluster_server, self.task_scheduler)
        device_routes = DeviceRoutes(self.cluster_server)
        
        # Register routes
        self.app.register_blueprint(cluster_routes.blueprint)
        self.app.register_blueprint(device_routes.blueprint)
        
        # Register task routes if scheduler is available
        if self.task_scheduler:
            task_routes = TaskRoutes(self.task_scheduler)
            self.app.register_blueprint(task_routes.blueprint)
        
        # Root endpoint
        @self.app.route('/')
        def root():
            return jsonify({
                'status': 'success',
                'message': 'Retire-Cluster API Server',
                'version': '1.0.0',
                'endpoints': {
                    'cluster': '/api/v1/cluster',
                    'devices': '/api/v1/devices',
                    'tasks': '/api/v1/tasks' if self.task_scheduler else None,
                    'docs': '/api/v1/docs'
                },
                'server_time': datetime.now().isoformat(),
                'uptime': self._get_uptime()
            })
        
        # API info endpoint
        @self.app.route('/api/v1')
        def api_info():
            return jsonify({
                'status': 'success',
                'api_version': '1.0.0',
                'server_info': {
                    'host': self.host,
                    'port': self.port,
                    'start_time': self.start_time.isoformat(),
                    'uptime': self._get_uptime(),
                    'debug_mode': self.debug
                },
                'features': {
                    'cluster_management': True,
                    'device_management': True,
                    'task_execution': self.task_scheduler is not None,
                    'authentication': self.auth.require_auth,
                    'rate_limiting': self.rate_limit is not None
                },
                'endpoints': self._get_available_endpoints()
            })
        
        # Health check endpoint
        @self.app.route('/health')
        def health():
            health_status = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'uptime_seconds': (datetime.now() - self.start_time).total_seconds(),
                'components': {
                    'api_server': 'healthy',
                    'cluster_server': 'healthy' if self.cluster_server else 'not_configured',
                    'task_scheduler': 'healthy' if self.task_scheduler else 'not_configured'
                }
            }
            return jsonify(health_status)
        
        # API documentation endpoint
        @self.app.route('/api/v1/docs')
        def api_docs():
            return jsonify({
                'status': 'success',
                'documentation': {
                    'title': 'Retire-Cluster REST API',
                    'version': '1.0.0',
                    'description': 'REST API for managing Retire-Cluster distributed computing system',
                    'base_url': f'http://{self.host}:{self.port}/api/v1',
                    'authentication': {
                        'required': self.auth.require_auth,
                        'method': 'API Key',
                        'header': 'X-API-Key or Authorization: Bearer <key>'
                    },
                    'endpoints': self._get_endpoint_documentation()
                }
            })
    
    def _register_error_handlers(self) -> None:
        """Register error handlers"""
        
        # 404 handler
        @self.app.errorhandler(404)
        def not_found(error):
            error_response = ErrorResponse(
                message="Endpoint not found",
                error_code="NOT_FOUND"
            )
            return jsonify(error_response.to_dict()), 404
        
        # 405 handler
        @self.app.errorhandler(405)
        def method_not_allowed(error):
            error_response = ErrorResponse(
                message="Method not allowed",
                error_code="METHOD_NOT_ALLOWED"
            )
            return jsonify(error_response.to_dict()), 405
        
        # 500 handler
        @self.app.errorhandler(500)
        def internal_error(error):
            self.logger.error(f"Internal server error: {error}")
            error_response = ErrorResponse(
                message="Internal server error",
                error_code="INTERNAL_ERROR"
            )
            return jsonify(error_response.to_dict()), 500
        
        # General exception handler
        @self.app.errorhandler(Exception)
        def handle_exception(error):
            return create_error_handler(self.logger)(error)
    
    def start(self, threaded: bool = True) -> None:
        """Start the API server"""
        if self.is_running:
            self.logger.warning("API server is already running")
            return
        
        self.logger.info(f"Starting API server on {self.host}:{self.port}")
        
        if threaded:
            self.server_thread = threading.Thread(
                target=self._run_server,
                daemon=True
            )
            self.server_thread.start()
        else:
            self._run_server()
    
    def _run_server(self) -> None:
        """Run the Flask server"""
        try:
            self.is_running = True
            self.app.run(
                host=self.host,
                port=self.port,
                debug=self.debug,
                use_reloader=False,  # Disable reloader in production
                threaded=True
            )
        except Exception as e:
            self.logger.error(f"Error running API server: {e}")
            self.is_running = False
    
    def stop(self) -> None:
        """Stop the API server"""
        self.logger.info("Stopping API server...")
        self.is_running = False
        
        # Note: Flask's built-in server doesn't have a clean way to stop
        # In production, use a proper WSGI server like Gunicorn
        if self.server_thread and self.server_thread.is_alive():
            self.logger.warning("Cannot cleanly stop Flask development server")
    
    def _get_uptime(self) -> str:
        """Get server uptime in human readable format"""
        uptime_seconds = (datetime.now() - self.start_time).total_seconds()
        
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    def _get_available_endpoints(self) -> Dict[str, List[str]]:
        """Get list of available API endpoints"""
        endpoints = {
            'cluster': [
                'GET /api/v1/cluster/status',
                'GET /api/v1/cluster/health',
                'GET /api/v1/cluster/metrics',
                'GET /api/v1/cluster/config',
                'POST /api/v1/cluster/shutdown'
            ],
            'devices': [
                'GET /api/v1/devices',
                'GET /api/v1/devices/{device_id}',
                'GET /api/v1/devices/{device_id}/status',
                'POST /api/v1/devices/{device_id}/ping',
                'DELETE /api/v1/devices/{device_id}',
                'GET /api/v1/devices/summary'
            ]
        }
        
        if self.task_scheduler:
            endpoints['tasks'] = [
                'POST /api/v1/tasks',
                'GET /api/v1/tasks',
                'GET /api/v1/tasks/{task_id}',
                'GET /api/v1/tasks/{task_id}/status',
                'GET /api/v1/tasks/{task_id}/result',
                'POST /api/v1/tasks/{task_id}/cancel',
                'POST /api/v1/tasks/{task_id}/retry',
                'GET /api/v1/tasks/statistics',
                'GET /api/v1/tasks/types'
            ]
        
        return endpoints
    
    def _get_endpoint_documentation(self) -> Dict[str, Any]:
        """Get detailed endpoint documentation"""
        docs = {
            'cluster_endpoints': {
                'GET /cluster/status': {
                    'description': 'Get overall cluster status and statistics',
                    'response': 'Cluster statistics including device count, health, resources'
                },
                'GET /cluster/health': {
                    'description': 'Health check for cluster components',
                    'response': 'Health status of API, cluster server, task scheduler'
                },
                'GET /cluster/metrics': {
                    'description': 'Get detailed cluster metrics',
                    'response': 'Detailed metrics including device utilization, performance'
                }
            },
            'device_endpoints': {
                'GET /devices': {
                    'description': 'List all devices with filtering and pagination',
                    'parameters': 'page, page_size, status, role, platform, tags',
                    'response': 'Paginated list of devices with capabilities'
                },
                'GET /devices/{device_id}': {
                    'description': 'Get detailed information about specific device',
                    'response': 'Complete device information including capabilities and metrics'
                }
            }
        }
        
        if self.task_scheduler:
            docs['task_endpoints'] = {
                'POST /tasks': {
                    'description': 'Submit new task for execution',
                    'body': 'Task definition with type, payload, requirements',
                    'response': 'Task ID and submission confirmation'
                },
                'GET /tasks': {
                    'description': 'List tasks with filtering and pagination',
                    'parameters': 'page, page_size, status, task_type, priority, device_id',
                    'response': 'Paginated list of tasks'
                },
                'GET /tasks/{task_id}': {
                    'description': 'Get detailed task information',
                    'response': 'Complete task details including status and result'
                }
            }
        
        return docs