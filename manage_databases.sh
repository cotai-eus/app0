#!/bin/bash

# =====================================================
# 🎛️  SCRIPT DE CONTROLE DA ARQUITETURA MULTI-DATABASE
# Gerenciamento completo: Deploy, Backup, Monitoring
# =====================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="multi-database-app"
COMPOSE_FILE="docker-compose.yml"
BACKUP_DIR="./db/backups"
LOG_DIR="./backend/logs"

# =================== HELPER FUNCTIONS ===================

print_banner() {
    echo -e "${BLUE}"
    echo "======================================================"
    echo "🗄️  MULTI-DATABASE ARCHITECTURE MANAGER"
    echo "======================================================"
    echo -e "${NC}"
}

print_section() {
    echo -e "${CYAN}🔹 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_dependencies() {
    print_section "Checking dependencies..."
    
    local deps=("docker" "docker-compose" "curl")
    local missing=()
    
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            missing+=("$dep")
        fi
    done
    
    if [ ${#missing[@]} -ne 0 ]; then
        print_error "Missing dependencies: ${missing[*]}"
        echo "Please install missing dependencies and try again."
        exit 1
    fi
    
    print_success "All dependencies are installed"
}

create_directories() {
    print_section "Creating required directories..."
    
    local dirs=(
        "db/data/postgres" "db/data/mongodb" "db/data/mongodb-config" "db/data/redis"
        "db/data/grafana" "db/data/prometheus" "$BACKUP_DIR" "$LOG_DIR"
        "db/postgres-config" "db/mongo-config" "db/redis-config" "frontend/nginx-config/conf.d"
        "db/grafana-config/provisioning" "db/prometheus-config" "frontend/ssl-certs"
    )
    
    for dir in "${dirs[@]}"; do
        mkdir -p "$dir"
    done
    
    print_success "Directories created"
}

# =================== MAIN FUNCTIONS ===================

cmd_start() {
    print_banner
    print_section "Starting Multi-Database Architecture..."
    
    check_dependencies
    create_directories
    
    # Start services
    docker-compose up -d
    
    print_section "Waiting for services to be ready..."
    sleep 30
    
    # Check health
    cmd_health
    
    print_success "Architecture started successfully!"
    print_section "Access URLs:"
    echo "🐘 Adminer (PostgreSQL):     http://localhost:8080"
    echo "🍃 Mongo Express (MongoDB):  http://localhost:8081"
    echo "🔴 Redis Commander (Redis):  http://localhost:8082"
    echo "📊 Grafana (Monitoring):     http://localhost:3000"
    echo "📈 Prometheus (Metrics):     http://localhost:9090"
}

cmd_stop() {
    print_section "Stopping Multi-Database Architecture..."
    docker-compose down
    print_success "Architecture stopped"
}

cmd_restart() {
    print_section "Restarting Multi-Database Architecture..."
    docker-compose restart
    sleep 15
    cmd_health
    print_success "Architecture restarted"
}

cmd_health() {
    print_section "Checking health of all services..."
    
    local services=("postgres" "mongodb" "redis" "adminer" "mongo-express" "redis-commander")
    local healthy=0
    local total=${#services[@]}
    
    for service in "${services[@]}"; do
        local status=$(docker-compose ps -q "$service" | xargs docker inspect --format='{{.State.Health.Status}}' 2>/dev/null || echo "unknown")
        
        case $status in
            "healthy")
                echo -e "  ${GREEN}✅ $service: healthy${NC}"
                ((healthy++))
                ;;
            "unhealthy")
                echo -e "  ${RED}❌ $service: unhealthy${NC}"
                ;;
            "starting")
                echo -e "  ${YELLOW}🔄 $service: starting${NC}"
                ;;
            *)
                echo -e "  ${YELLOW}❓ $service: unknown${NC}"
                ;;
        esac
    done
    
    echo
    if [ $healthy -eq $total ]; then
        print_success "All services are healthy ($healthy/$total)"
    else
        print_warning "Some services may need attention ($healthy/$total healthy)"
    fi
}

cmd_logs() {
    local service=${1:-""}
    
    if [ -n "$service" ]; then
        print_section "Showing logs for $service..."
        docker-compose logs -f "$service"
    else
        print_section "Showing logs for all services..."
        docker-compose logs -f
    fi
}

cmd_backup() {
    print_section "Creating backups..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_path="$BACKUP_DIR/$timestamp"
    mkdir -p "$backup_path"
    
    # PostgreSQL backup
    print_section "Backing up PostgreSQL..."
    docker-compose exec -T postgres pg_dump -U app_user app_relational > "$backup_path/postgres_backup.sql"
    gzip "$backup_path/postgres_backup.sql"
    
    # MongoDB backup
    print_section "Backing up MongoDB..."
    docker-compose exec -T mongodb mongodump --db app_flexible --archive > "$backup_path/mongodb_backup.archive"
    gzip "$backup_path/mongodb_backup.archive"
    
    # Redis backup
    print_section "Backing up Redis..."
    docker-compose exec -T redis redis-cli --rdb - > "$backup_path/redis_backup.rdb"
    gzip "$backup_path/redis_backup.rdb"
    
    # Create backup info file
    cat > "$backup_path/backup_info.txt" << EOF
Backup created: $(date)
PostgreSQL: postgres_backup.sql.gz
MongoDB: mongodb_backup.archive.gz
Redis: redis_backup.rdb.gz
EOF
    
    print_success "Backup completed: $backup_path"
}

