"""
LLM-specific Celery tasks for document processing and AI operations.
"""

import asyncio
import sys
import os
from typing import Dict, Any, List, Optional, Union
from uuid import UUID

from celery import Task
from celery.exceptions import Retry

from app.tasks.celery_app import celery_app
from app.tasks.base_task import BaseTask
from app.core.logging import get_logger_with_context

# Add LLM module to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

try:
    from llm.manager import LLMManager
    from llm.models import AIProcessingResult, ExtractedTenderData, QuotationStructure
    from llm.exceptions import LLMException, ModelNotAvailableException, ProcessingTimeoutException
    llm_available = True
except ImportError as e:
    llm_available = False

logger = get_logger_with_context(component="llm_tasks")


class LLMTask(BaseTask):
    """Base class for LLM processing tasks."""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        super().on_failure(exc, task_id, args, kwargs, einfo)
        logger.error(f"LLM task {task_id} failed: {exc}")
    
    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success."""
        super().on_success(retval, task_id, args, kwargs)
        logger.info(f"LLM task {task_id} completed successfully")


# Document Processing Tasks

@celery_app.task(
    bind=True, 
    base=LLMTask, 
    name="llm_tasks.extract_document_text",
    autoretry_for=(LLMException,),
    retry_kwargs={'max_retries': 3, 'countdown': 60}
)
def extract_document_text(self, file_path: str, file_type: str = None) -> Dict[str, Any]:
    """Extract text from a document file."""
    return asyncio.run(extract_document_text_async(self, file_path, file_type))


async def extract_document_text_async(task: Task, file_path: str, file_type: str = None) -> Dict[str, Any]:
    """Async version of document text extraction."""
    if not llm_available:
        raise LLMException("LLM services not available")
    
    try:
        async with LLMManager() as llm_manager:
            task.update_state(state="PROGRESS", meta={"status": "extracting_text"})
            
            result = await llm_manager.extract_text(file_path)
            
            return {
                "text": result.extracted_text,
                "metadata": result.metadata,
                "confidence": result.confidence_score,
                "processing_time": result.processing_time_seconds
            }
            
    except Exception as e:
        logger.error(f"Text extraction failed: {e}")
        raise LLMException(f"Text extraction failed: {str(e)}")


@celery_app.task(
    bind=True, 
    base=LLMTask, 
    name="llm_tasks.analyze_tender_document",
    autoretry_for=(LLMException,),
    retry_kwargs={'max_retries': 3, 'countdown': 120}
)
def analyze_tender_document(self, text: str, document_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """Analyze tender document and extract structured data."""
    return asyncio.run(analyze_tender_document_async(self, text, document_metadata))


async def analyze_tender_document_async(task: Task, text: str, document_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """Async version of tender document analysis."""
    if not llm_available:
        raise LLMException("LLM services not available")
    
    try:
        async with LLMManager() as llm_manager:
            task.update_state(state="PROGRESS", meta={"status": "analyzing_tender"})
            
            result = await llm_manager.extract_tender_data(text, document_metadata or {})
            
            return {
                "tender_data": result.extracted_data.dict() if result.extracted_data else {},
                "confidence": result.confidence_score,
                "metadata": result.metadata,
                "processing_time": result.processing_time_seconds
            }
            
    except Exception as e:
        logger.error(f"Tender analysis failed: {e}")
        raise LLMException(f"Tender analysis failed: {str(e)}")


@celery_app.task(
    bind=True, 
    base=LLMTask, 
    name="llm_tasks.generate_quotation",
    autoretry_for=(LLMException,),
    retry_kwargs={'max_retries': 3, 'countdown': 180}
)
def generate_quotation(self, tender_data: Dict[str, Any], company_profile: Dict[str, Any] = None) -> Dict[str, Any]:
    """Generate a quotation based on tender data."""
    return asyncio.run(generate_quotation_async(self, tender_data, company_profile))


async def generate_quotation_async(task: Task, tender_data: Dict[str, Any], company_profile: Dict[str, Any] = None) -> Dict[str, Any]:
    """Async version of quotation generation."""
    if not llm_available:
        raise LLMException("LLM services not available")
    
    try:
        async with LLMManager() as llm_manager:
            task.update_state(state="PROGRESS", meta={"status": "generating_quotation"})
            
            result = await llm_manager.generate_quotation(tender_data, company_profile or {})
            
            return {
                "quotation": result.extracted_data.dict() if result.extracted_data else {},
                "confidence": result.confidence_score,
                "metadata": result.metadata,
                "processing_time": result.processing_time_seconds
            }
            
    except Exception as e:
        logger.error(f"Quotation generation failed: {e}")
        raise LLMException(f"Quotation generation failed: {str(e)}")


@celery_app.task(
    bind=True, 
    base=LLMTask, 
    name="llm_tasks.analyze_risks",
    autoretry_for=(LLMException,),
    retry_kwargs={'max_retries': 3, 'countdown': 120}
)
def analyze_risks(self, tender_data: Dict[str, Any], quotation_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Analyze risks associated with a tender."""
    return asyncio.run(analyze_risks_async(self, tender_data, quotation_data))


