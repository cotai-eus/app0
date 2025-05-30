#!/bin/bash

# =====================================================
# 🔄 DATABASE RESTORE SCRIPT
# PostgreSQL + MongoDB + Redis restore automation
# =====================================================

set -euo pipefail

# Configuration
BACKUP_DIR="/home/app/backups"
LOG_FILE="/home/app/logs/restore_$(date +%Y%m%d_%H%M%S).log"

# Database credentials
POSTGRES_USER="app_user"
POSTGRES_DB="app_relational"
MONGO_USER="admin"
MONGO_PASS="secure_password_here"
MONGO_DB="app_flexible"
REDIS_AUTH="redis_password_here"

# Create log directory
mkdir -p "$(dirname "$LOG_FILE")"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Error handling
handle_error() {
    log "ERROR: Restore failed at line $1"
    exit 1
}

trap 'handle_error $LINENO' ERR

# Usage function
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  -d, --date DATE     Restore from specific date (YYYYMMDD_HHMMSS format)"
    echo "  -p, --postgres      Restore only PostgreSQL"
    echo "  -m, --mongodb       Restore only MongoDB"
    echo "  -r, --redis         Restore only Redis"
    echo "  -l, --list          List available backups"
    echo "  -h, --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --date 20231201_143000"
    echo "  $0 --postgres --date 20231201_143000"
    echo "  $0 --list"
    exit 1
}

# List available backups
list_backups() {
    log "📋 Available backups:"
    echo ""
    echo "PostgreSQL backups:"
    find "$BACKUP_DIR/postgresql" -name "*.sql.gz" -o -name "*.dump" | sort -r | head -10
    echo ""
    echo "MongoDB backups:"
    find "$BACKUP_DIR/mongodb" -name "*.tar.gz" | sort -r | head -10
    echo ""
    echo "Redis backups:"
    find "$BACKUP_DIR/redis" -name "*.rdb.gz" | sort -r | head -10
    exit 0
}

# Restore PostgreSQL
restore_postgres() {
    local backup_date=$1
    log "📊 Starting PostgreSQL restore from $backup_date..."
    
    local sql_backup="$BACKUP_DIR/postgresql/postgresql_backup_${backup_date}.sql.gz"
    local custom_backup="$BACKUP_DIR/postgresql/postgresql_backup_${backup_date}.dump"
    
    if [ -f "$custom_backup" ]; then
        log "Using custom format backup: $custom_backup"
        # Stop connections and drop/recreate database
        docker exec app_postgres psql -U "$POSTGRES_USER" -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$POSTGRES_DB';"
        docker exec app_postgres psql -U "$POSTGRES_USER" -d postgres -c "DROP DATABASE IF EXISTS $POSTGRES_DB;"
        docker exec app_postgres psql -U "$POSTGRES_USER" -d postgres -c "CREATE DATABASE $POSTGRES_DB;"
        
        # Copy backup to container and restore
        docker cp "$custom_backup" app_postgres:/tmp/restore.dump
        docker exec app_postgres pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v /tmp/restore.dump
        docker exec app_postgres rm -f /tmp/restore.dump
        
    elif [ -f "$sql_backup" ]; then
        log "Using SQL backup: $sql_backup"
        # Decompress and restore
        gunzip -c "$sql_backup" | docker exec -i app_postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
    else
        log "❌ PostgreSQL backup not found for date: $backup_date"
        return 1
    fi
    
    log "✅ PostgreSQL restore completed"
}

# Restore MongoDB
restore_mongodb() {
    local backup_date=$1
    log "📄 Starting MongoDB restore from $backup_date..."
    
    local backup_file="$BACKUP_DIR/mongodb/mongodb_backup_${backup_date}.tar.gz"
    
    if [ ! -f "$backup_file" ]; then
        log "❌ MongoDB backup not found for date: $backup_date"
        return 1
    fi
    
    # Extract backup
    local temp_dir="/tmp/mongodb_restore_$$"
    mkdir -p "$temp_dir"
    tar -xzf "$backup_file" -C "$temp_dir"
    
    # Copy to container
    docker cp "$temp_dir/." app_mongodb:/tmp/mongodb_restore/
    
    # Drop existing database and restore
    docker exec app_mongodb mongosh --username "$MONGO_USER" --password "$MONGO_PASS" --authenticationDatabase admin --eval "db.getSiblingDB('$MONGO_DB').dropDatabase()"
    
    # Restore from dump
    docker exec app_mongodb mongorestore \
        --username "$MONGO_USER" \
        --password "$MONGO_PASS" \
        --authenticationDatabase admin \
        --db "$MONGO_DB" \
        /tmp/mongodb_restore/"$MONGO_DB"
    
    # Cleanup
    rm -rf "$temp_dir"
    docker exec app_mongodb rm -rf /tmp/mongodb_restore
    
    log "✅ MongoDB restore completed"
}

# Restore Redis
restore_redis() {
    local backup_date=$1
    log "💾 Starting Redis restore from $backup_date..."
    
    local backup_file="$BACKUP_DIR/redis/redis_backup_${backup_date}.rdb.gz"
    
    if [ ! -f "$backup_file" ]; then
        log "❌ Redis backup not found for date: $backup_date"
        return 1
    fi
    
    # Stop Redis temporarily
    docker exec app_redis redis-cli -a "$REDIS_AUTH" --no-auth-warning FLUSHALL
    docker stop app_redis
    
    # Decompress and copy backup
    gunzip -c "$backup_file" > /tmp/dump.rdb
    docker cp /tmp/dump.rdb app_redis:/data/dump.rdb
    rm -f /tmp/dump.rdb
    
    # Start Redis
    docker start app_redis
    
    # Wait for Redis to be ready
    until docker exec app_redis redis-cli -a "$REDIS_AUTH" --no-auth-warning ping | grep -q PONG; do
        sleep 1
    done
    
    log "✅ Redis restore completed"
}

# Main script
main() {
    local restore_date=""
    local postgres_only=false
    local mongodb_only=false
    local redis_only=false
    local restore_all=true
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -d|--date)
                restore_date="$2"
                shift 2
                ;;
            -p|--postgres)
                postgres_only=true
                restore_all=false
                shift
                ;;
            -m|--mongodb)
                mongodb_only=true
                restore_all=false
                shift
                ;;
            -r|--redis)
                redis_only=true
                restore_all=false
                shift
                ;;
            -l|--list)
                list_backups
                ;;
            -h|--help)
                usage
                ;;
            *)
                echo "Unknown option: $1"
                usage
                ;;
        esac
    done
    
    if [ -z "$restore_date" ]; then
        echo "Error: Please specify a backup date with -d/--date"
        echo "Use -l/--list to see available backups"
        usage
    fi
    
    log "🚀 Starting database restore process for date: $restore_date"
    
    # Create confirmation prompt
    echo "⚠️  WARNING: This will overwrite existing data!"
    echo "Are you sure you want to restore from backup $restore_date? (yes/no)"
    read -r confirmation
    
    if [ "$confirmation" != "yes" ]; then
        log "Restore cancelled by user"
        exit 0
    fi
    
    # Perform restores
    if [ "$restore_all" = true ] || [ "$postgres_only" = true ]; then
        restore_postgres "$restore_date"
    fi
    
    if [ "$restore_all" = true ] || [ "$mongodb_only" = true ]; then
        restore_mongodb "$restore_date"
    fi
    
    if [ "$restore_all" = true ] || [ "$redis_only" = true ]; then
        restore_redis "$restore_date"
    fi
    
    log "🎉 Database restore process completed successfully!"
}

# Run main function with all arguments
main "$@"
