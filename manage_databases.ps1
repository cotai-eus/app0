# =====================================================
# 🎛️  MULTI-DATABASE ARCHITECTURE MANAGER (PowerShell)
# Wrapper para gerenciamento em ambiente Windows/WSL
# =====================================================

param(
    [Parameter(Mandatory=$true, Position=0)]
    [ValidateSet("start", "stop", "restart", "health", "logs", "backup", "restore", "init", "clean", "monitor", "shell", "update", "status", "help")]
    [string]$Command,
    
    [Parameter(Position=1)]
    [string]$Parameter
)

# Colors for output
$Colors = @{
    Red = "Red"
    Green = "Green" 
    Yellow = "Yellow"
    Blue = "Blue"
    Cyan = "Cyan"
}

function Write-ColoredOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Colors[$Color]
}

function Test-WSLAvailable {
    try {
        $wslCheck = wsl --status 2>$null
        return $true
    }
    catch {
        return $false
    }
}

function Test-DockerAvailable {
    try {
        $dockerCheck = docker --version 2>$null
        return $true
    }
    catch {
        return $false
    }
}

function Show-Banner {
    Write-ColoredOutput "======================================================" "Blue"
    Write-ColoredOutput "🗄️  MULTI-DATABASE ARCHITECTURE MANAGER (PowerShell)" "Blue"
    Write-ColoredOutput "======================================================" "Blue"
}

function Show-Help {
    Show-Banner
    Write-Host ""
    Write-Host "Usage: .\manage_databases.ps1 <command> [options]"
    Write-Host ""
    Write-Host "Commands:"
    Write-ColoredOutput "  start           Start the entire architecture" "Green"
    Write-ColoredOutput "  stop            Stop all services" "Yellow"
    Write-ColoredOutput "  restart         Restart all services" "Yellow"
    Write-ColoredOutput "  health          Check health of all services" "Cyan"
    Write-ColoredOutput "  logs [service]  Show logs (all services or specific)" "Cyan"
    Write-ColoredOutput "  backup          Create backup of all databases" "Blue"
    Write-ColoredOutput "  restore <path>  Restore from backup directory" "Blue"
    Write-ColoredOutput "  init            Initialize databases with sample data" "Green"
    Write-ColoredOutput "  clean           Clean up all resources (destructive)" "Red"
    Write-ColoredOutput "  monitor         Real-time monitoring dashboard" "Cyan"
    Write-ColoredOutput "  shell <service> Open database shell (postgres/mongodb/redis)" "Cyan"
    Write-ColoredOutput "  update          Update Docker images" "Yellow"
    Write-ColoredOutput "  status          Show status and system information" "Cyan"
    Write-ColoredOutput "  help            Show this help message" "Blue"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\manage_databases.ps1 start                    # Start everything"
    Write-Host "  .\manage_databases.ps1 logs postgres            # Show PostgreSQL logs"
    Write-Host "  .\manage_databases.ps1 backup                   # Create backup"
    Write-Host "  .\manage_databases.ps1 shell mongo              # Open MongoDB shell"
    Write-Host ""
    Write-Host "Requirements:"
    Write-Host "  - Windows 10/11 with WSL2"
    Write-Host "  - Docker Desktop"
    Write-Host "  - Docker Compose"
    Write-Host ""
}

function Test-Prerequisites {
    Write-ColoredOutput "🔍 Checking prerequisites..." "Yellow"
    
    $allGood = $true
    
    # Check WSL
    if (Test-WSLAvailable) {
        Write-ColoredOutput "✅ WSL is available" "Green"
    } else {
        Write-ColoredOutput "❌ WSL is not available or not running" "Red"
        $allGood = $false
    }
    
    # Check Docker
    if (Test-DockerAvailable) {
        Write-ColoredOutput "✅ Docker is available" "Green"
    } else {
        Write-ColoredOutput "❌ Docker is not available or not running" "Red"
        Write-ColoredOutput "   Please start Docker Desktop" "Yellow"
        $allGood = $false
    }
    
    # Check if we're in the right directory
    if (Test-Path "docker-compose.yml") {
        Write-ColoredOutput "✅ Found docker-compose.yml" "Green"
    } else {
        Write-ColoredOutput "❌ docker-compose.yml not found" "Red"
        Write-ColoredOutput "   Please run this script from the app directory" "Yellow"
        $allGood = $false
    }
    
    if (-not $allGood) {
        Write-ColoredOutput "❌ Prerequisites not met. Please fix the issues above." "Red"
        exit 1
    }
}

