"""
Authentication API endpoints.
"""

from typing import List, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, get_current_user, get_current_active_user
from app.domains.auth.service import AuthService
from app.domains.auth.schemas import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserProfile,
    LoginRequest,
    LoginResponse,
    Token,
    RefreshTokenRequest,
    PasswordChange,
    ApiKeyCreate,
    ApiKeyResponse,
    ApiKeyWithSecret,
    SessionResponse,
)
from app.domains.auth.models import User
from app.core.security import SecurityScopes

router = APIRouter()
security = HTTPBearer()


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_session),
) -> Any:
    """Register a new user."""
    auth_service = AuthService(session)
    user = await auth_service.create_user(user_data)
    return user


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> Any:
    """Login user and return tokens."""
    auth_service = AuthService(session)
    
    # Get client info
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    user, token, session_token = await auth_service.login(
        login_data=login_data,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    # Set session cookie if session tracking is enabled
    if session_token:
        response.set_cookie(
            key="session_id",
            value=session_token,
            httponly=True,
            secure=True,
            samesite="lax",
        )
    
    return LoginResponse(
        user=user,
        token=token,
        session_id=session_token,
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    session: AsyncSession = Depends(get_session),
) -> Any:
    """Refresh access token."""
    auth_service = AuthService(session)
    token = await auth_service.refresh_access_token(refresh_data.refresh_token)
    return token


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> Any:
    """Logout current user."""
    auth_service = AuthService(session)
    
    # Get refresh token from request body or headers
    refresh_token = None
    if hasattr(request, "json"):
        body = await request.json()
        refresh_token = body.get("refresh_token")
    
    # Get session token from cookie
    session_token = request.cookies.get("session_id")
    
    await auth_service.logout(
        user_id=current_user.id,
        refresh_token=refresh_token,
        session_token=session_token,
    )
    
    # Clear session cookie
    response.delete_cookie(key="session_id")
    
    return {"message": "Successfully logged out"}


@router.post("/logout-all")
async def logout_all_sessions(
    response: Response,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> Any:
    """Logout user from all sessions."""
    auth_service = AuthService(session)
    await auth_service.logout_all_sessions(current_user.id)
    
    # Clear session cookie
    response.delete_cookie(key="session_id")
    
    return {"message": "Successfully logged out from all sessions"}


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get current user profile."""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> Any:
    """Update current user profile."""
    auth_service = AuthService(session)
    updated_user = await auth_service.update_user(current_user.id, user_data)
    return updated_user


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> Any:
    """Change user password."""
    auth_service = AuthService(session)
    await auth_service.change_password(
        user_id=current_user.id,
        current_password=password_data.current_password,
        new_password=password_data.new_password,
    )
    return {"message": "Password changed successfully"}


@router.get("/sessions", response_model=List[SessionResponse])
async def get_user_sessions(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> Any:
    """Get all active sessions for current user."""
    auth_service = AuthService(session)
    sessions = await auth_service.get_user_sessions(current_user.id)
    return sessions


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> Any:
    """Revoke a specific session."""
    auth_service = AuthService(session)
    await auth_service.revoke_session(current_user.id, session_id)
    return {"message": "Session revoked successfully"}


@router.post("/api-keys", response_model=ApiKeyWithSecret)
async def create_api_key(
    api_key_data: ApiKeyCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> Any:
    """Create a new API key."""
    auth_service = AuthService(session)
    api_key, secret = await auth_service.create_api_key(
        current_user.id, 
        api_key_data
    )
    
    return ApiKeyWithSecret(
        **api_key.__dict__,
        key=secret,
    )


@router.get("/api-keys", response_model=List[ApiKeyResponse])
async def get_api_keys(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> Any:
    """Get all API keys for current user."""
    auth_service = AuthService(session)
    api_keys = await auth_service.api_key_repo.get_user_api_keys(current_user.id)
    return api_keys


@router.delete("/api-keys/{api_key_id}")
async def revoke_api_key(
    api_key_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> Any:
    """Revoke an API key."""
    auth_service = AuthService(session)
    
    # Get API key and verify ownership
    api_key = await auth_service.api_key_repo.get_by_id(api_key_id)
    if not api_key or api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    await auth_service.api_key_repo.soft_delete(api_key_id)
    return {"message": "API key revoked successfully"}


# Admin endpoints
@router.get(
    "/users",
    response_model=List[UserResponse],
    dependencies=[Depends(get_current_user)],  # Add admin permission check
)
async def get_users(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
) -> Any:
    """Get all users (admin only)."""
    auth_service = AuthService(session)
    users = await auth_service.user_repo.get_multi(skip=skip, limit=limit)
    return users


@router.get(
    "/users/{user_id}",
    response_model=UserProfile,
    dependencies=[Depends(get_current_user)],  # Add admin permission check
)
async def get_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> Any:
    """Get user by ID (admin only)."""
    auth_service = AuthService(session)
    user = await auth_service.user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.put(
    "/users/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(get_current_user)],  # Add admin permission check
)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    session: AsyncSession = Depends(get_session),
) -> Any:
    """Update user (admin only)."""
    auth_service = AuthService(session)
    updated_user = await auth_service.update_user(user_id, user_data)
    return updated_user


@router.delete(
    "/users/{user_id}",
    dependencies=[Depends(get_current_user)],  # Add admin permission check
)
async def delete_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> Any:
    """Delete user (admin only)."""
    auth_service = AuthService(session)
    await auth_service.user_repo.soft_delete(user_id)
    return {"message": "User deleted successfully"}
