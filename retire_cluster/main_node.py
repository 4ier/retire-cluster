"""
Main node entry point for Retire-Cluster
"""

import argparse
import os
import sys
import signal
from pathlib import Path

from .core.config import Config
from .core.logger import setup_logging
from .communication.server import ClusterServer


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\nShutdown signal received, stopping server...")
    sys.exit(0)


def main():
    """Main entry point for the main node"""
    parser = argparse.ArgumentParser(
        description='Retire-Cluster Main Node Server',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Start with default config
  %(prog)s --config /path/config.json    # Use custom config file
  %(prog)s --host 0.0.0.0 --port 8080    # Override network settings
  %(prog)s --debug                       # Enable debug logging
        """
    )
    
    parser.add_argument(
        '--config', '-c',
        default='config.json',
        help='Configuration file path (default: config.json)'
    )
    
    parser.add_argument(
        '--host',
        help='Server host address (overrides config)'
    )
    
    parser.add_argument(
        '--port', '-p',
        type=int,
        help='Server port (overrides config)'
    )
    
    parser.add_argument(
        '--debug', '-d',
        action='store_true',
        help='Enable debug logging'
    )
    
    parser.add_argument(
        '--data-dir',
        default='./data',
        help='Data directory for database and logs (default: ./data)'
    )
    
    parser.add_argument(
        '--version', '-v',
        action='version',
        version='Retire-Cluster 1.0.0'
    )
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        config = Config(args.config)
        
        # Override with command line arguments
        if args.host:
            config.server.host = args.host
        if args.port:
            config.server.port = args.port
        
        # Setup data directory
        data_dir = Path(args.data_dir)
        data_dir.mkdir(exist_ok=True)
        
        config.database.path = str(data_dir / "cluster_metadata.json")
        config.logging.file_path = str(data_dir / "main_node.log")
        
        # Set logging level
        if args.debug:
            config.logging.level = "DEBUG"
        
        # Ensure directories exist
        config.ensure_directories()
        
        # Save updated configuration
        config.save()
        
        # Setup logging
        logger = setup_logging(config.to_dict())
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Create and start server
        logger.info("=" * 50)
        logger.info("Retire-Cluster Main Node Server v1.0.0")
        logger.info("=" * 50)
        logger.info(f"Configuration file: {args.config}")
        logger.info(f"Server address: {config.server.host}:{config.server.port}")
        logger.info(f"Data directory: {data_dir}")
        logger.info(f"Database path: {config.database.path}")
        logger.info(f"Log file: {config.logging.file_path}")
        logger.info(f"Debug mode: {args.debug}")
        logger.info("-" * 50)
        
        server = ClusterServer(config)
        server.start()
        
    except KeyboardInterrupt:
        print("\nServer shutdown requested")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()