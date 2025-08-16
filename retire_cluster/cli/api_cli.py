#!/usr/bin/env python3
"""
Command-line interface for Retire-Cluster API Server
"""

import argparse
import sys
import os
from pathlib import Path

from ..core.config import Config
from ..core.logger import get_logger


def main():
    """Main entry point for retire-cluster-api command"""
    parser = argparse.ArgumentParser(
        description='Retire-Cluster API Server - REST API for cluster management',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  retire-cluster-api                       # Start with default settings
  retire-cluster-api --port 8081          # Use custom port
  retire-cluster-api --host 0.0.0.0       # Bind to all interfaces
  retire-cluster-api --auth --api-key secret123  # Enable authentication
  retire-cluster-api --debug              # Enable debug mode
        """
    )
    
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='API server host address (default: 0.0.0.0 - all interfaces)'
    )
    
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=8081,
        help='API server port (default: 8081)'
    )
    
    parser.add_argument(
        '--cluster-host',
        default='localhost',
        help='Cluster main node host (default: localhost)'
    )
    
    parser.add_argument(
        '--cluster-port',
        type=int,
        default=8080,
        help='Cluster main node port (default: 8080)'
    )
    
    parser.add_argument(
        '--auth',
        action='store_true',
        help='Require API key authentication'
    )
    
    parser.add_argument(
        '--api-key',
        action='append',
        help='Valid API key (can be specified multiple times)'
    )
    
    parser.add_argument(
        '--no-cors',
        action='store_true',
        help='Disable CORS support'
    )
    
    parser.add_argument(
        '--no-rate-limit',
        action='store_true',
        help='Disable rate limiting'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )
    
    parser.add_argument(
        '--data-dir',
        type=Path,
        default=Path.home() / '.retire-cluster',
        help='Data directory (default: ~/.retire-cluster)'
    )
    
    args = parser.parse_args()
    
    # Check Flask availability
    try:
        from flask import Flask
    except ImportError:
        print("❌ Flask is required for API server")
        print("Install with: pip install retire-cluster[api]")
        sys.exit(1)
    
    # Setup data directory
    data_dir = args.data_dir
    data_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Setup logging
        log_level = "DEBUG" if args.debug else "INFO"
        logger = get_logger(
            name="api",
            log_file=str(data_dir / "api_server.log"),
            level=log_level
        )
        
        print("🚀 Retire-Cluster API Server Starting...")
        print(f"📍 API Server: {args.host}:{args.port}")
        print(f"🔗 Cluster Node: {args.cluster_host}:{args.cluster_port}")
        print(f"🔒 Authentication: {'Enabled' if args.auth else 'Disabled'}")
        print(f"🌐 CORS: {'Disabled' if args.no_cors else 'Enabled'}")
        print(f"⚡ Rate Limiting: {'Disabled' if args.no_rate_limit else 'Enabled'}")
        print("=" * 60)
        
        logger.info("Starting Retire-Cluster API Server")
        logger.info(f"API Server: {args.host}:{args.port}")
        logger.info(f"Cluster Node: {args.cluster_host}:{args.cluster_port}")
        
        # Connect to cluster server
        print("🔄 Connecting to cluster...")
        cluster_server = connect_to_cluster(args.cluster_host, args.cluster_port, logger)
        
        # Setup task scheduler if available
        task_scheduler = None
        try:
            from ..tasks import TaskScheduler, TaskQueue
            task_queue = TaskQueue()
            task_scheduler = TaskScheduler(task_queue)
            
            # Try to get device list from cluster and register with scheduler
            try:
                devices = cluster_server.device_registry.get_all_devices()
                for device in devices:
                    if device.get('status') == 'online':
                        task_scheduler.register_device(device['device_id'], device)
                
                task_scheduler.start()
                logger.info(f"Task scheduler started with {len(devices)} devices")
                print(f"⚙️  Task scheduler initialized with {len(devices)} devices")
            except Exception as e:
                logger.warning(f"Could not initialize task scheduler: {e}")
                print(f"⚠️  Task scheduler not available: {e}")
                task_scheduler = None
        except ImportError:
            logger.info("Task execution framework not available")
            print("📝 Task execution framework not available")
        
        # Create and start API server
        from ..api import APIServer
        
        api_server = APIServer(
            cluster_server=cluster_server,
            task_scheduler=task_scheduler,
            host=args.host,
            port=args.port,
            debug=args.debug,
            api_keys=args.api_key,
            require_auth=args.auth,
            enable_cors=not args.no_cors,
            enable_rate_limiting=not args.no_rate_limit
        )
        
        print("🎯 API server is ready!")
        print(f"📊 API endpoints available at: http://{args.host}:{args.port}/api/v1")
        print(f"📖 API documentation: http://{args.host}:{args.port}/api/v1/docs")
        print(f"❤️  Health check: http://{args.host}:{args.port}/health")
        print("\nPress Ctrl+C to stop...")
        
        # Start server (blocking)
        api_server.start(threaded=False)
        
    except KeyboardInterrupt:
        print("\n🛑 API server shutdown requested")
        if 'logger' in locals():
            logger.info("API server shutdown requested")
        if 'task_scheduler' in locals() and task_scheduler:
            task_scheduler.stop()
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def connect_to_cluster(host: str, port: int, logger):
    """Connect to cluster server"""
    # For now, create a mock cluster server for testing
    # In real implementation, this would connect to the actual cluster
    
    try:
        # Try to import cluster server
        from ..communication.server import ClusterServer
        from ..core.config import Config
        
        # Create a minimal config for API-only mode
        config = Config()
        config.server.host = host
        config.server.port = port
        
        # Create mock cluster server (for API testing)
        cluster_server = ClusterServer(config)
        
        logger.info(f"Connected to cluster at {host}:{port}")
        print(f"✅ Connected to cluster at {host}:{port}")
        
        return cluster_server
        
    except Exception as e:
        logger.error(f"Failed to connect to cluster: {e}")
        print(f"❌ Failed to connect to cluster at {host}:{port}")
        print(f"   Error: {e}")
        print("   Make sure the main node is running first with:")
        print(f"   retire-cluster-main --host {host} --port {port}")
        sys.exit(1)


if __name__ == "__main__":
    main()