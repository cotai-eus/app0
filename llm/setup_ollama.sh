#!/bin/bash

# Ollama Initialization Script for CotAi Backend
# This script downloads and configures the required AI models

set -e

echo "🤖 Starting Ollama Model Setup for CotAi..."

# Configuration
MODELS_TO_DOWNLOAD=(
    "llama3:8b"
    "llama3:instruct"
    "codellama:7b"
)

OLLAMA_URL="http://localhost:11434"
MAX_RETRIES=5
RETRY_DELAY=10

# Function to check if Ollama is running
check_ollama() {
    echo "Checking if Ollama is running..."
    for i in $(seq 1 $MAX_RETRIES); do
        if curl -f "$OLLAMA_URL/api/tags" >/dev/null 2>&1; then
            echo "✅ Ollama is running"
            return 0
        fi
        echo "⏳ Waiting for Ollama to start... (attempt $i/$MAX_RETRIES)"
        sleep $RETRY_DELAY
    done
    echo "❌ Ollama is not running after $MAX_RETRIES attempts"
    return 1
}

# Function to download model
download_model() {
    local model=$1
    echo "📥 Downloading model: $model"
    
    if curl -X POST "$OLLAMA_URL/api/pull" \
        -H "Content-Type: application/json" \
        -d "{\"name\":\"$model\"}" \
        --max-time 3600; then
        echo "✅ Successfully downloaded: $model"
        return 0
    else
        echo "❌ Failed to download: $model"
        return 1
    fi
}

# Function to list available models
list_models() {
    echo "📋 Listing available models:"
    curl -s "$OLLAMA_URL/api/tags" | jq '.models[].name' 2>/dev/null || echo "No models found or jq not available"
}

# Function to test model
test_model() {
    local model=$1
    echo "🧪 Testing model: $model"
    
    local test_prompt="{\"model\":\"$model\",\"prompt\":\"Hello, how are you?\",\"stream\":false}"
    
    if curl -X POST "$OLLAMA_URL/api/generate" \
        -H "Content-Type: application/json" \
        -d "$test_prompt" \
        --max-time 30 >/dev/null 2>&1; then
        echo "✅ Model $model is working correctly"
        return 0
    else
        echo "❌ Model $model test failed"
        return 1
    fi
}

# Main execution
main() {
    echo "🚀 CotAi Ollama Setup Script"
    echo "================================"
    
    # Check if Ollama is running
    if ! check_ollama; then
        echo "❌ Cannot proceed without Ollama running"
        exit 1
    fi
    
    # Download models
    echo "📥 Starting model downloads..."
    failed_models=()
    
    for model in "${MODELS_TO_DOWNLOAD[@]}"; do
        if download_model "$model"; then
            echo "✅ Model downloaded: $model"
        else
            echo "❌ Failed to download: $model"
            failed_models+=("$model")
        fi
    done
    
    # List all models
    echo ""
    list_models
    
    # Test models
    echo ""
    echo "🧪 Testing downloaded models..."
    for model in "${MODELS_TO_DOWNLOAD[@]}"; do
        # Skip failed downloads
        if [[ " ${failed_models[@]} " =~ " ${model} " ]]; then
            echo "⏭️  Skipping test for failed download: $model"
            continue
        fi
        test_model "$model"
    done
    
    # Summary
    echo ""
    echo "📊 Setup Summary:"
    echo "=================="
    echo "Total models to download: ${#MODELS_TO_DOWNLOAD[@]}"
    echo "Failed downloads: ${#failed_models[@]}"
    
    if [ ${#failed_models[@]} -eq 0 ]; then
        echo "🎉 All models downloaded successfully!"
        echo "✅ Ollama setup complete"
        exit 0
    else
        echo "⚠️  Some models failed to download:"
        printf '%s\n' "${failed_models[@]}"
        echo "❌ Setup completed with errors"
        exit 1
    fi
}

# Run main function
main "$@"
