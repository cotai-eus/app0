"""
Tenders domain schemas.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.shared.common.base_schemas import BaseSchema, TimestampSchema
from app.domains.tenders.models import TenderStatus, TenderType, QuoteStatus


# Tender schemas
class TenderBase(BaseModel):
    """Base tender schema with common fields."""
    
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    tender_type: TenderType
    category: Optional[str] = Field(None, max_length=100)
    subcategory: Optional[str] = Field(None, max_length=100)
    
    # Timeline
    submission_deadline: datetime
    opening_date: Optional[datetime] = None
    closing_date: Optional[datetime] = None
    
    # Budget information
    estimated_budget: Optional[Decimal] = Field(None, ge=0)
    minimum_budget: Optional[Decimal] = Field(None, ge=0)
    maximum_budget: Optional[Decimal] = Field(None, ge=0)
    currency: str = Field(default="USD", max_length=10)
    
    # Requirements
    requirements: Optional[Dict[str, Any]] = None
    evaluation_criteria: Optional[Dict[str, Any]] = None
    terms_and_conditions: Optional[str] = None
    
    # Delivery
    delivery_location: Optional[str] = Field(None, max_length=255)
    delivery_deadline: Optional[datetime] = None
    
    # Contact
    contact_person: Optional[str] = Field(None, max_length=255)
    contact_email: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=20)
    
    # Settings
    is_public: bool = Field(default=True)
    requires_registration: bool = Field(default=False)
    max_quotes: Optional[int] = Field(None, ge=1)
    
    # Metadata
    tags: Optional[List[str]] = None


class TenderCreate(TenderBase):
    """Schema for creating a new tender."""
    pass


class TenderUpdate(BaseModel):
    """Schema for updating tender information."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    tender_type: Optional[TenderType] = None
    category: Optional[str] = Field(None, max_length=100)
    subcategory: Optional[str] = Field(None, max_length=100)
    
    submission_deadline: Optional[datetime] = None
    opening_date: Optional[datetime] = None
    closing_date: Optional[datetime] = None
    
    estimated_budget: Optional[Decimal] = Field(None, ge=0)
    minimum_budget: Optional[Decimal] = Field(None, ge=0)
    maximum_budget: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=10)
    
    requirements: Optional[Dict[str, Any]] = None
    evaluation_criteria: Optional[Dict[str, Any]] = None
    terms_and_conditions: Optional[str] = None
    
    delivery_location: Optional[str] = Field(None, max_length=255)
    delivery_deadline: Optional[datetime] = None
    
    contact_person: Optional[str] = Field(None, max_length=255)
    contact_email: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=20)
    
    is_public: Optional[bool] = None
    requires_registration: Optional[bool] = None
    max_quotes: Optional[int] = Field(None, ge=1)
    
    tags: Optional[List[str]] = None


class TenderResponse(TenderBase, TimestampSchema):
    """Schema for tender response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tender_number: str
    company_id: UUID
    status: TenderStatus
    published_at: Optional[datetime] = None
    created_by_id: Optional[UUID] = None
    updated_by_id: Optional[UUID] = None


class TenderDetail(TenderResponse):
    """Detailed tender schema with additional information."""
    
    metadata: Optional[Dict[str, Any]] = None
    quote_count: Optional[int] = 0
    can_submit_quote: Optional[bool] = None


class TenderSummary(BaseModel):
    """Tender summary schema for listings."""
    
    id: UUID
    title: str
    tender_number: str
    tender_type: TenderType
    category: Optional[str] = None
    status: TenderStatus
    submission_deadline: datetime
    estimated_budget: Optional[Decimal] = None
    currency: str
    company_name: Optional[str] = None
    is_public: bool
    quote_count: Optional[int] = 0


# Quote schemas
class QuoteItemBase(BaseModel):
    """Base quote item schema."""
    
    description: str = Field(..., min_length=1)
    quantity: Decimal = Field(..., gt=0)
    unit: str = Field(..., max_length=50)
    unit_price: Decimal = Field(..., ge=0)
    total_price: Decimal = Field(..., ge=0)
    notes: Optional[str] = None


class QuoteItemCreate(QuoteItemBase):
    """Schema for creating quote item."""
    pass


class QuoteItemUpdate(BaseModel):
    """Schema for updating quote item."""
    
    description: Optional[str] = Field(None, min_length=1)
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit: Optional[str] = Field(None, max_length=50)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    total_price: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None


class QuoteItemResponse(QuoteItemBase, TimestampSchema):
    """Schema for quote item response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    quote_id: UUID


class QuoteBase(BaseModel):
    """Base quote schema."""
    
    # Pricing
    total_amount: Decimal = Field(..., ge=0)
    currency: str = Field(default="USD", max_length=10)
    
    # Delivery
    delivery_time: Optional[str] = Field(None, max_length=100)
    delivery_location: Optional[str] = Field(None, max_length=255)
    
    # Terms
    payment_terms: Optional[str] = None
    warranty_terms: Optional[str] = None
    additional_terms: Optional[str] = None
    
    # Validity
    valid_until: Optional[datetime] = None
    
    # Notes
    notes: Optional[str] = None


