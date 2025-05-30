"""
Dependências globais da API
"""

from typing import Generator, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.logging import get_logger_with_context
from app.core.redis_client import CacheService, get_redis
from app.core.security import SecurityScopes, TokenData, check_permissions, verify_token

logger = get_logger_with_context(component="dependencies")

# Security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> TokenData:
    """Extrai e valida o token JWT"""
    
    if not credentials:
        logger.warning("No authorization header provided")
        raise UnauthorizedException("Authorization header required")
    
    token = credentials.credentials
    token_data = verify_token(token)
    
    logger.debug("User authenticated", user_id=token_data.user_id)
    return token_data


async def get_current_user(
    token_data: TokenData = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Retorna dados do usuário atual"""
    
    # Aqui você implementaria a busca do usuário no banco
    # Por enquanto, retornamos os dados do token
    user_data = {
        "id": token_data.user_id,
        "username": token_data.username,
        "scopes": token_data.scopes,
        "is_active": True,
    }
    
    logger.debug("Current user retrieved", user_id=user_data["id"])
    return user_data


def require_permissions(required_scopes: list[str]):
    """Decorator/dependency para verificar permissões"""
    
    def permission_dependency(
        current_user: dict = Depends(get_current_user)
    ) -> dict:
        user_scopes = current_user.get("scopes", [])
        
        if not check_permissions(required_scopes, user_scopes):
            logger.warning(
                "Insufficient permissions",
                user_id=current_user["id"],
                required_scopes=required_scopes,
                user_scopes=user_scopes
            )
            raise ForbiddenException(
                f"Insufficient permissions. Required: {required_scopes}"
            )
        
        logger.debug(
            "Permission check passed",
            user_id=current_user["id"],
            required_scopes=required_scopes
        )
        
        return current_user
    
    return permission_dependency


def require_scope(scope: str):
    """Dependency para verificar escopo específico"""
    return require_permissions([scope])


# Dependências específicas para diferentes níveis de acesso
def require_authenticated():
    """Requer apenas autenticação"""
    return require_scope(SecurityScopes.AUTHENTICATED)


def require_admin():
    """Requer permissões de admin"""
    return require_scope(SecurityScopes.ADMIN)


def require_super_admin():
    """Requer permissões de super admin"""
    return require_scope(SecurityScopes.SUPER_ADMIN)


# Dependências para domínios específicos
def require_user_read():
    return require_scope(SecurityScopes.USER_READ)


def require_user_write():
    return require_scope(SecurityScopes.USER_WRITE)


def require_company_read():
    return require_scope(SecurityScopes.COMPANY_READ)


def require_company_write():
    return require_scope(SecurityScopes.COMPANY_WRITE)


def require_tender_read():
    return require_scope(SecurityScopes.TENDER_READ)


def require_tender_write():
    return require_scope(SecurityScopes.TENDER_WRITE)


def require_quote_read():
    return require_scope(SecurityScopes.QUOTE_READ)


def require_quote_write():
    return require_scope(SecurityScopes.QUOTE_WRITE)


async def get_cache_service(
    redis_client = Depends(get_redis)
) -> CacheService:
    """Dependency para o serviço de cache"""
    return CacheService(redis_client)


async def get_request_id(request: Request) -> str:
    """Dependency para obter o ID da requisição"""
    return getattr(request.state, "request_id", "unknown")


class CommonQueryParams:
    """Parâmetros de query comuns para paginação"""
    
    def __init__(
        self,
        skip: int = 0,
        limit: int = 100,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
    ):
        self.skip = max(0, skip)
        self.limit = min(1000, max(1, limit))  # Máximo de 1000 itens
        self.sort_by = sort_by
        self.sort_order = sort_order.lower() if sort_order else "asc"
        
        if self.sort_order not in ["asc", "desc"]:
            self.sort_order = "asc"


def get_common_params(
    skip: int = 0,
    limit: int = 100,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
) -> CommonQueryParams:
    """Dependency para parâmetros comuns de query"""
    return CommonQueryParams(skip, limit, sort_by, sort_order)