function Invoke-WSLCommand {
    param([string]$Command)
    
    try {
        # Change to the correct directory in WSL and run the command
        $wslPath = "/mnt/c" + (Get-Location).Path.Replace("C:", "").Replace("\", "/")
        $fullCommand = "cd '$wslPath' && $Command"
        
        Write-ColoredOutput "🔧 Executing: $Command" "Yellow"
        wsl bash -c $fullCommand
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColoredOutput "✅ Command completed successfully" "Green"
        } else {
            Write-ColoredOutput "❌ Command failed with exit code $LASTEXITCODE" "Red"
        }
    }
    catch {
        Write-ColoredOutput "❌ Failed to execute command: $_" "Red"
    }
}

function Start-Services {
    Show-Banner
    Write-ColoredOutput "🚀 Starting Multi-Database Architecture..." "Green"
    
    Test-Prerequisites
    
    # Make scripts executable and start
    Invoke-WSLCommand "chmod +x manage_databases.sh frontend/scripts/*.sh"
    Invoke-WSLCommand "./manage_databases.sh start"
    
    Write-Host ""
    Write-ColoredOutput "🌐 Access URLs:" "Cyan"
    Write-Host "🐘 Adminer (PostgreSQL):     http://localhost:8080"
    Write-Host "🍃 Mongo Express (MongoDB):  http://localhost:8081" 
    Write-Host "🔴 Redis Commander (Redis):  http://localhost:8082"
    Write-Host "📊 Grafana (Monitoring):     http://localhost:3000"
    Write-Host "📈 Prometheus (Metrics):     http://localhost:9090"
}

function Stop-Services {
    Write-ColoredOutput "🛑 Stopping Multi-Database Architecture..." "Yellow"
    Invoke-WSLCommand "./manage_databases.sh stop"
}

function Restart-Services {
    Write-ColoredOutput "🔄 Restarting Multi-Database Architecture..." "Yellow"
    Invoke-WSLCommand "./manage_databases.sh restart"
}

function Get-Health {
    Write-ColoredOutput "🏥 Checking health of all services..." "Cyan"
    Invoke-WSLCommand "./manage_databases.sh health"
}

function Get-Logs {
    if ($Parameter) {
        Write-ColoredOutput "📋 Showing logs for $Parameter..." "Cyan"
        Invoke-WSLCommand "./manage_databases.sh logs $Parameter"
    } else {
        Write-ColoredOutput "📋 Showing logs for all services..." "Cyan"
        Invoke-WSLCommand "./manage_databases.sh logs"
    }
}

function New-Backup {
    Write-ColoredOutput "💾 Creating backup..." "Blue"
    Invoke-WSLCommand "./manage_databases.sh backup"
}

function Restore-Backup {
    if (-not $Parameter) {
        Write-ColoredOutput "❌ Please provide backup path" "Red"
        Write-Host "Usage: .\manage_databases.ps1 restore <backup_path>"
        exit 1
    }
    
    Write-ColoredOutput "🔄 Restoring from backup: $Parameter" "Blue"
    Invoke-WSLCommand "./manage_databases.sh restore '$Parameter'"
}

function Initialize-Databases {
    Write-ColoredOutput "🎯 Initializing databases with sample data..." "Green"
    Invoke-WSLCommand "./manage_databases.sh init"
}

function Clear-AllData {
    Write-ColoredOutput "🧹 This will remove all data. Are you sure? (y/N)" "Red"
    $confirm = Read-Host
    
    if ($confirm -eq "y" -or $confirm -eq "Y") {
        Write-ColoredOutput "🧹 Cleaning up all resources..." "Red"
        Invoke-WSLCommand "./manage_databases.sh clean"
    } else {
        Write-ColoredOutput "❌ Cleanup cancelled" "Yellow"
    }
}

function Start-Monitoring {
    Write-ColoredOutput "📊 Starting monitoring dashboard..." "Cyan"
    Invoke-WSLCommand "./manage_databases.sh monitor"
}

function Open-Shell {
    if (-not $Parameter) {
        Write-ColoredOutput "❌ Please specify service: postgres, mongodb, or redis" "Red"
        exit 1
    }
    
    Write-ColoredOutput "🐚 Opening shell for $Parameter..." "Cyan"
    Invoke-WSLCommand "./manage_databases.sh shell $Parameter"
}

function Update-Images {
    Write-ColoredOutput "📦 Updating Docker images..." "Yellow"
    Invoke-WSLCommand "./manage_databases.sh update"
}

function Get-Status {
    Write-ColoredOutput "📊 Getting system status..." "Cyan"
    Invoke-WSLCommand "./manage_databases.sh status"
}

# Main execution logic
switch ($Command) {
    "start" { Start-Services }
    "stop" { Stop-Services }
    "restart" { Restart-Services }
    "health" { Get-Health }
    "logs" { Get-Logs }
    "backup" { New-Backup }
    "restore" { Restore-Backup }
    "init" { Initialize-Databases }
    "clean" { Clear-AllData }
    "monitor" { Start-Monitoring }
    "shell" { Open-Shell }
    "update" { Update-Images }
    "status" { Get-Status }
    "help" { Show-Help }
    default { Show-Help }
}
