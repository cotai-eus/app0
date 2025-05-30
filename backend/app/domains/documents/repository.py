"""
Document repository for CRUD operations.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.shared.common.repository import BaseRepository
from app.domains.documents.models import (
    Document, 
    TextExtraction, 
    AIProcessingJob,
    TenderAIAnalysis,
    AIPromptTemplate,
    AIResponseCache,
    DocumentType,
    ProcessingStatus,
    ExtractionType
)


class DocumentRepository(BaseRepository[Document]):
    """Repository for document operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Document, session)
    
    async def get_by_company(
        self, 
        company_id: UUID,
        document_type: Optional[DocumentType] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Document]:
        """Get documents by company."""
        query = select(Document).where(
            and_(
                Document.company_id == company_id,
                Document.deleted_at.is_(None)
            )
        )
        
        if document_type:
            query = query.where(Document.document_type == document_type)
            
        query = query.order_by(desc(Document.created_at)).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_user(
        self, 
        user_id: UUID,
        include_shared: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[Document]:
        """Get documents by user with optional shared documents."""
        conditions = [Document.uploaded_by == user_id]
        
        if include_shared:
            # Include documents shared with user
            conditions.append(Document.shared_with.contains([str(user_id)]))
        
        query = select(Document).where(
            and_(
                or_(*conditions),
                Document.deleted_at.is_(None)
            )
        ).order_by(desc(Document.created_at)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def search_documents(
        self,
        company_id: UUID,
        search_query: str,
        document_type: Optional[DocumentType] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Document]:
        """Search documents by content and metadata."""
        query = select(Document).where(
            and_(
                Document.company_id == company_id,
                Document.deleted_at.is_(None),
                or_(
                    Document.filename.ilike(f"%{search_query}%"),
                    Document.extracted_text.ilike(f"%{search_query}%"),
                    Document.doc_metadata.astext.ilike(f"%{search_query}%")
                )
            )
        )
        
        if document_type:
            query = query.where(Document.document_type == document_type)
            
        if date_from:
            query = query.where(Document.created_at >= date_from)
            
        if date_to:
            query = query.where(Document.created_at <= date_to)
            
        query = query.order_by(desc(Document.created_at)).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_pending_ai_processing(self, limit: int = 50) -> List[Document]:
        """Get documents pending AI processing."""
        query = select(Document).where(
            and_(
                Document.ai_processing_status == ProcessingStatus.PENDING,
                Document.deleted_at.is_(None)
            )
        ).order_by(Document.created_at).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update_ai_processing_status(
        self, 
        document_id: UUID, 
        status: ProcessingStatus,
        confidence_score: Optional[float] = None,
        ai_insights: Optional[Dict[str, Any]] = None
    ) -> Optional[Document]:
        """Update AI processing status and results."""
        document = await self.get_by_id(document_id)
        if not document:
            return None
        
        update_data = {
            'ai_processing_status': status,
            'ai_processed_at': datetime.utcnow()
        }
        
        if confidence_score is not None:
            update_data['confidence_score'] = confidence_score
            
        if ai_insights:
            update_data['ai_insights'] = ai_insights
        
        return await self.update(document, update_data)


class TextExtractionRepository(BaseRepository[TextExtraction]):
    """Repository for text extraction operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(TextExtraction, session)
    
    async def get_by_document(
        self, 
        document_id: UUID,
        extraction_type: Optional[ExtractionType] = None
    ) -> List[TextExtraction]:
        """Get text extractions for a document."""
        query = select(TextExtraction).where(
            and_(
                TextExtraction.document_id == document_id,
                TextExtraction.deleted_at.is_(None)
            )
        )
        
        if extraction_type:
            query = query.where(TextExtraction.extraction_type == extraction_type)
            
        query = query.order_by(desc(TextExtraction.created_at))
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_latest_by_document(
        self, 
        document_id: UUID,
        extraction_type: ExtractionType
    ) -> Optional[TextExtraction]:
        """Get latest text extraction for a document and type."""
        query = select(TextExtraction).where(
            and_(
                TextExtraction.document_id == document_id,
                TextExtraction.extraction_type == extraction_type,
                TextExtraction.deleted_at.is_(None)
            )
        ).order_by(desc(TextExtraction.created_at)).limit(1)
        
        result = await self.session.execute(query)
        return result.scalars().first()


class AIProcessingJobRepository(BaseRepository[AIProcessingJob]):
    """Repository for AI processing job operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(AIProcessingJob, session)
    
    async def get_by_document(
        self, 
        document_id: UUID,
        status: Optional[ProcessingStatus] = None
    ) -> List[AIProcessingJob]:
        """Get AI processing jobs for a document."""
        query = select(AIProcessingJob).where(
            AIProcessingJob.document_id == document_id
        )
        
        if status:
            query = query.where(AIProcessingJob.status == status)
            
        query = query.order_by(desc(AIProcessingJob.created_at))
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_pending_jobs(self, limit: int = 50) -> List[AIProcessingJob]:
        """Get pending AI processing jobs."""
        query = select(AIProcessingJob).where(
            AIProcessingJob.status == ProcessingStatus.PENDING
        ).order_by(AIProcessingJob.created_at).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update_job_status(
        self, 
        job_id: UUID, 
        status: ProcessingStatus,
        result_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> Optional[AIProcessingJob]:
        """Update job status and results."""
        job = await self.get_by_id(job_id)
        if not job:
            return None
        
        update_data = {
            'status': status,
            'updated_at': datetime.utcnow()
        }
        
        if status == ProcessingStatus.COMPLETED:
            update_data['completed_at'] = datetime.utcnow()
            if result_data:
                update_data['result_data'] = result_data
                
        elif status == ProcessingStatus.FAILED:
            update_data['completed_at'] = datetime.utcnow()
            if error_message:
                update_data['error_message'] = error_message
        
        return await self.update(job, update_data)


class TenderAIAnalysisRepository(BaseRepository[TenderAIAnalysis]):
    """Repository for tender AI analysis operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(TenderAIAnalysis, session)
    
    async def get_by_tender(self, tender_id: UUID) -> List[TenderAIAnalysis]:
        """Get AI analyses for a tender."""
        query = select(TenderAIAnalysis).where(
            and_(
                TenderAIAnalysis.tender_id == tender_id,
                TenderAIAnalysis.deleted_at.is_(None)
            )
        ).order_by(desc(TenderAIAnalysis.created_at))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_latest_by_tender(self, tender_id: UUID) -> Optional[TenderAIAnalysis]:
        """Get latest AI analysis for a tender."""
        query = select(TenderAIAnalysis).where(
            and_(
                TenderAIAnalysis.tender_id == tender_id,
                TenderAIAnalysis.deleted_at.is_(None)
            )
        ).order_by(desc(TenderAIAnalysis.created_at)).limit(1)
        
        result = await self.session.execute(query)
        return result.scalars().first()
    
    async def get_by_company_analysis(
        self, 
        company_id: UUID,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[TenderAIAnalysis]:
        """Get tender analyses for company with date filtering."""
        query = select(TenderAIAnalysis).join(
            TenderAIAnalysis.tender
        ).where(
            and_(
                TenderAIAnalysis.tender.has(company_id=company_id),
                TenderAIAnalysis.deleted_at.is_(None)
            )
        )
        
        if date_from:
            query = query.where(TenderAIAnalysis.created_at >= date_from)
            
        if date_to:
            query = query.where(TenderAIAnalysis.created_at <= date_to)
            
        query = query.order_by(desc(TenderAIAnalysis.created_at))
        result = await self.session.execute(query)
        return result.scalars().all()


class AIPromptTemplateRepository(BaseRepository[AIPromptTemplate]):
    """Repository for AI prompt template operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(AIPromptTemplate, session)
    
    async def get_by_company(
        self, 
        company_id: UUID,
        category: Optional[str] = None,
        is_active: bool = True
    ) -> List[AIPromptTemplate]:
        """Get prompt templates by company."""
        query = select(AIPromptTemplate).where(
            and_(
                AIPromptTemplate.company_id == company_id,
                AIPromptTemplate.deleted_at.is_(None)
            )
        )
        
        if category:
            query = query.where(AIPromptTemplate.category == category)
            
        if is_active:
            query = query.where(AIPromptTemplate.is_active == True)
            
        query = query.order_by(AIPromptTemplate.name)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_global_templates(
        self, 
        category: Optional[str] = None,
        is_active: bool = True
    ) -> List[AIPromptTemplate]:
        """Get global (system-wide) prompt templates."""
        query = select(AIPromptTemplate).where(
            and_(
                AIPromptTemplate.company_id.is_(None),
                AIPromptTemplate.deleted_at.is_(None)
            )
        )
        
        if category:
            query = query.where(AIPromptTemplate.category == category)
            
        if is_active:
            query = query.where(AIPromptTemplate.is_active == True)
            
        query = query.order_by(AIPromptTemplate.name)
        result = await self.session.execute(query)
        return result.scalars().all()


class AIResponseCacheRepository(BaseRepository[AIResponseCache]):
    """Repository for AI response cache operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(AIResponseCache, session)
    
    async def get_cached_response(
        self, 
        prompt_hash: str,
        model: str,
        company_id: Optional[UUID] = None
    ) -> Optional[AIResponseCache]:
        """Get cached AI response by prompt hash and model."""
        query = select(AIResponseCache).where(
            and_(
                AIResponseCache.prompt_hash == prompt_hash,
                AIResponseCache.model == model,
                AIResponseCache.expires_at > datetime.utcnow()
            )
        )
        
        if company_id:
            query = query.where(AIResponseCache.company_id == company_id)
        else:
            query = query.where(AIResponseCache.company_id.is_(None))
            
        result = await self.session.execute(query)
        return result.scalars().first()
    
    async def cleanup_expired(self) -> int:
        """Clean up expired cache entries."""
        expired_entries = await self.session.execute(
            select(AIResponseCache).where(
                AIResponseCache.expires_at <= datetime.utcnow()
            )
        )
        
        count = 0
        for entry in expired_entries.scalars():
            await self.session.delete(entry)
            count += 1
            
        return count
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = await self.session.execute(
            select(func.count(AIResponseCache.id))
        )
        
        expired = await self.session.execute(
            select(func.count(AIResponseCache.id)).where(
                AIResponseCache.expires_at <= datetime.utcnow()
            )
        )
        
        return {
            'total_entries': total.scalar() or 0,
            'expired_entries': expired.scalar() or 0,
            'active_entries': (total.scalar() or 0) - (expired.scalar() or 0)
        }
