#!/usr/bin/env python3
"""
Command-line interface for Retire-Cluster Main Node
"""

import argparse
import sys
from pathlib import Path

from ..core.config import Config
from ..core.logger import get_logger
from ..communication.server import ClusterServer


def create_default_config(config_path: Path):
    """Create default configuration file"""
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    default_config = {
        "server": {
            "host": "0.0.0.0",
            "port": 8080,
            "max_connections": 50
        },
        "database": {
            "path": str(config_path.parent / "cluster_data.json")
        },
        "logging": {
            "level": "INFO",
            "file_path": str(config_path.parent / "main_node.log")
        }
    }
    
    import json
    with open(config_path, 'w') as f:
        json.dump(default_config, f, indent=2)
    
    return default_config


def main():
    """Main entry point for retire-cluster-main command"""
    parser = argparse.ArgumentParser(
        description='Retire-Cluster Main Node - Cluster Management Server',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  retire-cluster-main                    # Start with default settings
  retire-cluster-main --port 9090       # Use custom port
  retire-cluster-main --host 0.0.0.0    # Bind to all interfaces
  retire-cluster-main --data-dir /opt/retire-cluster  # Custom data directory
        """
    )
    
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='Server host address (default: 0.0.0.0 - all interfaces)'
    )
    
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=8080,
        help='Server port (default: 8080)'
    )
    
    parser.add_argument(
        '--data-dir',
        type=Path,
        default=Path.home() / '.retire-cluster',
        help='Data directory for database and logs (default: ~/.retire-cluster)'
    )
    
    parser.add_argument(
        '--config',
        type=Path,
        help='Custom configuration file path'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    parser.add_argument(
        '--init-config',
        action='store_true',
        help='Create default configuration file and exit'
    )
    
    args = parser.parse_args()
    
    # Setup data directory
    data_dir = args.data_dir
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Configuration handling
    if args.config:
        config_path = args.config
    else:
        config_path = data_dir / 'main_config.json'
    
    # Initialize config if requested
    if args.init_config:
        config_data = create_default_config(config_path)
        print(f"✓ Created default configuration at: {config_path}")
        print(f"✓ Data directory: {data_dir}")
        print("\nEdit the configuration file and run 'retire-cluster-main' to start.")
        return
    
    # Create config if it doesn't exist
    if not config_path.exists():
        print(f"Creating default configuration at: {config_path}")
        create_default_config(config_path)
    
    try:
        # Load configuration
        config = Config(str(config_path))
        
        # Override with command line arguments
        if args.host:
            config.server.host = args.host
        if args.port:
            config.server.port = args.port
        
        # Setup paths
        config.database.path = str(data_dir / "cluster_data.json")
        config.logging.file_path = str(data_dir / "main_node.log")
        
        if args.debug:
            config.logging.level = "DEBUG"
        
        # Save updated configuration
        config.save()
        
        # Setup logging
        logger = get_logger(
            name="main",
            log_file=config.logging.file_path,
            level=config.logging.level
        )
        
        # Print startup information
        print("🚀 Retire-Cluster Main Node Starting...")
        print(f"📍 Server: {config.server.host}:{config.server.port}")
        print(f"📁 Data directory: {data_dir}")
        print(f"📄 Config file: {config_path}")
        print(f"📝 Log file: {config.logging.file_path}")
        print("=" * 50)
        
        logger.info("Starting Retire-Cluster Main Node")
        logger.info(f"Server: {config.server.host}:{config.server.port}")
        logger.info(f"Data directory: {data_dir}")
        
        # Create and start server
        server = ClusterServer(config)
        
        print("🎯 Main node is ready! Workers can connect to:")
        print(f"   {config.server.host}:{config.server.port}")
        print("\nPress Ctrl+C to stop...")
        
        server.start()
        
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested")
        logger.info("Main node shutdown requested")
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()