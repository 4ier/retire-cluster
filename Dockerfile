# Multi-stage Dockerfile for Retire-Cluster Main Node
# Optimized for NAS deployment with minimal image size

# Stage 1: Builder
FROM python:3.9-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies to user directory
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.9-slim

LABEL maintainer="Retire-Cluster Team"
LABEL description="Main Node server for Retire-Cluster idle device management"
LABEL version="1.0.0"

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    netcat-traditional \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/bash cluster && \
    mkdir -p /data/config /data/database /data/logs /app && \
    chown -R cluster:cluster /data /app

# Copy Python packages from builder
COPY --from=builder --chown=cluster:cluster /root/.local /home/cluster/.local

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=cluster:cluster retire_cluster/ ./retire_cluster/
COPY --chown=cluster:cluster README.md LICENSE ./

# Create default configuration if not exists
COPY --chown=cluster:cluster <<EOF /app/default_config.json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8080,
    "max_connections": 100
  },
  "web": {
    "enabled": true,
    "host": "0.0.0.0",
    "port": 5000,
    "debug": false
  },
  "database": {
    "path": "/data/database/cluster.db",
    "backup_enabled": true,
    "backup_interval": 3600
  },
  "logging": {
    "level": "INFO",
    "file": "/data/logs/cluster.log",
    "max_size": "10MB",
    "backup_count": 5
  },
  "cluster": {
    "heartbeat_interval": 60,
    "offline_threshold": 300,
    "task_timeout": 3600,
    "max_retries": 3
  }
}
EOF

# Create startup script
COPY --chown=cluster:cluster <<'EOF' /app/start.sh
#!/bin/bash
set -e

# Copy default config if not exists
if [ ! -f /data/config/config.json ]; then
    echo "Creating default configuration..."
    cp /app/default_config.json /data/config/config.json
fi

# Initialize database if not exists
if [ ! -f /data/database/cluster.db ]; then
    echo "Initializing database..."
    python -m retire_cluster.database.init
fi

# Start both Main Node and Web Dashboard
echo "Starting Retire-Cluster Main Node..."
python -m retire_cluster.main_node --config /data/config/config.json &
MAIN_PID=$!

echo "Starting Web Dashboard..."
python -m retire_cluster.web.app --config /data/config/config.json &
WEB_PID=$!

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
EOF

RUN chmod +x /app/start.sh

# Switch to non-root user
USER cluster

# Set environment variables
ENV PYTHONPATH=/app:/home/cluster/.local/lib/python3.9/site-packages
ENV PATH=/home/cluster/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/api/health || exit 1

# Expose ports
# 8080: Main Node API
# 5000: Web Dashboard
EXPOSE 8080 5000

# Volume mount points
VOLUME ["/data/config", "/data/database", "/data/logs"]

# Entry point
ENTRYPOINT ["/app/start.sh"]