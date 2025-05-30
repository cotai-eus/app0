#!/bin/bash

# =====================================================
# 🔍 SCRIPT DE VALIDAÇÃO FINAL DA ARQUITETURA
# Valida configuração completa e funcionalidades
# =====================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

VALIDATION_LOG="validation_$(date +%Y%m%d_%H%M%S).log"

print_header() {
    echo -e "${BLUE}"
    echo "========================================================="
    echo "🔍 VALIDAÇÃO FINAL - ARQUITETURA MULTI-DATABASE"
    echo "========================================================="
    echo -e "${NC}"
}

print_section() {
    echo -e "${CYAN}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: $1" >> "$VALIDATION_LOG"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1" >> "$VALIDATION_LOG"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >> "$VALIDATION_LOG"
}

validate_file_structure() {
    print_section "Validating file structure..."
    
    local required_files=(
        "docker-compose.yml"
        "manage_databases.sh"
        "manage_databases.ps1"
        "README.md"
        "db/README.md"
        "frontend/README.md"
        "db/postgres-config/postgresql.conf"
        "db/mongo-config/mongod.conf"
        "db/redis-config/redis.conf"
        "db/prometheus-config/prometheus.yml"
        "frontend/nginx-config/nginx.conf"
        "frontend/scripts/init_databases.sh"
        "frontend/scripts/backup_databases.sh"
        "frontend/scripts/validate_databases.sh"
        "frontend/scripts/validate_databases.ps1"
    )
    
    local missing_files=()
    
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            print_success "Found: $file"
        else
            print_error "Missing: $file"
            missing_files+=("$file")
        fi
    done
    
    if [ ${#missing_files[@]} -eq 0 ]; then
        print_success "All required files present"
        return 0
    else
        print_error "Missing ${#missing_files[@]} required files"
        return 1
    fi
}

validate_directories() {
    print_section "Validating directory structure..."
    
    local required_dirs=(
        "db/data"
        "db/data/postgres"
        "db/data/mongodb"
        "db/data/redis"
        "db/data/grafana"
        "db/data/prometheus"
        "frontend/scripts"
        "frontend/nginx-config"
        "frontend/ssl-certs"
        "backend/logs"
        "frontend/backups"
    )
    
    for dir in "${required_dirs[@]}"; do
        if [ -d "$dir" ]; then
            print_success "Directory exists: $dir"
        else
            print_warning "Creating directory: $dir"
            mkdir -p "$dir"
            print_success "Created: $dir"
        fi
    done
}

validate_scripts_executable() {
    print_section "Validating script permissions..."
    
    local scripts=(
        "manage_databases.sh"
        "frontend/scripts/init_databases.sh"
        "frontend/scripts/backup_databases.sh"
        "frontend/scripts/restore_databases.sh"
        "frontend/scripts/validate_databases.sh"
    )
    
    for script in "${scripts[@]}"; do
        if [ -f "$script" ]; then
            if [ -x "$script" ]; then
                print_success "Executable: $script"
            else
                print_warning "Making executable: $script"
                chmod +x "$script"
                print_success "Fixed permissions: $script"
            fi
        else
            print_error "Script not found: $script"
        fi
    done
}

validate_docker_compose() {
    print_section "Validating Docker Compose configuration..."
    
    if command -v docker-compose &> /dev/null; then
        if docker-compose config &> /dev/null; then
            print_success "Docker Compose configuration is valid"
        else
            print_error "Docker Compose configuration has errors"
            docker-compose config
            return 1
        fi
    else
        print_error "Docker Compose not installed"
        return 1
    fi
}

validate_config_files() {
    print_section "Validating configuration files..."
    
    # PostgreSQL config
    if [ -f "db/postgres-config/postgresql.conf" ]; then
        if grep -q "listen_addresses" "db/postgres-config/postgresql.conf"; then
            print_success "PostgreSQL config contains required settings"
        else
            print_warning "PostgreSQL config may be incomplete"
        fi
    fi
    
    # MongoDB config
    if [ -f "db/mongo-config/mongod.conf" ]; then
        if grep -q "authorization" "db/mongo-config/mongod.conf"; then
            print_success "MongoDB config contains security settings"
        else
            print_warning "MongoDB config may be incomplete"
        fi
    fi
    
    # Redis config
    if [ -f "db/redis-config/redis.conf" ]; then
        if grep -q "requirepass" "db/redis-config/redis.conf"; then
            print_success "Redis config contains security settings"
        else
            print_warning "Redis config may be incomplete"
        fi
    fi
    
    # Prometheus config
    if [ -f "db/prometheus-config/prometheus.yml" ]; then
        if grep -q "scrape_configs" "db/prometheus-config/prometheus.yml"; then
            print_success "Prometheus config contains scrape targets"
        else
            print_warning "Prometheus config may be incomplete"
        fi
    fi
}

validate_services_running() {
    print_section "Validating running services..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker not installed"
        return 1
    fi
    
    local services=("app_postgres" "app_mongodb" "app_redis" "app_grafana" "app_prometheus")
    local running_services=0
    
    for service in "${services[@]}"; do
        if docker ps --format "table {{.Names}}" | grep -q "$service"; then
            local status=$(docker inspect --format='{{.State.Health.Status}}' "$service" 2>/dev/null || echo "no-health-check")
            case $status in
                "healthy")
                    print_success "$service is running and healthy"
                    ((running_services++))
                    ;;
                "unhealthy")
                    print_warning "$service is running but unhealthy"
                    ;;
                "starting")
                    print_warning "$service is starting up"
                    ;;
                "no-health-check")
                    print_warning "$service is running (no health check)"
                    ((running_services++))
                    ;;
                *)
                    print_warning "$service status: $status"
                    ;;
            esac
        else
            print_warning "$service is not running"
        fi
    done
    
    if [ $running_services -gt 0 ]; then
        print_success "$running_services services are running"
    else
        print_warning "No services are currently running. Run './manage_databases.sh start' to start services."
    fi
}

