"""
Middleware stack para a aplicação
"""

import time
from typing import Callable

from fastapi import Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.logging import get_logger_with_context
from app.core.redis_client import CacheService, get_redis


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware para headers de segurança"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Headers de segurança
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware para rate limiting"""
    
    def __init__(self, app, calls: int = 60, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Pula rate limiting para health checks
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)
        
        # Identifica cliente
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        identifier = f"{client_ip}:{user_agent}"
        
        try:
            redis_client = await get_redis()
            cache_service = CacheService(redis_client)
            
            is_allowed, current_count = await cache_service.rate_limit_check(
                identifier, self.calls, self.period
            )
            
            if not is_allowed:
                logger = get_logger_with_context(
                    component="rate_limit",
                    client_ip=client_ip,
                    current_count=current_count,
                    limit=self.calls
                )
                logger.warning("Rate limit exceeded")
                
                return Response(
                    content="Rate limit exceeded",
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    headers={
                        "X-RateLimit-Limit": str(self.calls),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(time.time()) + self.period),
                    }
                )
            
            response = await call_next(request)
            
            # Adiciona headers de rate limit
            remaining = max(0, self.calls - current_count)
            response.headers["X-RateLimit-Limit"] = str(self.calls)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + self.period)
            
            return response
            
        except Exception as exc:
            # Em caso de erro no Redis, permite a requisição
            logger = get_logger_with_context(component="rate_limit")
            logger.error("Rate limit middleware error", error=str(exc))
            return await call_next(request)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware para adicionar ID único às requisições"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        import uuid
        
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware para coleta de métricas"""
    
    def __init__(self, app):
        super().__init__(app)
        self.setup_metrics()
    
    def setup_metrics(self):
        """Configura métricas Prometheus"""
        from prometheus_client import Counter, Histogram, Gauge
        
        self.request_count = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code']
        )
        
        self.request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration',
            ['method', 'endpoint']
        )
        
        self.active_requests = Gauge(
            'http_requests_active',
            'Active HTTP requests'
        )
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        self.active_requests.inc()
        
        try:
            response = await call_next(request)
            
            # Coleta métricas
            duration = time.time() - start_time
            method = request.method
            endpoint = request.url.path
            status_code = response.status_code
            
            self.request_count.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()
            
            self.request_duration.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            return response
            
        finally:
            self.active_requests.dec()


def setup_middleware(app):
    """Configura todos os middlewares da aplicação"""
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Trusted hosts (em produção)
    if not settings.debug:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["localhost", "127.0.0.1", "0.0.0.0"]
        )
    
    # Headers de segurança
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Rate limiting
    app.add_middleware(
        RateLimitMiddleware,
        calls=settings.rate_limit_per_minute,
        period=60
    )
    
    # Request ID
    app.add_middleware(RequestIDMiddleware)
    
    # Métricas
    app.add_middleware(MetricsMiddleware)
    
    # Logging de requisições (deve ser o último)
    from app.core.logging import log_request_middleware
    app.add_middleware(log_request_middleware())
