"""
Logging utilities for Retire-Cluster
"""

import logging
import logging.handlers
import os
import sys
from typing import Optional

# Global logger cache
_loggers = {}


def get_logger(name: str = "retire_cluster", 
               log_file: Optional[str] = None,
               level: str = "INFO",
               max_size_mb: int = 100,
               backup_count: int = 5) -> logging.Logger:
    """
    Get a configured logger instance
    
    Args:
        name: Logger name
        log_file: Log file path (optional)
        level: Logging level
        max_size_mb: Maximum log file size in MB
        backup_count: Number of backup files to keep
    
    Returns:
        Configured logger instance
    """
    if name in _loggers:
        return _loggers[name]
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if log_file specified)
    if log_file:
        try:
            # Ensure log directory exists
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            # Rotating file handler
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_size_mb * 1024 * 1024,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
        except Exception as e:
            logger.warning(f"Could not create file handler for {log_file}: {e}")
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    # Cache logger
    _loggers[name] = logger
    
    return logger


def setup_logging(config_dict: dict) -> logging.Logger:
    """
    Setup logging from configuration dictionary
    
    Args:
        config_dict: Configuration dictionary with logging settings
    
    Returns:
        Main logger instance
    """
    logging_config = config_dict.get('logging', {})
    
    return get_logger(
        name="retire_cluster",
        log_file=logging_config.get('file_path', './logs/retire_cluster.log'),
        level=logging_config.get('level', 'INFO'),
        max_size_mb=logging_config.get('max_size_mb', 100),
        backup_count=logging_config.get('backup_count', 5)
    )