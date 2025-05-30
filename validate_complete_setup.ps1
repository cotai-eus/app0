# =====================================================
# 🔍 SCRIPT DE VALIDAÇÃO FINAL - PowerShell
# Valida configuração completa da arquitetura
# =====================================================

param(
    [switch]$Detailed = $false
)

# Colors
$Colors = @{
    Red = "Red"
    Green = "Green"
    Yellow = "Yellow" 
    Blue = "Blue"
    Cyan = "Cyan"
}

$ValidationLog = "validation_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

function Write-ColoredOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Colors[$Color]
}

function Write-Log {
    param([string]$Level, [string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] $Level`: $Message"
    Add-Content -Path $ValidationLog -Value $logEntry
}

function Show-Header {
    Write-ColoredOutput "=========================================================" "Blue"
    Write-ColoredOutput "🔍 VALIDAÇÃO FINAL - ARQUITETURA MULTI-DATABASE" "Blue" 
    Write-ColoredOutput "=========================================================" "Blue"
}

function Show-Section {
    param([string]$Title)
    Write-ColoredOutput "📋 $Title" "Cyan"
}

function Write-Success {
    param([string]$Message)
    Write-ColoredOutput "✅ $Message" "Green"
    Write-Log "SUCCESS" $Message
}

function Write-Warning {
    param([string]$Message)
    Write-ColoredOutput "⚠️  $Message" "Yellow"
    Write-Log "WARNING" $Message
}

function Write-Error {
    param([string]$Message)
    Write-ColoredOutput "❌ $Message" "Red"
    Write-Log "ERROR" $Message
}

function Test-FileStructure {
    Show-Section "Validating file structure..."
    
    $requiredFiles = @(
        "docker-compose.yml",
        "manage_databases.sh",
        "manage_databases.ps1",
        "README.md",
        "db\README.md",
        "frontend\README.md",
        "db\postgres-config\postgresql.conf",
        "db\mongo-config\mongod.conf",
        "db\redis-config\redis.conf",
        "db\prometheus-config\prometheus.yml",
        "frontend\nginx-config\nginx.conf",
        "frontend\scripts\init_databases.sh",
        "frontend\scripts\backup_databases.sh",
        "frontend\scripts\validate_databases.sh",
        "frontend\scripts\validate_databases.ps1"
    )
    
    $missingFiles = @()
    
    foreach ($file in $requiredFiles) {
        if (Test-Path $file) {
            Write-Success "Found: $file"
        } else {
            Write-Error "Missing: $file"
            $missingFiles += $file
        }
    }
    
    if ($missingFiles.Count -eq 0) {
        Write-Success "All required files present"
        return $true
    } else {
        Write-Error "Missing $($missingFiles.Count) required files"
        return $false
    }
}

function Test-Directories {
    Show-Section "Validating directory structure..."
    
    $requiredDirs = @(
        "db\data",
        "db\data\postgres", 
        "db\data\mongodb",
        "db\data\redis",
        "db\data\grafana",
        "db\data\prometheus",
        "frontend\scripts",
        "frontend\nginx-config",
        "frontend\ssl-certs",
        "backend\logs",
        "frontend\backups"
    )
    
    foreach ($dir in $requiredDirs) {
        if (Test-Path $dir -PathType Container) {
            Write-Success "Directory exists: $dir"
        } else {
            Write-Warning "Creating directory: $dir"
            try {
                New-Item -ItemType Directory -Path $dir -Force | Out-Null
                Write-Success "Created: $dir"
            } catch {
                Write-Error "Failed to create: $dir - $_"
            }
        }
    }
}

function Test-Prerequisites {
    Show-Section "Validating prerequisites..."
    
    # Test Docker
    try {
        $dockerVersion = docker --version 2>$null
        if ($dockerVersion) {
            Write-Success "Docker is available: $dockerVersion"
        } else {
            Write-Error "Docker is not available"
            return $false
        }
    } catch {
        Write-Error "Docker is not available or not running"
        return $false
    }
    
    # Test Docker Compose
    try {
        $composeVersion = docker-compose --version 2>$null
        if ($composeVersion) {
            Write-Success "Docker Compose is available: $composeVersion"
        } else {
            Write-Error "Docker Compose is not available"
            return $false
        }
    } catch {
        Write-Error "Docker Compose is not available"
        return $false
    }
    
    # Test WSL (if we're in WSL context)
    try {
        $wslCheck = wsl --status 2>$null
        if ($wslCheck) {
            Write-Success "WSL is available and running"
        }
    } catch {
        Write-Warning "WSL not available (not required if running native Docker)"
    }
    
    return $true
}

function Test-DockerCompose {
    Show-Section "Validating Docker Compose configuration..."
    
    try {
        $configTest = docker-compose config 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Docker Compose configuration is valid"
            return $true
        } else {
            Write-Error "Docker Compose configuration has errors:"
            Write-Host $configTest -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Error "Failed to validate Docker Compose configuration: $_"
        return $false
    }
}

function Test-ConfigFiles {
    Show-Section "Validating configuration files..."
    
    $configs = @{
        "db\postgres-config\postgresql.conf" = "listen_addresses"
        "db\mongo-config\mongod.conf" = "authorization" 
        "db\redis-config\redis.conf" = "requirepass"
        "db\prometheus-config\prometheus.yml" = "scrape_configs"
    }
    
    foreach ($config in $configs.GetEnumerator()) {
        $file = $config.Key
        $requiredSetting = $config.Value
        
        if (Test-Path $file) {
            $content = Get-Content $file -Raw
            if ($content -match $requiredSetting) {
                Write-Success "$file contains required settings"
            } else {
                Write-Warning "$file may be incomplete (missing $requiredSetting)"
            }
        } else {
            Write-Error "Configuration file not found: $file"
        }
    }
}

function Test-RunningServices {
    Show-Section "Validating running services..."
    
    try {
        $containers = docker ps --format "table {{.Names}}" 2>$null
        if (-not $containers) {
            Write-Warning "No Docker containers are running. Start services with: .\manage_databases.ps1 start"
            return
        }
        
        $services = @("app_postgres", "app_mongodb", "app_redis", "app_grafana", "app_prometheus")
        $runningServices = 0
        
        foreach ($service in $services) {
            if ($containers -match $service) {
                try {
                    $health = docker inspect --format='{{.State.Health.Status}}' $service 2>$null
                    switch ($health) {
                        "healthy" {
                            Write-Success "$service is running and healthy"
                            $runningServices++
                        }
                        "unhealthy" {
                            Write-Warning "$service is running but unhealthy"
                        }
                        "starting" {
                            Write-Warning "$service is starting up"
                        }
                        default {
                            Write-Warning "$service is running (no health check or status: $health)"
                            $runningServices++
                        }
                    }
                } catch {
                    Write-Warning "$service status unknown"
                }
            } else {
                Write-Warning "$service is not running"
            }
        }
        
        if ($runningServices -gt 0) {
            Write-Success "$runningServices services are running"
        } else {
            Write-Warning "No services are currently running"
        }
    } catch {
        Write-Error "Failed to check running services: $_"
    }
}

function Test-WebInterfaces {
    Show-Section "Validating web interfaces..."
    
    $interfaces = @{
        8080 = "Adminer (PostgreSQL)"
        8081 = "Mongo Express (MongoDB)"
        8082 = "Redis Commander"
        3000 = "Grafana"
        9090 = "Prometheus"
    }
    
    foreach ($interface in $interfaces.GetEnumerator()) {
        $port = $interface.Key
        $name = $interface.Value
        
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:$port" -TimeoutSec 5 -UseBasicParsing 2>$null
            if ($response.StatusCode -eq 200) {
                Write-Success "$name is accessible on port $port"
            } else {
                Write-Warning "$name returned status $($response.StatusCode) on port $port"
            }
        } catch {
            Write-Warning "$name is not accessible on port $port (service may not be running)"
        }
    }
}

function Test-ScriptPermissions {
    Show-Section "Validating script accessibility..."
    
    $scripts = @(
        "manage_databases.sh",
        "manage_databases.ps1",
        "frontend\scripts\init_databases.sh",
        "frontend\scripts\backup_databases.sh",
        "frontend\scripts\validate_databases.sh",
        "frontend\scripts\validate_databases.ps1"
    )
    
    foreach ($script in $scripts) {
        if (Test-Path $script) {
            try {
                # Test if we can read the script
                $content = Get-Content $script -TotalCount 1 2>$null
                if ($content) {
                    Write-Success "Script is accessible: $script"
                } else {
                    Write-Warning "Script may have permission issues: $script"
                }
            } catch {
                Write-Warning "Cannot access script: $script - $_"
            }
        } else {
            Write-Error "Script not found: $script"
        }
    }
}

function Show-SummaryReport {
    Show-Section "Generating validation summary..."
    
    Write-Host ""
    Write-Host "========================================"
    Write-Host "📊 VALIDATION SUMMARY REPORT"
    Write-Host "========================================"
    Write-Host "Date: $(Get-Date)"
    Write-Host "Log file: $ValidationLog"
    Write-Host ""
    
    if (Test-Path $ValidationLog) {
        $logContent = Get-Content $ValidationLog
        $totalChecks = ($logContent | Measure-Object).Count
        $successChecks = ($logContent | Where-Object { $_ -match "SUCCESS" } | Measure-Object).Count
        $warningChecks = ($logContent | Where-Object { $_ -match "WARNING" } | Measure-Object).Count
        $errorChecks = ($logContent | Where-Object { $_ -match "ERROR" } | Measure-Object).Count
        
        Write-Host "Total checks: $totalChecks"
        Write-Host "✅ Successful: $successChecks"
        Write-Host "⚠️  Warnings: $warningChecks"
        Write-Host "❌ Errors: $errorChecks"
        Write-Host ""
        
        if ($errorChecks -eq 0) {
            if ($warningChecks -eq 0) {
                Write-Success "🎉 ALL VALIDATIONS PASSED! Architecture is ready for use."
            } else {
                Write-Warning "⚠️  Validation completed with warnings. Check the issues above."
            }
        } else {
            Write-Error "❌ Validation failed with errors. Please fix the issues above."
        }
    }
    
    Write-Host ""
    Write-Host "📋 Next steps:"
    Write-Host "1. Start services: .\manage_databases.ps1 start"
    Write-Host "2. Initialize data: .\manage_databases.ps1 init"
    Write-Host "3. Check health: .\manage_databases.ps1 health"
    Write-Host "4. Access interfaces: See README.md for URLs"
}

# Main execution
function Main {
    Show-Header
    
    "Starting comprehensive validation..." | Out-File -FilePath $ValidationLog
    
    Test-FileStructure
    Test-Directories  
    Test-Prerequisites
    Test-DockerCompose
    Test-ConfigFiles
    Test-ScriptPermissions
    Test-RunningServices
    Test-WebInterfaces
    
    Show-SummaryReport
}

# Run the validation
Main
