#!/usr/bin/env python3
"""
Command-line interface for Retire-Cluster Worker Node
"""

import argparse
import sys
import os
import platform
import socket
from pathlib import Path

from ..core.config import WorkerConfig
from ..core.logger import get_logger
from ..communication.client import ClusterClient


def generate_device_id():
    """Generate a unique device ID based on system information"""
    try:
        hostname = socket.gethostname()
        system = platform.system().lower()
        machine = platform.machine()
        
        # For Android/Termux, use a more descriptive format
        if any(indicator in os.environ for indicator in ['ANDROID_ROOT', 'ANDROID_DATA', 'PREFIX']):
            return f"android-{hostname}-{machine}".replace('.', '-')
        else:
            return f"{system}-{hostname}-{machine}".replace('.', '-')
            
    except Exception:
        # Fallback to simple format
        import os
        return f"{platform.system().lower()}-{os.getpid()}"


def detect_role():
    """Auto-detect appropriate role based on platform"""
    system = platform.system().lower()
    
    # Check for Android/Termux
    import os
    if any(indicator in os.environ for indicator in ['ANDROID_ROOT', 'ANDROID_DATA', 'PREFIX']):
        return 'mobile'
    
    # Check for common server indicators
    if system == 'linux':
        # Check if it's likely a server (headless, has Docker, etc.)
        server_indicators = [
            '/usr/bin/docker',
            '/usr/bin/systemctl',
            '/etc/systemd'
        ]
        if any(Path(p).exists() for p in server_indicators):
            return 'compute'
    
    return 'worker'  # Default role


def main():
    """Main entry point for retire-cluster-worker command"""
    parser = argparse.ArgumentParser(
        description='Retire-Cluster Worker Node - Join a cluster and execute tasks',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  retire-cluster-worker --join 192.168.1.100        # Join cluster with auto-generated ID
  retire-cluster-worker --join 192.168.1.100:8080 --device-id my-laptop  # Custom device ID
  retire-cluster-worker --join 192.168.1.100 --role mobile               # Specify role
  retire-cluster-worker --test 192.168.1.100        # Test connection only
        """
    )
    
    parser.add_argument(
        '--join',
        metavar='HOST[:PORT]',
        help='Join cluster by connecting to main node (e.g., 192.168.1.100 or 192.168.1.100:8080)'
    )
    
    parser.add_argument(
        '--device-id',
        help='Device identifier (auto-generated if not specified)'
    )
    
    parser.add_argument(
        '--role',
        choices=['worker', 'compute', 'storage', 'mobile'],
        help='Device role in cluster (auto-detected if not specified)'
    )
    
    parser.add_argument(
        '--test',
        metavar='HOST[:PORT]',
        help='Test connection to main node and show device info'
    )
    
    parser.add_argument(
        '--heartbeat-interval',
        type=int,
        default=60,
        help='Heartbeat interval in seconds (default: 60)'
    )
    
    parser.add_argument(
        '--data-dir',
        type=Path,
        default=Path.home() / '.retire-cluster',
        help='Data directory (default: ~/.retire-cluster)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.join and not args.test:
        parser.error("Must specify either --join or --test")
    
    # Parse host and port
    target = args.join or args.test
    if ':' in target:
        host, port_str = target.rsplit(':', 1)
        try:
            port = int(port_str)
        except ValueError:
            parser.error(f"Invalid port number: {port_str}")
    else:
        host = target
        port = 8080
    
    # Generate device ID if not provided
    device_id = args.device_id or generate_device_id()
    
    # Detect role if not provided
    role = args.role or detect_role()
    
    # Setup data directory
    data_dir = args.data_dir
    data_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Create worker configuration
        config = WorkerConfig()
        config.device_id = device_id
        config.role = role
        config.main_host = host
        config.main_port = port
        config.heartbeat_interval = args.heartbeat_interval
        
        # Setup logging
        log_level = "DEBUG" if args.debug else "INFO"
        logger = get_logger(
            name=f"worker.{device_id}",
            log_file=str(data_dir / f"worker_{device_id}.log"),
            level=log_level
        )
        
        # Create client
        client = ClusterClient(config)
        
        if args.test:
            # Test mode
            print("🔍 Retire-Cluster Worker Test Mode")
            print("=" * 50)
            
            # Show device information
            profile = client.profiler.get_device_profile()
            print(f"📱 Device ID: {profile['device_id']}")
            print(f"🏷️  Role: {profile['role']}")
            print(f"💻 Platform: {profile['platform']} ({profile.get('platform_details', {}).get('system', 'unknown')})")
            print(f"🌐 IP Address: {profile.get('ip_address', 'unknown')}")
            print(f"⚙️  CPU Cores: {profile.get('cpu_count', 'unknown')}")
            print(f"💾 Memory: {profile.get('memory_total_gb', 'unknown')} GB")
            print(f"💿 Storage: {profile.get('storage_total_gb', 'unknown')} GB")
            print(f"🏷️  Tags: {', '.join(profile.get('tags', []))}")
            print(f"📊 Has psutil: {profile.get('has_psutil', False)}")
            print()
            
            print(f"🔗 Testing connection to {host}:{port}...")
            if client.test_connection():
                print("✅ Connection successful!")
                
                status = client.get_cluster_status()
                if status:
                    stats = status.get('cluster_stats', {})
                    print(f"📊 Cluster Status:")
                    print(f"   Health: {stats.get('health_percentage', 0)}%")
                    print(f"   Online devices: {stats.get('online_devices', 0)}")
                    print(f"   Total devices: {stats.get('total_devices', 0)}")
                    
                    by_role = stats.get('by_role', {})
                    if by_role:
                        print(f"   Devices by role:")
                        for role_name, count in by_role.items():
                            print(f"     {role_name}: {count}")
                
                print(f"\n✅ Ready to join cluster with:")
                print(f"   retire-cluster-worker --join {host}:{port} --device-id {device_id}")
            else:
                print("❌ Connection failed!")
                print("   Check that the main node is running and accessible")
                sys.exit(1)
        
        else:
            # Normal mode - join cluster
            print("🚀 Retire-Cluster Worker Starting...")
            print(f"📱 Device ID: {device_id}")
            print(f"🏷️  Role: {role}")
            print(f"💻 Platform: {platform.system()} {platform.release()}")
            print(f"🔗 Connecting to: {host}:{port}")
            print(f"💓 Heartbeat interval: {args.heartbeat_interval}s")
            print("=" * 50)
            
            logger.info(f"Starting worker {device_id} with role {role}")
            logger.info(f"Connecting to main node: {host}:{port}")
            
            print("🔄 Joining cluster...")
            print("Press Ctrl+C to stop...")
            
            # Start worker
            client.run()
        
    except KeyboardInterrupt:
        print("\n🛑 Worker shutdown requested")
        if 'logger' in locals():
            logger.info("Worker shutdown requested")
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()