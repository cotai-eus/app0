"""
Main FastAPI application for CotAi backend.
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.api.middleware import (
    RequestIDMiddleware,
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    MetricsMiddleware,
)
from app.api.v1.endpoints import health
try:
    from app.api.v1.endpoints import auth, companies, tenders, forms, kanban, documents, monitoring, files, audit
except ImportError:
    auth = companies = tenders = forms = kanban = documents = monitoring = files = audit = None
from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.mongodb import init_mongodb, close_mongodb
from app.core.redis_client import init_redis, close_redis
from app.core.logging import setup_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting CotAi Backend...")
    
    # Initialize logging
    setup_logging()
    
    # Initialize databases
    await init_db()
    await init_mongodb()
    await init_redis()
    
    logger.info("CotAi Backend started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down CotAi Backend...")
    
    # Close database connections
    await close_db()
    await close_mongodb()
    await close_redis()
    
    logger.info("CotAi Backend shutdown complete")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
        lifespan=lifespan,
    )
    
    # Security middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Custom middleware (order matters - first added is outermost)
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIDMiddleware)
    
    # Include routers
    app.include_router(
        health.router,
        prefix=f"{settings.API_V1_STR}/health",
        tags=["health"],
    )
    
    if auth:
        app.include_router(
            auth.router,
            prefix=f"{settings.API_V1_STR}/auth",
            tags=["authentication"],
        )
    
    if companies:
        app.include_router(
            companies.router,
            prefix=f"{settings.API_V1_STR}/companies",
            tags=["companies"],
        )
    
    if tenders:
        app.include_router(
            tenders.router,
            prefix=f"{settings.API_V1_STR}/tenders",
            tags=["tenders"],
        )
    
    if forms:
        app.include_router(
            forms.router,
            prefix=f"{settings.API_V1_STR}/forms",
            tags=["forms"],
        )
    
    if kanban:
        app.include_router(
            kanban.router,
            prefix=f"{settings.API_V1_STR}",
            tags=["kanban"],
        )
    
    if documents:
        app.include_router(
            documents.router,
            prefix=f"{settings.API_V1_STR}/documents",
            tags=["documents", "ai"],
        )
    
    if monitoring:
        app.include_router(
            monitoring.router,
            prefix=f"{settings.API_V1_STR}/monitoring",
            tags=["monitoring", "analytics"],
        )
    
    if files:
        app.include_router(
            files.router,
            prefix=f"{settings.API_V1_STR}/files",
            tags=["files", "storage"],
        )
    
    if audit:
        app.include_router(
            audit.router,
            prefix=f"{settings.API_V1_STR}/audit",
            tags=["audit", "compliance"],
        )
    
    return app


# Create the FastAPI application
app = create_application()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "docs_url": f"{settings.API_V1_STR}/docs",
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.get("/ping")
async def ping():
    """Simple ping endpoint for load balancer health checks."""
    return {"status": "ok", "message": "pong"}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug",
    )
