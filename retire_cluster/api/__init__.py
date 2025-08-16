"""
REST API module for Retire-Cluster

This module provides a comprehensive REST API for interacting with the 
Retire-Cluster system, including:

- Cluster management and monitoring
- Device registration and status
- Task submission and management
- Real-time status updates
- Configuration management
"""

from .server import APIServer
from .routes import ClusterRoutes, DeviceRoutes, TaskRoutes
from .middleware import AuthMiddleware, CORSMiddleware, LoggingMiddleware
from .models import APIResponse, ErrorResponse, PaginatedResponse

__all__ = [
    'APIServer',
    'ClusterRoutes',
    'DeviceRoutes', 
    'TaskRoutes',
    'AuthMiddleware',
    'CORSMiddleware',
    'LoggingMiddleware',
    'APIResponse',
    'ErrorResponse',
    'PaginatedResponse'
]