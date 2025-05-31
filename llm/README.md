# LLM Module - CotAi Backend

## Overview

The LLM (Large Language Model) module provides comprehensive AI functionality for the CotAi backend system, enabling automated bidding document processing using local Ollama with NVIDIA GPU acceleration.

## Architecture

```
llm/
├── __init__.py           # Module exports and documentation
├── manager.py            # Main LLM service coordinator  
├── api.py               # FastAPI endpoints for LLM functionality
├── models.py            # Data models for AI processing
├── exceptions.py        # Custom AI-related exceptions
├── test_integration.py  # Integration tests
├── setup_ollama.sh      # Ollama setup script (Linux/macOS)
├── setup_ollama.ps1     # Ollama setup script (Windows)
└── services/
    ├── __init__.py      # Services module exports
    ├── text_extraction.py    # Document text extraction
    ├── ai_processing.py      # Core AI/LLM processing
    ├── prompt_manager.py     # AI prompt management
    ├── health_check.py       # System health monitoring
    ├── cache.py             # Redis-based result caching
    └── monitoring.py        # AI metrics and monitoring
```

## Key Features

### 🤖 AI Processing
- **Document Text Extraction**: Support for PDF, DOCX, and TXT files with OCR fallback
- **Tender Data Extraction**: AI-powered extraction of structured data from tender documents
- **Quotation Generation**: Automated quotation generation based on tender requirements
- **Risk Analysis**: AI-driven risk assessment for tender opportunities

### 📊 Performance & Monitoring
- **Result Caching**: Redis-based caching to avoid redundant AI calls
- **Performance Monitoring**: Comprehensive metrics collection and analysis
- **Health Checks**: Real-time system health monitoring
- **Batch Processing**: Efficient processing of multiple documents

### 🔧 Integration
- **FastAPI Endpoints**: RESTful API for all AI functionality
- **Async Architecture**: Full async/await support for optimal performance
- **Error Handling**: Robust error handling with custom exceptions
- **GPU Acceleration**: NVIDIA GPU support through Ollama

## Installation & Setup

### Prerequisites

1. **Docker & Docker Compose** (for containerized deployment)
2. **NVIDIA GPU Drivers** (for GPU acceleration)
3. **Python 3.9+** (for development)

### Quick Start

1. **Start the system with Docker Compose:**
   ```bash
   docker-compose up -d ollama
   ```

2. **Setup Ollama models:**
   ```bash
   # Linux/macOS
   ./llm/setup_ollama.sh
   
   # Windows
   ./llm/setup_ollama.ps1
   ```

3. **Initialize in Python:**
   ```python
   from llm import llm_manager
   
   # Initialize the LLM system
   await llm_manager.initialize()
   
   # Extract data from document
   result = await llm_manager.extract_tender_data("path/to/document.pdf")
   
   # Generate quotation
   quotation = await llm_manager.generate_quotation(tender_data, company_info)
   ```

### Manual Ollama Setup

If you prefer to set up Ollama manually:

1. **Install Ollama:**
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

2. **Start Ollama:**
   ```bash
   ollama serve
   ```

3. **Download models:**
   ```bash
   ollama pull llama3:8b
   ollama pull llama3:instruct
   ollama pull codellama:7b
   ```

## Configuration

All LLM settings are configured in `backend/app/core/config.py`:

```python
# Ollama API Configuration
OLLAMA_API_URL = "http://localhost:11434"
OLLAMA_DEFAULT_MODEL = "llama3:8b"
OLLAMA_TIMEOUT = 300.0
OLLAMA_MAX_RETRIES = 3

# GPU Performance Settings
OLLAMA_GPU_LAYERS = 35
OLLAMA_CONTEXT_LENGTH = 4096
OLLAMA_THREADS = 8
OLLAMA_TEMPERATURE = 0.1

# Document Processing
MAX_DOCUMENT_SIZE_MB = 50
TEXT_EXTRACTION_TIMEOUT = 120.0
CHUNK_SIZE_TOKENS = 3000
CHUNK_OVERLAP_TOKENS = 200

# Caching & Monitoring
AI_CACHE_TTL_HOURS = 24
AI_METRICS_RETENTION_DAYS = 30
AI_PROCESSING_TIMEOUT = 300.0
```

## API Endpoints

### Health & Status
- `GET /api/v1/llm/health` - Check system health
- `GET /api/v1/llm/status` - Get detailed system status

### Document Processing
- `POST /api/v1/llm/extract/upload` - Extract data from uploaded document
- `POST /api/v1/llm/extract/file` - Extract data from file path

### AI Operations
- `POST /api/v1/llm/quotation/generate` - Generate quotation
- `POST /api/v1/llm/risk/analyze` - Analyze risks
- `POST /api/v1/llm/batch/process` - Batch process documents

### Cache Management
- `POST /api/v1/llm/cache/clear` - Clear AI cache
- `GET /api/v1/llm/cache/stats` - Get cache statistics

### Monitoring
- `GET /api/v1/llm/metrics/operations` - Get operation metrics
- `GET /api/v1/llm/metrics/performance` - Get performance trends

