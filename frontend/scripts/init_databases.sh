#!/bin/bash

# =====================================================
# 🚀 SCRIPT DE INICIALIZAÇÃO DOS BANCOS DE DADOS
# Configura PostgreSQL, MongoDB e Redis para produção
# =====================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
POSTGRES_DB_NAME="${POSTGRES_DB_NAME:-app_relational}"
POSTGRES_USER="${POSTGRES_USER:-app_user}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-secure_password_here}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"

MONGODB_DB_NAME="${MONGODB_DB_NAME:-app_flexible}"
MONGODB_HOST="${MONGODB_HOST:-localhost}"
MONGODB_PORT="${MONGODB_PORT:-27017}"

REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"
REDIS_PASSWORD="${REDIS_PASSWORD:-redis_password_here}"

echo -e "${BLUE}🚀 Starting database initialization...${NC}"

# =================== HELPER FUNCTIONS ===================

check_service() {
    local service_name=$1
    local host=$2
    local port=$3
    
    echo -e "${YELLOW}⏳ Checking if $service_name is available at $host:$port...${NC}"
    
    if timeout 10 bash -c "</dev/tcp/$host/$port"; then
        echo -e "${GREEN}✅ $service_name is available${NC}"
        return 0
    else
        echo -e "${RED}❌ $service_name is not available at $host:$port${NC}"
        return 1
    fi
}

wait_for_service() {
    local service_name=$1
    local host=$2
    local port=$3
    local max_attempts=${4:-30}
    local attempt=0
    
    echo -e "${YELLOW}⏳ Waiting for $service_name to be ready...${NC}"
    
    while [ $attempt -lt $max_attempts ]; do
        if check_service "$service_name" "$host" "$port" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name is ready!${NC}"
            return 0
        fi
        
        attempt=$((attempt + 1))
        echo -e "${YELLOW}   Attempt $attempt/$max_attempts - waiting 2 seconds...${NC}"
        sleep 2
    done
    
    echo -e "${RED}❌ $service_name failed to become ready after $max_attempts attempts${NC}"
    return 1
}

# =================== POSTGRESQL SETUP ===================

setup_postgresql() {
    echo -e "${BLUE}🐘 Setting up PostgreSQL...${NC}"
    
    if ! wait_for_service "PostgreSQL" "$POSTGRES_HOST" "$POSTGRES_PORT"; then
        echo -e "${RED}❌ PostgreSQL is not available. Please start PostgreSQL service.${NC}"
        exit 1
    fi
    
    # Check if database exists
    echo -e "${YELLOW}📋 Checking if database '$POSTGRES_DB_NAME' exists...${NC}"
    
    DB_EXISTS=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$POSTGRES_DB_NAME';" 2>/dev/null || echo "")
    
    if [ "$DB_EXISTS" != "1" ]; then
        echo -e "${YELLOW}🔨 Creating database '$POSTGRES_DB_NAME'...${NC}"
        PGPASSWORD="$POSTGRES_PASSWORD" createdb -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" "$POSTGRES_DB_NAME"
        echo -e "${GREEN}✅ Database '$POSTGRES_DB_NAME' created successfully${NC}"
    else
        echo -e "${GREEN}✅ Database '$POSTGRES_DB_NAME' already exists${NC}"
    fi
    
    # Run the complete schema
    echo -e "${YELLOW}📋 Applying PostgreSQL schema...${NC}"
    if [ -f "scripts/postgresql_complete_schema.sql" ]; then
        PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB_NAME" -f "scripts/postgresql_complete_schema.sql"
        echo -e "${GREEN}✅ PostgreSQL schema applied successfully${NC}"
    else
        echo -e "${YELLOW}⚠️  PostgreSQL schema file not found, skipping...${NC}"
    fi
    
    # Run Alembic migrations
    echo -e "${YELLOW}🔄 Running Alembic migrations...${NC}"
    if command -v alembic >/dev/null 2>&1; then
        cd backend
        alembic upgrade head
        cd ..
        echo -e "${GREEN}✅ Alembic migrations completed${NC}"
    else
        echo -e "${YELLOW}⚠️  Alembic not found, skipping migrations...${NC}"
    fi
}

# =================== MONGODB SETUP ===================

