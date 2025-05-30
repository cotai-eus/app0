"""
Files models for file management, uploads, and access control.
Based on the database architecture plan.
"""
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, BigInteger, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.shared.common.base_models import BaseModel, TimestampMixin, SoftDeleteMixin, UserTrackingMixin


class AccessType(str, Enum):
    """Types of file access."""
    UPLOAD = "upload"
    DOWNLOAD = "download"
    VIEW = "view"
    PREVIEW = "preview"
    DELETE = "delete"
    SHARE = "share"
    COPY = "copy"
    MOVE = "move"


class AccessResult(str, Enum):
    """Result of file access attempt."""
    SUCCESS = "success"
    DENIED = "denied"
    NOT_FOUND = "not_found"
    ERROR = "error"
    QUOTA_EXCEEDED = "quota_exceeded"
    VIRUS_DETECTED = "virus_detected"


class FileAccessLog(BaseModel, TimestampMixin):
    """Audit log for file access and operations."""
    __tablename__ = "file_access_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # File identification
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    file_path = Column(String(500), nullable=False)
    filename = Column(String(255), nullable=False)
    
    # Access details
    access_type = Column(String(50), nullable=False)
    access_result = Column(String(50), nullable=False)
    
    # User context
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    session_id = Column(String(100))
    
    # Request context
    ip_address = Column(String(45))
    user_agent = Column(Text)
    request_id = Column(String(100))
    endpoint = Column(String(255))
    
    # File operation details
    bytes_transferred = Column(BigInteger)  # For uploads/downloads
    duration_ms = Column(Integer)  # Operation duration
    
    # Error details
    error_code = Column(String(50))
    error_message = Column(Text)
    
    # Security context
    security_scan_result = Column(String(50))  # clean, infected, suspicious
    virus_signature = Column(String(255))  # If virus detected
    
    # Sharing context (if applicable)
    shared_with = Column(JSON)  # Array of user IDs or external emails
    share_token = Column(String(100))  # For public/token-based shares
    share_expires_at = Column(DateTime)
    
    # Relationships
    document = relationship("Document", back_populates="file_access_logs")
    user = relationship("User")
    company = relationship("Company")

    __table_args__ = (
        Index('idx_file_access_logs_document_id', 'document_id'),
        Index('idx_file_access_logs_user_id', 'user_id'),
        Index('idx_file_access_logs_access_type', 'access_type'),
        Index('idx_file_access_logs_access_result', 'access_result'),
        Index('idx_file_access_logs_created_at', 'created_at'),
        Index('idx_file_access_logs_ip_address', 'ip_address'),
        # Composite indexes for common queries
        Index('idx_file_access_user_date', 'user_id', 'created_at'),
        Index('idx_file_access_company_date', 'company_id', 'created_at'),
        Index('idx_file_access_document_date', 'document_id', 'created_at'),
    )


class FileShare(BaseModel, TimestampMixin, UserTrackingMixin):
    """File sharing management and permissions."""
    __tablename__ = "file_shares"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # File identification
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    
    # Share configuration
    share_token = Column(String(100), unique=True, nullable=False)
    share_name = Column(String(255))  # Human-readable share name
    description = Column(Text)
    
    # Access permissions
    can_download = Column(Boolean, default=True)
    can_preview = Column(Boolean, default=True)
    can_copy = Column(Boolean, default=False)
    requires_password = Column(Boolean, default=False)
    password_hash = Column(String(255))  # Hashed password for protected shares
    
    # Access control
    allowed_emails = Column(JSON)  # Array of allowed email addresses
    allowed_domains = Column(JSON)  # Array of allowed domain patterns
    max_access_count = Column(Integer)  # Maximum number of accesses
    current_access_count = Column(Integer, default=0)
    
    # Time restrictions
    expires_at = Column(DateTime)
    available_from = Column(DateTime)  # When share becomes available
    available_until = Column(DateTime)  # When share stops being available
    
    # Security settings
    require_authentication = Column(Boolean, default=False)
    log_all_access = Column(Boolean, default=True)
    watermark_enabled = Column(Boolean, default=False)
    download_limit_per_user = Column(Integer)  # Max downloads per unique user
    
    # Status
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)  # Public link vs private share
    
    # Notifications
    notify_on_access = Column(Boolean, default=False)
    notification_emails = Column(JSON)  # Array of emails to notify
    
    # Relationships
    document = relationship("Document")

    __table_args__ = (
        Index('idx_file_shares_document_id', 'document_id'),
        Index('idx_file_shares_share_token', 'share_token'),
        Index('idx_file_shares_is_active', 'is_active'),
        Index('idx_file_shares_expires_at', 'expires_at'),
        Index('idx_file_shares_created_by', 'created_by'),
    )


