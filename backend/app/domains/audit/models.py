"""
Audit models for advanced logging, compliance tracking, and form management.
Based on the database architecture plan.
"""
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.shared.common.base_models import BaseModel, TimestampMixin, UserTrackingMixin

# Import FormStatus from forms domain to avoid duplication
from app.domains.forms.models import FormStatus


class AuditEventType(str, Enum):
    """Types of audit events."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"
    IMPORT = "import"
    SHARE = "share"
    DOWNLOAD = "download"
    UPLOAD = "upload"
    PERMISSION_CHANGE = "permission_change"
    CONFIG_CHANGE = "config_change"
    BACKUP = "backup"
    RESTORE = "restore"


class AuditSeverity(str, Enum):
    """Severity levels for audit events."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SubmissionStatus(str, Enum):
    """Status of form submissions."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_CHANGES = "requires_changes"


class AuditLog(BaseModel, TimestampMixin):
    """Comprehensive audit logging for compliance and security."""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Event identification
    event_type = Column(String(50), nullable=False)
    event_category = Column(String(100))  # Security, Data, System, User, etc.
    severity = Column(String(20), nullable=False, default=AuditSeverity.LOW)
    
    # Event details
    description = Column(Text, nullable=False)
    details = Column(JSON)  # Structured event details
    
    # User context
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    user_email = Column(String(255))  # Cached for deleted users
    user_role = Column(String(50))
    impersonated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))  # If user was impersonated
    
    # Session context
    session_id = Column(String(100))
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Request context
    request_id = Column(String(100))
    endpoint = Column(String(255))
    method = Column(String(10))
    request_data = Column(JSON)  # Request payload (sanitized)
    response_status = Column(Integer)
    
    # Resource context
    resource_type = Column(String(100))  # User, Document, Company, etc.
    resource_id = Column(String(100))  # ID of affected resource
    resource_name = Column(String(255))  # Human-readable resource name
    
    # Company context
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    company_name = Column(String(255))  # Cached for reference
    
    # Data changes
    old_values = Column(JSON)  # Previous values (for updates)
    new_values = Column(JSON)  # New values (for creates/updates)
    changed_fields = Column(JSON)  # Array of changed field names
    
    # Compliance tags
    compliance_tags = Column(JSON)  # GDPR, SOX, HIPAA, etc.
    retention_period_days = Column(Integer, default=2555)  # ~7 years default
    
    # Error tracking
    is_error = Column(Boolean, default=False)
    error_code = Column(String(50))
    error_message = Column(Text)
    
    # Additional metadata
    source_system = Column(String(100))  # API, Web, Mobile, etc.
    correlation_id = Column(String(100))  # For tracing related events
    parent_event_id = Column(UUID(as_uuid=True), ForeignKey("audit_logs.id"))
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    impersonator = relationship("User", foreign_keys=[impersonated_by])
    company = relationship("Company")
    parent_event = relationship("AuditLog", remote_side=[id])
    child_events = relationship("AuditLog", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_audit_logs_event_type', 'event_type'),
        Index('idx_audit_logs_user_id', 'user_id'),
        Index('idx_audit_logs_company_id', 'company_id'),
        Index('idx_audit_logs_resource_type', 'resource_type'),
        Index('idx_audit_logs_resource_id', 'resource_id'),
        Index('idx_audit_logs_severity', 'severity'),
        Index('idx_audit_logs_created_at', 'created_at'),
        Index('idx_audit_logs_ip_address', 'ip_address'),
        Index('idx_audit_logs_session_id', 'session_id'),
        Index('idx_audit_logs_is_error', 'is_error'),
        # Composite indexes for common queries
        Index('idx_audit_logs_user_date', 'user_id', 'created_at'),
        Index('idx_audit_logs_company_date', 'company_id', 'created_at'),
        Index('idx_audit_logs_resource_date', 'resource_type', 'resource_id', 'created_at'),
    )


class FormTemplate(BaseModel, TimestampMixin, UserTrackingMixin):
    """Dynamic form templates for data collection."""
    __tablename__ = "form_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Template identification
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    version = Column(String(50), default="1.0")
    
    # Form configuration
    form_schema = Column(JSON, nullable=False)  # JSON Schema for form fields
    ui_schema = Column(JSON)  # UI configuration (layout, styling, etc.)
    validation_rules = Column(JSON)  # Custom validation rules
    
    # Status and visibility
    status = Column(String(50), nullable=False, default=FormStatus.DRAFT)
    is_public = Column(Boolean, default=False)
    requires_authentication = Column(Boolean, default=True)
    
    # Access control
    allowed_roles = Column(JSON)  # Array of roles that can access this form
    allowed_users = Column(JSON)  # Array of specific user IDs
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    
    # Submission settings
    max_submissions_per_user = Column(Integer)  # Limit submissions per user
    submission_deadline = Column(DateTime)
    auto_save_enabled = Column(Boolean, default=True)
    allow_anonymous = Column(Boolean, default=False)
    
    # Workflow
    requires_approval = Column(Boolean, default=False)
    approval_workflow = Column(JSON)  # Approval steps and rules
    notification_settings = Column(JSON)  # Email notifications config
    
    # File handling
    allow_file_uploads = Column(Boolean, default=False)
    max_file_size_mb = Column(Integer, default=10)
    allowed_file_types = Column(JSON)  # Array of allowed MIME types
    
    # Analytics
    submission_count = Column(Integer, default=0)
    completion_rate = Column(Integer)  # Percentage of started forms completed
    avg_completion_time_minutes = Column(Integer)
    
    # Relationships
    company = relationship("Company")
    submissions = relationship("FormSubmission", back_populates="form_template", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_form_templates_slug', 'slug'),
        Index('idx_form_templates_status', 'status'),
        Index('idx_form_templates_company_id', 'company_id'),
        Index('idx_form_templates_is_public', 'is_public'),
        Index('idx_form_templates_created_by', 'created_by'),
    )


class FormSubmission(BaseModel, TimestampMixin, UserTrackingMixin):
    """Form submission data and tracking."""
    __tablename__ = "form_submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Form identification
    form_template_id = Column(UUID(as_uuid=True), ForeignKey("form_templates.id"), nullable=False)
    submission_token = Column(String(100), unique=True)  # For anonymous submissions
    
    # Submission data
    form_data = Column(JSON, nullable=False)  # Submitted form data
    status = Column(String(50), nullable=False, default=SubmissionStatus.DRAFT)
    
    # Submitter information
    submitter_email = Column(String(255))  # For anonymous submissions
    submitter_name = Column(String(255))  # For anonymous submissions
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    
    # Submission metadata
    ip_address = Column(String(45))
    user_agent = Column(Text)
    submission_source = Column(String(100))  # web, mobile, api, etc.
    
    # Processing
    started_at = Column(DateTime)  # When form was first opened
    submitted_at = Column(DateTime)  # When form was submitted
    completion_time_minutes = Column(Integer)  # Time taken to complete
    
    # Validation
    validation_errors = Column(JSON)  # Array of validation errors
    is_valid = Column(Boolean, default=True)
    validation_version = Column(String(50))  # Version of validation rules used
    
    # Workflow
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    reviewed_at = Column(DateTime)
    review_notes = Column(Text)
    approval_history = Column(JSON)  # Array of approval steps
    
    # File attachments
    attached_files = Column(JSON)  # Array of file IDs
    
    # Relationships
    form_template = relationship("FormTemplate", back_populates="submissions")
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    company = relationship("Company")

    __table_args__ = (
        Index('idx_form_submissions_form_template_id', 'form_template_id'),
        Index('idx_form_submissions_status', 'status'),
        Index('idx_form_submissions_created_by', 'created_by'),
        Index('idx_form_submissions_company_id', 'company_id'),
        Index('idx_form_submissions_submitted_at', 'submitted_at'),
        Index('idx_form_submissions_reviewed_by', 'reviewed_by'),
        # Composite indexes
        Index('idx_form_submissions_template_status', 'form_template_id', 'status'),
        Index('idx_form_submissions_user_date', 'created_by', 'created_at'),
    )


class DataRetentionPolicy(BaseModel, TimestampMixin, UserTrackingMixin):
    """Data retention policies for compliance."""
    __tablename__ = "data_retention_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Policy identification
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Scope
    data_type = Column(String(100), nullable=False)  # audit_logs, documents, etc.
    table_name = Column(String(100))  # Database table name
    
    # Retention rules
    retention_period_days = Column(Integer, nullable=False)
    archive_after_days = Column(Integer)  # Move to archive before deletion
    
    # Conditions
    conditions = Column(JSON)  # Conditions for applying this policy
    exclude_conditions = Column(JSON)  # Conditions for excluding records
    
    # Company scope
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    applies_to_all_companies = Column(Boolean, default=False)
    
    # Execution
    is_active = Column(Boolean, default=True)
    last_executed = Column(DateTime)
    next_execution = Column(DateTime)
    execution_frequency_days = Column(Integer, default=7)  # Run weekly
    
    # Statistics
    records_processed = Column(Integer, default=0)
    records_archived = Column(Integer, default=0)
    records_deleted = Column(Integer, default=0)
    
    # Compliance
    compliance_regulations = Column(JSON)  # GDPR, SOX, etc.
    legal_hold_exempt = Column(Boolean, default=False)
    
    # Relationships
    company = relationship("Company")

    __table_args__ = (
        Index('idx_data_retention_policies_data_type', 'data_type'),
        Index('idx_data_retention_policies_company_id', 'company_id'),
        Index('idx_data_retention_policies_is_active', 'is_active'),
        Index('idx_data_retention_policies_next_execution', 'next_execution'),
    )
