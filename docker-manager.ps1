# =====================================================
# 🐳 DOCKER MANAGEMENT SCRIPT - COTAI BACKEND
# Simplified deployment and management commands
# =====================================================

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("dev", "prod", "stop", "restart", "logs", "status", "clean", "backup", "restore", "update")]
    [string]$Action,
    
    [string]$Service = "",
    [switch]$Follow,
    [switch]$Build,
    [switch]$Force
)

# Configuration
$PROJECT_NAME = "cotai-backend"
$DEV_COMPOSE = "docker-compose.yml"
$PROD_COMPOSE = "docker-compose.prod.yml"

# Colors for output
function Write-ColorOutput {
    param([string]$ForegroundColor, [string]$Message)
    $currentColor = $Host.UI.RawUI.ForegroundColor
    $Host.UI.RawUI.ForegroundColor = $ForegroundColor
    Write-Output $Message
    $Host.UI.RawUI.ForegroundColor = $currentColor
}

function Show-Header {
    param([string]$Title)
    Write-ColorOutput "Cyan" ""
    Write-ColorOutput "Cyan" "=========================================="
    Write-ColorOutput "Cyan" "🐳 COTAI BACKEND - $Title"
    Write-ColorOutput "Cyan" "=========================================="
    Write-ColorOutput "Cyan" ""
}

function Show-Status {
    param([string]$Message, [string]$Status = "INFO")
    $color = switch ($Status) {
        "SUCCESS" { "Green" }
        "ERROR" { "Red" }
        "WARNING" { "Yellow" }
        default { "White" }
    }
    Write-ColorOutput $color "[$Status] $Message"
}

# Main functions
function Start-Development {
    Show-Header "STARTING DEVELOPMENT ENVIRONMENT"
    
    if ($Build) {
        Show-Status "Building development containers..." "INFO"
        docker-compose -f $DEV_COMPOSE -p $PROJECT_NAME build
    }
    
    Show-Status "Starting development services..." "INFO"
    docker-compose -f $DEV_COMPOSE -p $PROJECT_NAME up -d
    
    Show-Status "Development environment started successfully!" "SUCCESS"
    Show-Status "Services available at:" "INFO"
    Write-Output "  • Backend API: http://localhost:8000"
    Write-Output "  • LLM Service: http://localhost:8001"
    Write-Output "  • Grafana: http://localhost:3000 (admin/admin123)"
    Write-Output "  • Adminer: http://localhost:8080"
    Write-Output "  • Mongo Express: http://localhost:8081"
    Write-Output "  • Redis Commander: http://localhost:8082"
    Write-Output "  • Flower: http://localhost:5555"
}

function Start-Production {
    Show-Header "STARTING PRODUCTION ENVIRONMENT"
    
    # Check if production env file exists
    if (!(Test-Path ".env.production")) {
        Show-Status "Production environment file (.env.production) not found!" "ERROR"
        Show-Status "Please create .env.production with your production settings." "WARNING"
        return
    }
    
    if ($Build) {
        Show-Status "Building production containers..." "INFO"
        docker-compose -f $PROD_COMPOSE -p "${PROJECT_NAME}-prod" build
    }
    
    Show-Status "Starting production services..." "INFO"
    docker-compose -f $PROD_COMPOSE -p "${PROJECT_NAME}-prod" up -d
    
    Show-Status "Production environment started successfully!" "SUCCESS"
    Show-Status "Services available at:" "INFO"
    Write-Output "  • Application: https://localhost (via Nginx)"
    Write-Output "  • Monitoring: https://localhost/monitoring/"
    Write-Output "  • Metrics: https://localhost/metrics/ (internal only)"
}

function Stop-Services {
    param([string]$Environment = "both")
    
    Show-Header "STOPPING SERVICES"
    
    if ($Environment -eq "both" -or $Environment -eq "dev") {
        Show-Status "Stopping development environment..." "INFO"
        docker-compose -f $DEV_COMPOSE -p $PROJECT_NAME down
    }
    
    if ($Environment -eq "both" -or $Environment -eq "prod") {
        Show-Status "Stopping production environment..." "INFO"
        docker-compose -f $PROD_COMPOSE -p "${PROJECT_NAME}-prod" down
    }
    
    Show-Status "Services stopped successfully!" "SUCCESS"
}

function Restart-Services {
    Show-Header "RESTARTING SERVICES"
    
    if ($Service) {
        Show-Status "Restarting service: $Service" "INFO"
        docker-compose -f $DEV_COMPOSE -p $PROJECT_NAME restart $Service
    } else {
        Stop-Services "dev"
        Start-Development
    }
}

function Show-Logs {
    Show-Header "VIEWING LOGS"
    
    $composeFile = $DEV_COMPOSE
    $projectName = $PROJECT_NAME
    
    if ($Service) {
        Show-Status "Showing logs for service: $Service" "INFO"
        if ($Follow) {
            docker-compose -f $composeFile -p $projectName logs -f $Service
        } else {
            docker-compose -f $composeFile -p $projectName logs --tail=100 $Service
        }
    } else {
        Show-Status "Showing logs for all services" "INFO"
        if ($Follow) {
            docker-compose -f $composeFile -p $projectName logs -f
        } else {
            docker-compose -f $composeFile -p $projectName logs --tail=50
        }
    }
}

