"""
Retire-Cluster: A distributed system for repurposing idle devices
"""

__version__ = "1.0.0"
__author__ = "Retire-Cluster Team"
__email__ = "team@retire-cluster.com"

from .core.config import Config
from .core.logger import get_logger

__all__ = ["Config", "get_logger"]