## Usage Examples

### Extract Tender Data

```python
from llm import llm_manager
import asyncio

async def extract_tender():
    await llm_manager.initialize()
    
    # Extract from file
    result = await llm_manager.extract_tender_data("tender_document.pdf")
    
    if result.success:
        tender_data = result.data
        print(f"Tender Number: {tender_data.tender_number}")
        print(f"Organization: {tender_data.organization}")
        print(f"Value: {tender_data.estimated_value} {tender_data.currency}")
    else:
        print(f"Extraction failed: {result.error_message}")
    
    await llm_manager.close()

asyncio.run(extract_tender())
```

### Generate Quotation

```python
from llm import llm_manager
from llm.models import ExtractedTenderData, TenderItem

async def generate_quote():
    await llm_manager.initialize()
    
    # Create tender data
    tender_data = ExtractedTenderData(
        tender_number="TN-2024-001",
        organization="City Council",
        title="Road Maintenance",
        deadline="2024-12-31",
        estimated_value=100000.0,
        currency="USD",
        items=[
            TenderItem(
                description="Pothole repairs",
                quantity=200,
                unit="sq meters"
            )
        ]
    )
    
    # Company information
    company_info = {
        "name": "Construction Co Ltd",
        "experience_years": 10,
        "hourly_rate": 75.0,
        "markup_percentage": 15.0
    }
    
    # Generate quotation
    result = await llm_manager.generate_quotation(tender_data, company_info)
    
    if result.success:
        quotation = result.data
        print(f"Total Amount: {quotation.total_amount}")
        print(f"Delivery Time: {quotation.delivery_time}")
    else:
        print(f"Generation failed: {result.error_message}")
    
    await llm_manager.close()
```

### Batch Processing

```python
async def batch_process():
    await llm_manager.initialize()
    
    file_paths = [
        "tender1.pdf",
        "tender2.docx", 
        "tender3.txt"
    ]
    
    results = await llm_manager.process_document_batch(file_paths)
    
    for i, result in enumerate(results):
        if result.success:
            print(f"Document {i+1}: Success")
        else:
            print(f"Document {i+1}: Failed - {result.error_message}")
    
    await llm_manager.close()
```

## Testing

Run the integration tests to verify everything is working:

```bash
# Run integration tests
python llm/test_integration.py

# Or with pytest
pytest llm/test_integration.py -v
```

## Performance Optimization

### GPU Configuration

For optimal GPU performance, adjust these settings in your environment:

```bash
# Enable GPU layers (adjust based on your GPU memory)
export OLLAMA_GPU_LAYERS=35

# Optimize context length
export OLLAMA_CONTEXT_LENGTH=4096

# Set thread count (adjust based on CPU cores)
export OLLAMA_THREADS=8
```

### Memory Management

- **Document Size Limits**: Configure `MAX_DOCUMENT_SIZE_MB` based on available memory
- **Chunk Size**: Adjust `CHUNK_SIZE_TOKENS` for large documents
- **Cache TTL**: Set `AI_CACHE_TTL_HOURS` based on storage capacity

### Concurrent Processing

Control concurrent AI requests:

```python
# Limit concurrent requests
AI_CONCURRENT_REQUESTS = 3

# Rate limiting
AI_RATE_LIMIT_PER_MINUTE = 30
AI_RATE_LIMIT_PER_HOUR = 500
```

## Monitoring & Observability

### Metrics Collection

The system automatically collects:
- Operation success/failure rates
- Processing times
- Model usage statistics  
- Error frequencies
- Cache hit rates

### Health Checks

Regular health checks verify:
- Ollama service availability
- Model accessibility
- Redis connectivity
- System performance

### Logging

Configure logging levels:

```python
import logging

# Set log level for LLM operations
logging.getLogger("llm").setLevel(logging.INFO)

# Enable prompt/response logging (development only)
AI_LOG_PROMPTS = True
AI_LOG_RESPONSES = True
```

## Troubleshooting

### Common Issues

1. **Ollama Not Running**
   ```bash
   # Check if Ollama is running
   curl http://localhost:11434/api/tags
   
   # Start Ollama
   ollama serve
   ```

2. **Models Not Available**
   ```bash
   # List available models
   ollama list
   
   # Pull required models
   ollama pull llama3:8b
   ```

3. **GPU Not Detected**
   ```bash
   # Check NVIDIA drivers
   nvidia-smi
   
   # Verify Docker GPU support
   docker run --gpus all nvidia/cuda:11.0-base nvidia-smi
   ```

4. **Memory Issues**
   - Reduce `OLLAMA_CONTEXT_LENGTH`
   - Lower `CHUNK_SIZE_TOKENS`
   - Decrease `AI_CONCURRENT_REQUESTS`

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger("llm").setLevel(logging.DEBUG)
```

## Contributing

1. Follow the existing code structure
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Ensure all services handle errors gracefully
5. Maintain async/await patterns throughout

## License

This module is part of the CotAi backend system and follows the same licensing terms.
