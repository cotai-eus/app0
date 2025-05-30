"""
Tenders repository for database operations.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, or_, select, update, delete, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domains.tenders.models import (
    Tender,
    TenderDocument,
    Quote,
    QuoteItem,
    TenderInvitation,
    TenderWatch,
    TenderStatus,
    TenderType,
    QuoteStatus
)
from app.shared.common.base_repository import BaseRepository


class TenderRepository(BaseRepository[Tender]):
    """Repository for tender operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Tender, session)
    
    async def get_by_tender_number(self, tender_number: str) -> Optional[Tender]:
        """Get tender by tender number."""
        result = await self.session.execute(
            select(Tender).where(
                and_(
                    Tender.tender_number == tender_number,
                    Tender.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_company_tenders(
        self,
        company_id: UUID,
        status: Optional[TenderStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Tender]:
        """Get tenders by company."""
        query = select(Tender).where(
            and_(
                Tender.company_id == company_id,
                Tender.deleted_at.is_(None)
            )
        )
        
        if status:
            query = query.where(Tender.status == status)
        
        query = query.offset(skip).limit(limit).order_by(desc(Tender.created_at))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def search_tenders(
        self,
        search_query: Optional[str] = None,
        tender_type: Optional[TenderType] = None,
        category: Optional[str] = None,
        status: Optional[TenderStatus] = None,
        min_budget: Optional[Decimal] = None,
        max_budget: Optional[Decimal] = None,
        currency: Optional[str] = None,
        deadline_from: Optional[datetime] = None,
        deadline_to: Optional[datetime] = None,
        is_public: Optional[bool] = None,
        company_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Tender]:
        """Search tenders with filters."""
        query = select(Tender).where(Tender.deleted_at.is_(None))
        
        if search_query:
            search_filter = or_(
                Tender.title.ilike(f"%{search_query}%"),
                Tender.description.ilike(f"%{search_query}%"),
                Tender.tender_number.ilike(f"%{search_query}%")
            )
            query = query.where(search_filter)
        
        if tender_type:
            query = query.where(Tender.tender_type == tender_type)
        
        if category:
            query = query.where(Tender.category == category)
        
        if status:
            query = query.where(Tender.status == status)
        
        if min_budget is not None:
            query = query.where(Tender.estimated_budget >= min_budget)
        
        if max_budget is not None:
            query = query.where(Tender.estimated_budget <= max_budget)
        
        if currency:
            query = query.where(Tender.currency == currency)
        
        if deadline_from:
            query = query.where(Tender.submission_deadline >= deadline_from)
        
        if deadline_to:
            query = query.where(Tender.submission_deadline <= deadline_to)
        
        if is_public is not None:
            query = query.where(Tender.is_public == is_public)
        
        if company_id:
            query = query.where(Tender.company_id == company_id)
        
        query = query.offset(skip).limit(limit).order_by(desc(Tender.created_at))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_public_tenders(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[TenderStatus] = None
    ) -> List[Tender]:
        """Get public tenders."""
        query = select(Tender).where(
            and_(
                Tender.is_public == True,
                Tender.deleted_at.is_(None)
            )
        )
        
        if status:
            query = query.where(Tender.status == status)
        else:
            # Default to active tenders
            query = query.where(Tender.status.in_([TenderStatus.PUBLISHED, TenderStatus.ACTIVE]))
        
        query = query.offset(skip).limit(limit).order_by(desc(Tender.published_at))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_expiring_tenders(
        self,
        days_ahead: int = 7,
        company_id: Optional[UUID] = None
    ) -> List[Tender]:
        """Get tenders expiring within specified days."""
        expiry_date = datetime.utcnow() + timedelta(days=days_ahead)
        
        query = select(Tender).where(
            and_(
                Tender.submission_deadline <= expiry_date,
                Tender.submission_deadline > datetime.utcnow(),
                Tender.status.in_([TenderStatus.PUBLISHED, TenderStatus.ACTIVE]),
                Tender.deleted_at.is_(None)
            )
        )
        
        if company_id:
            query = query.where(Tender.company_id == company_id)
        
        query = query.order_by(asc(Tender.submission_deadline))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update_status(self, tender_id: UUID, status: TenderStatus) -> Optional[Tender]:
        """Update tender status."""
        tender = await self.get(tender_id)
        if tender:
            tender.status = status
            if status == TenderStatus.PUBLISHED and not tender.published_at:
                tender.published_at = datetime.utcnow()
            tender.updated_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(tender)
        return tender
    
    async def get_tender_stats(self, company_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Get tender statistics."""
        base_query = select(func.count(Tender.id)).where(Tender.deleted_at.is_(None))
        
        if company_id:
            base_query = base_query.where(Tender.company_id == company_id)
        
        # Total tenders
        total_count = await self.session.execute(base_query)
        
        # Active tenders
        active_count = await self.session.execute(
            base_query.where(Tender.status.in_([TenderStatus.PUBLISHED, TenderStatus.ACTIVE]))
        )
        
        # Draft tenders
        draft_count = await self.session.execute(
            base_query.where(Tender.status == TenderStatus.DRAFT)
        )
        
        # Closed tenders
        closed_count = await self.session.execute(
            base_query.where(Tender.status.in_([TenderStatus.CLOSED, TenderStatus.AWARDED]))
        )
        
        return {
            "total_tenders": total_count.scalar() or 0,
            "active_tenders": active_count.scalar() or 0,
            "draft_tenders": draft_count.scalar() or 0,
            "closed_tenders": closed_count.scalar() or 0,
        }


class QuoteRepository(BaseRepository[Quote]):
    """Repository for quote operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Quote, session)
    
    async def get_tender_quotes(
        self,
        tender_id: UUID,
        status: Optional[QuoteStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Quote]:
        """Get quotes for a tender."""
        query = select(Quote).where(
            and_(
                Quote.tender_id == tender_id,
                Quote.deleted_at.is_(None)
            )
        )
        
        if status:
            query = query.where(Quote.status == status)
        
        query = query.offset(skip).limit(limit).order_by(desc(Quote.created_at))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_company_quotes(
        self,
        company_id: UUID,
        status: Optional[QuoteStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Quote]:
        """Get quotes by company."""
        query = select(Quote).where(
            and_(
                Quote.company_id == company_id,
                Quote.deleted_at.is_(None)
            )
        )
        
        if status:
            query = query.where(Quote.status == status)
        
        query = query.offset(skip).limit(limit).order_by(desc(Quote.created_at))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_tender_and_company(
        self,
        tender_id: UUID,
        company_id: UUID
    ) -> Optional[Quote]:
        """Get quote by tender and company."""
        result = await self.session.execute(
            select(Quote).where(
                and_(
                    Quote.tender_id == tender_id,
                    Quote.company_id == company_id,
                    Quote.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_with_items(self, quote_id: UUID) -> Optional[Quote]:
        """Get quote with its items."""
        result = await self.session.execute(
            select(Quote)
            .options(selectinload(Quote.items))
            .where(
                and_(
                    Quote.id == quote_id,
                    Quote.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def submit_quote(self, quote_id: UUID) -> Optional[Quote]:
        """Submit a quote."""
        quote = await self.get(quote_id)
        if quote and quote.status == QuoteStatus.DRAFT:
            quote.status = QuoteStatus.SUBMITTED
            quote.submitted_at = datetime.utcnow()
            quote.updated_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(quote)
        return quote
    
    async def update_status(self, quote_id: UUID, status: QuoteStatus) -> Optional[Quote]:
        """Update quote status."""
        quote = await self.get(quote_id)
        if quote:
            quote.status = status
            quote.updated_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(quote)
        return quote
    
    async def get_quote_stats(self, company_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Get quote statistics."""
        base_query = select(func.count(Quote.id)).where(Quote.deleted_at.is_(None))
        
        if company_id:
            base_query = base_query.where(Quote.company_id == company_id)
        
        # Total quotes
        total_count = await self.session.execute(base_query)
        
        # Submitted quotes
        submitted_count = await self.session.execute(
            base_query.where(Quote.status == QuoteStatus.SUBMITTED)
        )
        
        # Draft quotes
        draft_count = await self.session.execute(
            base_query.where(Quote.status == QuoteStatus.DRAFT)
        )
        
        # Awarded quotes
        awarded_count = await self.session.execute(
            base_query.where(Quote.status == QuoteStatus.AWARDED)
        )
        
        # Total value
        value_query = select(func.sum(Quote.total_amount)).where(Quote.deleted_at.is_(None))
        if company_id:
            value_query = value_query.where(Quote.company_id == company_id)
        
        total_value_result = await self.session.execute(value_query)
        total_value = total_value_result.scalar() or Decimal('0')
        
        total_quotes = total_count.scalar() or 0
        average_value = total_value / total_quotes if total_quotes > 0 else Decimal('0')
        
        return {
            "total_quotes": total_quotes,
            "submitted_quotes": submitted_count.scalar() or 0,
            "draft_quotes": draft_count.scalar() or 0,
            "awarded_quotes": awarded_count.scalar() or 0,
            "total_value": total_value,
            "average_quote_value": average_value,
        }


class QuoteItemRepository(BaseRepository[QuoteItem]):
    """Repository for quote item operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(QuoteItem, session)
    
    async def get_quote_items(self, quote_id: UUID) -> List[QuoteItem]:
        """Get all items for a quote."""
        result = await self.session.execute(
            select(QuoteItem)
            .where(QuoteItem.quote_id == quote_id)
            .order_by(asc(QuoteItem.created_at))
        )
        return result.scalars().all()
    
    async def delete_quote_items(self, quote_id: UUID) -> int:
        """Delete all items for a quote."""
        result = await self.session.execute(
            delete(QuoteItem).where(QuoteItem.quote_id == quote_id)
        )
        await self.session.commit()
        return result.rowcount


class TenderDocumentRepository(BaseRepository[TenderDocument]):
    """Repository for tender document operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(TenderDocument, session)
    
    async def get_tender_documents(
        self,
        tender_id: UUID,
        document_type: Optional[str] = None,
        is_public: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[TenderDocument]:
        """Get tender documents."""
        query = select(TenderDocument).where(
            and_(
                TenderDocument.tender_id == tender_id,
                TenderDocument.deleted_at.is_(None)
            )
        )
        
        if document_type:
            query = query.where(TenderDocument.document_type == document_type)
        
        if is_public is not None:
            query = query.where(TenderDocument.is_public == is_public)
        
        query = query.offset(skip).limit(limit).order_by(
            asc(TenderDocument.display_order),
            asc(TenderDocument.created_at)
        )
        
        result = await self.session.execute(query)
        return result.scalars().all()


class TenderInvitationRepository(BaseRepository[TenderInvitation]):
    """Repository for tender invitation operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(TenderInvitation, session)
    
    async def get_tender_invitations(
        self,
        tender_id: UUID,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[TenderInvitation]:
        """Get tender invitations."""
        query = select(TenderInvitation).where(TenderInvitation.tender_id == tender_id)
        
        if status:
            query = query.where(TenderInvitation.status == status)
        
        query = query.offset(skip).limit(limit).order_by(desc(TenderInvitation.created_at))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_company_invitations(
        self,
        company_id: UUID,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[TenderInvitation]:
        """Get company invitations."""
        query = select(TenderInvitation).where(TenderInvitation.company_id == company_id)
        
        if status:
            query = query.where(TenderInvitation.status == status)
        
        query = query.offset(skip).limit(limit).order_by(desc(TenderInvitation.created_at))
        
        result = await self.session.execute(query)
        return result.scalars().all()


class TenderWatchRepository(BaseRepository[TenderWatch]):
    """Repository for tender watch operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(TenderWatch, session)
    
    async def get_by_tender_and_user(
        self,
        tender_id: UUID,
        user_id: UUID
    ) -> Optional[TenderWatch]:
        """Get tender watch by tender and user."""
        result = await self.session.execute(
            select(TenderWatch).where(
                and_(
                    TenderWatch.tender_id == tender_id,
                    TenderWatch.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_user_watches(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[TenderWatch]:
        """Get user's tender watches."""
        result = await self.session.execute(
            select(TenderWatch)
            .where(TenderWatch.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(desc(TenderWatch.created_at))
        )
        return result.scalars().all()
    
    async def get_tender_watchers(
        self,
        tender_id: UUID,
        notifications_enabled: Optional[bool] = None
    ) -> List[TenderWatch]:
        """Get users watching a tender."""
        query = select(TenderWatch).where(TenderWatch.tender_id == tender_id)
        
        if notifications_enabled is not None:
            query = query.where(TenderWatch.notifications_enabled == notifications_enabled)
        
        result = await self.session.execute(query)
        return result.scalars().all()
