"""
Configuração do Celery para tarefas assíncronas
"""

from celery import Celery

from app.core.config import settings
from app.core.logging import get_logger_with_context

logger = get_logger_with_context(component="celery")

# Configuração do Celery
celery_app = Celery(
    "cotai_backend",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.ai_tasks",
        "app.tasks.email_tasks",
        "app.tasks.report_tasks",
        "app.tasks.maintenance_tasks",
        "app.tasks.llm_tasks",  # New LLM-specific tasks
    ]
)

# Configurações do Celery
celery_app.conf.update(
    # Timezone
    timezone="UTC",
    enable_utc=True,
    
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    result_expires=3600,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    
    # Routing
    task_routes={
        "app.tasks.ai_tasks.*": {"queue": "ai_tasks"},
        "app.tasks.llm_tasks.*": {"queue": "llm_tasks"},  # New LLM queue
        "app.tasks.email_tasks.*": {"queue": "email_tasks"},
        "app.tasks.report_tasks.*": {"queue": "report_tasks"},
        "app.tasks.maintenance_tasks.*": {"queue": "maintenance_tasks"},
    },
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Error handling
    task_reject_on_worker_lost=True,
    task_ignore_result=False,
    
    # Beat schedule (para tarefas periódicas)
    beat_schedule={
        "health-check": {
            "task": "app.tasks.maintenance_tasks.health_check_task",
            "schedule": 300.0,  # A cada 5 minutos
        },
        "cleanup-expired-sessions": {
            "task": "app.tasks.maintenance_tasks.cleanup_expired_sessions",
            "schedule": 3600.0,  # A cada hora
        },
        "generate-daily-reports": {
            "task": "app.tasks.report_tasks.generate_daily_reports",
            "schedule": {
                "hour": 6,
                "minute": 0,
            },
        },
    },
)

# Configurações específicas para desenvolvimento
if settings.debug:
    celery_app.conf.update(
        task_always_eager=False,  # Para testar tarefas assíncronas
        task_eager_propagates=True,
    )

logger.info("Celery configured", broker=settings.celery_broker_url)
