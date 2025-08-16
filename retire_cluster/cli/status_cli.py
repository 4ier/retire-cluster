#!/usr/bin/env python3
"""
Command-line interface for Retire-Cluster Status Queries
"""

import argparse
import sys
import json
import socket
from datetime import datetime

from ..communication.protocol import Message, MessageType


def send_query(host, port, message_type, data=None, timeout=10):
    """Send query to main node and return response"""
    try:
        # Create message
        message = Message(
            message_type=message_type,
            sender_id="status-cli",
            data=data or {}
        )
        
        # Connect and send
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        
        sock.send(message.to_json().encode('utf-8'))
        
        # Receive response
        response_data = sock.recv(8192).decode('utf-8')
        if response_data:
            response = Message.from_json(response_data)
            sock.close()
            return response
        
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return None
    finally:
        try:
            sock.close()
        except:
            pass
    
    return None


def format_bytes(bytes_value):
    """Format bytes in human readable format"""
    if bytes_value is None:
        return "N/A"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"


def format_uptime(timestamp_str):
    """Format uptime from timestamp"""
    try:
        from datetime import datetime
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        now = datetime.now(timestamp.tzinfo)
        uptime = now - timestamp
        
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    except:
        return "N/A"


def main():
    """Main entry point for retire-cluster-status command"""
    parser = argparse.ArgumentParser(
        description='Retire-Cluster Status - Query cluster information',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  retire-cluster-status 192.168.1.100              # Show cluster overview
  retire-cluster-status 192.168.1.100 --devices    # List all devices
  retire-cluster-status 192.168.1.100 --device worker-001  # Show specific device
  retire-cluster-status 192.168.1.100 --json       # Output in JSON format
        """
    )
    
    parser.add_argument(
        'host',
        help='Main node host (e.g., 192.168.1.100 or 192.168.1.100:8080)'
    )
    
    parser.add_argument(
        '--devices',
        action='store_true',
        help='List all devices in the cluster'
    )
    
    parser.add_argument(
        '--device',
        metavar='DEVICE_ID',
        help='Show detailed information for specific device'
    )
    
    parser.add_argument(
        '--role',
        choices=['worker', 'compute', 'storage', 'mobile'],
        help='Filter devices by role'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output in JSON format'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=10,
        help='Connection timeout in seconds (default: 10)'
    )
    
    args = parser.parse_args()
    
    # Parse host and port
    if ':' in args.host:
        host, port_str = args.host.rsplit(':', 1)
        try:
            port = int(port_str)
        except ValueError:
            parser.error(f"Invalid port number: {port_str}")
    else:
        host = args.host
        port = 8080
    
    try:
        if args.device:
            # Query specific device
            response = send_query(host, port, MessageType.DEVICE_INFO, 
                                {'device_id': args.device}, args.timeout)
            
            if not response or response.message_type == MessageType.ERROR:
                error_msg = response.data.get('error') if response else "No response"
                print(f"❌ Failed to get device info: {error_msg}")
                sys.exit(1)
            
            result = response.data.get('result', {})
            device = result.get('device')
            
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                if device:
                    print(f"📱 Device: {device['device_id']}")
                    print(f"🏷️  Role: {device.get('role', 'unknown')}")
                    print(f"🔄 Status: {device.get('status', 'unknown')}")
                    print(f"💻 Platform: {device.get('platform', 'unknown')}")
                    print(f"🌐 IP Address: {device.get('ip_address', 'unknown')}")
                    print(f"💓 Last Heartbeat: {device.get('last_heartbeat', 'unknown')}")
                    
                    hardware = device.get('hardware', {})
                    print(f"⚙️  CPU Cores: {hardware.get('cpu_count', 'unknown')}")
                    print(f"💾 Memory: {hardware.get('memory_total_gb', 'unknown')} GB")
                    print(f"💿 Storage: {hardware.get('storage_total_gb', 'unknown')} GB")
                    
                    tags = device.get('tags', [])
                    if tags:
                        print(f"🏷️  Tags: {', '.join(tags)}")
                else:
                    print(f"❌ Device '{args.device}' not found")
        
        elif args.devices:
            # List all devices
            query_data = {}
            if args.role:
                query_data['role'] = args.role
            
            response = send_query(host, port, MessageType.LIST_DEVICES, 
                                query_data, args.timeout)
            
            if not response or response.message_type == MessageType.ERROR:
                error_msg = response.data.get('error') if response else "No response"
                print(f"❌ Failed to get device list: {error_msg}")
                sys.exit(1)
            
            result = response.data.get('result', {})
            devices = result.get('devices', [])
            
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                if devices:
                    print(f"📱 Devices ({len(devices)} found):")
                    print("-" * 80)
                    
                    for device in devices:
                        status_icon = "🟢" if device.get('status') == 'online' else "🔴"
                        print(f"{status_icon} {device['device_id']:<20} {device.get('role', 'unknown'):<10} "
                              f"{device.get('platform', 'unknown'):<10} {device.get('ip_address', 'unknown'):<15}")
                else:
                    filter_text = f" with role '{args.role}'" if args.role else ""
                    print(f"No devices found{filter_text}")
        
        else:
            # Show cluster overview
            response = send_query(host, port, MessageType.STATUS, {}, args.timeout)
            
            if not response or response.message_type == MessageType.ERROR:
                error_msg = response.data.get('error') if response else "No response"
                print(f"❌ Failed to get cluster status: {error_msg}")
                sys.exit(1)
            
            result = response.data.get('result', {})
            
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                stats = result.get('cluster_stats', {})
                
                print("🚀 Retire-Cluster Status")
                print("=" * 50)
                print(f"🌐 Main Node: {host}:{port}")
                print(f"📊 Health: {stats.get('health_percentage', 0)}%")
                print(f"📱 Online Devices: {stats.get('online_devices', 0)}")
                print(f"📱 Total Devices: {stats.get('total_devices', 0)}")
                
                # Resources summary
                resources = stats.get('total_resources', {})
                if resources:
                    print("\n💻 Total Resources:")
                    print(f"   ⚙️  CPU Cores: {resources.get('cpu_cores', 0)}")
                    print(f"   💾 Memory: {resources.get('memory_gb', 0)} GB")
                    print(f"   💿 Storage: {resources.get('storage_gb', 0)} GB")
                
                # Devices by role
                by_role = stats.get('by_role', {})
                if by_role:
                    print("\n📋 Devices by Role:")
                    for role, count in by_role.items():
                        print(f"   {role}: {count}")
                
                # Devices by platform
                by_platform = stats.get('by_platform', {})
                if by_platform:
                    print("\n💻 Devices by Platform:")
                    for platform_name, count in by_platform.items():
                        print(f"   {platform_name}: {count}")
                
                print(f"\n🕒 Last Updated: {result.get('timestamp', 'unknown')}")
                
                if stats.get('online_devices', 0) == 0:
                    print("\n💡 No devices online. Start workers with:")
                    print(f"   retire-cluster-worker --join {host}:{port}")
    
    except KeyboardInterrupt:
        print("\n🛑 Interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        if '--json' not in sys.argv:  # Don't show traceback in JSON mode
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()