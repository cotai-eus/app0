"""
Documents and AI Processing API endpoints.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session, get_current_user
from app.domains.auth.models import User
from app.domains.documents.service import AIProcessingService
from app.domains.documents.schemas import (
    DocumentCreate,
    DocumentResponse,
    DocumentUpdate,
    TextExtractionResponse,
    AIJobResponse,
    AIJobCreate,
    TenderAnalysisResponse,
    DocumentClassificationResponse,
    SummarizationResponse,
    AIPromptTemplateResponse,
    AIPromptTemplateCreate,
    AIAnalyticsResponse,
    BulkProcessingRequest,
)

router = APIRouter()


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    description: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Upload a document for AI processing."""
    try:
        service = AIProcessingService(db)
        
        # Read file content
        content = await file.read()
        
        # Create document
        document_data = DocumentCreate(
            title=title or file.filename,
            description=description,
            category=category,
            file_name=file.filename,
            file_size=len(content),
            mime_type=file.content_type,
            content=content,
            uploaded_by=current_user.id,
            tags=tags.split(',') if tags else []
        )
        
        document = await service.upload_document(document_data)
        return DocumentResponse.model_validate(document)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    category: Optional[str] = None,
    tags: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """List documents with filtering and pagination."""
    service = AIProcessingService(db)
    
    filters = {}
    if category:
        filters["category"] = category
    if tags:
        filters["tags"] = tags.split(',')
    if search:
        filters["search"] = search
        
    documents = await service.get_documents(
        skip=skip, 
        limit=limit, 
        filters=filters
    )
    return [DocumentResponse.model_validate(doc) for doc in documents]


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get a specific document."""
    service = AIProcessingService(db)
    document = await service.get_document(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
        
    return DocumentResponse.model_validate(document)


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: UUID,
    document_update: DocumentUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Update a document."""
    service = AIProcessingService(db)
    document = await service.update_document(document_id, document_update)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
        
    return DocumentResponse.model_validate(document)


@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Delete a document."""
    service = AIProcessingService(db)
    success = await service.delete_document(document_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
        
    return {"message": "Document deleted successfully"}


@router.post("/{document_id}/extract-text", response_model=TextExtractionResponse)
async def extract_text(
    document_id: UUID,
    force_reprocess: bool = False,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Extract text from a document."""
    service = AIProcessingService(db)
    result = await service.extract_text(document_id, force_reprocess)
    
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")
        
    return result


@router.post("/{document_id}/analyze-tender", response_model=TenderAnalysisResponse)
async def analyze_tender(
    document_id: UUID,
    analysis_type: str = "comprehensive",
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Analyze a tender document."""
    service = AIProcessingService(db)
    result = await service.analyze_tender(document_id, analysis_type)
    
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")
        
    return result


@router.post("/{document_id}/classify", response_model=DocumentClassificationResponse)
async def classify_document(
    document_id: UUID,
    classification_type: str = "category",
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Classify a document."""
    service = AIProcessingService(db)
    result = await service.classify_document(document_id, classification_type)
    
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")
        
    return result


@router.post("/{document_id}/summarize", response_model=SummarizationResponse)
async def summarize_document(
    document_id: UUID,
    summary_type: str = "brief",
    max_length: int = 500,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Summarize a document."""
    service = AIProcessingService(db)
    result = await service.summarize_document(document_id, summary_type, max_length)
    
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")
        
    return result


@router.post("/bulk-process", response_model=List[AIJobResponse])
async def bulk_process_documents(
    request: BulkProcessingRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Process multiple documents in bulk."""
    service = AIProcessingService(db)
    jobs = await service.bulk_process_documents(
        document_ids=request.document_ids,
        operations=request.operations,
        priority=request.priority
    )
    return [AIJobResponse.model_validate(job) for job in jobs]


# AI Jobs endpoints
@router.post("/jobs", response_model=AIJobResponse)
async def create_ai_job(
    job_data: AIJobCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Create an AI processing job."""
    service = AIProcessingService(db)
    job = await service.create_ai_job(job_data)
    return AIJobResponse.model_validate(job)


@router.get("/jobs", response_model=List[AIJobResponse])
async def list_ai_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    job_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """List AI processing jobs."""
    service = AIProcessingService(db)
    jobs = await service.get_ai_jobs(
        skip=skip, 
        limit=limit, 
        status=status, 
        job_type=job_type
    )
    return [AIJobResponse.model_validate(job) for job in jobs]


@router.get("/jobs/{job_id}", response_model=AIJobResponse)
async def get_ai_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get a specific AI job."""
    service = AIProcessingService(db)
    job = await service.get_ai_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return AIJobResponse.model_validate(job)


@router.post("/jobs/{job_id}/cancel")
async def cancel_ai_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Cancel an AI processing job."""
    service = AIProcessingService(db)
    success = await service.cancel_ai_job(job_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return {"message": "Job cancelled successfully"}


# AI Prompt Templates endpoints
@router.post("/templates", response_model=AIPromptTemplateResponse)
async def create_prompt_template(
    template_data: AIPromptTemplateCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Create an AI prompt template."""
    service = AIProcessingService(db)
    template = await service.create_prompt_template(template_data)
    return AIPromptTemplateResponse.model_validate(template)


@router.get("/templates", response_model=List[AIPromptTemplateResponse])
async def list_prompt_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """List AI prompt templates."""
    service = AIProcessingService(db)
    templates = await service.get_prompt_templates(
        skip=skip, 
        limit=limit, 
        category=category
    )
    return [AIPromptTemplateResponse.model_validate(template) for template in templates]


@router.get("/templates/{template_id}", response_model=AIPromptTemplateResponse)
async def get_prompt_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get a specific prompt template."""
    service = AIProcessingService(db)
    template = await service.get_prompt_template(template_id)
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
        
    return AIPromptTemplateResponse.model_validate(template)


# Analytics endpoints
@router.get("/analytics", response_model=AIAnalyticsResponse)
async def get_ai_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get AI processing analytics."""
    service = AIProcessingService(db)
    analytics = await service.get_analytics(start_date, end_date)
    return analytics


@router.get("/analytics/performance", response_model=dict)
async def get_performance_metrics(
    period: str = "7d",
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get AI performance metrics."""
    service = AIProcessingService(db)
    metrics = await service.get_performance_metrics(period)
    return metrics


@router.post("/analytics/cleanup")
async def cleanup_old_data(
    days: int = 30,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Clean up old AI processing data."""
    service = AIProcessingService(db)
    cleaned_count = await service.cleanup_old_data(days)
    return {"message": f"Cleaned up {cleaned_count} old records"}
