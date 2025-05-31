"""
LLM Integration Module for CotAi Backend

This module provides comprehensive AI/LLM capabilities for document processing,
tender analysis, quotation generation, and risk assessment using Ollama with
local AI models (Llama 3).

Core Features:
- Document text extraction (PDF, DOCX, TXT) with OCR fallback
- AI-powered tender data extraction and analysis
- Automated quotation generation
- Risk assessment and analysis
- Performance monitoring and health checks
- Redis-based result caching
- Comprehensive error handling and logging

Architecture:
- Services-based modular design
- Async/await support throughout
- Production-ready with monitoring
- GPU acceleration via Ollama
- Scalable and maintainable

Main Components:
- LLMServiceManager: Central coordinator for all AI operations
- TextExtractionService: Document processing and text extraction
- AIProcessingService: Core LLM integration with Ollama
- PromptManagerService: AI prompt management and templating
- HealthCheckService: System health monitoring
- CacheService: AI result caching with Redis
- MonitoringService: Performance metrics and analytics

Usage:
    from llm import llm_manager
    
    async with llm_manager as manager:
        result = await manager.process_document("document.pdf")
        quotation = await manager.generate_quotation(result.extracted_data)

Requirements:
- Ollama running with Llama 3 models
- Redis for caching
- GPU acceleration recommended
- Batch processing support
"""

from .manager import llm_manager, LLMServiceManager
from .models import (
    AIProcessingResult,
    ExtractedTenderData,
    TenderItem,
    QuotationStructure,
    DisputeTracking,
    AIMetric,
    HealthCheck,
    CacheEntry
)
from .services import (
    TextExtractionService,
    AIProcessingService,
    PromptManagerService,
    HealthCheckService,
    CacheService,
    MonitoringService
)
from .exceptions import (
    AIException,
    AIProcessingException,
    DocumentProcessingException,
    ModelUnavailableException,
    PromptException,
    CacheException,
    RateLimitException,
    ValidationException
)

__version__ = "1.0.0"
__author__ = "CotAi Development Team"

__all__ = [
    # Main manager
    "llm_manager",
    "LLMServiceManager",
    
    # Data models
    "AIProcessingResult",
    "ExtractedTenderData", 
    "TenderItem",
    "QuotationStructure",
    "DisputeTracking",
    "AIMetric",
    "HealthCheck",
    "CacheEntry",
    
    # Services
    "TextExtractionService",
    "AIProcessingService",
    "PromptManagerService", 
    "HealthCheckService",
    "CacheService",
    "MonitoringService",
    
    # Exceptions
    "AIException",
    "AIProcessingException",
    "DocumentProcessingException", 
    "ModelUnavailableException",
    "PromptException",
    "CacheException",
    "RateLimitException",
    "ValidationException",
]
