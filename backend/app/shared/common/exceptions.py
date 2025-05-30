"""
Common application exceptions.
"""

from typing import Any, Dict, Optional


class BaseAppException(Exception):
    """Base application exception."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(BaseAppException):
    """Resource not found exception."""
    pass


# Alias for compatibility
NotFoundException = NotFoundError


class ValidationError(BaseAppException):
    """Validation error exception."""
    pass


# Alias for compatibility
ValidationException = ValidationError


class PermissionError(BaseAppException):
    """Permission denied exception."""
    pass


# Alias for compatibility
PermissionDeniedException = PermissionError


class ConflictError(BaseAppException):
    """Resource conflict exception."""
    pass


# Alias for compatibility
ConflictException = ConflictError


class DatabaseError(BaseAppException):
    """Database operation error."""
    pass


class ServiceUnavailableError(BaseAppException):
    """Service unavailable error."""
    pass


class BusinessException(BaseAppException):
    """Business logic exception."""
    pass


class ConfigurationError(BaseAppException):
    """Configuration error exception."""
    pass


# Additional aliases for backward compatibility
CotAiException = BaseAppException
HTTPException = BaseAppException
BadRequestException = ValidationError
ForbiddenException = PermissionError
UnauthorizedException = PermissionError
