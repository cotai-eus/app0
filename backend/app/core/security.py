"""
Sistema de segurança - JWT, hashing e autenticação
"""

from datetime import datetime, timedelta
from typing import Any, Optional, Union

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import settings
from app.core.exceptions import UnauthorizedException
from app.core.logging import get_logger_with_context

logger = get_logger_with_context(component="security")

# Contexto para hashing de senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenData(BaseModel):
    """Dados do token JWT"""
    username: Optional[str] = None
    user_id: Optional[str] = None
    scopes: list[str] = []


class Token(BaseModel):
    """Resposta do token"""
    access_token: str
    token_type: str
    expires_in: int


def create_password_hash(password: str) -> str:
    """Cria hash da senha"""
    return pwd_context.hash(password)


# Alias para compatibilidade com imports existentes
get_password_hash = create_password_hash


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha está correta"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict, 
    expires_delta: Optional[timedelta] = None
) -> str:
    """Cria token JWT de acesso"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    
    to_encode.update({"exp": expire})
    
    try:
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.secret_key, 
            algorithm=settings.algorithm
        )
        
        logger.debug("Access token created", user_id=data.get("sub"))
        return encoded_jwt
        
    except Exception as exc:
        logger.error("Failed to create access token", error=str(exc))
        raise UnauthorizedException("Could not create access token")


def verify_token(token: str) -> TokenData:
    """Verifica e decodifica token JWT"""
    try:
        payload = jwt.decode(
            token, 
            settings.secret_key, 
            algorithms=[settings.algorithm]
        )
        
        username: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        scopes: list[str] = payload.get("scopes", [])
        
        if username is None:
            raise UnauthorizedException("Invalid token")
        
        token_data = TokenData(
            username=username,
            user_id=user_id,
            scopes=scopes
        )
        
        logger.debug("Token verified successfully", user_id=user_id)
        return token_data
        
    except JWTError as exc:
        logger.warning("Token verification failed", error=str(exc))
        raise UnauthorizedException("Could not validate credentials")


def create_refresh_token(user_id: str) -> str:
    """Cria token de refresh (válido por mais tempo)"""
    data = {
        "sub": user_id,
        "type": "refresh",
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    
    return jwt.encode(
        data, 
        settings.secret_key, 
        algorithm=settings.algorithm
    )


def verify_refresh_token(token: str) -> str:
    """Verifica token de refresh e retorna user_id"""
    try:
        payload = jwt.decode(
            token, 
            settings.secret_key, 
            algorithms=[settings.algorithm]
        )
        
        if payload.get("type") != "refresh":
            raise UnauthorizedException("Invalid refresh token")
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise UnauthorizedException("Invalid refresh token")
        
        return user_id
        
    except JWTError:
        raise UnauthorizedException("Invalid refresh token")


class SecurityScopes:
    """Definição de escopos de segurança"""
    
    # Autenticação básica
    AUTHENTICATED = "authenticated"
    
    # Gestão de usuários
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"
    
    # Gestão de empresas
    COMPANY_READ = "company:read"
    COMPANY_WRITE = "company:write"
    COMPANY_DELETE = "company:delete"
    
    # Gestão de licitações
    TENDER_READ = "tender:read"
    TENDER_WRITE = "tender:write"
    TENDER_DELETE = "tender:delete"
    
    # Gestão de cotações
    QUOTE_READ = "quote:read"
    QUOTE_WRITE = "quote:write"
    QUOTE_DELETE = "quote:delete"
    
    # Administração
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
    
    @classmethod
    def get_all_scopes(cls) -> list[str]:
        """Retorna todos os escopos disponíveis"""
        return [
            value for name, value in cls.__dict__.items() 
            if not name.startswith('_') and isinstance(value, str)
        ]


def check_permissions(required_scopes: list[str], user_scopes: list[str]) -> bool:
    """Verifica se o usuário tem as permissões necessárias"""
    
    # Super admin tem acesso a tudo
    if SecurityScopes.SUPER_ADMIN in user_scopes:
        return True
    
    # Admin tem acesso a operações básicas
    if SecurityScopes.ADMIN in user_scopes:
        admin_allowed = [
            SecurityScopes.USER_READ, SecurityScopes.USER_WRITE,
            SecurityScopes.COMPANY_READ, SecurityScopes.COMPANY_WRITE,
            SecurityScopes.TENDER_READ, SecurityScopes.TENDER_WRITE,
            SecurityScopes.QUOTE_READ, SecurityScopes.QUOTE_WRITE,
        ]
        if all(scope in admin_allowed for scope in required_scopes):
            return True
    
    # Verifica escopo específico
    return all(scope in user_scopes for scope in required_scopes)


def generate_api_key() -> str:
    """Gera uma chave de API"""
    import secrets
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """Cria hash da chave de API"""
    return create_password_hash(api_key)


def verify_api_key(api_key: str, hashed_key: str) -> bool:
    """Verifica chave de API"""
    return verify_password(api_key, hashed_key)