validate_connectivity() {
    print_section "Validating service connectivity..."
    
    # PostgreSQL
    if command -v psql &> /dev/null; then
        if PGPASSWORD=secure_password_here psql -h localhost -p 5432 -U app_user -d app_relational -c "SELECT 1;" &> /dev/null; then
            print_success "PostgreSQL connection successful"
        else
            print_warning "PostgreSQL connection failed (service may not be running)"
        fi
    else
        print_warning "psql not available for PostgreSQL testing"
    fi
    
    # MongoDB
    if command -v mongosh &> /dev/null; then
        if mongosh "mongodb://admin:secure_password_here@localhost:27017/app_flexible" --eval "db.runCommand('ping')" &> /dev/null; then
            print_success "MongoDB connection successful"
        else
            print_warning "MongoDB connection failed (service may not be running)"
        fi
    elif command -v mongo &> /dev/null; then
        if mongo "mongodb://admin:secure_password_here@localhost:27017/app_flexible" --eval "db.runCommand('ping')" &> /dev/null; then
            print_success "MongoDB connection successful"
        else
            print_warning "MongoDB connection failed (service may not be running)"
        fi
    else
        print_warning "mongo/mongosh not available for MongoDB testing"
    fi
    
    # Redis
    if command -v redis-cli &> /dev/null; then
        if redis-cli -h localhost -p 6379 -a redis_password_here ping &> /dev/null; then
            print_success "Redis connection successful"
        else
            print_warning "Redis connection failed (service may not be running)"
        fi
    else
        print_warning "redis-cli not available for Redis testing"
    fi
}

validate_web_interfaces() {
    print_section "Validating web interfaces..."
    
    local interfaces=(
        "8080:Adminer (PostgreSQL)"
        "8081:Mongo Express (MongoDB)"
        "8082:Redis Commander"
        "3000:Grafana"
        "9090:Prometheus"
    )
    
    for interface in "${interfaces[@]}"; do
        local port=$(echo "$interface" | cut -d: -f1)
        local name=$(echo "$interface" | cut -d: -f2)
        
        if curl -s --connect-timeout 5 "http://localhost:$port" &> /dev/null; then
            print_success "$name is accessible on port $port"
        else
            print_warning "$name is not accessible on port $port (service may not be running)"
        fi
    done
}

generate_summary_report() {
    print_section "Generating validation summary..."
    
    echo
    echo "========================================"
    echo "📊 VALIDATION SUMMARY REPORT"
    echo "========================================"
    echo "Date: $(date)"
    echo "Log file: $VALIDATION_LOG"
    echo
    
    local total_checks=$(grep -c "\[" "$VALIDATION_LOG" || echo "0")
    local success_checks=$(grep -c "SUCCESS" "$VALIDATION_LOG" || echo "0")
    local warning_checks=$(grep -c "WARNING" "$VALIDATION_LOG" || echo "0")
    local error_checks=$(grep -c "ERROR" "$VALIDATION_LOG" || echo "0")
    
    echo "Total checks: $total_checks"
    echo "✅ Successful: $success_checks"
    echo "⚠️  Warnings: $warning_checks"
    echo "❌ Errors: $error_checks"
    echo
    
    if [ "$error_checks" -eq 0 ]; then
        if [ "$warning_checks" -eq 0 ]; then
            print_success "🎉 ALL VALIDATIONS PASSED! Architecture is ready for use."
        else
            print_warning "⚠️  Validation completed with warnings. Check the issues above."
        fi
    else
        print_error "❌ Validation failed with errors. Please fix the issues above."
    fi
    
    echo
    echo "📋 Next steps:"
    echo "1. Start services: ./manage_databases.sh start"
    echo "2. Initialize data: ./manage_databases.sh init"
    echo "3. Check health: ./manage_databases.sh health"
    echo "4. Access interfaces: See README.md for URLs"
}

# Main execution
main() {
    print_header
    
    echo "Starting comprehensive validation..." > "$VALIDATION_LOG"
    
    validate_file_structure
    validate_directories
    validate_scripts_executable
    validate_docker_compose
    validate_config_files
    validate_services_running
    validate_connectivity
    validate_web_interfaces
    
    generate_summary_report
}

# Run if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
