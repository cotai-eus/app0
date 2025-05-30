"""
Authentication domain schemas.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.shared.common.base_schemas import BaseSchema, TimestampSchema


# User schemas
class UserBase(BaseModel):
    """Base user schema with common fields."""
    
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    timezone: str = Field(default="UTC", max_length=50)
    language: str = Field(default="en", max_length=10)


class UserCreate(UserBase):
    """Schema for creating a new user."""
    
    password: str = Field(..., min_length=8, max_length=128)


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    avatar_url: Optional[str] = None
    timezone: Optional[str] = Field(None, max_length=50)
    language: Optional[str] = Field(None, max_length=10)


class UserResponse(UserBase, TimestampSchema):
    """Schema for user response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    is_active: bool
    is_verified: bool
    avatar_url: Optional[str] = None
    last_login_at: Optional[datetime] = None


class UserProfile(UserResponse):
    """Extended user profile schema."""
    
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    password_changed_at: Optional[datetime] = None


# Authentication schemas
class Token(BaseModel):
    """JWT token response schema."""
    
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    refresh_token: Optional[str] = None


class TokenData(BaseModel):
    """Token payload data schema."""
    
    user_id: UUID
    email: str
    scopes: List[str] = []
    exp: datetime
    iat: datetime


class LoginRequest(BaseModel):
    """Login request schema."""
    
    email: EmailStr
    password: str
    remember_me: bool = False
    device_info: Optional[str] = None


class LoginResponse(BaseModel):
    """Login response schema."""
    
    user: UserResponse
    token: Token
    session_id: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""
    
    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Password reset request schema."""
    
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema."""
    
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


class PasswordChange(BaseModel):
    """Password change schema."""
    
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


# API Key schemas
class ApiKeyBase(BaseModel):
    """Base API key schema."""
    
    name: str = Field(..., min_length=1, max_length=100)
    scopes: Optional[List[str]] = None
    expires_at: Optional[datetime] = None
    allowed_ips: Optional[List[str]] = None


class ApiKeyCreate(ApiKeyBase):
    """Schema for creating an API key."""
    pass


class ApiKeyResponse(ApiKeyBase, TimestampSchema):
    """Schema for API key response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    prefix: str
    is_active: bool
    last_used_at: Optional[datetime] = None
    usage_count: int = 0


class ApiKeyWithSecret(ApiKeyResponse):
    """Schema for API key response with secret (only shown once)."""
    
    key: str  # Full API key, only shown on creation


# Session schemas
class SessionResponse(BaseModel):
    """User session response schema."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    device_info: Optional[str] = None
    ip_address: Optional[str] = None
    location: Optional[str] = None
    last_activity_at: Optional[datetime] = None
    created_at: datetime
    expires_at: datetime
    is_active: bool


# Permission schemas
class PermissionCheck(BaseModel):
    """Permission check request schema."""
    
    resource: str
    action: str
    resource_id: Optional[str] = None


class PermissionResponse(BaseModel):
    """Permission check response schema."""
    
    allowed: bool
    reason: Optional[str] = None