class FileQuota(BaseModel, TimestampMixin, UserTrackingMixin):
    """File storage quotas and usage tracking."""
    __tablename__ = "file_quotas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Quota scope
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))  # User-specific quota
    
    # Quota limits (in bytes)
    total_quota_bytes = Column(BigInteger, nullable=False)
    used_bytes = Column(BigInteger, default=0)
    reserved_bytes = Column(BigInteger, default=0)  # For pending uploads
    
    # File count limits
    max_files = Column(Integer)
    current_file_count = Column(Integer, default=0)
    
    # File type restrictions
    allowed_file_types = Column(JSON)  # Array of allowed MIME types
    blocked_file_types = Column(JSON)  # Array of blocked MIME types
    max_file_size_bytes = Column(BigInteger)  # Maximum individual file size
    
    # Usage tracking
    last_calculated = Column(DateTime, default=datetime.utcnow)
    is_over_quota = Column(Boolean, default=False)
    warning_sent = Column(Boolean, default=False)
    
    # Quota policies
    auto_cleanup_enabled = Column(Boolean, default=False)
    cleanup_after_days = Column(Integer, default=90)  # Auto-delete old files
    warn_at_percent = Column(Integer, default=80)  # Warn when 80% used
    
    # Relationships
    company = relationship("Company")
    user = relationship("User")

    __table_args__ = (
        Index('idx_file_quotas_company_id', 'company_id'),
        Index('idx_file_quotas_user_id', 'user_id'),
        Index('idx_file_quotas_is_over_quota', 'is_over_quota'),
        # Unique constraint for company-user quota
        Index('idx_file_quotas_company_user', 'company_id', 'user_id', unique=True),
    )


class FileVersion(BaseModel, TimestampMixin, UserTrackingMixin):
    """File version tracking and history."""
    __tablename__ = "file_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Version identification
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    
    # File details
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    file_hash = Column(String(64), nullable=False)  # SHA-256
    mime_type = Column(String(100), nullable=False)
    
    # Version metadata
    change_description = Column(Text)
    is_current = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    
    # Storage details
    storage_location = Column(String(500))  # Cloud storage path or local path
    compression_used = Column(String(50))  # Compression algorithm if any
    encrypted = Column(Boolean, default=False)
    
    # Relationships
    document = relationship("Document")

    __table_args__ = (
        Index('idx_file_versions_document_id', 'document_id'),
        Index('idx_file_versions_version_number', 'version_number'),
        Index('idx_file_versions_is_current', 'is_current'),
        Index('idx_file_versions_created_at', 'created_at'),
        # Composite index for document version lookup
        Index('idx_file_versions_document_version', 'document_id', 'version_number'),
    )


class FileUploadSession(BaseModel, TimestampMixin):
    """Chunked/resumable file upload session tracking."""
    __tablename__ = "file_upload_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Session identification
    session_token = Column(String(100), unique=True, nullable=False)
    upload_id = Column(String(100), unique=True)  # For cloud storage multipart uploads
    
    # File details
    filename = Column(String(255), nullable=False)
    total_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100))
    file_hash = Column(String(64))  # Expected final hash
    
    # Upload progress
    uploaded_chunks = Column(JSON)  # Array of completed chunk numbers
    uploaded_bytes = Column(BigInteger, default=0)
    chunk_size = Column(Integer, default=1048576)  # Default 1MB chunks
    
    # User context
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    
    # Target location
    target_folder = Column(String(500))
    replace_existing = Column(Boolean, default=False)
    
    # Session status
    is_completed = Column(Boolean, default=False)
    is_failed = Column(Boolean, default=False)
    failure_reason = Column(Text)
    
    # Expiration
    expires_at = Column(DateTime, nullable=False)
    
    # Temporary storage
    temp_file_path = Column(String(500))  # Temporary file location
    
    # Relationships
    user = relationship("User")
    company = relationship("Company")

    __table_args__ = (
        Index('idx_file_upload_sessions_session_token', 'session_token'),
        Index('idx_file_upload_sessions_user_id', 'user_id'),
        Index('idx_file_upload_sessions_is_completed', 'is_completed'),
        Index('idx_file_upload_sessions_expires_at', 'expires_at'),
        Index('idx_file_upload_sessions_created_at', 'created_at'),
    )
