# =====================================================
# 🔍 DOCKER ENVIRONMENT VALIDATION - COTAI BACKEND
# Comprehensive testing of all services and integrations
# =====================================================

param(
    [ValidateSet("dev", "prod", "all")]
    [string]$Environment = "dev",
    [switch]$Detailed,
    [switch]$HealthCheck,
    [switch]$Performance
)

# Configuration
$ErrorActionPreference = "Continue"
$ValidationResults = @()

# Colors for output
function Write-ColorOutput {
    param([string]$ForegroundColor, [string]$Message)
    $currentColor = $Host.UI.RawUI.ForegroundColor
    $Host.UI.RawUI.ForegroundColor = $ForegroundColor
    Write-Output $Message
    $Host.UI.RawUI.ForegroundColor = $currentColor
}

function Write-TestResult {
    param([string]$TestName, [bool]$Success, [string]$Details = "")
    
    $status = if ($Success) { "✅ PASS" } else { "❌ FAIL" }
    $color = if ($Success) { "Green" } else { "Red" }
    
    Write-ColorOutput $color "[$status] $TestName"
    if ($Details -and ($Detailed -or -not $Success)) {
        Write-ColorOutput "Gray" "    $Details"
    }
    
    $script:ValidationResults += [PSCustomObject]@{
        Test = $TestName
        Status = if ($Success) { "PASS" } else { "FAIL" }
        Details = $Details
        Timestamp = Get-Date
    }
}

function Test-ServiceHealth {
    param([string]$ServiceName, [string]$Url, [int]$TimeoutSeconds = 30)
    
    try {
        $response = Invoke-WebRequest -Uri $Url -TimeoutSec $TimeoutSeconds -UseBasicParsing
        $isHealthy = $response.StatusCode -eq 200
        $details = "Status: $($response.StatusCode), Response Time: $($response.Headers['X-Response-Time'])"
        Write-TestResult "Service Health: $ServiceName" $isHealthy $details
        return $isHealthy
    } catch {
        Write-TestResult "Service Health: $ServiceName" $false "Error: $($_.Exception.Message)"
        return $false
    }
}

function Test-DatabaseConnection {
    param([string]$ServiceName, [string]$ContainerName, [string]$TestCommand)
    
    try {
        $result = docker exec $ContainerName $TestCommand 2>&1
        $success = $LASTEXITCODE -eq 0
        Write-TestResult "Database Connection: $ServiceName" $success $result
        return $success
    } catch {
        Write-TestResult "Database Connection: $ServiceName" $false "Error: $($_.Exception.Message)"
        return $false
    }
}

function Test-ContainerStatus {
    param([string]$ContainerName)
    
    try {
        $container = docker ps --filter "name=$ContainerName" --format "{{.Status}}"
        $isRunning = $container -like "*Up*"
        $details = if ($container) { $container } else { "Container not found" }
        Write-TestResult "Container Status: $ContainerName" $isRunning $details
        return $isRunning
    } catch {
        Write-TestResult "Container Status: $ContainerName" $false "Error: $($_.Exception.Message)"
        return $false
    }
}

function Test-VolumeMount {
    param([string]$VolumeName)
    
    try {
        $volume = docker volume inspect $VolumeName 2>$null
        $exists = $volume -ne $null
        Write-TestResult "Volume Exists: $VolumeName" $exists
        return $exists
    } catch {
        Write-TestResult "Volume Exists: $VolumeName" $false "Error: $($_.Exception.Message)"
        return $false
    }
}

function Test-NetworkConnectivity {
    param([string]$FromContainer, [string]$ToContainer, [int]$Port)
    
    try {
        $result = docker exec $FromContainer nc -z $ToContainer $Port 2>&1
        $success = $LASTEXITCODE -eq 0
        Write-TestResult "Network: $FromContainer -> $ToContainer:$Port" $success
        return $success
    } catch {
        Write-TestResult "Network: $FromContainer -> $ToContainer:$Port" $false "Error: $($_.Exception.Message)"
        return $false
    }
}

