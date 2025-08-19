#!/bin/bash
# Fix port configuration and restart service

echo "🔧 Fixing port configuration for NAS deployment..."

# Check current status
echo "📊 Current container status:"
docker ps -a | grep retire-cluster

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Update .env file with correct port
echo "📝 Updating port configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
fi

# Set Web port to 5008
sed -i "s/WEB_PORT=.*/WEB_PORT=5008/" .env
sed -i "s/CLUSTER_PORT=.*/CLUSTER_PORT=8081/" .env

echo "✅ Port configuration updated:"
grep -E "(WEB_PORT|CLUSTER_PORT)" .env

# Restart services
echo "🚀 Starting services with new configuration..."
docker-compose up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🏥 Checking service health..."
if curl -f http://localhost:5008 &> /dev/null; then
    echo "✅ Web Dashboard is accessible at port 5008"
else
    echo "⚠️ Web Dashboard not responding, checking logs..."
    docker logs --tail 50 retire-cluster-main
fi

echo ""
echo "📋 Service URLs:"
echo "  Main Node API: http://$(hostname -I | awk '{print $1}'):8081"
echo "  Web Dashboard: http://$(hostname -I | awk '{print $1}'):5008"
echo ""
echo "💡 If still not accessible from other devices:"
echo "  1. Check NAS firewall settings"
echo "  2. Ensure Docker port binding is correct"
echo "  3. Verify network connectivity"