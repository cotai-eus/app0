"""
AI Processing service for document analysis, tender matching, and intelligent processing.
Based on the database architecture plan.
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID, uuid4
import json

from sqlalchemy.orm import Session
from app.core.exceptions import NotFoundError, ValidationError, ServiceError
from app.domains.documents.repository import (
    DocumentRepository, TextExtractionRepository, AIProcessingJobRepository,
    TenderAIAnalysisRepository, AIPromptTemplateRepository, AIResponseCacheRepository
)
from app.domains.documents.models import ProcessingStatus, AIJobType
from app.domains.documents.schemas import (
    DocumentResponse, AIProcessingJobCreate, AIProcessingJobResponse,
    TenderAIAnalysisCreate, TenderAIAnalysisResponse
)


class AIProcessingService:
    """Service for AI-powered document processing and analysis."""
    
    def __init__(self, db: Session):
        self.db = db
        self.document_repo = DocumentRepository(db)
        self.text_extraction_repo = TextExtractionRepository(db)
        self.ai_job_repo = AIProcessingJobRepository(db)
        self.tender_analysis_repo = TenderAIAnalysisRepository(db)
        self.prompt_template_repo = AIPromptTemplateRepository(db)
        self.response_cache_repo = AIResponseCacheRepository(db)
    
    async def process_document(
        self,
        document_id: str,
        company_id: str,
        job_type: AIJobType,
        user_id: str,
        priority: str = "normal",
        parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """Start AI processing for a document."""
        
        # Verify document exists and user has access
        document = self.document_repo.get_company_document(document_id, company_id)
        if not document:
            raise NotFoundError(f"Document {document_id} not found")
        
        # Check if similar job is already running
        existing_job = self.ai_job_repo.get_pending_job_for_document(document_id, job_type)
        if existing_job:
            return str(existing_job.id)
        
        # Create AI processing job
        job_data = AIProcessingJobCreate(
            document_id=UUID(document_id),
            job_type=job_type,
            priority=priority,
            parameters=parameters or {},
            created_by=UUID(user_id)
        )
        
        job = self.ai_job_repo.create_job(
            document_id=document_id,
            job_type=job_type,
            priority=priority,
            parameters=parameters or {},
            created_by=user_id
        )
        
        # Update document processing status
        self.document_repo.update_processing_status(
            document_id, ProcessingStatus.PROCESSING
        )
        
        # Queue job for processing (would integrate with Celery in production)
        await self._queue_ai_job(str(job.id), job_type, document_id, parameters or {})
        
        return str(job.id)
    
    async def _queue_ai_job(
        self,
        job_id: str,
        job_type: AIJobType,
        document_id: str,
        parameters: Dict[str, Any]
    ):
        """Queue AI job for background processing."""
        # In production, this would use Celery task queue
        # For now, simulate async processing
        
        try:
            if job_type == AIJobType.TEXT_EXTRACTION:
                await self._process_text_extraction(job_id, document_id, parameters)
            elif job_type == AIJobType.TENDER_ANALYSIS:
                await self._process_tender_analysis(job_id, document_id, parameters)
            elif job_type == AIJobType.CLASSIFICATION:
                await self._process_document_classification(job_id, document_id, parameters)
            elif job_type == AIJobType.SUMMARIZATION:
                await self._process_document_summarization(job_id, document_id, parameters)
            else:
                raise ValueError(f"Unsupported job type: {job_type}")
                
        except Exception as e:
            # Mark job as failed
            self.ai_job_repo.update_job_status(
                job_id, ProcessingStatus.FAILED, 
                error_message=str(e)
            )
            self.document_repo.update_processing_status(
                document_id, ProcessingStatus.FAILED
            )
    
    async def _process_text_extraction(
        self, 
        job_id: str, 
        document_id: str, 
        parameters: Dict[str, Any]
    ):
        """Process text extraction from document."""
        
        # Update job status
        self.ai_job_repo.update_job_status(job_id, ProcessingStatus.PROCESSING)
        
        # Simulate AI processing delay
        await asyncio.sleep(2)
        
        # Mock text extraction result
        extracted_text = f"Extracted text from document {document_id}"
        confidence_score = 0.95
        
        # Store extraction result
        extraction = self.text_extraction_repo.create_extraction(
            document_id=document_id,
            extraction_type="full_text",
            extracted_text=extracted_text,
            confidence_score=confidence_score,
            ai_job_id=job_id
        )
        
        # Update job with results
        result_data = {
            "extraction_id": str(extraction.id),
            "text_length": len(extracted_text),
            "confidence_score": confidence_score
        }
        
        self.ai_job_repo.update_job_status(
            job_id, ProcessingStatus.COMPLETED, 
            result=result_data
        )
        
        # Update document status
        self.document_repo.update_processing_status(
            document_id, ProcessingStatus.COMPLETED
        )
    
    async def _process_tender_analysis(
        self, 
        job_id: str, 
        document_id: str, 
        parameters: Dict[str, Any]
    ):
        """Process tender analysis for document."""
        
        # Update job status
        self.ai_job_repo.update_job_status(job_id, ProcessingStatus.PROCESSING)
        
        # Get document details
        document = self.document_repo.get_by_id(document_id)
        if not document:
            raise NotFoundError(f"Document {document_id} not found")
        
        # Simulate AI analysis delay
        await asyncio.sleep(3)
        
        # Mock tender analysis result
        analysis_result = {
            "tender_type": "infrastructure",
            "estimated_value": 1500000.0,
            "deadline": "2025-08-15",
            "requirements": [
                "Civil engineering experience",
                "Previous infrastructure projects",
                "Financial capacity > 2M"
            ],
            "key_terms": [
                "bridge construction",
                "concrete works",
                "environmental compliance"
            ],
            "compliance_score": 0.87,
            "recommendation": "suitable",
            "risk_factors": [
                "Tight deadline",
                "Environmental regulations"
            ]
        }
        
        # Store analysis result
        analysis = self.tender_analysis_repo.create_analysis(
            document_id=document_id,
            company_id=str(document.company_id),
            analysis_result=analysis_result,
            confidence_score=0.87,
            ai_job_id=job_id
        )
        
        # Update job with results
        result_data = {
            "analysis_id": str(analysis.id),
            "tender_type": analysis_result["tender_type"],
            "estimated_value": analysis_result["estimated_value"],
            "recommendation": analysis_result["recommendation"],
            "confidence_score": 0.87
        }
        
        self.ai_job_repo.update_job_status(
            job_id, ProcessingStatus.COMPLETED, 
            result=result_data
        )
        
        # Update document status
        self.document_repo.update_processing_status(
            document_id, ProcessingStatus.COMPLETED
        )
    
    async def _process_document_classification(
        self, 
        job_id: str, 
        document_id: str, 
        parameters: Dict[str, Any]
    ):
        """Process document classification."""
        
        # Update job status
        self.ai_job_repo.update_job_status(job_id, ProcessingStatus.PROCESSING)
        
        # Simulate AI processing
        await asyncio.sleep(1.5)
        
        # Mock classification result
        classification = {
            "category": "contract",
            "subcategory": "service_agreement",
            "confidence": 0.92,
            "tags": ["legal", "service", "commercial"]
        }
        
        # Update document with classification
        self.document_repo.update_document(
            document_id,
            {
                "doc_metadata": {
                    "ai_classification": classification
                }
            }
        )
        
        # Update job with results
        self.ai_job_repo.update_job_status(
            job_id, ProcessingStatus.COMPLETED, 
            result=classification
        )
        
        # Update document status
        self.document_repo.update_processing_status(
            document_id, ProcessingStatus.COMPLETED
        )
    
    async def _process_document_summarization(
        self, 
        job_id: str, 
        document_id: str, 
        parameters: Dict[str, Any]
    ):
        """Process document summarization."""
        
        # Update job status
        self.ai_job_repo.update_job_status(job_id, ProcessingStatus.PROCESSING)
        
        # Simulate AI processing
        await asyncio.sleep(2.5)
        
        # Mock summarization result
        summary = {
            "executive_summary": "This document outlines a service agreement...",
            "key_points": [
                "Service duration: 12 months",
                "Payment terms: Net 30",
                "Deliverables: Monthly reports"
            ],
            "word_count": 150,
            "original_length": 2500
        }
        
        # Update job with results
        self.ai_job_repo.update_job_status(
            job_id, ProcessingStatus.COMPLETED, 
            result=summary
        )
        
        # Update document status
        self.document_repo.update_processing_status(
            document_id, ProcessingStatus.COMPLETED
        )
    
    def get_job_status(self, job_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get AI processing job status."""
        job = self.ai_job_repo.get_by_id(job_id)
        if not job:
            return None
        
        # Basic access control - user must own the job or be admin
        if str(job.created_by) != user_id:
            # Add admin check here in production
            raise ValidationError("Access denied")
        
        return {
            "id": str(job.id),
            "document_id": str(job.document_id),
            "job_type": job.job_type,
            "status": job.status,
            "priority": job.priority,
            "progress_percentage": job.progress_percentage,
            "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "result": job.result,
            "error_message": job.error_message
        }
    
    def get_user_jobs(
        self, 
        user_id: str, 
        company_id: str,
        status: Optional[ProcessingStatus] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get AI processing jobs for a user."""
        jobs = self.ai_job_repo.get_user_jobs(user_id, status, limit)
        
        return [
            {
                "id": str(job.id),
                "document_id": str(job.document_id),
                "job_type": job.job_type,
                "status": job.status,
                "priority": job.priority,
                "created_at": job.created_at.isoformat(),
                "completed_at": job.completed_at.isoformat() if job.completed_at else None
            }
            for job in jobs
        ]
    
    def get_document_analysis(
        self, 
        document_id: str, 
        company_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get comprehensive AI analysis for a document."""
        
        # Verify document access
        document = self.document_repo.get_company_document(document_id, company_id)
        if not document:
            raise NotFoundError(f"Document {document_id} not found")
        
        # Get text extractions
        extractions = self.text_extraction_repo.get_document_extractions(document_id)
        
        # Get tender analysis
        tender_analysis = self.tender_analysis_repo.get_document_analysis(document_id)
        
        # Get processing jobs
        jobs = self.ai_job_repo.get_document_jobs(document_id)
        
        analysis_data = {
            "document_id": document_id,
            "processing_status": document.processing_status,
            "text_extractions": [
                {
                    "id": str(ext.id),
                    "extraction_type": ext.extraction_type,
                    "confidence_score": ext.confidence_score,
                    "created_at": ext.created_at.isoformat(),
                    "text_preview": ext.extracted_text[:200] + "..." if len(ext.extracted_text) > 200 else ext.extracted_text
                }
                for ext in extractions
            ],
            "tender_analysis": {
                "id": str(tender_analysis.id),
                "analysis_result": tender_analysis.analysis_result,
                "confidence_score": tender_analysis.confidence_score,
                "created_at": tender_analysis.created_at.isoformat()
            } if tender_analysis else None,
            "processing_jobs": [
                {
                    "id": str(job.id),
                    "job_type": job.job_type,
                    "status": job.status,
                    "created_at": job.created_at.isoformat(),
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None
                }
                for job in jobs
            ]
        }
        
        return analysis_data
    
    def get_company_analytics(
        self, 
        company_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get AI processing analytics for a company."""
        
        # Get job statistics
        job_stats = self.ai_job_repo.get_job_statistics(company_id, days)
        
        # Get tender analysis statistics  
        tender_stats = self.tender_analysis_repo.get_company_analytics(company_id, days)
        
        # Get processing performance
        performance_stats = self.ai_job_repo.get_performance_metrics(company_id, days)
        
        return {
            "period_days": days,
            "job_statistics": job_stats,
            "tender_analysis": tender_stats,
            "performance_metrics": performance_stats,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def cancel_job(self, job_id: str, user_id: str) -> bool:
        """Cancel an AI processing job."""
        job = self.ai_job_repo.get_by_id(job_id)
        if not job:
            return False
        
        # Access control
        if str(job.created_by) != user_id:
            raise ValidationError("Access denied")
        
        # Can only cancel pending or processing jobs
        if job.status not in [ProcessingStatus.PENDING, ProcessingStatus.PROCESSING]:
            raise ValidationError("Cannot cancel completed or failed jobs")
        
        # Update job status
        self.ai_job_repo.update_job_status(
            job_id, ProcessingStatus.CANCELLED
        )
        
        # Update document status if needed
        if job.document_id:
            self.document_repo.update_processing_status(
                str(job.document_id), ProcessingStatus.CANCELLED
            )
        
        return True
    
    def retry_failed_job(self, job_id: str, user_id: str) -> bool:
        """Retry a failed AI processing job."""
        job = self.ai_job_repo.get_by_id(job_id)
        if not job:
            return False
        
        # Access control
        if str(job.created_by) != user_id:
            raise ValidationError("Access denied")
        
        # Can only retry failed jobs
        if job.status != ProcessingStatus.FAILED:
            raise ValidationError("Can only retry failed jobs")
        
        # Reset job status
        self.ai_job_repo.update_job_status(
            job_id, ProcessingStatus.PENDING,
            error_message=None
        )
        
        # Update document status
        if job.document_id:
            self.document_repo.update_processing_status(
                str(job.document_id), ProcessingStatus.PENDING
            )
        
        # Re-queue job (would use Celery in production)
        asyncio.create_task(
            self._queue_ai_job(job_id, job.job_type, str(job.document_id), job.parameters or {})
        )
        
        return True
    
    def get_prompt_templates(
        self, 
        company_id: str,
        template_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get AI prompt templates for a company."""
        templates = self.prompt_template_repo.get_company_templates(company_id, template_type)
        
        return [
            {
                "id": str(template.id),
                "name": template.name,
                "template_type": template.template_type,
                "prompt_template": template.prompt_template,
                "variables": template.variables,
                "is_active": template.is_active,
                "usage_count": template.usage_count
            }
            for template in templates
        ]
    
    def create_prompt_template(
        self,
        company_id: str,
        name: str,
        template_type: str,
        prompt_template: str,
        variables: List[str],
        created_by: str,
        **kwargs
    ) -> str:
        """Create a new AI prompt template."""
        template = self.prompt_template_repo.create_template(
            company_id=company_id,
            name=name,
            template_type=template_type,
            prompt_template=prompt_template,
            variables=variables,
            created_by=created_by,
            **kwargs
        )
        
        return str(template.id)
    
    def clear_cache(self, company_id: str, cache_key: Optional[str] = None) -> int:
        """Clear AI response cache."""
        if cache_key:
            count = self.response_cache_repo.delete_cache_entry(cache_key)
        else:
            count = self.response_cache_repo.clear_company_cache(company_id)
        
        return count
