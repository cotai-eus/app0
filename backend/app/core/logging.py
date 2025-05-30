"""
Sistema de logging estruturado
"""

import logging
import sys
from typing import Any, Dict

import structlog
from structlog import configure, get_logger
from structlog.stdlib import LoggerFactory

from app.core.config import settings


def setup_logging() -> None:
    """Configura o sistema de logging estruturado"""
    
    # Configuração do logging padrão
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper()),
    )

    # Processadores para logging estruturado
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Formato de saída baseado na configuração
    if settings.log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    # Configuração do structlog
    configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger_with_context(**context: Any) -> structlog.BoundLogger:
    """Retorna um logger com contexto adicional"""
    logger = get_logger()
    if context:
        logger = logger.bind(**context)
    return logger


def log_request_middleware():
    """Middleware para logging de requisições"""
    import time
    from fastapi import Request, Response
    from starlette.middleware.base import BaseHTTPMiddleware
    
    class LoggingMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            start_time = time.time()
            
            # Contexto da requisição
            request_context = {
                "method": request.method,
                "url": str(request.url),
                "user_agent": request.headers.get("user-agent"),
                "client_ip": request.client.host if request.client else None,
            }
            
            logger = get_logger_with_context(**request_context)
            
            try:
                response: Response = await call_next(request)
                
                # Log da resposta
                process_time = time.time() - start_time
                logger.info(
                    "Request completed",
                    status_code=response.status_code,
                    process_time=f"{process_time:.4f}s",
                )
                
                return response
                
            except Exception as exc:
                process_time = time.time() - start_time
                logger.error(
                    "Request failed",
                    error=str(exc),
                    process_time=f"{process_time:.4f}s",
                    exc_info=True,
                )
                raise
    
    return LoggingMiddleware


def log_exception(exc: Exception, context: Dict[str, Any] = None) -> None:
    """Log estruturado de exceções"""
    logger = get_logger()
    if context:
        logger = logger.bind(**context)
    
    logger.error(
        "Exception occurred",
        exception_type=type(exc).__name__,
        exception_message=str(exc),
        exc_info=True,
    )
