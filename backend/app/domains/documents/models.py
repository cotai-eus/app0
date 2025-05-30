"""
Document models for file management and AI processing.
Based on the database architecture plan.
"""
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, BigInteger, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.shared.common.base_models import BaseModel, TimestampMixin, SoftDeleteMixin, UserTrackingMixin


class DocumentType(str, Enum):
    """Types of documents that can be processed."""
    PDF = "pdf"
    WORD = "word" 
    EXCEL = "excel"
    POWERPOINT = "powerpoint"
    IMAGE = "image"
    TEXT = "text"
    OTHER = "other"


class DocumentStatus(str, Enum):
    """Status of document processing."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    ARCHIVED = "archived"


class ProcessingStatus(str, Enum):
    """Status of AI processing jobs."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProcessingType(str, Enum):
    """Types of AI processing."""
    TEXT_EXTRACTION = "text_extraction"
    TENDER_ANALYSIS = "tender_analysis"
    DOCUMENT_CLASSIFICATION = "document_classification"
    CONTENT_SUMMARIZATION = "content_summarization"
    CUSTOM_ANALYSIS = "custom_analysis"


class Document(BaseModel, TimestampMixin, SoftDeleteMixin, UserTrackingMixin):
    """Main document model for file storage and metadata."""
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False)  # Size in bytes
    mime_type = Column(String(100), nullable=False)
    document_type = Column(String(50), nullable=False, default=DocumentType.OTHER)
    status = Column(String(50), nullable=False, default=DocumentStatus.UPLOADED)
    
    # File metadata
    file_hash = Column(String(64), nullable=False, unique=True)  # SHA-256 hash
    checksum = Column(String(32))  # MD5 checksum for integrity
    
    # Organization
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    folder_path = Column(String(500))  # Logical folder structure
    tags = Column(JSON)  # Array of tags
    
    # Processing flags
    is_ai_processable = Column(Boolean, default=True)
    is_sensitive = Column(Boolean, default=False)
    retention_date = Column(DateTime)  # When document should be deleted
    
    # Access control
    is_public = Column(Boolean, default=False)
    allowed_users = Column(JSON)  # Array of user IDs with access
    allowed_roles = Column(JSON)  # Array of roles with access
      # Metadata
    doc_metadata = Column(JSON)  # Flexible metadata storage
    description = Column(Text)
    version = Column(Integer, default=1)
    parent_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"))
    
    # Relationships
    company = relationship("Company", back_populates="documents")
    text_extractions = relationship("TextExtraction", back_populates="document", cascade="all, delete-orphan")
    ai_processing_jobs = relationship("AIProcessingJob", back_populates="document", cascade="all, delete-orphan")
    tender_analyses = relationship("TenderAIAnalysis", back_populates="document", cascade="all, delete-orphan")
    file_access_logs = relationship("FileAccessLog", back_populates="document", cascade="all, delete-orphan")
    parent_document = relationship("Document", remote_side=[id])
    child_documents = relationship("Document", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_documents_company_id', 'company_id'),
        Index('idx_documents_status', 'status'),
        Index('idx_documents_document_type', 'document_type'),
        Index('idx_documents_file_hash', 'file_hash'),
        Index('idx_documents_created_by', 'created_by'),
        Index('idx_documents_created_at', 'created_at'),
    )


class TextExtraction(BaseModel, TimestampMixin, UserTrackingMixin):
    """Text extraction results from documents."""
    __tablename__ = "text_extractions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    
    # Extracted content
    raw_text = Column(Text)  # Raw extracted text
    formatted_text = Column(Text)  # Cleaned and formatted text
    structured_data = Column(JSON)  # Structured data if applicable (tables, forms, etc.)
    
    # Extraction metadata
    extraction_method = Column(String(100))  # OCR, PDF parser, etc.
    confidence_score = Column(Integer)  # 0-100 confidence in extraction quality
    page_count = Column(Integer)
    word_count = Column(Integer)
    language_detected = Column(String(10))
    
    # Processing info
    processing_time_ms = Column(Integer)
    extraction_engine = Column(String(100))  # Which engine was used
    extraction_version = Column(String(50))  # Version of extraction engine
    
    # Error handling
    has_errors = Column(Boolean, default=False)
    error_details = Column(JSON)
    quality_metrics = Column(JSON)  # Quality assessment metrics
    
    # Relationships
    document = relationship("Document", back_populates="text_extractions")

    __table_args__ = (
        Index('idx_text_extractions_document_id', 'document_id'),
        Index('idx_text_extractions_created_at', 'created_at'),
        Index('idx_text_extractions_extraction_method', 'extraction_method'),
    )


class AIProcessingJob(BaseModel, TimestampMixin, UserTrackingMixin):
    """AI processing jobs for documents."""
    __tablename__ = "ai_processing_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    
    # Job details
    job_type = Column(String(100), nullable=False)  # ProcessingType enum
    status = Column(String(50), nullable=False, default=ProcessingStatus.PENDING)
    priority = Column(Integer, default=5)  # 1-10, 10 being highest
    
    # Processing configuration
    ai_model = Column(String(100))  # Which AI model to use
    processing_params = Column(JSON)  # Model-specific parameters
    prompt_template_id = Column(UUID(as_uuid=True), ForeignKey("ai_prompt_templates.id"))
    
    # Execution tracking
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    processing_time_ms = Column(Integer)
    worker_id = Column(String(100))  # Celery worker ID
    
    # Results
    result_data = Column(JSON)  # Processing results
    confidence_score = Column(Integer)  # 0-100 confidence in results
    tokens_used = Column(Integer)  # For LLM cost tracking
    cost_estimate = Column(Integer)  # Cost in cents
    
    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Relationships
    document = relationship("Document", back_populates="ai_processing_jobs")
    prompt_template = relationship("AIPromptTemplate", back_populates="processing_jobs")

    __table_args__ = (
        Index('idx_ai_processing_jobs_document_id', 'document_id'),
        Index('idx_ai_processing_jobs_status', 'status'),
        Index('idx_ai_processing_jobs_job_type', 'job_type'),
        Index('idx_ai_processing_jobs_created_at', 'created_at'),
        Index('idx_ai_processing_jobs_priority', 'priority'),
    )


