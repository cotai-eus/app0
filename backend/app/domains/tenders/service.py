"""
Tenders service for business logic.
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.tenders.models import (
    Tender, 
    Quote, 
    QuoteItem, 
    TenderDocument, 
    TenderInvitation, 
    TenderWatch,
    TenderStatus,
    TenderType,
    QuoteStatus
)
from app.domains.tenders.repository import (
    TenderRepository,
    QuoteRepository,
    QuoteItemRepository,
    TenderDocumentRepository,
    TenderInvitationRepository,
    TenderWatchRepository
)
from app.domains.tenders.schemas import (
    TenderCreate,
    TenderUpdate,
    TenderSearchFilters,
    QuoteCreate,
    QuoteUpdate,
    QuoteSearchFilters,
    TenderDocumentCreate,
    TenderInvitationCreate,
    TenderWatchCreate
)
from app.domains.companies.repository import CompanyUserRepository
from app.core.exceptions import (
    BusinessError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError
)
from app.shared.common.base_service import BaseService


class TenderService(BaseService):
    """Service for tender business logic."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.tender_repo = TenderRepository(session)
        self.quote_repo = QuoteRepository(session)
        self.quote_item_repo = QuoteItemRepository(session)
        self.document_repo = TenderDocumentRepository(session)
        self.invitation_repo = TenderInvitationRepository(session)
        self.watch_repo = TenderWatchRepository(session)
        self.company_user_repo = CompanyUserRepository(session)
    
    async def create_tender(
        self,
        tender_data: TenderCreate,
        company_id: UUID,
        created_by_id: UUID
    ) -> Tender:
        """Create a new tender."""
        # Check if user has permission to create tenders for the company
        await self._check_company_admin_permission(company_id, created_by_id)
        
        # Generate unique tender number
        tender_number = await self._generate_tender_number()
        
        # Validate dates
        if tender_data.submission_deadline <= datetime.utcnow():
            raise ValidationError("Submission deadline must be in the future")
        
        if tender_data.opening_date and tender_data.opening_date <= tender_data.submission_deadline:
            raise ValidationError("Opening date must be after submission deadline")
        
        # Create tender
        tender = Tender(
            **tender_data.model_dump(exclude_unset=True),
            company_id=company_id,
            tender_number=tender_number,
            created_by_id=created_by_id,
            updated_by_id=created_by_id
        )
        
        return await self.tender_repo.create(tender)
    
    async def get_tender(self, tender_id: UUID, user_id: UUID) -> Tender:
        """Get tender by ID with permission check."""
        tender = await self.tender_repo.get(tender_id)
        if not tender:
            raise NotFoundError("Tender not found")
        
        # Check if user has access to this tender
        if not tender.is_public:
            await self._check_company_access(tender.company_id, user_id)
        
        return tender
    
    async def update_tender(
        self,
        tender_id: UUID,
        tender_data: TenderUpdate,
        user_id: UUID
    ) -> Tender:
        """Update tender information."""
        tender = await self.tender_repo.get(tender_id)
        if not tender:
            raise NotFoundError("Tender not found")
        
        # Check permissions
        await self._check_company_admin_permission(tender.company_id, user_id)
        
        # Validate that tender can be updated
        if tender.status not in [TenderStatus.DRAFT, TenderStatus.PUBLISHED]:
            raise ValidationError("Cannot update tender in current status")
        
        # Validate dates if provided
        if tender_data.submission_deadline and tender_data.submission_deadline <= datetime.utcnow():
            raise ValidationError("Submission deadline must be in the future")
        
        # Update tender
        update_data = tender_data.model_dump(exclude_unset=True)
        update_data["updated_by_id"] = user_id
        
        return await self.tender_repo.update(tender_id, update_data)
    
    async def delete_tender(self, tender_id: UUID, user_id: UUID) -> bool:
        """Soft delete tender."""
        tender = await self.tender_repo.get(tender_id)
        if not tender:
            raise NotFoundError("Tender not found")
        
        await self._check_company_admin_permission(tender.company_id, user_id)
        
        # Can only delete draft tenders
        if tender.status != TenderStatus.DRAFT:
            raise ValidationError("Can only delete draft tenders")
        
        await self.tender_repo.soft_delete(tender_id, user_id)
        return True
    
    async def publish_tender(self, tender_id: UUID, user_id: UUID) -> Tender:
        """Publish a tender."""
        tender = await self.tender_repo.get(tender_id)
        if not tender:
            raise NotFoundError("Tender not found")
        
        await self._check_company_admin_permission(tender.company_id, user_id)
        
        if tender.status != TenderStatus.DRAFT:
            raise ValidationError("Can only publish draft tenders")
        
        # Validate tender is ready for publishing
        if not tender.title or not tender.description:
            raise ValidationError("Tender must have title and description")
        
        if tender.submission_deadline <= datetime.utcnow():
            raise ValidationError("Submission deadline must be in the future")
        
        return await self.tender_repo.update_status(tender_id, TenderStatus.PUBLISHED)
    
    async def close_tender(self, tender_id: UUID, user_id: UUID) -> Tender:
        """Close a tender."""
        tender = await self.tender_repo.get(tender_id)
        if not tender:
            raise NotFoundError("Tender not found")
        
        await self._check_company_admin_permission(tender.company_id, user_id)
        
        if tender.status not in [TenderStatus.PUBLISHED, TenderStatus.ACTIVE]:
            raise ValidationError("Can only close published or active tenders")
        
        return await self.tender_repo.update_status(tender_id, TenderStatus.CLOSED)
    
    async def search_tenders(
        self,
        filters: TenderSearchFilters,
        user_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Tender]:
        """Search tenders with filters."""
        return await self.tender_repo.search_tenders(
            search_query=filters.search_query,
            tender_type=filters.tender_type,
            category=filters.category,
            status=filters.status,
            min_budget=filters.min_budget,
            max_budget=filters.max_budget,
            currency=filters.currency,
            deadline_from=filters.deadline_from,
            deadline_to=filters.deadline_to,
            is_public=filters.is_public,
            company_id=filters.company_id,
            skip=skip,
            limit=limit
        )
    
    async def get_public_tenders(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[TenderStatus] = None
    ) -> List[Tender]:
        """Get public tenders."""
        return await self.tender_repo.get_public_tenders(skip, limit, status)
    
    async def get_company_tenders(
        self,
        company_id: UUID,
        user_id: UUID,
        status: Optional[TenderStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Tender]:
        """Get tenders for a company."""
        await self._check_company_access(company_id, user_id)
        
        return await self.tender_repo.get_company_tenders(
            company_id, status, skip, limit
        )
    
    async def get_tender_stats(self, company_id: UUID, user_id: UUID) -> Dict[str, Any]:
        """Get tender statistics for a company."""
        await self._check_company_access(company_id, user_id)
        return await self.tender_repo.get_tender_stats(company_id)
    
    # Quote Management
    async def create_quote(
        self,
        tender_id: UUID,
        quote_data: QuoteCreate,
        company_id: UUID,
        created_by_id: UUID
    ) -> Quote:
        """Create a new quote."""
        # Check if user has permission to create quotes for the company
        await self._check_company_access(company_id, created_by_id)
        
        # Get tender and validate
        tender = await self.tender_repo.get(tender_id)
        if not tender:
            raise NotFoundError("Tender not found")
        
        if tender.status not in [TenderStatus.PUBLISHED, TenderStatus.ACTIVE]:
            raise ValidationError("Cannot quote on this tender")
        
        if tender.submission_deadline <= datetime.utcnow():
            raise ValidationError("Tender submission deadline has passed")
        
        # Check if company can submit quote
        if not tender.is_public:
            # Check if company is invited
            invitation = await self.invitation_repo.get_by_tender_and_company(tender_id, company_id)
            if not invitation or invitation.status != "accepted":
                raise PermissionDeniedError("Company not invited to this tender")
        
        # Check if quote already exists
        existing_quote = await self.quote_repo.get_by_tender_and_company(tender_id, company_id)
        if existing_quote:
            raise ValidationError("Quote already exists for this tender")
        
        # Create quote
        quote = Quote(
            tender_id=tender_id,
            company_id=company_id,
            **quote_data.model_dump(exclude={'items'}),
            created_by_id=created_by_id,
            updated_by_id=created_by_id
        )
        
        quote = await self.quote_repo.create(quote)
        
        # Create quote items
        for item_data in quote_data.items:
            quote_item = QuoteItem(
                quote_id=quote.id,
                **item_data.model_dump()
            )
            await self.quote_item_repo.create(quote_item)
        
        return quote
    
    async def update_quote(
        self,
        quote_id: UUID,
        quote_data: QuoteUpdate,
        user_id: UUID
    ) -> Quote:
        """Update quote information."""
        quote = await self.quote_repo.get(quote_id)
        if not quote:
            raise NotFoundError("Quote not found")
        
        # Check permissions
        await self._check_company_access(quote.company_id, user_id)
        
        # Can only update draft quotes
        if quote.status != QuoteStatus.DRAFT:
            raise ValidationError("Can only update draft quotes")
        
        # Check if tender is still open
        tender = await self.tender_repo.get(quote.tender_id)
        if tender and tender.submission_deadline <= datetime.utcnow():
            raise ValidationError("Tender submission deadline has passed")
        
        # Update quote
        update_data = quote_data.model_dump(exclude_unset=True)
        update_data["updated_by_id"] = user_id
        
        return await self.quote_repo.update(quote_id, update_data)
    
    async def submit_quote(self, quote_id: UUID, user_id: UUID) -> Quote:
        """Submit a quote."""
        quote = await self.quote_repo.get(quote_id)
        if not quote:
            raise NotFoundError("Quote not found")
        
        await self._check_company_access(quote.company_id, user_id)
        
        if quote.status != QuoteStatus.DRAFT:
            raise ValidationError("Can only submit draft quotes")
        
        # Check if tender is still open
        tender = await self.tender_repo.get(quote.tender_id)
        if tender and tender.submission_deadline <= datetime.utcnow():
            raise ValidationError("Tender submission deadline has passed")
        
        # Validate quote has items
        items = await self.quote_item_repo.get_quote_items(quote_id)
        if not items:
            raise ValidationError("Quote must have at least one item")
        
        return await self.quote_repo.submit_quote(quote_id)
    
    async def get_quote(self, quote_id: UUID, user_id: UUID) -> Quote:
        """Get quote by ID with permission check."""
        quote = await self.quote_repo.get_with_items(quote_id)
        if not quote:
            raise NotFoundError("Quote not found")
        
        # Check if user has access to this quote
        # Either company member or tender owner
        try:
            await self._check_company_access(quote.company_id, user_id)
        except PermissionDeniedError:
            # Check if user is from tender company
            tender = await self.tender_repo.get(quote.tender_id)
            if tender:
                await self._check_company_access(tender.company_id, user_id)
            else:
                raise
        
        return quote
    
    async def get_tender_quotes(
        self,
        tender_id: UUID,
        user_id: UUID,
        status: Optional[QuoteStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Quote]:
        """Get quotes for a tender."""
        tender = await self.tender_repo.get(tender_id)
        if not tender:
            raise NotFoundError("Tender not found")
        
        # Check if user has access to view quotes
        await self._check_company_access(tender.company_id, user_id)
        
        return await self.quote_repo.get_tender_quotes(tender_id, status, skip, limit)
    
    async def get_company_quotes(
        self,
        company_id: UUID,
        user_id: UUID,
        status: Optional[QuoteStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Quote]:
        """Get quotes for a company."""
        await self._check_company_access(company_id, user_id)
        
        return await self.quote_repo.get_company_quotes(company_id, status, skip, limit)
    
    async def get_quote_stats(self, company_id: UUID, user_id: UUID) -> Dict[str, Any]:
        """Get quote statistics for a company."""
        await self._check_company_access(company_id, user_id)
        return await self.quote_repo.get_quote_stats(company_id)
    
    # Document Management
    async def create_tender_document(
        self,
        tender_id: UUID,
        document_data: TenderDocumentCreate,
        user_id: UUID
    ) -> TenderDocument:
        """Create tender document."""
        tender = await self.tender_repo.get(tender_id)
        if not tender:
            raise NotFoundError("Tender not found")
        
        await self._check_company_admin_permission(tender.company_id, user_id)
        
        document = TenderDocument(
            tender_id=tender_id,
            **document_data.model_dump(exclude_unset=True),
            created_by_id=user_id,
            updated_by_id=user_id
        )
        
        return await self.document_repo.create(document)
    
    async def get_tender_documents(
        self,
        tender_id: UUID,
        user_id: Optional[UUID] = None,
        document_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[TenderDocument]:
        """Get tender documents."""
        tender = await self.tender_repo.get(tender_id)
        if not tender:
            raise NotFoundError("Tender not found")
        
        # For private tenders, check access
        is_public = None
        if not tender.is_public and user_id:
            try:
                await self._check_company_access(tender.company_id, user_id)
                # User is from tender company, can see all documents
            except PermissionDeniedError:
                # User is not from tender company, only public documents
                is_public = True
        elif not tender.is_public:
            # No user provided and tender is private, only public documents
            is_public = True
        
        return await self.document_repo.get_tender_documents(
            tender_id=tender_id,
            document_type=document_type,
            is_public=is_public,
            skip=skip,
            limit=limit
        )
    
    # Watch/Follow Management
    async def watch_tender(
        self,
        tender_id: UUID,
        user_id: UUID,
        watch_data: TenderWatchCreate
    ) -> TenderWatch:
        """Add tender to user's watch list."""
        tender = await self.tender_repo.get(tender_id)
        if not tender:
            raise NotFoundError("Tender not found")
        
        # Check if already watching
        existing_watch = await self.watch_repo.get_by_tender_and_user(tender_id, user_id)
        if existing_watch:
            # Update existing watch
            existing_watch.notifications_enabled = watch_data.notifications_enabled
            existing_watch.updated_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(existing_watch)
            return existing_watch
        
        # Create new watch
        watch = TenderWatch(
            tender_id=tender_id,
            user_id=user_id,
            **watch_data.model_dump()
        )
        
        return await self.watch_repo.create(watch)
    
    async def unwatch_tender(self, tender_id: UUID, user_id: UUID) -> bool:
        """Remove tender from user's watch list."""
        watch = await self.watch_repo.get_by_tender_and_user(tender_id, user_id)
        if watch:
            await self.watch_repo.delete(watch.id)
            return True
        return False
    
    async def get_user_watches(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[TenderWatch]:
        """Get user's tender watches."""
        return await self.watch_repo.get_user_watches(user_id, skip, limit)
    
    # Helper methods
    async def _generate_tender_number(self) -> str:
        """Generate unique tender number."""
        import random
        import string
        
        while True:
            # Generate format: TND-YYYY-XXXXXX
            year = datetime.utcnow().year
            random_part = ''.join(random.choices(string.digits, k=6))
            tender_number = f"TND-{year}-{random_part}"
            
            # Check if number already exists
            existing = await self.tender_repo.get_by_tender_number(tender_number)
            if not existing:
                return tender_number
    
    async def _check_company_access(self, company_id: UUID, user_id: UUID):
        """Check if user has access to company."""
        company_user = await self.company_user_repo.get_by_company_and_user(
            company_id, user_id
        )
        if not company_user or not company_user.is_active:
            raise PermissionDeniedError("Access denied to this company")
        return company_user
    
    async def _check_company_admin_permission(self, company_id: UUID, user_id: UUID):
        """Check if user has admin permission in company."""
        company_user = await self._check_company_access(company_id, user_id)
        if company_user.role not in ["owner", "admin", "manager"]:
            raise PermissionDeniedError("Admin permission required")
        return company_user
