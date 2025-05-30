"""
Authentication service for business logic.
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.auth.models import User, RefreshToken, ApiKey, UserSession
from app.domains.auth.repository import (
    UserRepository,
    RefreshTokenRepository,
    ApiKeyRepository,
    UserSessionRepository,
)
from app.domains.auth.schemas import (
    UserCreate,
    UserUpdate,
    LoginRequest,
    Token,
    ApiKeyCreate,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    get_password_hash,
)
from app.core.config import settings
from app.shared.common.base_service import BaseService


class AuthService(BaseService):
    """Authentication service for user management and authentication."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.user_repo = UserRepository(session)
        self.refresh_token_repo = RefreshTokenRepository(session)
        self.api_key_repo = ApiKeyRepository(session)
        self.session_repo = UserSessionRepository(session)
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user."""
        # Check if email already exists
        existing_user = await self.user_repo.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user
        user = await self.user_repo.create_user(
            email=user_data.email,
            password=user_data.password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone=user_data.phone,
            timezone=user_data.timezone,
            language=user_data.language,
        )
        
        self.logger.info(f"User created: {user.email}")
        return user
    
    async def authenticate_user(
        self, 
        email: str, 
        password: str
    ) -> Optional[User]:
        """Authenticate user with email and password."""
        user = await self.user_repo.get_active_by_email(email)
        if not user:
            return None
        
        # Check if user is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account is temporarily locked"
            )
        
        # Verify password
        if not await self.user_repo.verify_password(user, password):
            # Increment failed attempts
            await self.user_repo.increment_failed_login(user.id)
            
            # Lock account if too many failed attempts
            if int(user.failed_login_attempts) >= settings.MAX_LOGIN_ATTEMPTS - 1:
                await self.user_repo.lock_user(
                    user.id, 
                    timedelta(minutes=settings.ACCOUNT_LOCK_MINUTES)
                )
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail="Account locked due to too many failed attempts"
                )
            
            return None
        
        # Update last login
        await self.user_repo.update_last_login(user.id)
        return user
    
    async def login(
        self, 
        login_data: LoginRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[User, Token, Optional[str]]:
        """Login user and create tokens."""
        user = await self.authenticate_user(
            login_data.email, 
            login_data.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email not verified"
            )
        
        # Create access token
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        # Create refresh token if remember_me is True
        refresh_token = None
        if login_data.remember_me:
            refresh_token_data = create_refresh_token()
            refresh_token = refresh_token_data["token"]
            
            # Store refresh token in database
            await self.refresh_token_repo.create({
                "user_id": user.id,
                "token_hash": refresh_token_data["token_hash"],
                "expires_at": refresh_token_data["expires_at"],
                "device_info": login_data.device_info,
                "ip_address": ip_address,
            })
        
        # Create user session
        session_token = None
        if settings.TRACK_USER_SESSIONS:
            session_token = secrets.token_urlsafe(32)
            await self.session_repo.create({
                "user_id": user.id,
                "session_token": session_token,
                "expires_at": datetime.utcnow() + timedelta(
                    seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
                ),
                "device_info": login_data.device_info,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "last_activity_at": datetime.utcnow(),
            })
        
        token = Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_token=refresh_token,
        )
        
        self.logger.info(f"User logged in: {user.email}")
        return user, token, session_token
    
    async def refresh_access_token(self, refresh_token: str) -> Token:
        """Refresh access token using refresh token."""
        # Hash the refresh token
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        
        # Get refresh token from database
        stored_token = await self.refresh_token_repo.get_by_token_hash(
            token_hash
        )
        
        if not stored_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user
        user = await self.user_repo.get_by_id(stored_token.user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new access token
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
    
    async def logout(
        self, 
        user_id: UUID, 
        refresh_token: Optional[str] = None,
        session_token: Optional[str] = None,
    ) -> None:
        """Logout user and revoke tokens."""
        # Revoke refresh token if provided
        if refresh_token:
            token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
            await self.refresh_token_repo.revoke_token(token_hash)
        
        # Revoke session if provided
        if session_token:
            await self.session_repo.revoke_session(session_token)
        
        self.logger.info(f"User logged out: {user_id}")
    
    async def logout_all_sessions(self, user_id: UUID) -> None:
        """Logout user from all sessions."""
        # Revoke all refresh tokens
        await self.refresh_token_repo.revoke_all_user_tokens(user_id)
        
        # Revoke all sessions
        await self.session_repo.revoke_all_user_sessions(user_id)
        
        self.logger.info(f"All sessions revoked for user: {user_id}")
    
    async def update_user(
        self, 
        user_id: UUID, 
        user_data: UserUpdate
    ) -> User:
        """Update user information."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        update_data = user_data.model_dump(exclude_unset=True)
        updated_user = await self.user_repo.update(user_id, update_data)
        
        self.logger.info(f"User updated: {user.email}")
        return updated_user
    
    async def change_password(
        self, 
        user_id: UUID, 
        current_password: str, 
        new_password: str
    ) -> None:
        """Change user password."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password
        if not await self.user_repo.verify_password(user, current_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        await self.user_repo.update_password(user_id, new_password)
        
        # Revoke all sessions except current
        await self.logout_all_sessions(user_id)
        
        self.logger.info(f"Password changed for user: {user.email}")
    
    async def create_api_key(
        self, 
        user_id: UUID, 
        api_key_data: ApiKeyCreate
    ) -> Tuple[ApiKey, str]:
        """Create a new API key."""
        # Generate API key
        key = f"cotai_{secrets.token_urlsafe(32)}"
        prefix = key[:12]  # "cotai_" + first 6 chars
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        # Create API key record
        api_key = await self.api_key_repo.create({
            "name": api_key_data.name,
            "key_hash": key_hash,
            "prefix": prefix,
            "user_id": user_id,
            "scopes": api_key_data.scopes,
            "expires_at": api_key_data.expires_at,
            "allowed_ips": api_key_data.allowed_ips,
        })
        
        self.logger.info(f"API key created: {api_key.name} for user {user_id}")
        return api_key, key
    
    async def verify_api_key(self, api_key: str) -> Optional[ApiKey]:
        """Verify API key and return the key object."""
        if not api_key.startswith("cotai_"):
            return None
        
        prefix = api_key[:12]
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Get API key by prefix
        stored_key = await self.api_key_repo.get_by_prefix(prefix)
        if not stored_key or stored_key.key_hash != key_hash:
            return None
        
        # Update usage statistics
        await self.api_key_repo.update_usage(stored_key.id)
        
        return stored_key
    
    async def get_user_sessions(self, user_id: UUID) -> List[UserSession]:
        """Get all active sessions for a user."""
        return await self.session_repo.get_user_sessions(user_id)
    
    async def revoke_session(
        self, 
        user_id: UUID, 
        session_id: UUID
    ) -> None:
        """Revoke a specific user session."""
        session = await self.session_repo.get_by_id(session_id)
        if not session or session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        await self.session_repo.revoke_session(session.session_token)
        self.logger.info(f"Session revoked: {session_id} for user {user_id}")
    
    async def cleanup_expired_tokens(self) -> None:
        """Clean up expired tokens and sessions."""
        refresh_count = await self.refresh_token_repo.cleanup_expired_tokens()
        session_count = await self.session_repo.cleanup_expired_sessions()
        
        self.logger.info(
            f"Cleaned up {refresh_count} refresh tokens and "
            f"{session_count} sessions"
        )
