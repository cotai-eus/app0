# Ollama Initialization Script for CotAi Backend (PowerShell)
# This script downloads and configures the required AI models

param(
    [string]$OllamaUrl = "http://localhost:11434",
    [int]$MaxRetries = 5,
    [int]$RetryDelay = 10
)

# Configuration
$ModelsToDownload = @(
    "llama3:8b",
    "llama3:instruct", 
    "codellama:7b"
)

Write-Host "🤖 Starting Ollama Model Setup for CotAi..." -ForegroundColor Cyan

# Function to check if Ollama is running
function Test-OllamaConnection {
    Write-Host "Checking if Ollama is running..." -ForegroundColor Yellow
    
    for ($i = 1; $i -le $MaxRetries; $i++) {
        try {
            $response = Invoke-RestMethod -Uri "$OllamaUrl/api/tags" -Method Get -TimeoutSec 5
            Write-Host "✅ Ollama is running" -ForegroundColor Green
            return $true
        }
        catch {
            Write-Host "⏳ Waiting for Ollama to start... (attempt $i/$MaxRetries)" -ForegroundColor Yellow
            Start-Sleep -Seconds $RetryDelay
        }
    }
    
    Write-Host "❌ Ollama is not running after $MaxRetries attempts" -ForegroundColor Red
    return $false
}

# Function to download model
function Install-OllamaModel {
    param([string]$ModelName)
    
    Write-Host "📥 Downloading model: $ModelName" -ForegroundColor Cyan
    
    try {
        $body = @{
            name = $ModelName
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Uri "$OllamaUrl/api/pull" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 3600
        Write-Host "✅ Successfully downloaded: $ModelName" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "❌ Failed to download: $ModelName - $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Function to list available models
function Get-OllamaModels {
    Write-Host "📋 Listing available models:" -ForegroundColor Cyan
    
    try {
        $response = Invoke-RestMethod -Uri "$OllamaUrl/api/tags" -Method Get -TimeoutSec 10
        if ($response.models) {
            $response.models | ForEach-Object { Write-Host "  - $($_.name)" -ForegroundColor Gray }
        } else {
            Write-Host "  No models found" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "  Failed to retrieve model list" -ForegroundColor Red
    }
}

# Function to test model
function Test-OllamaModel {
    param([string]$ModelName)
    
    Write-Host "🧪 Testing model: $ModelName" -ForegroundColor Cyan
    
    try {
        $body = @{
            model = $ModelName
            prompt = "Hello, how are you?"
            stream = $false
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Uri "$OllamaUrl/api/generate" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 30
        Write-Host "✅ Model $ModelName is working correctly" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "❌ Model $ModelName test failed - $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Main execution
function Main {
    Write-Host "🚀 CotAi Ollama Setup Script" -ForegroundColor Magenta
    Write-Host "================================" -ForegroundColor Magenta
    
    # Check if Ollama is running
    if (-not (Test-OllamaConnection)) {
        Write-Host "❌ Cannot proceed without Ollama running" -ForegroundColor Red
        exit 1
    }
    
    # Download models
    Write-Host "📥 Starting model downloads..." -ForegroundColor Cyan
    $failedModels = @()
    
    foreach ($model in $ModelsToDownload) {
        if (Install-OllamaModel -ModelName $model) {
            Write-Host "✅ Model downloaded: $model" -ForegroundColor Green
        } else {
            Write-Host "❌ Failed to download: $model" -ForegroundColor Red
            $failedModels += $model
        }
    }
    
    # List all models
    Write-Host ""
    Get-OllamaModels
    
    # Test models
    Write-Host ""
    Write-Host "🧪 Testing downloaded models..." -ForegroundColor Cyan
    foreach ($model in $ModelsToDownload) {
        # Skip failed downloads
        if ($model -in $failedModels) {
            Write-Host "⏭️  Skipping test for failed download: $model" -ForegroundColor Yellow
            continue
        }
        Test-OllamaModel -ModelName $model
    }
    
    # Summary
    Write-Host ""
    Write-Host "📊 Setup Summary:" -ForegroundColor Magenta
    Write-Host "==================" -ForegroundColor Magenta
    Write-Host "Total models to download: $($ModelsToDownload.Count)" -ForegroundColor White
    Write-Host "Failed downloads: $($failedModels.Count)" -ForegroundColor White
    
    if ($failedModels.Count -eq 0) {
        Write-Host "🎉 All models downloaded successfully!" -ForegroundColor Green
        Write-Host "✅ Ollama setup complete" -ForegroundColor Green
        exit 0
    } else {
        Write-Host "⚠️  Some models failed to download:" -ForegroundColor Yellow
        $failedModels | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
        Write-Host "❌ Setup completed with errors" -ForegroundColor Red
        exit 1
    }
}

# Run main function
Main
