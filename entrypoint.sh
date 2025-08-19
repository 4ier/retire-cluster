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

# Create web server script
cat > /tmp/start_web.py << 'EOF'
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/app')
from retire_cluster.web.app import create_app

if __name__ == '__main__':
    app = create_app()
    print('Web Dashboard starting on port 5000...')
    print('Access the terminal at: http://<your-ip>:5000/cli')
    app.run(host='0.0.0.0', port=5000, debug=False)
EOF

# Start web dashboard (foreground)
echo "Starting web dashboard on port 5000..."
exec python /tmp/start_web.py