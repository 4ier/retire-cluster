"""
Configuration management for Retire-Cluster
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class ServerConfig:
    """Main server configuration"""
    host: str = "0.0.0.0"
    port: int = 8080
    max_connections: int = 50
    timeout: int = 10


@dataclass
class DatabaseConfig:
    """Database configuration"""
    path: str = "./data/cluster_metadata.db"
    backup_enabled: bool = True
    backup_interval: int = 3600


@dataclass
class HeartbeatConfig:
    """Heartbeat monitoring configuration"""
    interval_seconds: int = 60
    timeout_threshold: int = 300
    cleanup_interval: int = 1800


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    file_path: str = "./logs/retire_cluster.log"
    max_size_mb: int = 100
    backup_count: int = 5


@dataclass
class WorkerConfig:
    """Worker node configuration"""
    device_id: str = ""
    role: str = "worker"
    main_host: str = "localhost"
    main_port: int = 8080
    heartbeat_interval: int = 60
    max_concurrent_tasks: int = 2


class Config:
    """Main configuration class"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config.json"
        self.server = ServerConfig()
        self.database = DatabaseConfig()
        self.heartbeat = HeartbeatConfig()
        self.logging = LoggingConfig()
        self.worker = WorkerConfig()
        
        self.load()
    
    def load(self) -> None:
        """Load configuration from file"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Update configurations
                if 'server' in data:
                    self.server = ServerConfig(**data['server'])
                if 'database' in data:
                    self.database = DatabaseConfig(**data['database'])
                if 'heartbeat' in data:
                    self.heartbeat = HeartbeatConfig(**data['heartbeat'])
                if 'logging' in data:
                    self.logging = LoggingConfig(**data['logging'])
                if 'worker' in data:
                    self.worker = WorkerConfig(**data['worker'])
                    
            except Exception as e:
                print(f"Warning: Failed to load config from {self.config_path}: {e}")
                print("Using default configuration")
    
    def save(self) -> None:
        """Save configuration to file"""
        try:
            # Ensure config directory exists
            config_dir = os.path.dirname(self.config_path)
            if config_dir:
                os.makedirs(config_dir, exist_ok=True)
            
            data = {
                'server': asdict(self.server),
                'database': asdict(self.database),
                'heartbeat': asdict(self.heartbeat),
                'logging': asdict(self.logging),
                'worker': asdict(self.worker)
            }
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Error: Failed to save config to {self.config_path}: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'server': asdict(self.server),
            'database': asdict(self.database),
            'heartbeat': asdict(self.heartbeat),
            'logging': asdict(self.logging),
            'worker': asdict(self.worker)
        }
    
    def ensure_directories(self) -> None:
        """Ensure required directories exist"""
        directories = [
            os.path.dirname(self.database.path),
            os.path.dirname(self.logging.file_path),
            "./data",
            "./logs"
        ]
        
        for directory in directories:
            if directory:
                os.makedirs(directory, exist_ok=True)