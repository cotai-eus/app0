"""
Classe base para tarefas Celery
"""

from celery import Task
from celery.exceptions import Retry

from app.core.logging import get_logger_with_context


class BaseTask(Task):
    """Classe base para todas as tarefas Celery"""
    
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3, "countdown": 60}
    retry_backoff = True
    retry_jitter = True
    
    def __init__(self):
        self.logger = get_logger_with_context(
            component="celery_task",
            task_name=self.name
        )
    
    def on_success(self, retval, task_id, args, kwargs):
        """Executado quando a tarefa é bem-sucedida"""
        self.logger.info(
            "Task completed successfully",
            task_id=task_id,
            result=retval
        )
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Executado quando a tarefa falha"""
        self.logger.error(
            "Task failed",
            task_id=task_id,
            error=str(exc),
            traceback=str(einfo)
        )
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Executado quando a tarefa é reexecutada"""
        self.logger.warning(
            "Task retry",
            task_id=task_id,
            error=str(exc),
            retry_count=self.request.retries
        )
    
    def apply_async_with_context(self, args=None, kwargs=None, **options):
        """Executa tarefa com contexto adicional"""
        
        # Adiciona contexto padrão
        context = {
            "timestamp": "utcnow",
            "environment": "development" if settings.debug else "production",
        }
        
        if kwargs is None:
            kwargs = {}
        
        kwargs.update({"context": context})
        
        return self.apply_async(args=args, kwargs=kwargs, **options)
