"""
Companies domain schemas.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr, ConfigDict

from app.shared.common.base_schemas import BaseSchema, TimestampSchema


# Company schemas
class CompanyBase(BaseModel):
    """Base company schema with common fields."""
    
    name: str = Field(..., min_length=1, max_length=255)
    legal_name: Optional[str] = Field(None, max_length=255)
    tax_id: Optional[str] = Field(None, max_length=50)
    registration_number: Optional[str] = Field(None, max_length=100)
    
    # Contact information
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = Field(None, max_length=255)
    
    # Address information
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    
    # Business information
    industry: Optional[str] = Field(None, max_length=100)
    company_size: Optional[str] = Field(None, max_length=50)
    founded_year: Optional[int] = Field(None, ge=1800, le=2100)
    description: Optional[str] = None


class CompanyCreate(CompanyBase):
    """Schema for creating a new company."""
    pass


class CompanyUpdate(BaseModel):
    """Schema for updating company information."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    legal_name: Optional[str] = Field(None, max_length=255)
    tax_id: Optional[str] = Field(None, max_length=50)
    registration_number: Optional[str] = Field(None, max_length=100)
    
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = Field(None, max_length=255)
    
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    
    industry: Optional[str] = Field(None, max_length=100)
    company_size: Optional[str] = Field(None, max_length=50)
    founded_year: Optional[int] = Field(None, ge=1800, le=2100)
    description: Optional[str] = None
    logo_url: Optional[str] = None


class CompanyResponse(CompanyBase, TimestampSchema):
    """Schema for company response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    is_active: bool
    is_verified: bool
    verification_date: Optional[datetime] = None
    logo_url: Optional[str] = None
    parent_company_id: Optional[UUID] = None


class CompanyDetail(CompanyResponse):
    """Detailed company schema with additional information."""
    
    settings: Optional[Dict[str, Any]] = None
    created_by_id: Optional[UUID] = None
    updated_by_id: Optional[UUID] = None


# Company user schemas
class CompanyUserBase(BaseModel):
    """Base company user schema."""
    
    role: str = Field(..., max_length=50)
    permissions: Optional[Dict[str, Any]] = None


class CompanyUserInvite(BaseModel):
    """Schema for inviting users to company."""
    
    email: EmailStr
    role: str = Field(..., max_length=50)
    permissions: Optional[Dict[str, Any]] = None


class CompanyUserUpdate(BaseModel):
    """Schema for updating company user."""
    
    role: Optional[str] = Field(None, max_length=50)
    permissions: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class CompanyUserResponse(CompanyUserBase, TimestampSchema):
    """Schema for company user response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    company_id: UUID
    user_id: UUID
    is_active: bool
    invited_at: Optional[datetime] = None
    joined_at: Optional[datetime] = None
    invited_by_id: Optional[UUID] = None


class CompanyUserDetail(CompanyUserResponse):
    """Detailed company user schema with user information."""
    
    user_email: Optional[str] = None
    user_first_name: Optional[str] = None
    user_last_name: Optional[str] = None


# Company invitation schemas
class CompanyInvitationResponse(BaseModel):
    """Schema for company invitation response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    company_id: UUID
    email: str
    role: str
    status: str
    token: str
    expires_at: datetime
    invited_by_id: UUID
    accepted_by_id: Optional[UUID] = None
    accepted_at: Optional[datetime] = None
    created_at: datetime


class CompanyInvitationAccept(BaseModel):
    """Schema for accepting company invitation."""
    
    token: str = Field(..., min_length=1)


# Company document schemas
class CompanyDocumentBase(BaseModel):
    """Base company document schema."""
    
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    document_type: str = Field(..., max_length=50)
    tags: Optional[List[str]] = None


class CompanyDocumentCreate(CompanyDocumentBase):
    """Schema for creating company document."""
    
    file_url: str = Field(..., min_length=1)
    file_name: str = Field(..., min_length=1, max_length=255)
    file_size: Optional[int] = Field(None, ge=0)
    mime_type: Optional[str] = Field(None, max_length=100)
    expires_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class CompanyDocumentUpdate(BaseModel):
    """Schema for updating company document."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    document_type: Optional[str] = Field(None, max_length=50)
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class CompanyDocumentResponse(CompanyDocumentBase, TimestampSchema):
    """Schema for company document response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    company_id: UUID
    file_url: str
    file_name: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    is_active: bool
    expires_at: Optional[datetime] = None
    created_by_id: Optional[UUID] = None


# Company settings schemas
class CompanySettingsBase(BaseModel):
    """Base company settings schema."""
    
    timezone: str = Field(default="UTC", max_length=50)
    currency: str = Field(default="USD", max_length=10)
    language: str = Field(default="en", max_length=10)
    date_format: str = Field(default="YYYY-MM-DD", max_length=20)
    fiscal_year_start: str = Field(default="01-01", max_length=5)


class CompanySettingsCreate(CompanySettingsBase):
    """Schema for creating company settings."""
    
    business_hours: Optional[Dict[str, Any]] = None
    email_notifications: bool = Field(default=True)
    slack_webhook_url: Optional[str] = None
    teams_webhook_url: Optional[str] = None
    features_enabled: Optional[Dict[str, bool]] = None
    integrations: Optional[Dict[str, Any]] = None


class CompanySettingsUpdate(BaseModel):
    """Schema for updating company settings."""
    
    timezone: Optional[str] = Field(None, max_length=50)
    currency: Optional[str] = Field(None, max_length=10)
    language: Optional[str] = Field(None, max_length=10)
    date_format: Optional[str] = Field(None, max_length=20)
    fiscal_year_start: Optional[str] = Field(None, max_length=5)
    business_hours: Optional[Dict[str, Any]] = None
    email_notifications: Optional[bool] = None
    slack_webhook_url: Optional[str] = None
    teams_webhook_url: Optional[str] = None
    features_enabled: Optional[Dict[str, bool]] = None
    integrations: Optional[Dict[str, Any]] = None


class CompanySettingsResponse(CompanySettingsBase, TimestampSchema):
    """Schema for company settings response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    company_id: UUID
    business_hours: Optional[Dict[str, Any]] = None
    email_notifications: bool
    slack_webhook_url: Optional[str] = None
    teams_webhook_url: Optional[str] = None
    features_enabled: Optional[Dict[str, bool]] = None
    integrations: Optional[Dict[str, Any]] = None


# Statistics and summary schemas
class CompanyStats(BaseModel):
    """Company statistics schema."""
    
    total_users: int = 0
    active_users: int = 0
    total_tenders: int = 0
    active_tenders: int = 0
    total_quotes: int = 0
    pending_quotes: int = 0


class CompanySummary(BaseModel):
    """Company summary schema for listings."""
    
    id: UUID
    name: str
    industry: Optional[str] = None
    company_size: Optional[str] = None
    is_verified: bool
    logo_url: Optional[str] = None
    user_role: Optional[str] = None  # Current user's role in this company
