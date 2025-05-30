"""
Authentication repository for database operations.
"""

from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID

from sqlalchemy import and_, or_, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.auth.models import User, RefreshToken, ApiKey, UserSession
from app.shared.common.base_repository import BaseRepository
from app.core.security import get_password_hash, verify_password


class UserRepository(BaseRepository[User]):
    """Repository for user operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        result = await self.session.execute(
            select(User).where(
                and_(
                    User.email == email,
                    User.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_active_by_email(self, email: str) -> Optional[User]:
        """Get active user by email address."""
        result = await self.session.execute(
            select(User).where(
                and_(
                    User.email == email,
                    User.is_active == True,
                    User.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def create_user(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        **kwargs
    ) -> User:
        """Create a new user with hashed password."""
        hashed_password = get_password_hash(password)
        
        user_data = {
            "email": email,
            "hashed_password": hashed_password,
            "first_name": first_name,
            "last_name": last_name,
            "password_changed_at": datetime.utcnow(),
            **kwargs
        }
        
        return await self.create(user_data)
    
    async def verify_password(self, user: User, password: str) -> bool:
        """Verify user password."""
        return verify_password(password, user.hashed_password)
    
    async def update_password(self, user_id: UUID, new_password: str) -> bool:
        """Update user password."""
        hashed_password = get_password_hash(new_password)
        
        result = await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                hashed_password=hashed_password,
                password_changed_at=datetime.utcnow(),
                failed_login_attempts=0,
                locked_until=None
            )
        )
        
        await self.session.commit()
        return result.rowcount > 0
    
    async def increment_failed_login(self, user_id: UUID) -> None:
        """Increment failed login attempts."""
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                failed_login_attempts=User.failed_login_attempts + 1
            )
        )
        await self.session.commit()
    
    async def lock_user(self, user_id: UUID, lock_duration: timedelta) -> None:
        """Lock user account for specified duration."""
        locked_until = datetime.utcnow() + lock_duration
        
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(locked_until=locked_until)
        )
        await self.session.commit()
    
    async def unlock_user(self, user_id: UUID) -> None:
        """Unlock user account."""
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                locked_until=None,
                failed_login_attempts=0
            )
        )
        await self.session.commit()
    
    async def update_last_login(self, user_id: UUID) -> None:
        """Update user's last login timestamp."""
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                last_login_at=datetime.utcnow(),
                failed_login_attempts=0
            )
        )
        await self.session.commit()


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    """Repository for refresh token operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(RefreshToken, session)
    
    async def get_by_token_hash(self, token_hash: str) -> Optional[RefreshToken]:
        """Get refresh token by token hash."""
        result = await self.session.execute(
            select(RefreshToken).where(
                and_(
                    RefreshToken.token_hash == token_hash,
                    RefreshToken.is_revoked == False,
                    RefreshToken.expires_at > datetime.utcnow()
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def revoke_token(self, token_hash: str) -> bool:
        """Revoke a refresh token."""
        result = await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .values(is_revoked=True)
        )
        await self.session.commit()
        return result.rowcount > 0
    
    async def revoke_all_user_tokens(self, user_id: UUID) -> int:
        """Revoke all refresh tokens for a user."""
        result = await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .values(is_revoked=True)
        )
        await self.session.commit()
        return result.rowcount
    
    async def cleanup_expired_tokens(self) -> int:
        """Clean up expired refresh tokens."""
        result = await self.session.execute(
            delete(RefreshToken).where(
                RefreshToken.expires_at < datetime.utcnow()
            )
        )
        await self.session.commit()
        return result.rowcount


class ApiKeyRepository(BaseRepository[ApiKey]):
    """Repository for API key operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(ApiKey, session)
    
    async def get_by_prefix(self, prefix: str) -> Optional[ApiKey]:
        """Get API key by prefix."""
        result = await self.session.execute(
            select(ApiKey).where(
                and_(
                    ApiKey.prefix == prefix,
                    ApiKey.is_active == True,
                    ApiKey.deleted_at.is_(None),
                    or_(
                        ApiKey.expires_at.is_(None),
                        ApiKey.expires_at > datetime.utcnow()
                    )
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_user_api_keys(self, user_id: UUID) -> List[ApiKey]:
        """Get all API keys for a user."""
        result = await self.session.execute(
            select(ApiKey).where(
                and_(
                    ApiKey.user_id == user_id,
                    ApiKey.deleted_at.is_(None)
                )
            ).order_by(ApiKey.created_at.desc())
        )
        return result.scalars().all()
    
    async def update_usage(self, api_key_id: UUID) -> None:
        """Update API key usage statistics."""
        await self.session.execute(
            update(ApiKey)
            .where(ApiKey.id == api_key_id)
            .values(
                last_used_at=datetime.utcnow(),
                usage_count=ApiKey.usage_count + 1
            )
        )
        await self.session.commit()


class UserSessionRepository(BaseRepository[UserSession]):
    """Repository for user session operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(UserSession, session)
    
    async def get_by_token(self, session_token: str) -> Optional[UserSession]:
        """Get session by token."""
        result = await self.session.execute(
            select(UserSession).where(
                and_(
                    UserSession.session_token == session_token,
                    UserSession.is_active == True,
                    UserSession.expires_at > datetime.utcnow()
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_user_sessions(
        self, 
        user_id: UUID, 
        active_only: bool = True
    ) -> List[UserSession]:
        """Get all sessions for a user."""
        conditions = [UserSession.user_id == user_id]
        
        if active_only:
            conditions.extend([
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            ])
        
        result = await self.session.execute(
            select(UserSession)
            .where(and_(*conditions))
            .order_by(UserSession.last_activity_at.desc())
        )
        return result.scalars().all()
    
    async def update_activity(self, session_token: str) -> None:
        """Update session last activity."""
        await self.session.execute(
            update(UserSession)
            .where(UserSession.session_token == session_token)
            .values(last_activity_at=datetime.utcnow())
        )
        await self.session.commit()
    
    async def revoke_session(self, session_token: str) -> bool:
        """Revoke a user session."""
        result = await self.session.execute(
            update(UserSession)
            .where(UserSession.session_token == session_token)
            .values(is_active=False)
        )
        await self.session.commit()
        return result.rowcount > 0
    
    async def revoke_all_user_sessions(
        self, 
        user_id: UUID, 
        except_token: Optional[str] = None
    ) -> int:
        """Revoke all sessions for a user, optionally except one."""
        conditions = [UserSession.user_id == user_id]
        
        if except_token:
            conditions.append(UserSession.session_token != except_token)
        
        result = await self.session.execute(
            update(UserSession)
            .where(and_(*conditions))
            .values(is_active=False)
        )
        await self.session.commit()
        return result.rowcount
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        result = await self.session.execute(
            delete(UserSession).where(
                UserSession.expires_at < datetime.utcnow()
            )
        )
        await self.session.commit()
        return result.rowcount
