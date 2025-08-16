"""
Worker node entry point for Retire-Cluster
"""

import argparse
import os
import sys
import signal
import platform
from pathlib import Path

from .core.config import WorkerConfig
from .core.logger import get_logger
from .communication.client import ClusterClient


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\nShutdown signal received, stopping worker...")
    sys.exit(0)


def generate_device_id() -> str:
    """Generate a unique device ID based on system information"""
    try:
        import socket
        hostname = socket.gethostname()
        
        # For Android/Termux, use a more descriptive format
        if 'ANDROID_ROOT' in os.environ or 'PREFIX' in os.environ:
            return f"android-{hostname}-{platform.machine()}"
        else:
            return f"{platform.system().lower()}-{hostname}-{platform.machine()}"
            
    except Exception:
        # Fallback to simple format
        return f"{platform.system().lower()}-worker-{os.getpid()}"


def main():
    """Main entry point for the worker node"""
    parser = argparse.ArgumentParser(
        description='Retire-Cluster Worker Node Client',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --device-id my-phone-01                    # Basic usage
  %(prog)s --device-id tablet-01 --role mobile        # Set device role
  %(prog)s --main-host 192.168.1.100 --main-port 8080 # Connect to custom main node
  %(prog)s --auto-id --role worker                     # Auto-generate device ID
  %(prog)s --test                                      # Test connection only
        """
    )
    
    parser.add_argument(
        '--device-id',
        help='Unique device identifier (required unless --auto-id used)'
    )
    
    parser.add_argument(
        '--auto-id',
        action='store_true',
        help='Auto-generate device ID based on system info'
    )
    
    parser.add_argument(
        '--role',
        default='worker',
        choices=['worker', 'storage', 'compute', 'mobile', 'nas'],
        help='Device role in the cluster (default: worker)'
    )
    
    parser.add_argument(
        '--main-host',
        default='192.168.0.116',
        help='Main node host address (default: 192.168.0.116)'
    )
    
    parser.add_argument(
        '--main-port',
        type=int,
        default=8080,
        help='Main node port (default: 8080)'
    )
    
    parser.add_argument(
        '--heartbeat-interval',
        type=int,
        default=60,
        help='Heartbeat interval in seconds (default: 60)'
    )
    
    parser.add_argument(
        '--max-tasks',
        type=int,
        default=2,
        help='Maximum concurrent tasks (default: 2)'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test connection and show device profile'
    )
    
    parser.add_argument(
        '--debug', '-d',
        action='store_true',
        help='Enable debug logging'
    )
    
    parser.add_argument(
        '--config',
        help='Configuration file path (optional)'
    )
    
    parser.add_argument(
        '--version', '-v',
        action='version',
        version='Retire-Cluster Worker 1.0.0'
    )
    
    args = parser.parse_args()
    
    try:
        # Determine device ID
        if args.auto_id:
            device_id = generate_device_id()
            print(f"Auto-generated device ID: {device_id}")
        elif args.device_id:
            device_id = args.device_id
        else:
            parser.error("Either --device-id or --auto-id must be specified")
        
        # Create worker configuration
        if args.config and os.path.exists(args.config):
            # Load from config file (simplified - would need proper config loading)
            config = WorkerConfig()
        else:
            config = WorkerConfig()
        
        # Override with command line arguments
        config.device_id = device_id
        config.role = args.role
        config.main_host = args.main_host
        config.main_port = args.main_port
        config.heartbeat_interval = args.heartbeat_interval
        config.max_concurrent_tasks = args.max_tasks
        
        # Setup logging
        log_level = "DEBUG" if args.debug else "INFO"
        logger = get_logger(
            name=f"worker.{device_id}",
            level=log_level
        )
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Create client
        client = ClusterClient(config)
        
        if args.test:
            # Test mode - show device info and test connection
            logger.info("=" * 50)
            logger.info("Retire-Cluster Worker Node Test Mode")
            logger.info("=" * 50)
            
            # Show device profile
            profile = client.profiler.get_device_profile()
            logger.info("Device Profile:")
            for key, value in profile.items():
                if isinstance(value, dict):
                    logger.info(f"  {key}:")
                    for k, v in value.items():
                        logger.info(f"    {k}: {v}")
                elif isinstance(value, list):
                    logger.info(f"  {key}: {', '.join(map(str, value))}")
                else:
                    logger.info(f"  {key}: {value}")
            
            logger.info("-" * 50)
            logger.info("Testing connection to main node...")
            
            if client.test_connection():
                logger.info("✅ Connection test successful!")
                
                # Try to get cluster status
                status = client.get_cluster_status()
                if status:
                    logger.info("Cluster Status:")
                    cluster_stats = status.get('cluster_stats', {})
                    logger.info(f"  Total devices: {cluster_stats.get('total_devices', 0)}")
                    logger.info(f"  Online devices: {cluster_stats.get('online_devices', 0)}")
                    logger.info(f"  Cluster health: {cluster_stats.get('health_percentage', 0)}%")
                    
                    by_role = cluster_stats.get('by_role', {})
                    if by_role:
                        logger.info("  Devices by role:")
                        for role, count in by_role.items():
                            logger.info(f"    {role}: {count}")
            else:
                logger.error("❌ Connection test failed!")
                sys.exit(1)
        
        else:
            # Normal mode - start worker
            logger.info("=" * 50)
            logger.info("Retire-Cluster Worker Node v1.0.0")
            logger.info("=" * 50)
            logger.info(f"Device ID: {device_id}")
            logger.info(f"Role: {config.role}")
            logger.info(f"Main node: {config.main_host}:{config.main_port}")
            logger.info(f"Heartbeat interval: {config.heartbeat_interval}s")
            logger.info(f"Max concurrent tasks: {config.max_concurrent_tasks}")
            logger.info(f"Platform: {platform.system()} {platform.release()}")
            logger.info(f"Architecture: {platform.machine()}")
            logger.info(f"Debug mode: {args.debug}")
            logger.info("-" * 50)
            
            # Start worker
            client.run()
        
    except KeyboardInterrupt:
        print("\nWorker shutdown requested")
    except Exception as e:
        print(f"Error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()