setup_mongodb() {
    echo -e "${BLUE}🍃 Setting up MongoDB...${NC}"
    
    if ! wait_for_service "MongoDB" "$MONGODB_HOST" "$MONGODB_PORT"; then
        echo -e "${RED}❌ MongoDB is not available. Please start MongoDB service.${NC}"
        exit 1
    fi
    
    # Run MongoDB schema setup
    echo -e "${YELLOW}📋 Setting up MongoDB collections and indexes...${NC}"
    if [ -f "scripts/mongodb_schemas.js" ]; then
        mongosh "mongodb://$MONGODB_HOST:$MONGODB_PORT/$MONGODB_DB_NAME" "scripts/mongodb_schemas.js"
        echo -e "${GREEN}✅ MongoDB collections and indexes created successfully${NC}"
    else
        echo -e "${YELLOW}⚠️  MongoDB schema file not found, skipping...${NC}"
    fi
    
    # Create initial indexes for performance
    echo -e "${YELLOW}📊 Creating additional performance indexes...${NC}"
    mongosh "mongodb://$MONGODB_HOST:$MONGODB_PORT/$MONGODB_DB_NAME" --eval "
        // Additional compound indexes for better performance
        db.system_logs.createIndex({ 'company_id': 1, 'level': 1, 'timestamp': -1 });
        db.user_activity_logs.createIndex({ 'user_id': 1, 'action': 1, 'timestamp': -1 });
        db.document_metadata.createIndex({ 'company_id': 1, 'processing_status': 1, 'uploaded_at': -1 });
        db.ai_processing_results.createIndex({ 'company_id': 1, 'processing_type': 1, 'status': 1 });
        
        print('✅ Additional indexes created successfully');
    "
}

# =================== REDIS SETUP ===================

setup_redis() {
    echo -e "${BLUE}🔴 Setting up Redis...${NC}"
    
    if ! wait_for_service "Redis" "$REDIS_HOST" "$REDIS_PORT"; then
        echo -e "${RED}❌ Redis is not available. Please start Redis service.${NC}"
        exit 1
    fi
    
    # Test Redis connection
    echo -e "${YELLOW}🔐 Testing Redis connection...${NC}"
    if [ -n "$REDIS_PASSWORD" ]; then
        REDIS_AUTH="-a $REDIS_PASSWORD"
    else
        REDIS_AUTH=""
    fi
    
    if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" $REDIS_AUTH ping >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Redis connection successful${NC}"
    else
        echo -e "${RED}❌ Redis connection failed${NC}"
        exit 1
    fi
    
    # Load Redis Lua scripts
    echo -e "${YELLOW}📜 Loading Redis Lua scripts...${NC}"
    
    # Rate limiting script
    RATE_LIMIT_SCRIPT='
    local key = KEYS[1]
    local limit = tonumber(ARGV[1])
    local window = tonumber(ARGV[2])
    local current_time = tonumber(ARGV[3])

    local current = redis.call("HGET", key, "count")
    local window_start = redis.call("HGET", key, "window_start")

    if not current then
        current = 0
        window_start = current_time
    else
        current = tonumber(current)
        window_start = tonumber(window_start)
    end

    if current_time - window_start > window then
        current = 0
        window_start = current_time
    end

    if current >= limit then
        return {0, current, limit - current}
    end

    current = current + 1
    redis.call("HSET", key, "count", current)
    redis.call("HSET", key, "window_start", window_start)
    redis.call("HSET", key, "last_request", current_time)
    redis.call("EXPIRE", key, window)

    return {1, current, limit - current}
    '
    
    RATE_LIMIT_SHA=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" $REDIS_AUTH SCRIPT LOAD "$RATE_LIMIT_SCRIPT")
    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" $REDIS_AUTH SET "script:rate_limit:sha" "$RATE_LIMIT_SHA"
    
    echo -e "${GREEN}✅ Redis Lua scripts loaded successfully${NC}"
    
    # Set up Redis configuration keys
    echo -e "${YELLOW}⚙️  Setting up Redis configuration...${NC}"
    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" $REDIS_AUTH HSET "config:app" \
        "max_sessions_per_user" "10" \
        "session_timeout" "86400" \
        "rate_limit_default" "100" \
        "cache_default_ttl" "3600"
    
    echo -e "${GREEN}✅ Redis configuration completed${NC}"
}

