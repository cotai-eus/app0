"""
Tenders domain models.
"""

from datetime import datetime
from typing import Optional
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Column, String, Text, Boolean, DateTime, Integer, 
    Numeric, Index, ForeignKey, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship
import enum

from app.shared.common.base_models import (
    BaseModel, 
    TimestampMixin, 
    SoftDeleteMixin, 
    UserTrackingMixin
)


class TenderStatus(str, enum.Enum):
    """Tender status enumeration."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ACTIVE = "active"
    CLOSED = "closed"
    AWARDED = "awarded"
    CANCELLED = "cancelled"


class TenderType(str, enum.Enum):
    """Tender type enumeration."""
    RFQ = "rfq"  # Request for Quote
    RFP = "rfp"  # Request for Proposal
    ITB = "itb"  # Invitation to Bid
    EOI = "eoi"  # Expression of Interest
    AUCTION = "auction"


class QuoteStatus(str, enum.Enum):
    """Quote status enumeration."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    SHORTLISTED = "shortlisted"
    AWARDED = "awarded"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class Tender(BaseModel, TimestampMixin, SoftDeleteMixin, UserTrackingMixin):
    """Tender model for managing procurement requests."""
    
    __tablename__ = "tenders"
    
    # Basic tender information
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    tender_number = Column(String(100), nullable=False, unique=True, index=True)
    
    # Tender classification
    tender_type = Column(SQLEnum(TenderType), nullable=False, index=True)
    category = Column(String(100), nullable=True, index=True)
    subcategory = Column(String(100), nullable=True)
    
    # Company association
    company_id = Column(PGUUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    
    # Status and timeline
    status = Column(SQLEnum(TenderStatus), default=TenderStatus.DRAFT, nullable=False, index=True)
    
    # Important dates
    published_at = Column(DateTime, nullable=True)
    submission_deadline = Column(DateTime, nullable=False, index=True)
    opening_date = Column(DateTime, nullable=True)
    closing_date = Column(DateTime, nullable=True)
    
    # Budget and financial information
    estimated_budget = Column(Numeric(15, 2), nullable=True)
    minimum_budget = Column(Numeric(15, 2), nullable=True)
    maximum_budget = Column(Numeric(15, 2), nullable=True)
    currency = Column(String(10), default="USD", nullable=False)
    
    # Requirements and specifications
    requirements = Column(JSONB, nullable=True)  # Detailed requirements
    evaluation_criteria = Column(JSONB, nullable=True)  # How quotes will be evaluated
    terms_and_conditions = Column(Text, nullable=True)
    
    # Delivery and location
    delivery_location = Column(String(255), nullable=True)
    delivery_deadline = Column(DateTime, nullable=True)
    
    # Contact information
    contact_person = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    
    # Settings and configurations
    is_public = Column(Boolean, default=True, nullable=False)  # Public or private tender
    requires_registration = Column(Boolean, default=False, nullable=False)
    max_quotes = Column(Integer, nullable=True)  # Maximum number of quotes allowed
      # Metadata
    tags = Column(JSONB, nullable=True)  # Tender tags
    tender_metadata = Column(JSONB, nullable=True)  # Additional metadata
      # Relationships
    company = relationship("Company", backref="tenders")
    ai_analyses = relationship("TenderAIAnalysis", back_populates="tender", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_tenders_company_status", "company_id", "status"),
        Index("idx_tenders_type_category", "tender_type", "category"),
        Index("idx_tenders_deadline", "submission_deadline"),
        Index("idx_tenders_public", "is_public", "status"),
        Index("idx_tenders_published", "published_at"),
    )


class TenderDocument(BaseModel, TimestampMixin, SoftDeleteMixin, UserTrackingMixin):
    """Tender document model for storing tender-related documents."""
    
    __tablename__ = "tender_documents"
    
    tender_id = Column(PGUUID(as_uuid=True), ForeignKey("tenders.id"), nullable=False, index=True)
    
    # Document information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    document_type = Column(String(50), nullable=False)  # specification, terms, attachment, etc.
    
    # File information
    file_url = Column(Text, nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    
    # Access control
    is_public = Column(Boolean, default=True, nullable=False)  # Public or restricted access
    
    # Order for display
    display_order = Column(Integer, default=0, nullable=False)
    
    # Relationships
    tender = relationship("Tender", backref="documents")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_tender_documents_tender", "tender_id"),
        Index("idx_tender_documents_type", "document_type"),
        Index("idx_tender_documents_public", "is_public"),
    )


class Quote(BaseModel, TimestampMixin, SoftDeleteMixin, UserTrackingMixin):
    """Quote model for supplier responses to tenders."""
    
    __tablename__ = "quotes"
    
    # Basic quote information
    tender_id = Column(PGUUID(as_uuid=True), ForeignKey("tenders.id"), nullable=False, index=True)
    supplier_id = Column(PGUUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    quote_number = Column(String(100), nullable=False, unique=True, index=True)
    
    # Quote content
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Financial information
    total_amount = Column(Numeric(15, 2), nullable=False, index=True)
    currency = Column(String(10), default="USD", nullable=False)
    tax_amount = Column(Numeric(15, 2), nullable=True)
    discount_amount = Column(Numeric(15, 2), nullable=True)
    
    # Timeline
    status = Column(SQLEnum(QuoteStatus), default=QuoteStatus.DRAFT, nullable=False, index=True)
    submitted_at = Column(DateTime, nullable=True, index=True)
    valid_until = Column(DateTime, nullable=False)
    delivery_date = Column(DateTime, nullable=True)
    
    # Terms and conditions
    payment_terms = Column(Text, nullable=True)
    delivery_terms = Column(Text, nullable=True)
    warranty_terms = Column(Text, nullable=True)
    
    # Quote items and details
    items = Column(JSONB, nullable=True)  # Quote line items
    attachments = Column(JSONB, nullable=True)  # File attachments
    
    # Evaluation
    score = Column(Numeric(5, 2), nullable=True)  # Evaluation score
    evaluation_notes = Column(Text, nullable=True)
    evaluated_by_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    evaluated_at = Column(DateTime, nullable=True)
      # Metadata
    quote_metadata = Column(JSONB, nullable=True)
    
    # Relationships
    tender = relationship("Tender", backref="quotes")
    supplier = relationship("Company", backref="supplier_quotes")
    evaluated_by = relationship("User")
    
    # Unique constraint to prevent duplicate quotes from same supplier
    __table_args__ = (
        Index("idx_quotes_tender_supplier", "tender_id", "supplier_id", unique=True),
        Index("idx_quotes_status", "status"),
        Index("idx_quotes_amount", "total_amount"),
        Index("idx_quotes_submitted", "submitted_at"),
        Index("idx_quotes_evaluation", "score"),
    )


class QuoteItem(BaseModel, TimestampMixin):
    """Quote item model for detailed line items in quotes."""
    
    __tablename__ = "quote_items"
    
    quote_id = Column(PGUUID(as_uuid=True), ForeignKey("quotes.id"), nullable=False, index=True)
    
    # Item information
    item_number = Column(String(50), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Specifications
    specifications = Column(JSONB, nullable=True)
    brand = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    
    # Quantity and pricing
    quantity = Column(Numeric(10, 2), nullable=False)
    unit = Column(String(50), nullable=True)  # pieces, kg, meters, etc.
    unit_price = Column(Numeric(15, 2), nullable=False)
    total_price = Column(Numeric(15, 2), nullable=False)
    
    # Delivery
    delivery_date = Column(DateTime, nullable=True)
    delivery_location = Column(String(255), nullable=True)
    
    # Order for display
    line_number = Column(Integer, nullable=False)
    
    # Relationships
    quote = relationship("Quote", backref="quote_items")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_quote_items_quote", "quote_id"),
        Index("idx_quote_items_line", "quote_id", "line_number"),
    )


class TenderInvitation(BaseModel, TimestampMixin):
    """Tender invitation model for inviting specific suppliers."""
    
    __tablename__ = "tender_invitations"
    
    tender_id = Column(PGUUID(as_uuid=True), ForeignKey("tenders.id"), nullable=False, index=True)
    supplier_id = Column(PGUUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    
    # Invitation details
    invited_by_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    invitation_message = Column(Text, nullable=True)
    
    # Status tracking
    status = Column(String(20), default="sent", nullable=False)  # sent, viewed, responded, declined
    viewed_at = Column(DateTime, nullable=True)
    responded_at = Column(DateTime, nullable=True)
    
    # Relationships
    tender = relationship("Tender", backref="invitations")
    supplier = relationship("Company", backref="tender_invitations")
    invited_by = relationship("User")
    
    # Unique constraint to prevent duplicate invitations
    __table_args__ = (
        Index("idx_tender_invitations_unique", "tender_id", "supplier_id", unique=True),
        Index("idx_tender_invitations_status", "status"),
    )


class TenderWatch(BaseModel, TimestampMixin):
    """Tender watch model for users following tenders."""
    
    __tablename__ = "tender_watches"
    
    tender_id = Column(PGUUID(as_uuid=True), ForeignKey("tenders.id"), nullable=False, index=True)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Watch settings
    notifications_enabled = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    tender = relationship("Tender", backref="watchers")
    user = relationship("User", backref="watched_tenders")
    
    # Unique constraint to prevent duplicate watches
    __table_args__ = (
        Index("idx_tender_watches_unique", "tender_id", "user_id", unique=True),
    )
