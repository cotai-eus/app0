"""
LLM Service Manager

Main service manager that coordinates all AI/LLM services and provides
a unified interface for the backend application.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from .services import (
    TextExtractionService,
    AIProcessingService,
    PromptManagerService,
    HealthCheckService,
    cache_service,
    monitoring_service
)
from .models import AIProcessingResult, ExtractedTenderData, QuotationStructure
from .exceptions import AIProcessingError, ModelUnavailableError
from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class LLMServiceManager:
    """Main service manager for all LLM operations."""
    
    def __init__(self):        self.text_extraction = TextExtractionService()
        self.ai_processing = AIProcessingService()
        self.prompt_manager = PromptManagerService()
        self.health_check = HealthCheckService()
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize all LLM services."""
        if self._initialized:
            return
            
        try:
            logger.info("Initializing LLM Service Manager...")
            
            # Initialize services in order
            await self.prompt_manager.initialize()
            await self.ai_processing.initialize()
            await cache_service.initialize()
            await monitoring_service.initialize()
            await self.health_check.initialize()
            
            # Verify system health
            health_status = await self.health_check.check_system_health()
            if not health_status.healthy:
                raise ModelUnavailableError(f"LLM system not healthy: {health_status.details}")
            
            self._initialized = True
            logger.info("✅ LLM Service Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM Service Manager: {e}")
            raise AIProcessingError(f"LLM initialization failed: {e}")
    
    async def close(self) -> None:
        """Close all LLM services."""
        try:
            await cache_service.close()
            await monitoring_service.close()
            await self.ai_processing.close()
            self._initialized = False
            logger.info("LLM Service Manager closed")
        except Exception as e:
            logger.error(f"Error closing LLM Service Manager: {e}")
    
    @asynccontextmanager
    async def _monitor_operation(self, operation: str):
        """Context manager to monitor AI operations."""
        start_time = asyncio.get_event_loop().time()
        success = False
        error_type = None
        
        try:
            yield
            success = True
        except Exception as e:
            error_type = type(e).__name__
            raise
        finally:
            processing_time = asyncio.get_event_loop().time() - start_time
            await monitoring_service.record_operation(
                operation=operation,
                success=success,
                processing_time=processing_time,
                error_type=error_type
            )
    
    async def extract_tender_data(
        self,
        file_path: str,
        use_cache: bool = True
    ) -> AIProcessingResult:
        """
        Extract tender data from a document file.
        
        Args:
            file_path: Path to the document file
            use_cache: Whether to use cached results
            
        Returns:
            AIProcessingResult with extracted tender data
        """
        async with self._monitor_operation("extract_tender_data"):
            try:
                # Extract text from document
                text_content = await self.text_extraction.extract_text(file_path)
                
                # Check cache first
                if use_cache and settings.ai_cache_enabled:
                    cached_result = await cache_service.get_cached_result(
                        content=text_content,
                        operation="extract_tender_data"
                    )
                    if cached_result:
                        logger.debug("Using cached tender extraction result")
                        return cached_result
                
                # Process with AI
                result = await self.ai_processing.extract_tender_data(text_content)
                
                # Cache successful results
                if result.success and use_cache and settings.ai_cache_enabled:
                    await cache_service.cache_result(
                        content=text_content,
                        operation="extract_tender_data",
                        result=result
                    )
                
                return result
                
            except Exception as e:
                logger.error(f"Tender data extraction failed: {e}")
                return AIProcessingResult(
                    success=False,
                    data=None,
                    error_message=str(e),
                    metadata={"file_path": file_path}
                )
    
    async def generate_quotation(
        self,
        tender_data: ExtractedTenderData,
        company_info: Dict[str, Any],
        use_cache: bool = True
    ) -> AIProcessingResult:
        """
        Generate a quotation based on tender data and company information.
        
        Args:
            tender_data: Extracted tender data
            company_info: Company information for quotation
            use_cache: Whether to use cached results
            
        Returns:
            AIProcessingResult with generated quotation
        """
        async with self._monitor_operation("generate_quotation"):
            try:
                # Create input context
                quotation_context = {
                    "tender_data": tender_data.dict(),
                    "company_info": company_info
                }
                
                # Check cache
                if use_cache and settings.ai_cache_enabled:
                    cache_key = f"{tender_data.tender_number}_{hash(str(company_info))}"
                    cached_result = await cache_service.get_cached_result(
                        content=cache_key,
                        operation="generate_quotation"
                    )
                    if cached_result:
                        logger.debug("Using cached quotation result")
                        return cached_result
                
                # Generate quotation with AI
                result = await self.ai_processing.generate_quotation(
                    tender_data=tender_data,
                    company_info=company_info
                )
                
                # Cache successful results
                if result.success and use_cache and settings.ai_cache_enabled:
                    await cache_service.cache_result(
                        content=cache_key,
                        operation="generate_quotation",
                        result=result
                    )
                
                return result
                
            except Exception as e:
                logger.error(f"Quotation generation failed: {e}")
                return AIProcessingResult(
                    success=False,
                    data=None,
                    error_message=str(e),
                    metadata={"tender_number": tender_data.tender_number}
                )
    
    async def analyze_risks(
        self,
        tender_data: ExtractedTenderData,
        use_cache: bool = True
    ) -> AIProcessingResult:
        """
        Analyze risks in a tender.
        
        Args:
            tender_data: Extracted tender data
            use_cache: Whether to use cached results
            
        Returns:
            AIProcessingResult with risk analysis
        """
        async with self._monitor_operation("analyze_risks"):
            try:
                # Check cache
                if use_cache and settings.ai_cache_enabled:
                    cache_key = f"risk_analysis_{tender_data.tender_number}"
                    cached_result = await cache_service.get_cached_result(
                        content=cache_key,
                        operation="analyze_risks"
                    )
                    if cached_result:
                        logger.debug("Using cached risk analysis result")
                        return cached_result
                
                # Analyze risks with AI
                result = await self.ai_processing.analyze_risks(tender_data)
                
                # Cache successful results
                if result.success and use_cache and settings.ai_cache_enabled:
                    await cache_service.cache_result(
                        content=cache_key,
                        operation="analyze_risks",
                        result=result
                    )
                
                return result
                
            except Exception as e:
                logger.error(f"Risk analysis failed: {e}")
                return AIProcessingResult(
                    success=False,
                    data=None,
                    error_message=str(e),
                    metadata={"tender_number": tender_data.tender_number}
                )
    
    async def process_document_batch(
        self,
        file_paths: List[str],
        operations: List[str] = None
    ) -> List[AIProcessingResult]:
        """
        Process multiple documents in batch.
        
        Args:
            file_paths: List of document file paths
            operations: List of operations to perform (default: ["extract_tender_data"])
            
        Returns:
            List of AIProcessingResult for each document
        """
        operations = operations or ["extract_tender_data"]
        results = []
        
        # Limit concurrent processing
        semaphore = asyncio.Semaphore(settings.ai_concurrent_requests)
        
        async def process_single_document(file_path: str) -> AIProcessingResult:
            async with semaphore:
                if "extract_tender_data" in operations:
                    return await self.extract_tender_data(file_path)
                # Add other operations as needed
                return AIProcessingResult(
                    success=False,
                    data=None,
                    error_message="Unknown operation",
                    metadata={"file_path": file_path}
                )
        
        # Process all documents concurrently
        tasks = [process_single_document(fp) for fp in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(AIProcessingResult(
                    success=False,
                    data=None,
                    error_message=str(result),
                    metadata={"file_path": file_paths[i]}
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        try:
            # Get health status
            health_status = await self.health_check.check_system_health()
            
            # Get monitoring summary
            monitoring_summary = await monitoring_service.get_health_summary()
            
            # Get cache stats
            cache_stats = await cache_service.get_cache_stats()
            
            return {
                "initialized": self._initialized,
                "health": health_status.dict(),
                "monitoring": monitoring_summary,
                "cache": cache_stats,
                "services": {
                    "text_extraction": "available",
                    "ai_processing": "available",
                    "prompt_manager": "available",
                    "cache_service": "available" if cache_service.redis_client else "disabled",
                    "monitoring_service": "available"
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {
                "initialized": self._initialized,
                "error": str(e),
                "services": {
                    "text_extraction": "unknown",
                    "ai_processing": "unknown", 
                    "prompt_manager": "unknown",
                    "cache_service": "unknown",
                    "monitoring_service": "unknown"
                }
            }
    
    async def clear_cache(self, operation: str = None) -> Dict[str, Any]:
        """Clear AI cache."""
        try:
            cleared_count = await cache_service.invalidate_cache(operation)
            return {
                "success": True,
                "cleared_entries": cleared_count,
                "operation": operation or "all"
            }
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Global LLM service manager instance
llm_manager = LLMServiceManager()