cmd_restore() {
    local backup_path=${1:-""}
    
    if [ -z "$backup_path" ] || [ ! -d "$backup_path" ]; then
        print_error "Please provide a valid backup directory path"
        echo "Usage: $0 restore /path/to/backup/directory"
        exit 1
    fi
    
    print_section "Restoring from backup: $backup_path"
    print_warning "This will overwrite existing data. Continue? (y/N)"
    read -r confirm
    
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        print_warning "Restore cancelled"
        exit 0
    fi
    
    # PostgreSQL restore
    if [ -f "$backup_path/postgres_backup.sql.gz" ]; then
        print_section "Restoring PostgreSQL..."
        gunzip -c "$backup_path/postgres_backup.sql.gz" | docker-compose exec -T postgres psql -U app_user app_relational
    fi
    
    # MongoDB restore
    if [ -f "$backup_path/mongodb_backup.archive.gz" ]; then
        print_section "Restoring MongoDB..."
        gunzip -c "$backup_path/mongodb_backup.archive.gz" | docker-compose exec -T mongodb mongorestore --db app_flexible --archive
    fi
    
    # Redis restore (requires restart)
    if [ -f "$backup_path/redis_backup.rdb.gz" ]; then
        print_section "Restoring Redis..."
        docker-compose stop redis
        gunzip -c "$backup_path/redis_backup.rdb.gz" > "data/redis/dump.rdb"
        docker-compose start redis
    fi
    
    print_success "Restore completed"
}

cmd_init() {
    print_section "Initializing databases with sample data..."
    
    # Wait for services to be ready
    sleep 10
    
    # Run initialization script inside Python container
    docker-compose exec postgres python3 -c "
import asyncio
import sys
import os
sys.path.append('/scripts')
from create_initial_data import DatabaseInitializer

async def main():
    initializer = DatabaseInitializer()
    await initializer.run()

if __name__ == '__main__':
    asyncio.run(main())
"
    
    print_success "Database initialization completed"
}

cmd_clean() {
    print_section "Cleaning up resources..."
    print_warning "This will remove all containers, volumes, and data. Continue? (y/N)"
    read -r confirm
    
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        print_warning "Cleanup cancelled"
        exit 0
    fi
    
    docker-compose down -v --remove-orphans
    docker system prune -f
    
    print_success "Cleanup completed"
}

cmd_monitor() {
    print_section "Real-time monitoring..."
    
    while true; do
        clear
        print_banner
        cmd_health
        
        echo
        print_section "Resource Usage:"
        docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
        
        echo
        print_section "Disk Usage:"
        df -h | grep -E "(docker|data)"
        
        echo
        echo "Press Ctrl+C to exit monitoring..."
        sleep 5
    done
}

cmd_shell() {
    local service=${1:-"postgres"}
    
    case $service in
        "postgres"|"pg")
            print_section "Opening PostgreSQL shell..."
            docker-compose exec postgres psql -U app_user app_relational
            ;;
        "mongodb"|"mongo")
            print_section "Opening MongoDB shell..."
            docker-compose exec mongodb mongosh app_flexible
            ;;
        "redis")
            print_section "Opening Redis shell..."
            docker-compose exec redis redis-cli
            ;;
        *)
            print_error "Unknown service: $service"
            echo "Available services: postgres, mongodb, redis"
            exit 1
            ;;
    esac
}

cmd_update() {
    print_section "Updating Docker images..."
    docker-compose pull
    print_success "Images updated. Restart to apply changes."
}

cmd_status() {
    print_section "Service Status:"
    docker-compose ps
    
    echo
    print_section "System Information:"
    echo "Docker version: $(docker --version)"
    echo "Docker Compose version: $(docker-compose --version)"
    echo "Available disk space: $(df -h . | tail -1 | awk '{print $4}')"
    echo "Memory usage: $(free -h | grep Mem | awk '{print $3 "/" $2}')"
}

# =================== MAIN EXECUTION ===================

show_help() {
    print_banner
    echo "Usage: $0 <command> [options]"
    echo
    echo "Commands:"
    echo "  start           Start the entire architecture"
    echo "  stop            Stop all services"
    echo "  restart         Restart all services"
    echo "  health          Check health of all services"
    echo "  logs [service]  Show logs (all services or specific)"
    echo "  backup          Create backup of all databases"
    echo "  restore <path>  Restore from backup directory"
    echo "  init            Initialize databases with sample data"
    echo "  clean           Clean up all resources (destructive)"
    echo "  monitor         Real-time monitoring dashboard"
    echo "  shell <service> Open database shell (postgres/mongodb/redis)"
    echo "  update          Update Docker images"
    echo "  status          Show status and system information"
    echo "  help            Show this help message"
    echo
    echo "Examples:"
    echo "  $0 start                    # Start everything"
    echo "  $0 logs postgres            # Show PostgreSQL logs"
    echo "  $0 backup                   # Create backup"
    echo "  $0 restore ./backups/20231201_120000  # Restore from backup"
    echo "  $0 shell mongo              # Open MongoDB shell"
    echo
}

case "${1:-help}" in
    "start")
        cmd_start
        ;;
    "stop")
        cmd_stop
        ;;
    "restart")
        cmd_restart
        ;;
    "health")
        cmd_health
        ;;
    "logs")
        cmd_logs "$2"
        ;;
    "backup")
        cmd_backup
        ;;
    "restore")
        cmd_restore "$2"
        ;;
    "init")
        cmd_init
        ;;
    "clean")
        cmd_clean
        ;;
    "monitor")
        cmd_monitor
        ;;
    "shell")
        cmd_shell "$2"
        ;;
    "update")
        cmd_update
        ;;
    "status")
        cmd_status
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac
