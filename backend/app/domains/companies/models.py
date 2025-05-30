"""
Companies domain models.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from enum import Enum

from sqlalchemy import Column, String, Text, Boolean, DateTime, Integer, Index, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship

from app.shared.common.base_models import (
    BaseModel, 
    TimestampMixin, 
    SoftDeleteMixin, 
    UserTrackingMixin
)


class CompanyPlanType(str, Enum):
    """Company plan types"""
    BASIC = "BASIC"
    PRO = "PRO"
    ENTERPRISE = "ENTERPRISE"


class CompanyStatus(str, Enum):
    """Company status"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class Company(BaseModel, TimestampMixin, SoftDeleteMixin):
    """Company model for managing business entities."""
    
    __tablename__ = "companies"
    
    # Basic company information
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(100), nullable=False, unique=True)
    cnpj = Column(String(18), nullable=True, unique=True, index=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    logo_url = Column(String(500), nullable=True)
    
    # Plan configurations
    plan_type = Column(String(50), default=CompanyPlanType.BASIC.value, nullable=False)
    max_users = Column(Integer, default=5, nullable=False)
    max_storage_gb = Column(Integer, default=10, nullable=False)
    features = Column(JSONB, nullable=True, default={})  # {"kanban": true, "chat": false}
    
    # Company configurations
    business_hours = Column(JSONB, nullable=True, default={})  # {"monday": {"start": "09:00", "end": "18:00"}}
    timezone = Column(String(50), default="America/Sao_Paulo", nullable=False)
    
    # Status
    status = Column(String(20), default=CompanyStatus.ACTIVE.value, nullable=False)
      # Relationships
    users = relationship("User", back_populates="company")
    company_users = relationship("CompanyUser", back_populates="company")
    parent_company_id = Column(PGUUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    parent_company = relationship("Company", remote_side="Company.id", backref="subsidiaries")
    
    # New domain relationships
    documents = relationship("Document", back_populates="company")
    ai_prompt_templates = relationship("AIPromptTemplate", back_populates="company")
    file_quotas = relationship("FileQuota", back_populates="company")
    audit_logs = relationship("AuditLog", back_populates="company")
    form_templates = relationship("FormTemplate", back_populates="company")
    form_submissions = relationship("FormSubmission", back_populates="company")
    data_retention_policies = relationship("DataRetentionPolicy", back_populates="company")
    rate_limit_policies = relationship("RateLimitPolicies", back_populates="company")
    celery_tasks = relationship("CeleryTask", back_populates="company")
    task_schedules = relationship("TaskSchedule", back_populates="company")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_companies_name_active", "name", "status"),
        Index("idx_companies_cnpj", "cnpj"),
        Index("idx_companies_slug", "slug"),
        Index("idx_companies_parent", "parent_company_id"),
    )


class CompanyUserRole(str, Enum):
    """Company user roles"""
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    USER = "USER"
    VIEWER = "VIEWER"


class CompanyUser(BaseModel, TimestampMixin, SoftDeleteMixin):
    """Association between companies and users with roles."""
    
    __tablename__ = "company_users"
    
    company_id = Column(PGUUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Role and permissions
    role = Column(String(50), nullable=False, default=CompanyUserRole.USER.value)
    permissions = Column(JSONB, nullable=True, default={})  # Specific permissions
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    invited_at = Column(DateTime(timezone=True), nullable=True)
    joined_at = Column(DateTime(timezone=True), nullable=True)
    invited_by_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    company = relationship("Company", back_populates="company_users")
    user = relationship("User", foreign_keys=[user_id])
    invited_by = relationship("User", foreign_keys=[invited_by_id])
    
    # Unique constraint to prevent duplicate memberships
    __table_args__ = (
        UniqueConstraint("company_id", "user_id", name="uq_company_users_unique"),
        Index("idx_company_users_role", "company_id", "role"),
        Index("idx_company_users_active", "company_id", "is_active"),
    )


class CompanyInvitation(BaseModel, TimestampMixin):
    """Company invitation model for inviting users to join companies."""
    
    __tablename__ = "company_invitations"
    
    company_id = Column(PGUUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    email = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    
    # Invitation details
    token = Column(String(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    
    # Status
    status = Column(
        String(20), 
        default="pending", 
        nullable=False
    )  # pending, accepted, expired, revoked
    
    # Tracking
    invited_by_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    accepted_by_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    accepted_at = Column(DateTime, nullable=True)
    
    # Relationships
    company = relationship("Company", backref="invitations")
    invited_by = relationship("User", foreign_keys=[invited_by_id])
    accepted_by = relationship("User", foreign_keys=[accepted_by_id])
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_company_invitations_email_company", "email", "company_id"),
        Index("idx_company_invitations_token", "token"),
        Index("idx_company_invitations_status", "status"),
        Index("idx_company_invitations_expires", "expires_at"),
    )


class CompanyDocument(BaseModel, TimestampMixin, SoftDeleteMixin, UserTrackingMixin):
    """Company document model for storing company-related documents."""
    
    __tablename__ = "company_documents"
    
    company_id = Column(PGUUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    
    # Document information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    document_type = Column(String(50), nullable=False)  # certificate, license, contract, etc.
    
    # File information
    file_url = Column(Text, nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
      # Metadata
    tags = Column(JSONB, nullable=True)  # Document tags
    document_metadata = Column(JSONB, nullable=True)  # Additional metadata
    
    # Status and dates
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    company = relationship("Company", backref="documents")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_company_documents_company", "company_id"),
        Index("idx_company_documents_type", "document_type"),
        Index("idx_company_documents_expires", "expires_at"),
    )


class CompanySettings(BaseModel, TimestampMixin, UserTrackingMixin):
    """Company settings model for storing company-specific configurations."""
    
    __tablename__ = "company_settings"
    
    company_id = Column(PGUUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, unique=True)
    
    # General settings
    timezone = Column(String(50), default="UTC", nullable=False)
    currency = Column(String(10), default="USD", nullable=False)
    language = Column(String(10), default="en", nullable=False)
    date_format = Column(String(20), default="YYYY-MM-DD", nullable=False)
    
    # Business settings
    fiscal_year_start = Column(String(5), default="01-01", nullable=False)  # MM-DD format
    business_hours = Column(JSONB, nullable=True)  # Working hours configuration
    
    # Notification settings
    email_notifications = Column(Boolean, default=True, nullable=False)
    slack_webhook_url = Column(Text, nullable=True)
    teams_webhook_url = Column(Text, nullable=True)
    
    # Feature flags
    features_enabled = Column(JSONB, nullable=True)  # Enabled features
    
    # Integration settings
    integrations = Column(JSONB, nullable=True)  # Third-party integrations
    
    # Relationships
    company = relationship("Company", backref="settings_config", uselist=False)
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_company_settings_company", "company_id"),
    )
