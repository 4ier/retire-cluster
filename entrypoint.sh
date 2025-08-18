#!/bin/sh
# Entrypoint script to start both main node and web dashboard

set -e

echo "Starting Retire-Cluster services..."

# Start main node in background
echo "Starting main node on port 8080..."
python -m retire_cluster.main_node &
MAIN_PID=$!

# Wait for main node to initialize
sleep 3

# Start web dashboard (foreground)
echo "Starting web dashboard on port 5000..."
export FLASK_APP=retire_cluster.web.app
export WEB_PORT=5000

# Use exec to replace shell with web process
exec python -m retire_cluster.web.app --port 5000