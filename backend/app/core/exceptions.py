"""
Sistema de exceções personalizadas e tratamento de erros
"""

from typing import Any, Dict, Optional

from fastapi import HTTPException, Request, status
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger_with_context, log_exception


class CotAiException(Exception):
    """Exceção base da aplicação"""
    
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(CotAiException):
    """Exceção para erros de validação"""
    
    def __init__(self, message: str, field: str = None, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details={"field": field, **(details or {})}
        )


class NotFoundException(CotAiException):
    """Exceção para recursos não encontrados"""
    
    def __init__(self, resource: str, identifier: Any = None):
        message = f"{resource} not found"
        if identifier:
            message += f" (ID: {identifier})"
        
        super().__init__(
            message=message,
            code="NOT_FOUND",
            details={"resource": resource, "identifier": str(identifier)}
        )


class UnauthorizedException(CotAiException):
    """Exceção para erros de autenticação"""
    
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
        )


class ForbiddenException(CotAiException):
    """Exceção para erros de autorização"""
    
    def __init__(self, message: str = "Access forbidden"):
        super().__init__(
            message=message,
            code="FORBIDDEN",
        )


class BusinessException(CotAiException):
    """Exceção para regras de negócio"""
    
    def __init__(self, message: str, rule: str = None):
        super().__init__(
            message=message,
            code="BUSINESS_RULE_VIOLATION",
            details={"rule": rule}
        )


class ExternalServiceException(CotAiException):
    """Exceção para erros em serviços externos"""
    
    def __init__(self, service: str, message: str, status_code: int = None):
        super().__init__(
            message=f"External service error ({service}): {message}",
            code="EXTERNAL_SERVICE_ERROR",
            details={"service": service, "status_code": status_code}
        )


class DatabaseException(CotAiException):
    """Exceção para erros de banco de dados"""
    
    def __init__(self, message: str, operation: str = None):
        super().__init__(
            message=f"Database error: {message}",
            code="DATABASE_ERROR",
            details={"operation": operation}
        )


# Handlers de exceção

async def cotai_exception_handler(request: Request, exc: CotAiException) -> JSONResponse:
    """Handler para exceções personalizadas da aplicação"""
    
    # Map de códigos para status HTTP
    status_map = {
        "VALIDATION_ERROR": status.HTTP_400_BAD_REQUEST,
        "NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "UNAUTHORIZED": status.HTTP_401_UNAUTHORIZED,
        "FORBIDDEN": status.HTTP_403_FORBIDDEN,
        "BUSINESS_RULE_VIOLATION": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "EXTERNAL_SERVICE_ERROR": status.HTTP_502_BAD_GATEWAY,
        "DATABASE_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "INTERNAL_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
    }
    
    status_code = status_map.get(exc.code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Log do erro
    logger = get_logger_with_context(
        url=str(request.url),
        method=request.method,
        error_code=exc.code,
    )
    
    if status_code >= 500:
        logger.error("Application error", error=exc.message, details=exc.details)
    else:
        logger.warning("Client error", error=exc.message, details=exc.details)
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


async def validation_exception_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """Handler para erros de validação do Pydantic"""
    
    logger = get_logger_with_context(
        url=str(request.url),
        method=request.method,
    )
    
    logger.warning("Validation error", errors=exc.errors())
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Validation failed",
                "details": {
                    "errors": exc.errors()
                }
            }
        },
    )


async def http_exception_handler_custom(
    request: Request, exc: HTTPException
) -> JSONResponse:
    """Handler customizado para HTTPException"""
    
    logger = get_logger_with_context(
        url=str(request.url),
        method=request.method,
        status_code=exc.status_code,
    )
    
    if exc.status_code >= 500:
        logger.error("HTTP error", error=exc.detail)
    else:
        logger.warning("HTTP error", error=exc.detail)
    
    return await http_exception_handler(request, exc)


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler para exceções não tratadas"""
    
    log_exception(
        exc,
        context={
            "url": str(request.url),
            "method": request.method,
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {},
            }
        },
    )
