"""
Authentication domain initialization.
"""

from app.domains.auth.models import User, RefreshToken, ApiKey, UserSession
from app.domains.auth.repository import (
    UserRepository,
    RefreshTokenRepository,
    ApiKeyRepository,
    UserSessionRepository,
)
from app.domains.auth.service import AuthService
from app.domains.auth.schemas import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserProfile,
    LoginRequest,
    LoginResponse,
    Token,
    ApiKeyCreate,
    ApiKeyResponse,
    SessionResponse,
)

__all__ = [
    # Models
    "User",
    "RefreshToken",
    "ApiKey",
    "UserSession",
    # Repositories
    "UserRepository",
    "RefreshTokenRepository",
    "ApiKeyRepository",
    "UserSessionRepository",
    # Service
    "AuthService",
    # Schemas
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserProfile",
    "LoginRequest",
    "LoginResponse",
    "Token",
    "ApiKeyCreate",
    "ApiKeyResponse",
    "SessionResponse",
]