async def analyze_risks_async(task: Task, tender_data: Dict[str, Any], quotation_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Async version of risk analysis."""
    if not llm_available:
        raise LLMException("LLM services not available")
    
    try:
        async with LLMManager() as llm_manager:
            task.update_state(state="PROGRESS", meta={"status": "analyzing_risks"})
            
            result = await llm_manager.analyze_risks(tender_data, quotation_data or {})
            
            return {
                "risk_analysis": result.extracted_data.dict() if result.extracted_data else {},
                "confidence": result.confidence_score,
                "metadata": result.metadata,
                "processing_time": result.processing_time_seconds
            }
            
    except Exception as e:
        logger.error(f"Risk analysis failed: {e}")
        raise LLMException(f"Risk analysis failed: {str(e)}")


# Batch Processing Tasks

@celery_app.task(
    bind=True, 
    base=LLMTask, 
    name="llm_tasks.process_document_batch",
    autoretry_for=(LLMException,),
    retry_kwargs={'max_retries': 2, 'countdown': 300}
)
def process_document_batch(self, file_paths: List[str], operations: List[str] = None) -> Dict[str, Any]:
    """Process multiple documents in batch."""
    return asyncio.run(process_document_batch_async(self, file_paths, operations))


async def process_document_batch_async(task: Task, file_paths: List[str], operations: List[str] = None) -> Dict[str, Any]:
    """Async version of batch document processing."""
    if not llm_available:
        raise LLMException("LLM services not available")
    
    operations = operations or ["extract_text", "analyze_tender"]
    results = {}
    
    try:
        async with LLMManager() as llm_manager:
            total_files = len(file_paths)
            
            for i, file_path in enumerate(file_paths):
                task.update_state(
                    state="PROGRESS", 
                    meta={
                        "status": f"processing_file_{i+1}_of_{total_files}",
                        "current_file": file_path,
                        "progress": int((i / total_files) * 100)
                    }
                )
                
                file_results = {}
                
                # Extract text
                if "extract_text" in operations:
                    text_result = await llm_manager.extract_text(file_path)
                    file_results["text_extraction"] = {
                        "text": text_result.extracted_text,
                        "confidence": text_result.confidence_score
                    }
                
                # Analyze tender if text extraction was successful
                if "analyze_tender" in operations and "text_extraction" in file_results:
                    tender_result = await llm_manager.extract_tender_data(
                        file_results["text_extraction"]["text"]
                    )
                    file_results["tender_analysis"] = {
                        "data": tender_result.extracted_data.dict() if tender_result.extracted_data else {},
                        "confidence": tender_result.confidence_score
                    }
                
                results[file_path] = file_results
            
            return {
                "results": results,
                "total_processed": len(file_paths),
                "status": "completed"
            }
            
    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        raise LLMException(f"Batch processing failed: {str(e)}")


# Monitoring and Maintenance Tasks

@celery_app.task(
    bind=True, 
    base=LLMTask, 
    name="llm_tasks.health_check",
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 2, 'countdown': 30}
)
def llm_health_check(self) -> Dict[str, Any]:
    """Perform health check on LLM services."""
    return asyncio.run(llm_health_check_async(self))


async def llm_health_check_async(task: Task) -> Dict[str, Any]:
    """Async version of LLM health check."""
    if not llm_available:
        return {"status": "unavailable", "message": "LLM services not available"}
    
    try:
        async with LLMManager() as llm_manager:
            health_status = await llm_manager.health_check()
            return health_status.dict()
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "message": str(e)}


@celery_app.task(
    bind=True, 
    base=LLMTask, 
    name="llm_tasks.cleanup_cache",
)
def cleanup_llm_cache(self, max_age_hours: int = 24) -> Dict[str, Any]:
    """Clean up old cache entries."""
    return asyncio.run(cleanup_llm_cache_async(self, max_age_hours))


async def cleanup_llm_cache_async(task: Task, max_age_hours: int = 24) -> Dict[str, Any]:
    """Async version of cache cleanup."""
    if not llm_available:
        return {"status": "skipped", "message": "LLM services not available"}
    
    try:
        async with LLMManager() as llm_manager:
            cleanup_result = await llm_manager.cleanup_cache(max_age_hours)
            return {
                "status": "completed",
                "cleaned_entries": cleanup_result.get("cleaned_entries", 0),
                "remaining_entries": cleanup_result.get("remaining_entries", 0)
            }
            
    except Exception as e:
        logger.error(f"Cache cleanup failed: {e}")
        return {"status": "failed", "message": str(e)}


# Workflow Tasks

@celery_app.task(
    bind=True, 
    base=LLMTask, 
    name="llm_tasks.complete_tender_workflow",
    autoretry_for=(LLMException,),
    retry_kwargs={'max_retries': 2, 'countdown': 300}
)
def complete_tender_workflow(
    self, 
    file_path: str, 
    company_profile: Dict[str, Any] = None,
    include_risk_analysis: bool = True
) -> Dict[str, Any]:
    """Complete end-to-end tender processing workflow."""
    return asyncio.run(complete_tender_workflow_async(self, file_path, company_profile, include_risk_analysis))


async def complete_tender_workflow_async(
    task: Task, 
    file_path: str, 
    company_profile: Dict[str, Any] = None,
    include_risk_analysis: bool = True
) -> Dict[str, Any]:
    """Async version of complete tender workflow."""
    if not llm_available:
        raise LLMException("LLM services not available")
    
    try:
        async with LLMManager() as llm_manager:
            workflow_result = {}
            
            # Step 1: Extract text
            task.update_state(state="PROGRESS", meta={"step": "extracting_text", "progress": 20})
            text_result = await llm_manager.extract_text(file_path)
            workflow_result["text_extraction"] = {
                "success": True,
                "confidence": text_result.confidence_score,
                "text_length": len(text_result.extracted_text)
            }
            
            # Step 2: Analyze tender
            task.update_state(state="PROGRESS", meta={"step": "analyzing_tender", "progress": 40})
            tender_result = await llm_manager.extract_tender_data(text_result.extracted_text)
            workflow_result["tender_analysis"] = {
                "success": True,
                "confidence": tender_result.confidence_score,
                "data": tender_result.extracted_data.dict() if tender_result.extracted_data else {}
            }
            
            # Step 3: Generate quotation
            task.update_state(state="PROGRESS", meta={"step": "generating_quotation", "progress": 60})
            quotation_result = await llm_manager.generate_quotation(
                workflow_result["tender_analysis"]["data"], 
                company_profile or {}
            )
            workflow_result["quotation"] = {
                "success": True,
                "confidence": quotation_result.confidence_score,
                "data": quotation_result.extracted_data.dict() if quotation_result.extracted_data else {}
            }
            
            # Step 4: Risk analysis (optional)
            if include_risk_analysis:
                task.update_state(state="PROGRESS", meta={"step": "analyzing_risks", "progress": 80})
                risk_result = await llm_manager.analyze_risks(
                    workflow_result["tender_analysis"]["data"],
                    workflow_result["quotation"]["data"]
                )
                workflow_result["risk_analysis"] = {
                    "success": True,
                    "confidence": risk_result.confidence_score,
                    "data": risk_result.extracted_data.dict() if risk_result.extracted_data else {}
                }
            
            task.update_state(state="PROGRESS", meta={"step": "completed", "progress": 100})
            
            return {
                "status": "completed",
                "workflow_result": workflow_result,
                "file_path": file_path
            }
            
    except Exception as e:
        logger.error(f"Tender workflow failed: {e}")
        raise LLMException(f"Tender workflow failed: {str(e)}")
