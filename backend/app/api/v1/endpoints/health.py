"""
Sistema de health check e monitoramento
"""

import asyncio
import time
from datetime import datetime
from typing import Dict

import psutil
from fastapi import APIRouter, Depends
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, generate_latest
from starlette.responses import Response

from app.core.config import settings
from app.core.database import engine
from app.core.logging import get_logger_with_context
from app.core.mongodb import mongodb
from app.core.redis_client import redis_client
from app.shared.common.base_schemas import HealthResponse, MetricsResponse

logger = get_logger_with_context(component="health")

# Router para endpoints de monitoramento
router = APIRouter(prefix="/health", tags=["Health"])

# Tempo de início da aplicação
startup_time = time.time()


async def check_database() -> tuple[str, str]:
    """Verifica conectividade com PostgreSQL"""
    try:
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        return "healthy", "PostgreSQL connection successful"
    except Exception as exc:
        logger.error("Database health check failed", error=str(exc))
        return "unhealthy", f"PostgreSQL error: {str(exc)}"


async def check_redis() -> tuple[str, str]:
    """Verifica conectividade com Redis"""
    try:
        if not redis_client.client:
            await redis_client.connect()
        await redis_client.client.ping()
        return "healthy", "Redis connection successful"
    except Exception as exc:
        logger.error("Redis health check failed", error=str(exc))
        return "unhealthy", f"Redis error: {str(exc)}"


async def check_mongodb() -> tuple[str, str]:
    """Verifica conectividade com MongoDB"""
    try:
        if not mongodb.client:
            from app.core.mongodb import connect_to_mongo
            await connect_to_mongo()
        await mongodb.client.admin.command("ping")
        return "healthy", "MongoDB connection successful"
    except Exception as exc:
        logger.error("MongoDB health check failed", error=str(exc))
        return "unhealthy", f"MongoDB error: {str(exc)}"


async def check_all_services() -> Dict[str, str]:
    """Verifica todos os serviços"""
    services = {}
    
    # Executa verificações em paralelo
    db_status, db_message = await check_database()
    redis_status, redis_message = await check_redis()
    mongo_status, mongo_message = await check_mongodb()
    
    services["database"] = f"{db_status}: {db_message}"
    services["redis"] = f"{redis_status}: {redis_message}"
    services["mongodb"] = f"{mongo_status}: {mongo_message}"
    
    return services


@router.get("/", response_model=HealthResponse)
async def health_check():
    """Endpoint básico de health check"""
    uptime = time.time() - startup_time
    
    return HealthResponse(
        status="healthy",
        version=settings.version,
        uptime=uptime
    )


@router.get("/detailed", response_model=HealthResponse)
async def detailed_health_check():
    """Health check detalhado incluindo serviços externos"""
    uptime = time.time() - startup_time
    services = await check_all_services()
    
    # Determina status geral
    overall_status = "healthy"
    for service_status in services.values():
        if "unhealthy" in service_status:
            overall_status = "degraded"
            break
    
    return HealthResponse(
        status=overall_status,
        version=settings.version,
        uptime=uptime,
        services=services
    )


@router.get("/ready")
async def readiness_check():
    """Verifica se a aplicação está pronta para receber tráfego"""
    services = await check_all_services()
    
    # Verifica se todos os serviços críticos estão healthy
    critical_services = ["database", "redis"]
    ready = all(
        "healthy" in services.get(service, "")
        for service in critical_services
    )
    
    status_code = 200 if ready else 503
    
    return Response(
        content=f"Ready: {ready}",
        status_code=status_code,
        headers={"Content-Type": "text/plain"}
    )


@router.get("/live")
async def liveness_check():
    """Verifica se a aplicação está viva (para Kubernetes)"""
    return Response(
        content="Alive",
        status_code=200,
        headers={"Content-Type": "text/plain"}
    )


@router.get("/metrics")
async def get_metrics():
    """Endpoint para métricas Prometheus"""
    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST
    )


@router.get("/metrics/detailed", response_model=MetricsResponse)
async def get_detailed_metrics():
    """Métricas detalhadas em formato JSON"""
    
    # Métricas de sistema
    memory = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent()
    
    # Métricas de banco de dados
    db_pool = engine.pool
    db_connections = {
        "total": db_pool.size(),
        "checked_in": db_pool.checkedin(),
        "checked_out": db_pool.checkedout(),
        "overflow": db_pool.overflow(),
    }
    
    return MetricsResponse(
        requests_total=0,  # Implementar contador de requisições
        requests_per_second=0.0,  # Implementar média
        average_response_time=0.0,  # Implementar média
        active_connections=0,  # Implementar contador
        memory_usage={
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used,
            "free": memory.free
        },
        database_connections=db_connections
    )


# Monitoramento periódico em background
class HealthMonitor:
    """Monitor de saúde em background"""
    
    def __init__(self):
        self.monitoring = False
        self.last_check = None
        self.check_interval = settings.health_check_interval
    
    async def start_monitoring(self):
        """Inicia monitoramento em background"""
        if self.monitoring:
            return
        
        self.monitoring = True
        logger.info("Health monitoring started", interval=self.check_interval)
        
        while self.monitoring:
            try:
                await self.perform_health_check()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("Health monitoring error", error=str(exc))
                await asyncio.sleep(5)  # Retry após erro
    
    async def stop_monitoring(self):
        """Para monitoramento"""
        self.monitoring = False
        logger.info("Health monitoring stopped")
    
    async def perform_health_check(self):
        """Executa verificação de saúde"""
        start_time = time.time()
        
        try:
            services = await check_all_services()
            check_duration = time.time() - start_time
            
            # Log do resultado
            healthy_services = sum(
                1 for status in services.values() 
                if "healthy" in status
            )
            total_services = len(services)
            
            logger.info(
                "Health check completed",
                healthy_services=healthy_services,
                total_services=total_services,
                check_duration=f"{check_duration:.3f}s"
            )
            
            self.last_check = datetime.utcnow()
            
        except Exception as exc:
            logger.error("Health check failed", error=str(exc))


# Instância global do monitor
health_monitor = HealthMonitor()
