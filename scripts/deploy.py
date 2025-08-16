#!/usr/bin/env python3
"""
Deployment script for Retire-Cluster
Simple deployment to remote hosts via SSH
"""

import argparse
import os
import subprocess
import sys
import tempfile
import tarfile
from pathlib import Path
from typing import List, Dict, Any


def run_command(command: List[str], cwd: str = None) -> bool:
    """Run a command and return success status"""
    try:
        result = subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {' '.join(command)}")
        print(f"Error: {e.stderr}")
        return False


def create_package() -> str:
    """Create deployment package"""
    print("Creating deployment package...")
    
    # Get project root
    project_root = Path(__file__).parent.parent
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        package_path = os.path.join(temp_dir, "retire-cluster.tar.gz")
        
        # Create tar archive
        with tarfile.open(package_path, "w:gz") as tar:
            # Add main package
            tar.add(project_root / "retire_cluster", arcname="retire_cluster")
            
            # Add configuration files
            tar.add(project_root / "setup.py", arcname="setup.py")
            tar.add(project_root / "requirements.txt", arcname="requirements.txt")
            
            # Add scripts
            if (project_root / "scripts").exists():
                tar.add(project_root / "scripts", arcname="scripts")
        
        # Copy to final location
        final_package = project_root / "dist" / "retire-cluster.tar.gz"
        final_package.parent.mkdir(exist_ok=True)
        
        import shutil
        shutil.copy2(package_path, final_package)
        
        print(f"Package created: {final_package}")
        return str(final_package)


def deploy_to_host(host: str, username: str, package_path: str, node_type: str, 
                   port: int = 22, key_file: str = None) -> bool:
    """Deploy package to remote host"""
    print(f"Deploying to {username}@{host}:{port} as {node_type} node...")
    
    # Build SSH command prefix
    ssh_cmd = ["ssh"]
    scp_cmd = ["scp"]
    
    if port != 22:
        ssh_cmd.extend(["-p", str(port)])
        scp_cmd.extend(["-P", str(port)])
    
    if key_file:
        ssh_cmd.extend(["-i", key_file])
        scp_cmd.extend(["-i", key_file])
    
    host_spec = f"{username}@{host}"
    
    try:
        # Test connection
        print(f"Testing connection to {host_spec}...")
        test_cmd = ssh_cmd + [host_spec, "echo 'Connection successful'"]
        if not run_command(test_cmd):
            print(f"Failed to connect to {host_spec}")
            return False
        
        # Copy package
        print("Copying package...")
        copy_cmd = scp_cmd + [package_path, f"{host_spec}:~/retire-cluster.tar.gz"]
        if not run_command(copy_cmd):
            print("Failed to copy package")
            return False
        
        # Extract and install
        print("Extracting and installing...")
        install_commands = [
            "tar -xzf retire-cluster.tar.gz",
            "cd retire-cluster",
            "python3 -m pip install --user .",
            "mkdir -p ~/.local/bin"
        ]
        
        for cmd in install_commands:
            ssh_install_cmd = ssh_cmd + [host_spec, cmd]
            if not run_command(ssh_install_cmd):
                print(f"Failed to run: {cmd}")
                return False
        
        # Create configuration based on node type
        if node_type == "main":
            config_content = """{{
  "server": {{
    "host": "0.0.0.0",
    "port": 8080
  }},
  "database": {{
    "path": "./data/cluster_metadata.json"
  }},
  "logging": {{
    "level": "INFO",
    "file_path": "./logs/main_node.log"
  }}
}}"""
            
            config_cmd = ssh_cmd + [host_spec, f"echo '{config_content}' > config.json"]
            run_command(config_cmd)
            
        elif node_type == "worker":
            config_content = """{{
  "device": {{
    "id": "auto-generated",
    "role": "worker"
  }},
  "main_node": {{
    "host": "192.168.0.116",
    "port": 8080
  }}
}}"""
            
            config_cmd = ssh_cmd + [host_spec, f"echo '{config_content}' > worker_config.json"]
            run_command(config_cmd)
        
        print(f"Successfully deployed to {host_spec}")
        return True
        
    except Exception as e:
        print(f"Deployment failed: {e}")
        return False


def main():
    """Main deployment function"""
    parser = argparse.ArgumentParser(description='Deploy Retire-Cluster to remote hosts')
    
    parser.add_argument('--package', help='Use existing package file')
    parser.add_argument('--hosts', required=True, help='Comma-separated list of host:username:type[:port[:keyfile]]')
    
    args = parser.parse_args()
    
    # Create package if not provided
    if args.package and os.path.exists(args.package):
        package_path = args.package
    else:
        package_path = create_package()
    
    # Parse hosts
    hosts = []
    for host_spec in args.hosts.split(','):
        parts = host_spec.strip().split(':')
        if len(parts) < 3:
            print(f"Invalid host specification: {host_spec}")
            print("Format: host:username:type[:port[:keyfile]]")
            continue
        
        host_config = {
            'host': parts[0],
            'username': parts[1],
            'type': parts[2],
            'port': int(parts[3]) if len(parts) > 3 else 22,
            'key_file': parts[4] if len(parts) > 4 else None
        }
        hosts.append(host_config)
    
    # Deploy to each host
    success_count = 0
    for host_config in hosts:
        if deploy_to_host(
            host_config['host'],
            host_config['username'],
            package_path,
            host_config['type'],
            host_config['port'],
            host_config['key_file']
        ):
            success_count += 1
    
    print(f"\nDeployment completed: {success_count}/{len(hosts)} hosts successful")
    
    if success_count > 0:
        print("\nNext steps:")
        print("1. SSH to main node and run: python3 -m retire_cluster.main_node")
        print("2. SSH to worker nodes and run: python3 -m retire_cluster.worker_node --auto-id")


if __name__ == "__main__":
    main()