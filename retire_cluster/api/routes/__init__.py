"""
API routes for Retire-Cluster REST API
"""

from .cluster import ClusterRoutes
from .devices import DeviceRoutes  
from .tasks import TaskRoutes
from .config import ConfigRoutes

__all__ = [
    'ClusterRoutes',
    'DeviceRoutes',
    'TaskRoutes', 
    'ConfigRoutes'
]