class TenderAIAnalysis(BaseModel, TimestampMixin, UserTrackingMixin):
    """AI analysis results for tender documents."""
    __tablename__ = "tender_ai_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    tender_id = Column(UUID(as_uuid=True), ForeignKey("tenders.id"))
    
    # Analysis results
    summary = Column(Text)
    key_requirements = Column(JSON)  # Array of extracted requirements
    deadlines = Column(JSON)  # Array of important dates
    budget_info = Column(JSON)  # Budget/financial information
    risk_assessment = Column(JSON)  # Risk factors identified
    
    # Scoring
    opportunity_score = Column(Integer)  # 0-100 opportunity score
    complexity_score = Column(Integer)  # 0-100 complexity score
    competition_level = Column(String(50))  # LOW, MEDIUM, HIGH
    recommendation = Column(String(50))  # BID, NO_BID, INVESTIGATE
    
    # Analysis metadata
    ai_model_used = Column(String(100))
    analysis_version = Column(String(50))
    confidence_score = Column(Integer)  # 0-100 overall confidence
    processing_time_ms = Column(Integer)
    
    # Extracted entities
    organizations_mentioned = Column(JSON)  # Companies/orgs mentioned
    locations = Column(JSON)  # Geographic locations
    technologies = Column(JSON)  # Technologies/skills required
    certifications_required = Column(JSON)  # Required certifications
    
    # Relationships
    document = relationship("Document", back_populates="tender_analyses")
    tender = relationship("Tender", back_populates="ai_analyses")

    __table_args__ = (
        Index('idx_tender_ai_analyses_document_id', 'document_id'),
        Index('idx_tender_ai_analyses_tender_id', 'tender_id'),
        Index('idx_tender_ai_analyses_opportunity_score', 'opportunity_score'),
        Index('idx_tender_ai_analyses_recommendation', 'recommendation'),
    )


class AIPromptTemplate(BaseModel, TimestampMixin, UserTrackingMixin):
    """Templates for AI prompts used in processing."""
    __tablename__ = "ai_prompt_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Template content
    system_prompt = Column(Text)  # System/instruction prompt
    user_prompt_template = Column(Text, nullable=False)  # Template with variables
    variables = Column(JSON)  # Available variables and their descriptions
    
    # Configuration
    processing_type = Column(String(100), nullable=False)  # ProcessingType enum
    ai_model = Column(String(100))  # Recommended AI model
    max_tokens = Column(Integer)
    temperature = Column(Integer)  # 0-100 (will be divided by 100)
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    success_rate = Column(Integer)  # 0-100 success rate
    avg_processing_time_ms = Column(Integer)
    
    # Version control
    version = Column(String(50), default="1.0")
    is_active = Column(Boolean, default=True)
    parent_template_id = Column(UUID(as_uuid=True), ForeignKey("ai_prompt_templates.id"))
    
    # Organization
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    is_global = Column(Boolean, default=False)  # Available to all companies
    tags = Column(JSON)  # Array of tags for categorization
    
    # Relationships
    company = relationship("Company", back_populates="ai_prompt_templates")
    processing_jobs = relationship("AIProcessingJob", back_populates="prompt_template")
    parent_template = relationship("AIPromptTemplate", remote_side=[id])
    child_templates = relationship("AIPromptTemplate", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_ai_prompt_templates_processing_type', 'processing_type'),
        Index('idx_ai_prompt_templates_company_id', 'company_id'),
        Index('idx_ai_prompt_templates_is_active', 'is_active'),
        Index('idx_ai_prompt_templates_is_global', 'is_global'),
    )


class AIResponseCache(BaseModel, TimestampMixin):
    """Cache for AI responses to avoid repeated processing."""
    __tablename__ = "ai_response_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Cache key components
    content_hash = Column(String(64), nullable=False)  # SHA-256 of input content
    prompt_hash = Column(String(64), nullable=False)  # SHA-256 of prompt
    model_name = Column(String(100), nullable=False)
    model_params_hash = Column(String(64))  # Hash of model parameters
    
    # Cached response
    response_data = Column(JSON, nullable=False)
    confidence_score = Column(Integer)
    tokens_used = Column(Integer)
    processing_time_ms = Column(Integer)
    
    # Cache metadata
    hit_count = Column(Integer, default=0)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    
    # Relationships and indexing
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    
    __table_args__ = (
        Index('idx_ai_response_cache_content_hash', 'content_hash'),
        Index('idx_ai_response_cache_prompt_hash', 'prompt_hash'),
        Index('idx_ai_response_cache_model_name', 'model_name'),
        Index('idx_ai_response_cache_expires_at', 'expires_at'),
        Index('idx_ai_response_cache_company_id', 'company_id'),
        # Composite index for fast cache lookups
        Index('idx_ai_cache_lookup', 'content_hash', 'prompt_hash', 'model_name'),
    )
