#!/bin/bash
# Retire-Cluster Backup Script
# Automated backup for Docker deployment on NAS

set -e

# Configuration
BACKUP_ROOT="/volume1/backups/retire-cluster"
DATA_PATH="/volume1/docker/retire-cluster"
RETENTION_DAYS=7
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${BACKUP_ROOT}/${TIMESTAMP}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Functions
log_info() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} INFO: $1"
}

log_warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} WARN: $1"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} ERROR: $1"
}

# Create backup directory
create_backup_dir() {
    log_info "Creating backup directory: ${BACKUP_DIR}"
    mkdir -p "${BACKUP_DIR}"
}

# Backup database
backup_database() {
    log_info "Backing up database..."
    
    # Create database backup using SQLite backup command
    docker exec retire-cluster-main sqlite3 /data/database/cluster.db ".backup '${BACKUP_DIR}/cluster.db.backup'"
    
    # Also create SQL dump for portability
    docker exec retire-cluster-main sqlite3 /data/database/cluster.db .dump > "${BACKUP_DIR}/cluster.sql"
    
    log_info "Database backup completed"
}

# Backup configuration
backup_config() {
    log_info "Backing up configuration..."
    
    # Copy config files
    cp -r "${DATA_PATH}/config" "${BACKUP_DIR}/"
    
    # Copy environment file if exists
    if [ -f "../.env" ]; then
        cp "../.env" "${BACKUP_DIR}/.env.backup"
    fi
    
    log_info "Configuration backup completed"
}

# Backup logs (optional, last 1000 lines)
backup_logs() {
    log_info "Backing up recent logs..."
    
    # Create logs directory
    mkdir -p "${BACKUP_DIR}/logs"
    
    # Copy recent logs
    if [ -d "${DATA_PATH}/logs" ]; then
        for logfile in "${DATA_PATH}/logs"/*.log; do
            if [ -f "$logfile" ]; then
                filename=$(basename "$logfile")
                tail -n 1000 "$logfile" > "${BACKUP_DIR}/logs/${filename}.recent"
            fi
        done
    fi
    
    # Docker container logs
    docker logs --tail 1000 retire-cluster-main > "${BACKUP_DIR}/logs/docker.log" 2>&1 || true
    
    log_info "Logs backup completed"
}

# Create backup archive
create_archive() {
    log_info "Creating backup archive..."
    
    cd "${BACKUP_ROOT}"
    tar -czf "backup_${TIMESTAMP}.tar.gz" "${TIMESTAMP}/"
    
    # Remove uncompressed backup directory
    rm -rf "${BACKUP_DIR}"
    
    # Calculate archive size
    ARCHIVE_SIZE=$(du -h "backup_${TIMESTAMP}.tar.gz" | cut -f1)
    log_info "Backup archive created: backup_${TIMESTAMP}.tar.gz (${ARCHIVE_SIZE})"
}

# Clean old backups
cleanup_old_backups() {
    log_info "Cleaning up old backups (retention: ${RETENTION_DAYS} days)..."
    
    # Find and remove old backup files
    find "${BACKUP_ROOT}" -name "backup_*.tar.gz" -type f -mtime +${RETENTION_DAYS} -exec rm {} \; 2>/dev/null || true
    
    # Count remaining backups
    BACKUP_COUNT=$(find "${BACKUP_ROOT}" -name "backup_*.tar.gz" -type f | wc -l)
    log_info "Retained ${BACKUP_COUNT} backup(s)"
}

# Verify backup
verify_backup() {
    log_info "Verifying backup integrity..."
    
    # Test archive integrity
    if tar -tzf "${BACKUP_ROOT}/backup_${TIMESTAMP}.tar.gz" > /dev/null 2>&1; then
        log_info "Backup verification successful"
        return 0
    else
        log_error "Backup verification failed!"
        return 1
    fi
}

# Send notification (optional - for Synology/QNAP)
send_notification() {
    local status=$1
    local message=$2
    
    # Synology notification
    if command -v synodsmnotify &> /dev/null; then
        synodsmnotify -t "Retire-Cluster Backup" -m "$message" @administrators
    fi
    
    # QNAP notification (if applicable)
    # Add QNAP notification command here if needed
}

# Main backup function
perform_backup() {
    log_info "Starting Retire-Cluster backup..."
    
    # Check if container is running
    if ! docker ps | grep -q retire-cluster-main; then
        log_error "Container retire-cluster-main is not running!"
        exit 1
    fi
    
    # Create backup
    create_backup_dir
    backup_database
    backup_config
    backup_logs
    create_archive
    
    # Verify and cleanup
    if verify_backup; then
        cleanup_old_backups
        log_info "Backup completed successfully!"
        send_notification "success" "Retire-Cluster backup completed: backup_${TIMESTAMP}.tar.gz"
        exit 0
    else
        log_error "Backup failed!"
        send_notification "error" "Retire-Cluster backup failed at ${TIMESTAMP}"
        exit 1
    fi
}

# Restore function
restore_backup() {
    local BACKUP_FILE=$1
    
    if [ -z "$BACKUP_FILE" ]; then
        log_error "Backup file not specified"
        echo "Usage: $0 restore <backup_file.tar.gz>"
        exit 1
    fi
    
    if [ ! -f "$BACKUP_FILE" ]; then
        log_error "Backup file not found: $BACKUP_FILE"
        exit 1
    fi
    
    log_warn "This will restore the backup and overwrite current data!"
    read -p "Are you sure? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        log_info "Restore cancelled"
        exit 0
    fi
    
    log_info "Stopping services..."
    docker-compose down || docker compose down
    
    log_info "Extracting backup..."
    TEMP_DIR=$(mktemp -d)
    tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"
    
    # Find the backup directory (it should be named with timestamp)
    BACKUP_CONTENT=$(find "$TEMP_DIR" -maxdepth 1 -type d | tail -1)
    
    log_info "Restoring configuration..."
    cp -r "$BACKUP_CONTENT/config/"* "${DATA_PATH}/config/"
    
    log_info "Restoring database..."
    cp "$BACKUP_CONTENT/cluster.db.backup" "${DATA_PATH}/database/cluster.db"
    
    log_info "Starting services..."
    docker-compose up -d || docker compose up -d
    
    # Cleanup
    rm -rf "$TEMP_DIR"
    
    log_info "Restore completed successfully!"
    send_notification "success" "Retire-Cluster restore completed from ${BACKUP_FILE}"
}

# Parse command line arguments
case "${1:-backup}" in
    backup)
        perform_backup
        ;;
    restore)
        restore_backup "$2"
        ;;
    *)
        echo "Usage: $0 [backup|restore <backup_file>]"
        echo ""
        echo "Commands:"
        echo "  backup              Create a new backup (default)"
        echo "  restore <file>      Restore from a backup file"
        echo ""
        echo "Examples:"
        echo "  $0                  # Create backup"
        echo "  $0 backup           # Create backup"
        echo "  $0 restore backup_20240115_103000.tar.gz"
        exit 1
        ;;
esac