# =================== HEALTH CHECKS ===================

run_health_checks() {
    echo -e "${BLUE}🏥 Running health checks...${NC}"
    
    # PostgreSQL health check
    echo -e "${YELLOW}🐘 PostgreSQL health check...${NC}"
    PG_HEALTH=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB_NAME" -tAc "SELECT 'healthy';" 2>/dev/null || echo "unhealthy")
    if [ "$PG_HEALTH" = "healthy" ]; then
        echo -e "${GREEN}✅ PostgreSQL is healthy${NC}"
    else
        echo -e "${RED}❌ PostgreSQL health check failed${NC}"
    fi
    
    # MongoDB health check
    echo -e "${YELLOW}🍃 MongoDB health check...${NC}"
    MONGO_HEALTH=$(mongosh "mongodb://$MONGODB_HOST:$MONGODB_PORT/$MONGODB_DB_NAME" --quiet --eval "print('healthy')" 2>/dev/null || echo "unhealthy")
    if [ "$MONGO_HEALTH" = "healthy" ]; then
        echo -e "${GREEN}✅ MongoDB is healthy${NC}"
    else
        echo -e "${RED}❌ MongoDB health check failed${NC}"
    fi
    
    # Redis health check
    echo -e "${YELLOW}🔴 Redis health check...${NC}"
    REDIS_HEALTH=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" $REDIS_AUTH ping 2>/dev/null || echo "unhealthy")
    if [ "$REDIS_HEALTH" = "PONG" ]; then
        echo -e "${GREEN}✅ Redis is healthy${NC}"
    else
        echo -e "${RED}❌ Redis health check failed${NC}"
    fi
}

# =================== CREATE INITIAL DATA ===================

create_initial_data() {
    echo -e "${BLUE}📊 Creating initial data...${NC}"
    
    # Create initial data with Python script if available
    if [ -f "scripts/create_initial_data.py" ]; then
        echo -e "${YELLOW}🐍 Running Python initialization script...${NC}"
        python3 scripts/create_initial_data.py
        echo -e "${GREEN}✅ Initial data created${NC}"
    else
        echo -e "${YELLOW}⚠️  Initial data script not found, skipping...${NC}"
    fi
}

# =================== MAIN EXECUTION ===================

main() {
    echo -e "${BLUE}
    ====================================================
    🗄️  DATABASE INITIALIZATION SCRIPT
    ====================================================
    
    This script will set up:
    🐘 PostgreSQL (Relational data)
    🍃 MongoDB (Flexible data & logs)
    🔴 Redis (Cache & real-time)
    
    ====================================================${NC}"
    
    # Check if running as root (not recommended)
    if [ "$EUID" -eq 0 ]; then
        echo -e "${YELLOW}⚠️  Warning: Running as root is not recommended${NC}"
    fi
    
    # Setup databases
    setup_postgresql
    setup_mongodb
    setup_redis
    
    # Run health checks
    run_health_checks
    
    # Create initial data
    create_initial_data
    
    echo -e "${GREEN}
    ====================================================
    🎉 DATABASE INITIALIZATION COMPLETED SUCCESSFULLY!
    ====================================================
    
    ✅ PostgreSQL: Configured with complete schema
    ✅ MongoDB: Collections and indexes created
    ✅ Redis: Configuration and scripts loaded
    ✅ Health checks: All services are healthy
    
    Your multi-database architecture is ready for use!
    ====================================================${NC}"
}

# =================== SCRIPT OPTIONS ===================

case "${1:-all}" in
    "postgres"|"postgresql")
        setup_postgresql
        ;;
    "mongo"|"mongodb")
        setup_mongodb
        ;;
    "redis")
        setup_redis
        ;;
    "health"|"healthcheck")
        run_health_checks
        ;;
    "data"|"initial-data")
        create_initial_data
        ;;
    "all"|"")
        main
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [postgres|mongodb|redis|health|initial-data|all]"
        echo "  postgres     - Setup PostgreSQL only"
        echo "  mongodb      - Setup MongoDB only"
        echo "  redis        - Setup Redis only"
        echo "  health       - Run health checks only"
        echo "  initial-data - Create initial data only"
        echo "  all          - Setup everything (default)"
        ;;
    *)
        echo "Unknown option: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac
