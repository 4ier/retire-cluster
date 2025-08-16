"""
API middleware for authentication, CORS, logging, and other cross-cutting concerns
"""

import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List
from functools import wraps
import logging

try:
    from flask import request, g, jsonify, Response
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    # Mock objects for when Flask is not available
    class MockRequest:
        method = "GET"
        path = "/"
        remote_addr = "127.0.0.1"
        headers = {}
        args = {}
        json = {}
    
    request = MockRequest()
    g = type('g', (), {})()


class AuthMiddleware:
    """Authentication and authorization middleware"""
    
    def __init__(self, api_keys: Optional[List[str]] = None, require_auth: bool = False):
        self.api_keys = set(api_keys or [])
        self.require_auth = require_auth
        self.logger = logging.getLogger("api.auth")
    
    def __call__(self, f: Callable) -> Callable:
        """Decorator to apply authentication"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not self.require_auth:
                return f(*args, **kwargs)
            
            # Check API key in headers
            api_key = request.headers.get('X-API-Key') or request.headers.get('Authorization')
            
            if api_key and api_key.startswith('Bearer '):
                api_key = api_key[7:]  # Remove 'Bearer ' prefix
            
            if not api_key:
                self.logger.warning(f"Missing API key from {request.remote_addr}")
                return jsonify({
                    'status': 'error',
                    'message': 'API key required',
                    'error_code': 'MISSING_API_KEY'
                }), 401
            
            if api_key not in self.api_keys:
                self.logger.warning(f"Invalid API key from {request.remote_addr}")
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid API key',
                    'error_code': 'INVALID_API_KEY'
                }), 401
            
            # Store authenticated info in request context
            g.authenticated = True
            g.api_key = api_key
            
            return f(*args, **kwargs)
        
        return decorated_function


class CORSMiddleware:
    """CORS (Cross-Origin Resource Sharing) middleware"""
    
    def __init__(self, 
                 origins: List[str] = None,
                 methods: List[str] = None,
                 headers: List[str] = None,
                 allow_credentials: bool = True):
        self.origins = origins or ['*']
        self.methods = methods or ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
        self.headers = headers or ['Content-Type', 'Authorization', 'X-API-Key']
        self.allow_credentials = allow_credentials
    
    def apply_cors_headers(self, response: Response) -> Response:
        """Apply CORS headers to response"""
        origin = request.headers.get('Origin')
        
        if '*' in self.origins or (origin and origin in self.origins):
            response.headers['Access-Control-Allow-Origin'] = origin or '*'
        
        response.headers['Access-Control-Allow-Methods'] = ', '.join(self.methods)
        response.headers['Access-Control-Allow-Headers'] = ', '.join(self.headers)
        
        if self.allow_credentials:
            response.headers['Access-Control-Allow-Credentials'] = 'true'
        
        return response
    
    def handle_preflight(self) -> Response:
        """Handle OPTIONS preflight requests"""
        response = Response()
        return self.apply_cors_headers(response)


class LoggingMiddleware:
    """Request/response logging middleware"""
    
    def __init__(self, log_level: str = "INFO", include_body: bool = False):
        self.logger = logging.getLogger("api.requests")
        self.logger.setLevel(getattr(logging, log_level.upper()))
        self.include_body = include_body
    
    def __call__(self, f: Callable) -> Callable:
        """Decorator to log requests"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate request ID
            request_id = str(uuid.uuid4())
            g.request_id = request_id
            
            start_time = time.time()
            
            # Log request
            self.log_request(request_id)
            
            try:
                # Execute the function
                response = f(*args, **kwargs)
                
                # Log successful response
                duration = time.time() - start_time
                self.log_response(request_id, 200, duration)
                
                return response
                
            except Exception as e:
                # Log error response
                duration = time.time() - start_time
                self.log_response(request_id, 500, duration, str(e))
                raise
        
        return decorated_function
    
    def log_request(self, request_id: str) -> None:
        """Log incoming request"""
        log_data = {
            'request_id': request_id,
            'method': request.method,
            'path': request.path,
            'remote_addr': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', ''),
            'timestamp': datetime.now().isoformat()
        }
        
        if self.include_body and request.method in ['POST', 'PUT', 'PATCH']:
            try:
                log_data['body'] = request.get_json() if request.is_json else request.get_data(as_text=True)
            except Exception:
                log_data['body'] = '<unable to parse>'
        
        self.logger.info(f"Request: {json.dumps(log_data)}")
    
    def log_response(self, request_id: str, status_code: int, duration: float, error: str = None) -> None:
        """Log response"""
        log_data = {
            'request_id': request_id,
            'status_code': status_code,
            'duration_ms': round(duration * 1000, 2),
            'timestamp': datetime.now().isoformat()
        }
        
        if error:
            log_data['error'] = error
        
        if status_code >= 400:
            self.logger.error(f"Response: {json.dumps(log_data)}")
        else:
            self.logger.info(f"Response: {json.dumps(log_data)}")


