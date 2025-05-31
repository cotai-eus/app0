#!/bin/bash

# =====================================================
# 🗄️ AUTOMATED DATABASE BACKUP SCRIPT
# PostgreSQL + MongoDB + Redis backup automation
# =====================================================

set -euo pipefail

# Configuration
BACKUP_DIR="/home/app/frontend/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7
LOG_FILE="/home/app/backend/logs/backup_${DATE}.log"

# Database credentials
POSTGRES_USER="app_user"
POSTGRES_DB="app_relational"
POSTGRES_HOST="localhost"
POSTGRES_PORT="5432"

MONGO_USER="admin"
MONGO_PASS="secure_password_here"
MONGO_HOST="localhost"
MONGO_PORT="27017"
MONGO_DB="app_flexible"

REDIS_HOST="localhost"
REDIS_PORT="6379"
REDIS_AUTH="redis_password_here"

# Create directories
mkdir -p "$BACKUP_DIR"/{postgresql,mongodb,redis}
mkdir -p "$(dirname "$LOG_FILE")"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Error handling
handle_error() {
    log "ERROR: Backup failed at line $1"
    exit 1
}

trap 'handle_error $LINENO' ERR

log "🚀 Starting database backup process..."

# =================== POSTGRESQL BACKUP ===================
log "📊 Starting PostgreSQL backup..."

POSTGRES_BACKUP_FILE="$BACKUP_DIR/postgresql/postgresql_backup_${DATE}.sql"
POSTGRES_CUSTOM_BACKUP="$BACKUP_DIR/postgresql/postgresql_backup_${DATE}.dump"

# SQL dump
docker exec app_postgres pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" > "$POSTGRES_BACKUP_FILE"

# Custom format dump (compressed)
docker exec app_postgres pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f "/tmp/backup.dump"
docker cp app_postgres:/tmp/backup.dump "$POSTGRES_CUSTOM_BACKUP"
docker exec app_postgres rm -f /tmp/backup.dump

# Compress SQL dump
gzip "$POSTGRES_BACKUP_FILE"

# Get backup size
POSTGRES_SIZE=$(du -sh "$POSTGRES_CUSTOM_BACKUP" | cut -f1)
log "✅ PostgreSQL backup completed: $POSTGRES_SIZE"

# =================== MONGODB BACKUP ===================
log "📄 Starting MongoDB backup..."

MONGODB_BACKUP_DIR="$BACKUP_DIR/mongodb/mongodb_backup_${DATE}"
mkdir -p "$MONGODB_BACKUP_DIR"

# Create mongodump
docker exec app_mongodb mongodump \
    --username "$MONGO_USER" \
    --password "$MONGO_PASS" \
    --authenticationDatabase admin \
    --db "$MONGO_DB" \
    --out /tmp/mongodb_backup

# Copy backup from container
docker cp app_mongodb:/tmp/mongodb_backup/. "$MONGODB_BACKUP_DIR"
docker exec app_mongodb rm -rf /tmp/mongodb_backup

# Compress MongoDB backup
tar -czf "${MONGODB_BACKUP_DIR}.tar.gz" -C "$(dirname "$MONGODB_BACKUP_DIR")" "$(basename "$MONGODB_BACKUP_DIR")"
rm -rf "$MONGODB_BACKUP_DIR"

# Get backup size
MONGODB_SIZE=$(du -sh "${MONGODB_BACKUP_DIR}.tar.gz" | cut -f1)
log "✅ MongoDB backup completed: $MONGODB_SIZE"

# =================== REDIS BACKUP ===================
log "💾 Starting Redis backup..."

REDIS_BACKUP_FILE="$BACKUP_DIR/redis/redis_backup_${DATE}.rdb"

# Create Redis backup using BGSAVE
docker exec app_redis redis-cli -a "$REDIS_AUTH" --no-auth-warning BGSAVE

# Wait for background save to complete
while [ "$(docker exec app_redis redis-cli -a "$REDIS_AUTH" --no-auth-warning LASTSAVE)" == "$(docker exec app_redis redis-cli -a "$REDIS_AUTH" --no-auth-warning LASTSAVE)" ]; do
    sleep 1
done

# Copy RDB file
docker cp app_redis:/data/dump.rdb "$REDIS_BACKUP_FILE"

# Compress Redis backup
gzip "$REDIS_BACKUP_FILE"

# Get backup size
REDIS_SIZE=$(du -sh "${REDIS_BACKUP_FILE}.gz" | cut -f1)
log "✅ Redis backup completed: $REDIS_SIZE"

# =================== CLEANUP OLD BACKUPS ===================
log "🧹 Cleaning up old backups (older than $RETENTION_DAYS days)..."

find "$BACKUP_DIR" -type f -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -type f -name "*.dump" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -type f -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -type f -name "*.rdb.gz" -mtime +$RETENTION_DAYS -delete

# =================== BACKUP VERIFICATION ===================
log "🔍 Verifying backups..."

# Verify PostgreSQL backup
if [ -f "${POSTGRES_BACKUP_FILE}.gz" ] && [ -f "$POSTGRES_CUSTOM_BACKUP" ]; then
    log "✅ PostgreSQL backup files verified"
else
    log "❌ PostgreSQL backup verification failed"
    exit 1
fi

# Verify MongoDB backup
if [ -f "${MONGODB_BACKUP_DIR}.tar.gz" ]; then
    log "✅ MongoDB backup file verified"
else
    log "❌ MongoDB backup verification failed"
    exit 1
fi

# Verify Redis backup
if [ -f "${REDIS_BACKUP_FILE}.gz" ]; then
    log "✅ Redis backup file verified"
else
    log "❌ Redis backup verification failed"
    exit 1
fi

# =================== SUMMARY ===================
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
log "🎉 Backup process completed successfully!"
log "📊 Backup summary:"
log "   - PostgreSQL: $POSTGRES_SIZE"
log "   - MongoDB: $MONGODB_SIZE"
log "   - Redis: $REDIS_SIZE"
log "   - Total backup size: $TOTAL_SIZE"
log "   - Backup location: $BACKUP_DIR"

# =================== OPTIONAL: UPLOAD TO CLOUD ===================
# Uncomment and configure if you want to upload backups to cloud storage
# log "☁️ Uploading backups to cloud storage..."
# 
# # Example for AWS S3
# # aws s3 cp "$BACKUP_DIR" s3://your-backup-bucket/database-backups/$(date +%Y/%m/%d)/ --recursive
# 
# # Example for Google Cloud Storage
# # gsutil -m cp -r "$BACKUP_DIR" gs://your-backup-bucket/database-backups/$(date +%Y/%m/%d)/
# 
# # Example for Azure Blob Storage
# # az storage blob upload-batch --destination backup-container --source "$BACKUP_DIR" --destination-path "database-backups/$(date +%Y/%m/%d)"

log "✨ All backup operations completed successfully at $(date)"
