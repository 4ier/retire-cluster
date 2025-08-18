#!/bin/bash
# Retire-Cluster Health Monitoring Script
# Monitors container health and sends alerts on issues

set -e

# Configuration
CHECK_INTERVAL=60  # seconds
MAX_FAILURES=3
ALERT_COOLDOWN=3600  # seconds between repeated alerts
LOG_FILE="/var/log/retire-cluster-monitor.log"
ENV_FILE=".env"  # Path to environment file

# State tracking
FAILURE_COUNT=0
LAST_ALERT_TIME=0

# Colors for console output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Logging functions
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} INFO: $1" | tee -a "$LOG_FILE"
}

log_warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} WARN: $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} ERROR: $1" | tee -a "$LOG_FILE"
}

# Send alert notification
send_alert() {
    local level=$1
    local message=$2
    
    # Check cooldown
    local current_time=$(date +%s)
    if [ $((current_time - LAST_ALERT_TIME)) -lt $ALERT_COOLDOWN ]; then
        log_info "Alert suppressed due to cooldown"
        return
    fi
    
    LAST_ALERT_TIME=$current_time
    
    # Log alert
    log_error "ALERT: $message"
    
    # Synology DSM notification
    if command -v synodsmnotify &> /dev/null; then
        synodsmnotify -t "Retire-Cluster Alert" -m "$message" @administrators
    fi
    
    # Email notification (if configured)
    if [ -n "$ALERT_EMAIL" ]; then
        echo "$message" | mail -s "Retire-Cluster Alert - $level" "$ALERT_EMAIL" 2>/dev/null || true
    fi
    
    # Webhook notification (if configured)
    if [ -n "$ALERT_WEBHOOK" ]; then
        curl -X POST "$ALERT_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "{\"level\":\"$level\",\"message\":\"$message\",\"timestamp\":\"$(date -Iseconds)\"}" \
            2>/dev/null || true
    fi
}

# Check container status
check_container() {
    local container_name="retire-cluster-main"
    
    # Check if container exists
    if ! docker ps -a --format "{{.Names}}" | grep -q "^${container_name}$"; then
        log_error "Container ${container_name} does not exist"
        return 1
    fi
    
    # Check if container is running
    local status=$(docker inspect -f '{{.State.Status}}' "$container_name" 2>/dev/null)
    if [ "$status" != "running" ]; then
        log_error "Container is not running (status: $status)"
        return 1
    fi
    
    # Check container health
    local health=$(docker inspect -f '{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "none")
    if [ "$health" = "unhealthy" ]; then
        log_error "Container is unhealthy"
        return 1
    fi
    
    return 0
}

# Check API health
check_api_health() {
    # Load port configuration from .env
    local api_port="8081"  # default
    if [ -f "$ENV_FILE" ]; then
        source "$ENV_FILE" 2>/dev/null
        api_port="${CLUSTER_PORT:-8081}"
    fi
    
    local api_url="http://localhost:${api_port}/api/health"
    local response
    
    # Make health check request
    response=$(curl -s -f -w "\n%{http_code}" "$api_url" 2>/dev/null) || return 1
    
    # Extract HTTP status code
    local http_code=$(echo "$response" | tail -1)
    
    if [ "$http_code" != "200" ]; then
        log_error "API health check failed (HTTP $http_code)"
        return 1
    fi
    
    return 0
}

# Check web dashboard
check_web_dashboard() {
    # Load port configuration from .env
    local web_port="5001"  # default
    if [ -f "$ENV_FILE" ]; then
        source "$ENV_FILE" 2>/dev/null
        web_port="${WEB_PORT:-5001}"
    fi
    
    local web_url="http://localhost:${web_port}"
    
    # Simple connectivity check
    if ! curl -s -f -o /dev/null "$web_url" 2>/dev/null; then
        log_warn "Web dashboard not accessible"
        return 1
    fi
    
    return 0
}

# Check resource usage
check_resources() {
    local container_name="retire-cluster-main"
    
    # Get container stats
    local stats=$(docker stats --no-stream --format "json" "$container_name" 2>/dev/null)
    
    if [ -n "$stats" ]; then
        # Parse CPU and memory usage
        local cpu_percent=$(echo "$stats" | jq -r '.CPUPerc' | sed 's/%//')
        local mem_usage=$(echo "$stats" | jq -r '.MemUsage' | cut -d'/' -f1)
        local mem_limit=$(echo "$stats" | jq -r '.MemUsage' | cut -d'/' -f2)
        
        # Check CPU threshold
        if (( $(echo "$cpu_percent > 90" | bc -l) )); then
            log_warn "High CPU usage: ${cpu_percent}%"
        fi
        
        # Log current stats
        log_info "Resources - CPU: ${cpu_percent}%, Memory: ${mem_usage}/${mem_limit}"
    fi
    
    return 0
}

# Check disk space
check_disk_space() {
    local data_path="/volume1/docker/retire-cluster"
    
    # Get disk usage percentage
    local disk_usage=$(df -h "$data_path" | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ "$disk_usage" -gt 90 ]; then
        log_error "Critical disk space: ${disk_usage}% used"
        send_alert "critical" "Disk space critical: ${disk_usage}% used at ${data_path}"
        return 1
    elif [ "$disk_usage" -gt 80 ]; then
        log_warn "Low disk space: ${disk_usage}% used"
        return 0
    fi
    
    return 0
}

# Check database integrity
check_database() {
    local container_name="retire-cluster-main"
    
    # Run integrity check
    if docker exec "$container_name" sqlite3 /data/database/cluster.db "PRAGMA integrity_check;" | grep -q "ok"; then
        return 0
    else
        log_error "Database integrity check failed"
        return 1
    fi
}

# Attempt auto-recovery
attempt_recovery() {
    log_warn "Attempting auto-recovery..."
    
    # Try restarting the container
    docker restart retire-cluster-main
    
    # Wait for container to start
    sleep 30
    
    # Check if recovery successful
    if check_container && check_api_health; then
        log_info "Auto-recovery successful"
        send_alert "info" "Retire-Cluster auto-recovery successful after $FAILURE_COUNT failures"
        FAILURE_COUNT=0
        return 0
    else
        log_error "Auto-recovery failed"
        return 1
    fi
}

# Main monitoring loop
monitor_loop() {
    log_info "Starting health monitoring (interval: ${CHECK_INTERVAL}s)..."
    
    while true; do
        # Perform health checks
        local all_healthy=true
        
        # Container check
        if ! check_container; then
            all_healthy=false
            FAILURE_COUNT=$((FAILURE_COUNT + 1))
        fi
        
        # API health check
        if ! check_api_health; then
            all_healthy=false
            FAILURE_COUNT=$((FAILURE_COUNT + 1))
        fi
        
        # Web dashboard check (warning only)
        check_web_dashboard || true
        
        # Resource checks
        check_resources || true
        check_disk_space || true
        
        # Database check (less frequent)
        if [ $(($(date +%s) % 3600)) -lt $CHECK_INTERVAL ]; then
            check_database || log_warn "Database check failed"
        fi
        
        # Handle failures
        if [ "$all_healthy" = true ]; then
            if [ $FAILURE_COUNT -gt 0 ]; then
                log_info "Health restored after $FAILURE_COUNT failures"
            fi
            FAILURE_COUNT=0
        else
            log_error "Health check failed (failure count: $FAILURE_COUNT)"
            
            if [ $FAILURE_COUNT -ge $MAX_FAILURES ]; then
                send_alert "critical" "Retire-Cluster health check failed $FAILURE_COUNT times"
                
                # Attempt recovery
                if ! attempt_recovery; then
                    send_alert "critical" "Retire-Cluster auto-recovery failed - manual intervention required"
                fi
            fi
        fi
        
        # Wait for next check
        sleep $CHECK_INTERVAL
    done
}

# Handle signals
trap 'log_info "Monitoring stopped"; exit 0' SIGTERM SIGINT

# Main execution
main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --interval)
                CHECK_INTERVAL="$2"
                shift 2
                ;;
            --max-failures)
                MAX_FAILURES="$2"
                shift 2
                ;;
            --email)
                ALERT_EMAIL="$2"
                shift 2
                ;;
            --webhook)
                ALERT_WEBHOOK="$2"
                shift 2
                ;;
            --env-file)
                ENV_FILE="$2"
                shift 2
                ;;
            --daemon)
                DAEMON_MODE=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --interval SECONDS      Check interval (default: 60)"
                echo "  --max-failures COUNT    Max failures before alert (default: 3)"
                echo "  --email ADDRESS         Email for alerts"
                echo "  --webhook URL           Webhook URL for alerts"
                echo "  --env-file PATH         Path to .env file (default: .env)"
                echo "  --daemon                Run as daemon"
                echo "  --help                  Show this help"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Start monitoring
    if [ "$DAEMON_MODE" = true ]; then
        # Run in background
        nohup "$0" > /dev/null 2>&1 &
        echo $! > /var/run/retire-cluster-monitor.pid
        log_info "Started monitoring daemon (PID: $!)"
    else
        # Run in foreground
        monitor_loop
    fi
}

# Run main function
main "$@"