"""
AI Processing Tasks for Celery.
"""

import asyncio
from typing import Dict, Any, List, Optional
from uuid import UUID

from celery import Task
from sqlalchemy.ext.asyncio import AsyncSession

from app.tasks.celery_app import celery_app
from app.tasks.base_task import BaseTask
from app.core.database import get_async_session
from app.domains.documents.service import AIProcessingService
from app.domains.documents.models import AIProcessingJob, Document
from app.domains.documents.schemas import (
    DocumentCreate,
    AIJobCreate,
    TextExtractionRequest,
    TenderAnalysisRequest,
    DocumentClassificationRequest,
    SummarizationRequest,
    BulkProcessingRequest,
)
from app.core.logging import get_logger_with_context

logger = get_logger_with_context(component="ai_tasks")


class AIProcessingTask(BaseTask):
    """Base class for AI processing tasks."""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        super().on_failure(exc, task_id, args, kwargs, einfo)
        # Update job status to failed
        asyncio.run(self._update_job_status(task_id, "failed", str(exc)))
    
    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success."""
        super().on_success(retval, task_id, args, kwargs)
        # Update job status to completed
        asyncio.run(self._update_job_status(task_id, "completed"))
    
    async def _update_job_status(self, task_id: str, status: str, error_message: str = None):
        """Update AI job status."""
        try:
            async with get_async_session() as db:
                service = AIProcessingService(db)
                await service.update_job_status(task_id, status, error_message)
        except Exception as e:
            logger.error(f"Failed to update job status: {e}")


@celery_app.task(bind=True, base=AIProcessingTask, name="ai_tasks.process_document")
def process_document(self, document_id: str, operations: List[str], options: Dict[str, Any] = None):
    """Process a document with specified AI operations."""
    return asyncio.run(process_document_async(self, document_id, operations, options))


async def process_document_async(task: Task, document_id: str, operations: List[str], options: Dict[str, Any] = None):
    """Async version of document processing."""
    try:
        options = options or {}
        results = {}
        
        async with get_async_session() as db:
            service = AIProcessingService(db)
            
            # Update job status to running
            await service.update_job_status(task.request.id, "running")
            
            for operation in operations:
                try:
                    task.update_state(
                        state="PROGRESS",
                        meta={
                            "current_operation": operation,
                            "completed_operations": list(results.keys()),
                            "total_operations": len(operations)
                        }
                    )
                    
                    if operation == "extract_text":
                        result = await service.extract_text(
                            UUID(document_id),
                            force_reprocess=options.get("force_reprocess", False)
                        )
                        results["text_extraction"] = result
                        
                    elif operation == "analyze_tender":
                        result = await service.analyze_tender(
                            UUID(document_id),
                            analysis_type=options.get("analysis_type", "comprehensive")
                        )
                        results["tender_analysis"] = result
                        
                    elif operation == "classify":
                        result = await service.classify_document(
                            UUID(document_id),
                            classification_type=options.get("classification_type", "category")
                        )
                        results["classification"] = result
                        
                    elif operation == "summarize":
                        result = await service.summarize_document(
                            UUID(document_id),
                            summary_type=options.get("summary_type", "brief"),
                            max_length=options.get("max_length", 500)
                        )
                        results["summarization"] = result
                        
                    else:
                        logger.warning(f"Unknown operation: {operation}")
                        
                except Exception as e:
                    logger.error(f"Error in operation {operation}: {e}")
                    results[operation] = {"error": str(e)}
        
        return {
            "document_id": document_id,
            "completed_operations": list(results.keys()),
            "results": results,
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Document processing failed: {e}")
        raise


@celery_app.task(bind=True, base=AIProcessingTask, name="ai_tasks.bulk_process_documents")
def bulk_process_documents(self, document_ids: List[str], operations: List[str], options: Dict[str, Any] = None):
    """Process multiple documents in bulk."""
    return asyncio.run(bulk_process_documents_async(self, document_ids, operations, options))


async def bulk_process_documents_async(task: Task, document_ids: List[str], operations: List[str], options: Dict[str, Any] = None):
    """Async version of bulk document processing."""
    try:
        options = options or {}
        results = {}
        total_documents = len(document_ids)
        
        async with get_async_session() as db:
            service = AIProcessingService(db)
            
            # Update job status to running
            await service.update_job_status(task.request.id, "running")
            
            for i, document_id in enumerate(document_ids):
                try:
                    task.update_state(
                        state="PROGRESS",
                        meta={
                            "current_document": document_id,
                            "completed_documents": i,
                            "total_documents": total_documents,
                            "progress_percentage": int((i / total_documents) * 100)
                        }
                    )
                    
                    # Create individual processing job for each document
                    job_data = AIJobCreate(
                        job_type="document_processing",
                        document_id=UUID(document_id),
                        parameters={
                            "operations": operations,
                            "options": options
                        },
                        priority=options.get("priority", "medium")
                    )
                    
                    job = await service.create_ai_job(job_data)
                    
                    # Process the document asynchronously
                    process_document.delay(document_id, operations, options)
                    
                    results[document_id] = {
                        "job_id": str(job.id),
                        "status": "queued"
                    }
                    
                except Exception as e:
                    logger.error(f"Error processing document {document_id}: {e}")
                    results[document_id] = {"error": str(e)}
        
        return {
            "total_documents": total_documents,
            "processed_documents": len(results),
            "results": results,
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Bulk processing failed: {e}")
        raise


@celery_app.task(bind=True, base=AIProcessingTask, name="ai_tasks.extract_text")
def extract_text_task(self, document_id: str, force_reprocess: bool = False):
    """Extract text from a document."""
    return asyncio.run(extract_text_async(self, document_id, force_reprocess))


async def extract_text_async(task: Task, document_id: str, force_reprocess: bool = False):
    """Async text extraction."""
    try:
        async with get_async_session() as db:
            service = AIProcessingService(db)
            
            # Update job status
            await service.update_job_status(task.request.id, "running")
            
            result = await service.extract_text(UUID(document_id), force_reprocess)
            
            return {
                "document_id": document_id,
                "result": result,
                "status": "completed"
            }
            
    except Exception as e:
        logger.error(f"Text extraction failed: {e}")
        raise


@celery_app.task(bind=True, base=AIProcessingTask, name="ai_tasks.analyze_tender")
def analyze_tender_task(self, document_id: str, analysis_type: str = "comprehensive"):
    """Analyze a tender document."""
    return asyncio.run(analyze_tender_async(self, document_id, analysis_type))


async def analyze_tender_async(task: Task, document_id: str, analysis_type: str = "comprehensive"):
    """Async tender analysis."""
    try:
        async with get_async_session() as db:
            service = AIProcessingService(db)
            
            # Update job status
            await service.update_job_status(task.request.id, "running")
            
            result = await service.analyze_tender(UUID(document_id), analysis_type)
            
            return {
                "document_id": document_id,
                "analysis_type": analysis_type,
                "result": result,
                "status": "completed"
            }
            
    except Exception as e:
        logger.error(f"Tender analysis failed: {e}")
        raise


@celery_app.task(bind=True, base=AIProcessingTask, name="ai_tasks.classify_document")
def classify_document_task(self, document_id: str, classification_type: str = "category"):
    """Classify a document."""
    return asyncio.run(classify_document_async(self, document_id, classification_type))


async def classify_document_async(task: Task, document_id: str, classification_type: str = "category"):
    """Async document classification."""
    try:
        async with get_async_session() as db:
            service = AIProcessingService(db)
            
            # Update job status
            await service.update_job_status(task.request.id, "running")
            
            result = await service.classify_document(UUID(document_id), classification_type)
            
            return {
                "document_id": document_id,
                "classification_type": classification_type,
                "result": result,
                "status": "completed"
            }
            
    except Exception as e:
        logger.error(f"Document classification failed: {e}")
        raise


@celery_app.task(bind=True, base=AIProcessingTask, name="ai_tasks.summarize_document")
def summarize_document_task(self, document_id: str, summary_type: str = "brief", max_length: int = 500):
    """Summarize a document."""
    return asyncio.run(summarize_document_async(self, document_id, summary_type, max_length))


async def summarize_document_async(task: Task, document_id: str, summary_type: str = "brief", max_length: int = 500):
    """Async document summarization."""
    try:
        async with get_async_session() as db:
            service = AIProcessingService(db)
            
            # Update job status
            await service.update_job_status(task.request.id, "running")
            
            result = await service.summarize_document(UUID(document_id), summary_type, max_length)
            
            return {
                "document_id": document_id,
                "summary_type": summary_type,
                "max_length": max_length,
                "result": result,
                "status": "completed"
            }
            
    except Exception as e:
        logger.error(f"Document summarization failed: {e}")
        raise


@celery_app.task(bind=True, base=BaseTask, name="ai_tasks.cleanup_old_data")
def cleanup_old_data(self, days: int = 30):
    """Clean up old AI processing data."""
    return asyncio.run(cleanup_old_data_async(self, days))


async def cleanup_old_data_async(task: Task, days: int = 30):
    """Async cleanup of old data."""
    try:
        async with get_async_session() as db:
            service = AIProcessingService(db)
            
            cleaned_count = await service.cleanup_old_data(days)
            
            return {
                "cleaned_records": cleaned_count,
                "days": days,
                "status": "completed"
            }
            
    except Exception as e:
        logger.error(f"Data cleanup failed: {e}")
        raise


@celery_app.task(bind=True, base=BaseTask, name="ai_tasks.generate_performance_report")
def generate_performance_report(self, period: str = "7d"):
    """Generate AI performance report."""
    return asyncio.run(generate_performance_report_async(self, period))


async def generate_performance_report_async(task: Task, period: str = "7d"):
    """Async performance report generation."""
    try:
        async with get_async_session() as db:
            service = AIProcessingService(db)
            
            metrics = await service.get_performance_metrics(period)
            analytics = await service.get_analytics()
            
            return {
                "period": period,
                "metrics": metrics,
                "analytics": analytics,
                "generated_at": task.request.timestamp,
                "status": "completed"
            }
            
    except Exception as e:
        logger.error(f"Performance report generation failed: {e}")
        raise


# Periodic tasks
@celery_app.task(bind=True, base=BaseTask, name="ai_tasks.periodic_cleanup")
def periodic_cleanup(self):
    """Periodic cleanup of old AI data."""
    return cleanup_old_data.delay(days=30)


@celery_app.task(bind=True, base=BaseTask, name="ai_tasks.periodic_analytics_update")
def periodic_analytics_update(self):
    """Periodic update of AI analytics."""
    return asyncio.run(periodic_analytics_update_async(self))


async def periodic_analytics_update_async(task: Task):
    """Update AI analytics periodically."""
    try:
        async with get_async_session() as db:
            service = AIProcessingService(db)
            
            # Update performance metrics
            await service.update_performance_metrics()
            
            # Cache analytics data
            await service.cache_analytics_data()
            
            return {
                "updated_at": task.request.timestamp,
                "status": "completed"
            }
            
    except Exception as e:
        logger.error(f"Analytics update failed: {e}")
        raise
