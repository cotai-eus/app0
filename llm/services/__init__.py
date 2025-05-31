"""
LLM Services Module

This module contains all AI-related services for the CotAi backend system.
Services include text extraction, AI processing, prompt management, health checks,
caching, and monitoring.

Available Services:
- TextExtractionService: Extract text from various document formats
- AIProcessingService: Core LLM integration with Ollama
- PromptManager: Manage and template AI prompts
- HealthCheckService: Monitor LLM system health
- CacheService: AI result caching with Redis
- MonitoringService: AI metrics and performance monitoring
"""

from .text_extraction import TextExtractionService
from .ai_processing import AIProcessingService
from .prompt_manager import PromptManagerService
from .health_check import HealthCheckService
from .cache import CacheService, cache_service
from .monitoring import MonitoringService, monitoring_service

__all__ = [
    "TextExtractionService",
    "AIProcessingService", 
    "PromptManagerService",
    "HealthCheckService",
    "CacheService",
    "cache_service",
    "MonitoringService", 
    "monitoring_service",
]