function Test-Performance {
    param([string]$ServiceUrl, [string]$ServiceName)
    
    if (-not $Performance) { return $true }
    
    try {
        $startTime = Get-Date
        $response = Invoke-WebRequest -Uri $ServiceUrl -UseBasicParsing
        $endTime = Get-Date
        $responseTime = ($endTime - $startTime).TotalMilliseconds
        
        $isGoodPerformance = $responseTime -lt 5000  # 5 seconds
        $details = "Response time: ${responseTime}ms"
        Write-TestResult "Performance: $ServiceName" $isGoodPerformance $details
        return $isGoodPerformance
    } catch {
        Write-TestResult "Performance: $ServiceName" $false "Error: $($_.Exception.Message)"
        return $false
    }
}

function Get-DockerEnvironmentInfo {
    Write-ColorOutput "Cyan" "=== DOCKER ENVIRONMENT INFO ==="
    
    try {
        $dockerVersion = docker --version
        Write-Output "Docker Version: $dockerVersion"
    } catch {
        Write-ColorOutput "Red" "Docker not available: $($_.Exception.Message)"
    }
    
    try {
        $composeVersion = docker-compose --version
        Write-Output "Docker Compose Version: $composeVersion"
    } catch {
        Write-ColorOutput "Red" "Docker Compose not available: $($_.Exception.Message)"
    }
    
    # System resources
    $memory = Get-ComputerInfo | Select-Object TotalPhysicalMemory
    $memoryGB = [math]::Round($memory.TotalPhysicalMemory / 1GB, 2)
    Write-Output "System Memory: ${memoryGB} GB"
    
    Write-Output ""
}

function Test-DevelopmentEnvironment {
    Write-ColorOutput "Cyan" "=== TESTING DEVELOPMENT ENVIRONMENT ==="
    
    # Test core containers
    $containers = @(
        "cotai_backend",
        "cotai_llm_service", 
        "cotai_postgres",
        "cotai_mongodb",
        "cotai_redis",
        "cotai_ollama",
        "cotai_celery_worker",
        "cotai_celery_beat"
    )
    
    foreach ($container in $containers) {
        Test-ContainerStatus $container
    }
    
    # Test health endpoints
    if ($HealthCheck) {
        Start-Sleep -Seconds 10  # Wait for services to be ready
        
        Test-ServiceHealth "Backend API" "http://localhost:8000/health"
        Test-ServiceHealth "LLM Service" "http://localhost:8001/health" 60
        Test-ServiceHealth "Ollama" "http://localhost:11434/api/tags" 60
        Test-ServiceHealth "Grafana" "http://localhost:3000/api/health"
        Test-ServiceHealth "Prometheus" "http://localhost:9090/-/healthy"
    }
    
    # Test database connections
    Test-DatabaseConnection "PostgreSQL" "cotai_postgres" "pg_isready -U app_user"
    Test-DatabaseConnection "MongoDB" "cotai_mongodb" "mongosh --eval 'db.adminCommand(\"ping\")'"
    Test-DatabaseConnection "Redis" "cotai_redis" "redis-cli ping"
    
    # Test volumes
    $volumes = @(
        "cotai-backend_postgres_data",
        "cotai-backend_mongodb_data",
        "cotai-backend_redis_data",
        "cotai-backend_ollama_models"
    )
    
    foreach ($volume in $volumes) {
        Test-VolumeMount $volume
    }
    
    # Test network connectivity
    Test-NetworkConnectivity "cotai_backend" "postgres" 5432
    Test-NetworkConnectivity "cotai_backend" "mongodb" 27017
    Test-NetworkConnectivity "cotai_backend" "redis" 6379
    Test-NetworkConnectivity "cotai_llm_service" "ollama" 11434
    
    # Performance tests
    if ($Performance) {
        Test-Performance "http://localhost:8000/health" "Backend API"
        Test-Performance "http://localhost:8001/health" "LLM Service"
    }
}