function Show-ServiceStatus {
    Show-Header "SERVICE STATUS"
    
    Show-Status "Development Environment:" "INFO"
    docker-compose -f $DEV_COMPOSE -p $PROJECT_NAME ps
    
    Write-Output ""
    Show-Status "Production Environment:" "INFO"
    docker-compose -f $PROD_COMPOSE -p "${PROJECT_NAME}-prod" ps
    
    Write-Output ""
    Show-Status "Container Resource Usage:" "INFO"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
}

function Clean-Environment {
    Show-Header "CLEANING ENVIRONMENT"
    
    if ($Force) {
        Show-Status "Force cleaning all containers, networks, and volumes..." "WARNING"
        docker-compose -f $DEV_COMPOSE -p $PROJECT_NAME down -v --remove-orphans
        docker-compose -f $PROD_COMPOSE -p "${PROJECT_NAME}-prod" down -v --remove-orphans
        docker system prune -f
        docker volume prune -f
    } else {
        Show-Status "Cleaning containers and networks (keeping volumes)..." "INFO"
        docker-compose -f $DEV_COMPOSE -p $PROJECT_NAME down --remove-orphans
        docker-compose -f $PROD_COMPOSE -p "${PROJECT_NAME}-prod" down --remove-orphans
    }
    
    Show-Status "Environment cleaned successfully!" "SUCCESS"
}

function Backup-Data {
    Show-Header "CREATING BACKUP"
    
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupDir = "backups/$timestamp"
    
    Show-Status "Creating backup directory: $backupDir" "INFO"
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    
    # Backup databases
    Show-Status "Backing up PostgreSQL..." "INFO"
    docker exec cotai_postgres pg_dump -U app_user app_relational > "$backupDir/postgres_backup.sql"
    
    Show-Status "Backing up MongoDB..." "INFO"
    docker exec cotai_mongodb mongodump --out /data/backup
    docker cp cotai_mongodb:/data/backup "$backupDir/mongodb_backup"
    
    # Backup volumes
    Show-Status "Backing up Docker volumes..." "INFO"
    docker run --rm -v cotai-backend_ollama_models:/data -v ${PWD}/${backupDir}:/backup alpine tar czf /backup/ollama_models.tar.gz -C /data .
    docker run --rm -v cotai-backend_llm_models:/data -v ${PWD}/${backupDir}:/backup alpine tar czf /backup/llm_models.tar.gz -C /data .
    
    Show-Status "Backup completed successfully: $backupDir" "SUCCESS"
}

function Restore-Data {
    param([string]$BackupPath)
    
    Show-Header "RESTORING FROM BACKUP"
    
    if (!(Test-Path $BackupPath)) {
        Show-Status "Backup path not found: $BackupPath" "ERROR"
        return
    }
    
    Show-Status "Restoring from: $BackupPath" "INFO"
    
    # Restore PostgreSQL
    if (Test-Path "$BackupPath/postgres_backup.sql") {
        Show-Status "Restoring PostgreSQL..." "INFO"
        Get-Content "$BackupPath/postgres_backup.sql" | docker exec -i cotai_postgres psql -U app_user -d app_relational
    }
    
    # Restore MongoDB
    if (Test-Path "$BackupPath/mongodb_backup") {
        Show-Status "Restoring MongoDB..." "INFO"
        docker cp "$BackupPath/mongodb_backup" cotai_mongodb:/data/restore
        docker exec cotai_mongodb mongorestore /data/restore
    }
    
    Show-Status "Restore completed successfully!" "SUCCESS"
}

function Update-Services {
    Show-Header "UPDATING SERVICES"
    
    Show-Status "Pulling latest images..." "INFO"
    docker-compose -f $DEV_COMPOSE pull
    docker-compose -f $PROD_COMPOSE pull
    
    Show-Status "Rebuilding containers..." "INFO"
    docker-compose -f $DEV_COMPOSE build --no-cache
    
    Show-Status "Update completed successfully!" "SUCCESS"
}

# Main execution
switch ($Action) {
    "dev" { Start-Development }
    "prod" { Start-Production }
    "stop" { Stop-Services }
    "restart" { Restart-Services }
    "logs" { Show-Logs }
    "status" { Show-ServiceStatus }
    "clean" { Clean-Environment }
    "backup" { Backup-Data }
    "restore" { 
        if ($Service) {
            Restore-Data $Service
        } else {
            Show-Status "Please specify backup path with -Service parameter" "ERROR"
        }
    }
    "update" { Update-Services }
    default { 
        Show-Status "Invalid action: $Action" "ERROR"
        Write-Output "Usage: .\docker-manager.ps1 -Action <dev|prod|stop|restart|logs|status|clean|backup|restore|update> [-Service <service_name>] [-Follow] [-Build] [-Force]"
    }
}