class RateLimitMiddleware:
    """Rate limiting middleware"""
    
    def __init__(self, 
                 requests_per_minute: int = 60,
                 requests_per_hour: int = 1000,
                 burst_size: int = 10):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour  
        self.burst_size = burst_size
        
        # Simple in-memory storage (use Redis in production)
        self.request_counts = {}
        self.logger = logging.getLogger("api.ratelimit")
    
    def __call__(self, f: Callable) -> Callable:
        """Decorator to apply rate limiting"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_id = self.get_client_id()
            current_time = time.time()
            
            if self.is_rate_limited(client_id, current_time):
                self.logger.warning(f"Rate limit exceeded for client {client_id}")
                return jsonify({
                    'status': 'error',
                    'message': 'Rate limit exceeded',
                    'error_code': 'RATE_LIMIT_EXCEEDED'
                }), 429
            
            self.record_request(client_id, current_time)
            return f(*args, **kwargs)
        
        return decorated_function
    
    def get_client_id(self) -> str:
        """Get client identifier (IP address or API key)"""
        if hasattr(g, 'api_key'):
            return f"key:{g.api_key}"
        return f"ip:{request.remote_addr}"
    
    def is_rate_limited(self, client_id: str, current_time: float) -> bool:
        """Check if client is rate limited"""
        if client_id not in self.request_counts:
            return False
        
        requests = self.request_counts[client_id]
        
        # Clean old requests
        minute_ago = current_time - 60
        hour_ago = current_time - 3600
        
        requests['minute'] = [t for t in requests['minute'] if t > minute_ago]
        requests['hour'] = [t for t in requests['hour'] if t > hour_ago]
        
        # Check limits
        if len(requests['minute']) >= self.requests_per_minute:
            return True
        if len(requests['hour']) >= self.requests_per_hour:
            return True
        
        return False
    
    def record_request(self, client_id: str, current_time: float) -> None:
        """Record a request for rate limiting"""
        if client_id not in self.request_counts:
            self.request_counts[client_id] = {'minute': [], 'hour': []}
        
        self.request_counts[client_id]['minute'].append(current_time)
        self.request_counts[client_id]['hour'].append(current_time)


class ValidationMiddleware:
    """Request validation middleware"""
    
    def __init__(self):
        self.logger = logging.getLogger("api.validation")
        
        # Try to import jsonschema for validation
        try:
            import jsonschema
            self.jsonschema = jsonschema
            self.validation_available = True
        except ImportError:
            self.validation_available = False
            self.logger.warning("jsonschema not available, validation disabled")
    
    def validate_json(self, schema: Dict[str, Any]) -> Callable:
        """Decorator to validate JSON request against schema"""
        def decorator(f: Callable) -> Callable:
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if not self.validation_available:
                    return f(*args, **kwargs)
                
                if not request.is_json:
                    return jsonify({
                        'status': 'error',
                        'message': 'Content-Type must be application/json',
                        'error_code': 'INVALID_CONTENT_TYPE'
                    }), 400
                
                try:
                    data = request.get_json()
                    self.jsonschema.validate(data, schema)
                except self.jsonschema.ValidationError as e:
                    self.logger.warning(f"Validation error: {e.message}")
                    return jsonify({
                        'status': 'error',
                        'message': f'Validation error: {e.message}',
                        'error_code': 'VALIDATION_ERROR',
                        'error_details': {
                            'field': list(e.path),
                            'message': e.message
                        }
                    }), 400
                except Exception as e:
                    return jsonify({
                        'status': 'error',
                        'message': f'Invalid JSON: {str(e)}',
                        'error_code': 'INVALID_JSON'
                    }), 400
                
                return f(*args, **kwargs)
            
            return decorated_function
        return decorator


def create_error_handler(logger: logging.Logger) -> Callable:
    """Create error handler for unhandled exceptions"""
    def handle_error(error: Exception) -> tuple:
        """Handle unhandled exceptions"""
        request_id = getattr(g, 'request_id', 'unknown')
        
        logger.error(f"Unhandled error in request {request_id}: {str(error)}", exc_info=True)
        
        return jsonify({
            'status': 'error',
            'message': 'Internal server error',
            'error_code': 'INTERNAL_ERROR',
            'request_id': request_id
        }), 500
    
    return handle_error