function Test-ProductionEnvironment {
    Write-ColorOutput "Cyan" "=== TESTING PRODUCTION ENVIRONMENT ==="
    
    # Test production containers
    $containers = @(
        "cotai_nginx",
        "cotai_backend",
        "cotai_llm_service",
        "cotai_postgres",
        "cotai_mongodb", 
        "cotai_redis",
        "cotai_ollama",
        "cotai_celery_worker_1",
        "cotai_celery_worker_2",
        "cotai_celery_beat"
    )
    
    foreach ($container in $containers) {
        Test-ContainerStatus $container
    }
    
    # Test SSL endpoints (if certificates exist)
    if ($HealthCheck) {
        try {
            Test-ServiceHealth "Nginx HTTPS" "https://localhost/health"
            Test-ServiceHealth "API via Nginx" "https://localhost/api/health"
            Test-ServiceHealth "LLM via Nginx" "https://localhost/llm/health"
        } catch {
            Write-TestResult "SSL Configuration" $false "HTTPS endpoints not available - check SSL certificates"
        }
    }
    
    # Test resource limits
    $resourceTests = docker stats --no-stream --format "{{.Container}},{{.CPUPerc}},{{.MemUsage}}" | Where-Object { $_ -like "cotai_*" }
    foreach ($line in $resourceTests) {
        $parts = $line -split ","
        $container = $parts[0]
        $cpu = $parts[1] -replace "%", ""
        $memory = $parts[2] -split "/" | Select-Object -First 1
        
        $cpuOk = [double]$cpu -lt 90
        $memoryOk = $memory -notlike "*GiB*" -or ([double]($memory -replace "GiB", "") -lt 8)
        
        Write-TestResult "Resource Usage: $container" ($cpuOk -and $memoryOk) "CPU: ${cpu}%, Memory: $memory"
    }
}

function Generate-Report {
    Write-ColorOutput "Cyan" "=== VALIDATION SUMMARY ==="
    
    $totalTests = $ValidationResults.Count
    $passedTests = ($ValidationResults | Where-Object { $_.Status -eq "PASS" }).Count
    $failedTests = $totalTests - $passedTests
    $successRate = if ($totalTests -gt 0) { [math]::Round(($passedTests / $totalTests) * 100, 2) } else { 0 }
    
    Write-Output "Total Tests: $totalTests"
    Write-ColorOutput "Green" "Passed: $passedTests"
    Write-ColorOutput "Red" "Failed: $failedTests"
    Write-ColorOutput "Yellow" "Success Rate: ${successRate}%"
    
    if ($failedTests -gt 0) {
        Write-Output ""
        Write-ColorOutput "Red" "FAILED TESTS:"
        $ValidationResults | Where-Object { $_.Status -eq "FAIL" } | ForEach-Object {
            Write-ColorOutput "Red" "  • $($_.Test): $($_.Details)"
        }
    }
    
    # Save detailed report
    $reportPath = "validation_report_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
    $ValidationResults | ConvertTo-Json -Depth 3 | Out-File $reportPath
    Write-Output ""
    Write-Output "Detailed report saved to: $reportPath"
    
    return $successRate -ge 80  # Consider 80% success rate as acceptable
}

# Main execution
Write-ColorOutput "Cyan" "🔍 COTAI BACKEND - DOCKER VALIDATION"
Write-Output "Environment: $Environment | Detailed: $Detailed | Health Check: $HealthCheck | Performance: $Performance"
Write-Output ""

Get-DockerEnvironmentInfo

switch ($Environment) {
    "dev" { Test-DevelopmentEnvironment }
    "prod" { Test-ProductionEnvironment }
    "all" { 
        Test-DevelopmentEnvironment
        Write-Output ""
        Test-ProductionEnvironment
    }
}

Write-Output ""
$overallSuccess = Generate-Report

if ($overallSuccess) {
    Write-ColorOutput "Green" "🎉 VALIDATION COMPLETED SUCCESSFULLY!"
    exit 0
} else {
    Write-ColorOutput "Red" "❌ VALIDATION FAILED - Please check the issues above"
    exit 1
}