class QuoteCreate(QuoteBase):
    """Schema for creating a new quote."""
    
    items: List[QuoteItemCreate] = Field(..., min_length=1)


class QuoteUpdate(BaseModel):
    """Schema for updating quote information."""
    
    total_amount: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=10)
    delivery_time: Optional[str] = Field(None, max_length=100)
    delivery_location: Optional[str] = Field(None, max_length=255)
    payment_terms: Optional[str] = None
    warranty_terms: Optional[str] = None
    additional_terms: Optional[str] = None
    valid_until: Optional[datetime] = None
    notes: Optional[str] = None


class QuoteResponse(QuoteBase, TimestampSchema):
    """Schema for quote response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tender_id: UUID
    company_id: UUID
    status: QuoteStatus
    submitted_at: Optional[datetime] = None
    created_by_id: Optional[UUID] = None
    updated_by_id: Optional[UUID] = None


class QuoteDetail(QuoteResponse):
    """Detailed quote schema with items."""
    
    items: List[QuoteItemResponse] = []
    tender_title: Optional[str] = None
    company_name: Optional[str] = None


class QuoteSummary(BaseModel):
    """Quote summary schema for listings."""
    
    id: UUID
    tender_id: UUID
    tender_title: str
    company_name: str
    total_amount: Decimal
    currency: str
    status: QuoteStatus
    submitted_at: Optional[datetime] = None
    delivery_time: Optional[str] = None


# Tender document schemas
class TenderDocumentBase(BaseModel):
    """Base tender document schema."""
    
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    document_type: str = Field(..., max_length=50)
    is_public: bool = Field(default=True)
    display_order: int = Field(default=0, ge=0)


class TenderDocumentCreate(TenderDocumentBase):
    """Schema for creating tender document."""
    
    file_url: str = Field(..., min_length=1)
    file_name: str = Field(..., min_length=1, max_length=255)
    file_size: Optional[int] = Field(None, ge=0)
    mime_type: Optional[str] = Field(None, max_length=100)


class TenderDocumentUpdate(BaseModel):
    """Schema for updating tender document."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    document_type: Optional[str] = Field(None, max_length=50)
    is_public: Optional[bool] = None
    display_order: Optional[int] = Field(None, ge=0)


class TenderDocumentResponse(TenderDocumentBase, TimestampSchema):
    """Schema for tender document response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tender_id: UUID
    file_url: str
    file_name: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    created_by_id: Optional[UUID] = None


# Tender invitation schemas
class TenderInvitationBase(BaseModel):
    """Base tender invitation schema."""
    
    company_id: UUID
    message: Optional[str] = None


class TenderInvitationCreate(TenderInvitationBase):
    """Schema for creating tender invitation."""
    pass


class TenderInvitationResponse(TenderInvitationBase, TimestampSchema):
    """Schema for tender invitation response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tender_id: UUID
    status: str
    invited_by_id: UUID
    responded_at: Optional[datetime] = None
    response: Optional[str] = None


# Tender watch schemas
class TenderWatchCreate(BaseModel):
    """Schema for creating tender watch."""
    
    notifications_enabled: bool = Field(default=True)


class TenderWatchResponse(TimestampSchema):
    """Schema for tender watch response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tender_id: UUID
    user_id: UUID
    notifications_enabled: bool


# Search and filter schemas
class TenderSearchFilters(BaseModel):
    """Schema for tender search filters."""
    
    search_query: Optional[str] = None
    tender_type: Optional[TenderType] = None
    category: Optional[str] = None
    status: Optional[TenderStatus] = None
    min_budget: Optional[Decimal] = Field(None, ge=0)
    max_budget: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = None
    deadline_from: Optional[datetime] = None
    deadline_to: Optional[datetime] = None
    is_public: Optional[bool] = None
    company_id: Optional[UUID] = None


class QuoteSearchFilters(BaseModel):
    """Schema for quote search filters."""
    
    tender_id: Optional[UUID] = None
    company_id: Optional[UUID] = None
    status: Optional[QuoteStatus] = None
    min_amount: Optional[Decimal] = Field(None, ge=0)
    max_amount: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = None
    submitted_from: Optional[datetime] = None
    submitted_to: Optional[datetime] = None


# Statistics schemas
class TenderStats(BaseModel):
    """Tender statistics schema."""
    
    total_tenders: int = 0
    active_tenders: int = 0
    draft_tenders: int = 0
    closed_tenders: int = 0
    total_quotes_received: int = 0
    average_quotes_per_tender: float = 0.0


class QuoteStats(BaseModel):
    """Quote statistics schema."""
    
    total_quotes: int = 0
    submitted_quotes: int = 0
    draft_quotes: int = 0
    awarded_quotes: int = 0
    total_value: Decimal = Decimal('0')
    average_quote_value: Decimal = Decimal('0')
