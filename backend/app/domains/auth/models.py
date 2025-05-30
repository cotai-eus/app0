"""
Authentication domain models.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from enum import Enum

from sqlalchemy import Column, String, Boolean, DateTime, Text, Index, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, INET
from sqlalchemy.orm import relationship

from app.shared.common.base_models import BaseModel, TimestampMixin, SoftDeleteMixin


class UserRole(str, Enum):
    """User roles enum"""
    MASTER = "MASTER"
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    USER = "USER"
    VIEWER = "VIEWER"


class UserStatus(str, Enum):
    """User status enum"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    PENDING = "PENDING"
    SUSPENDED = "SUSPENDED"


class User(BaseModel, TimestampMixin):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    # Foreign key to company
    company_id = Column(PGUUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    
    # Basic user data
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    
    # Role and permissions
    role = Column(String(20), nullable=False, default=UserRole.USER.value)
    permissions = Column(JSONB, nullable=True, default={})
    
    # Status and control
    status = Column(String(20), nullable=False, default=UserStatus.ACTIVE.value)
    email_verified = Column(Boolean, default=False, nullable=False)
    must_change_password = Column(Boolean, default=False, nullable=False)
    
    # Metadata
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    password_changed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    company = relationship("Company", back_populates="users")
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_users_company_email", "company_id", "email", unique=True),
        Index("idx_users_email_active", "email", "status"),
        Index("idx_users_company_role", "company_id", "role"),
        Index("idx_users_created_at", "created_at"),
    )


class UserProfile(BaseModel, TimestampMixin):
    """User profile with additional information."""
    
    __tablename__ = "user_profiles"
    
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Personal information
    bio = Column(Text, nullable=True)
    phone = Column(String(20), nullable=True)
    department = Column(String(100), nullable=True)
    position = Column(String(100), nullable=True)
    location = Column(String(255), nullable=True)
    birth_date = Column(DateTime, nullable=True)
    
    # System preferences
    language = Column(String(10), default="pt-BR", nullable=False)
    theme = Column(String(20), default="light", nullable=False)  # light, dark, auto
    notifications_email = Column(Boolean, default=True, nullable=False)
    notifications_push = Column(Boolean, default=True, nullable=False)
    notifications_desktop = Column(Boolean, default=True, nullable=False)
    
    # Work configurations
    working_hours = Column(JSONB, nullable=True, default={})
    calendar_integration = Column(JSONB, nullable=True, default={})
    
    # Relationship
    user = relationship("User", back_populates="profile")


class UserSession(BaseModel, TimestampMixin):
    """User session for advanced session management (API Temporal)."""
    
    __tablename__ = "user_sessions"
    
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Token and identification
    token_hash = Column(String(255), nullable=False)
    refresh_token_hash = Column(String(255), nullable=True)
    device_fingerprint = Column(String(255), nullable=True)
    
    # Session information
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    device_type = Column(String(20), nullable=True)  # desktop, mobile, tablet
    os_info = Column(String(100), nullable=True)
    browser_info = Column(String(100), nullable=True)
    location_data = Column(JSONB, nullable=True, default={})
    
    # Advanced temporal control
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_activity = Column(DateTime(timezone=True), nullable=False)
    max_idle_minutes = Column(Integer, default=30, nullable=False)
    
    # Auto-renewal settings
    auto_renew = Column(Boolean, default=True, nullable=False)
    renewal_count = Column(Integer, default=0, nullable=False)
    max_renewals = Column(Integer, default=100, nullable=False)
    
    # Activity control
    activity_score = Column(Integer, default=100, nullable=False)  # 0-100
    suspicious_activity = Column(Boolean, default=False, nullable=False)
    failed_requests = Column(Integer, default=0, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    force_logout = Column(Boolean, default=False, nullable=False)
    logout_reason = Column(String(100), nullable=True)
    last_renewed_at = Column(DateTime(timezone=True), nullable=False)
    
    # Relationship
    user = relationship("User", back_populates="sessions")
    activities = relationship("SessionActivity", back_populates="session", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_user_sessions_user_id", "user_id"),
        Index("idx_user_sessions_token", "token_hash"),
        Index("idx_user_sessions_active", "is_active", "expires_at"),
        Index("idx_user_sessions_activity", "last_activity"),
    )


class SessionActivity(BaseModel):
    """Session activity monitoring."""
    
    __tablename__ = "session_activities"
    
    session_id = Column(PGUUID(as_uuid=True), ForeignKey("user_sessions.id", ondelete="CASCADE"), nullable=False)
    
    # Activity details
    activity_type = Column(String(50), nullable=False)  # PAGE_VIEW, API_CALL, UPLOAD, etc
    endpoint = Column(String(255), nullable=True)
    method = Column(String(10), nullable=True)
    
    # Metrics
    response_time_ms = Column(Integer, nullable=True)
    status_code = Column(Integer, nullable=True)
    bytes_transferred = Column(Integer, default=0, nullable=False)
    
    # Context
    referrer = Column(String(500), nullable=True)
    user_agent_changes = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime(timezone=True), nullable=False)
    
    # Relationship
    session = relationship("UserSession", back_populates="activities")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_session_activities_session", "session_id"),
        Index("idx_session_activities_created", "created_at"),
        Index("idx_session_activities_type", "activity_type"),
    )


class RefreshToken(BaseModel, TimestampMixin):
    """Refresh token model for JWT token management."""
    
    __tablename__ = "refresh_tokens"
    
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), nullable=False, unique=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Device and session tracking
    device_fingerprint = Column(String(255), nullable=True)
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Relationship
    user = relationship("User")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_refresh_tokens_user_active", "user_id", "is_active"),
        Index("idx_refresh_tokens_expires", "expires_at"),
    )


class ApiKey(BaseModel, TimestampMixin, SoftDeleteMixin):
    """API Key model for programmatic access."""
    
    __tablename__ = "api_keys"
    
    # Foreign key to user
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # API Key details
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    key_hash = Column(String(255), nullable=False, unique=True, index=True)
    
    # Permissions and scope
    scopes = Column(JSONB, nullable=False, default=[])  # List of allowed scopes
    permissions = Column(JSONB, nullable=True, default={})
    
    # Usage tracking
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    usage_count = Column(Integer, default=0, nullable=False)
    
    # Limits
    rate_limit = Column(Integer, nullable=True)  # Requests per hour
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # IP restrictions
    allowed_ips = Column(JSONB, nullable=True, default=[])  # List of allowed IP ranges
    
    # Relationship
    user = relationship("User")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_api_keys_user_active", "user_id", "is_active"),
        Index("idx_api_keys_expires", "expires_at"),
        Index("idx_api_keys_last_used", "last_used_at"),
    )
