"""
Monitoring and Maintenance Tasks for Celery.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from celery import Task
from sqlalchemy.ext.asyncio import AsyncSession

from app.tasks.celery_app import celery_app
from app.tasks.base_task import BaseTask
from app.core.database import get_async_session
from app.domains.monitoring.service import MonitoringService
from app.domains.files.repository import FileRepository, FileQuotaRepository
from app.domains.audit.repository import AuditLogRepository, DataRetentionPolicyRepository
from app.core.logging import get_logger_with_context

logger = get_logger_with_context(component="monitoring_tasks")


@celery_app.task(bind=True, base=BaseTask, name="monitoring_tasks.collect_system_metrics")
def collect_system_metrics(self):
    """Collect system metrics periodically."""
    return asyncio.run(collect_system_metrics_async(self))


async def collect_system_metrics_async(task: Task):
    """Async system metrics collection."""
    try:
        async with get_async_session() as db:
            service = MonitoringService(db)
            
            # Collect current system metrics
            metrics = await service.collect_system_metrics()
            
            return {
                "metrics_collected": len(metrics),
                "collected_at": datetime.utcnow().isoformat(),
                "status": "completed"
            }
            
    except Exception as e:
        logger.error(f"System metrics collection failed: {e}")
        raise


@celery_app.task(bind=True, base=BaseTask, name="monitoring_tasks.check_services_health")
def check_services_health(self):
    """Check health of all services."""
    return asyncio.run(check_services_health_async(self))


async def check_services_health_async(task: Task):
    """Async service health checking."""
    try:
        async with get_async_session() as db:
            service = MonitoringService(db)
            
            # Get all services and check their health
            services = await service.get_services_health()
            unhealthy_services = []
            
            for srv in services:
                if srv.status != "healthy":
                    unhealthy_services.append({
                        "service_name": srv.service_name,
                        "status": srv.status,
                        "last_check": srv.last_check.isoformat() if srv.last_check else None
                    })
            
            # If there are unhealthy services, create alerts
            if unhealthy_services:
                for srv in unhealthy_services:
                    await service.create_alert({
                        "alert_type": "service_health",
                        "severity": "high" if srv["status"] == "critical" else "medium",
                        "message": f"Service {srv['service_name']} is {srv['status']}",
                        "metadata": srv
                    })
            
            return {
                "total_services": len(services),
                "healthy_services": len(services) - len(unhealthy_services),
                "unhealthy_services": len(unhealthy_services),
                "unhealthy_details": unhealthy_services,
                "checked_at": datetime.utcnow().isoformat(),
                "status": "completed"
            }
            
    except Exception as e:
        logger.error(f"Service health check failed: {e}")
        raise


@celery_app.task(bind=True, base=BaseTask, name="monitoring_tasks.cleanup_old_metrics")
def cleanup_old_metrics(self, days: int = 30):
    """Clean up old monitoring metrics."""
    return asyncio.run(cleanup_old_metrics_async(self, days))


async def cleanup_old_metrics_async(task: Task, days: int = 30):
    """Async cleanup of old metrics."""
    try:
        async with get_async_session() as db:
            service = MonitoringService(db)
            
            # Clean up old data
            cleaned_counts = await service.cleanup_old_data(
                days=days,
                data_types=["api_metrics", "system_metrics", "security_events"]
            )
            
            return {
                "cleaned_records": cleaned_counts,
                "retention_days": days,
                "cleaned_at": datetime.utcnow().isoformat(),
                "status": "completed"
            }
            
    except Exception as e:
        logger.error(f"Metrics cleanup failed: {e}")
        raise


@celery_app.task(bind=True, base=BaseTask, name="monitoring_tasks.generate_dashboard_data")
def generate_dashboard_data(self, period: str = "24h"):
    """Generate dashboard data cache."""
    return asyncio.run(generate_dashboard_data_async(self, period))


async def generate_dashboard_data_async(task: Task, period: str = "24h"):
    """Async dashboard data generation."""
    try:
        async with get_async_session() as db:
            service = MonitoringService(db)
            
            # Generate dashboard data
            dashboard_data = await service.get_dashboard_data(period)
            
            # Cache the data
            await service.cache_dashboard_data(dashboard_data, period)
            
            return {
                "period": period,
                "data_points": len(dashboard_data.get("metrics", [])),
                "generated_at": datetime.utcnow().isoformat(),
                "status": "completed"
            }
            
    except Exception as e:
        logger.error(f"Dashboard data generation failed: {e}")
        raise


@celery_app.task(bind=True, base=BaseTask, name="monitoring_tasks.analyze_performance_trends")
def analyze_performance_trends(self, hours: int = 24):
    """Analyze performance trends and create alerts if needed."""
    return asyncio.run(analyze_performance_trends_async(self, hours))


async def analyze_performance_trends_async(task: Task, hours: int = 24):
    """Async performance trends analysis."""
    try:
        async with get_async_session() as db:
            service = MonitoringService(db)
            
            # Get performance data
            performance_data = await service.get_performance_dashboard(hours)
            
            alerts_created = []
            
            # Analyze response time trends
            if "avg_response_time" in performance_data:
                avg_response_time = performance_data["avg_response_time"]
                if avg_response_time > 2000:  # 2 seconds threshold
                    alert = await service.create_alert({
                        "alert_type": "performance",
                        "severity": "high" if avg_response_time > 5000 else "medium",
                        "message": f"High average response time: {avg_response_time}ms",
                        "metadata": {"avg_response_time": avg_response_time, "period": f"{hours}h"}
                    })
                    alerts_created.append(alert)
            
            # Analyze error rate
            if "error_rate" in performance_data:
                error_rate = performance_data["error_rate"]
                if error_rate > 5:  # 5% error rate threshold
                    alert = await service.create_alert({
                        "alert_type": "error_rate",
                        "severity": "high" if error_rate > 10 else "medium",
                        "message": f"High error rate: {error_rate}%",
                        "metadata": {"error_rate": error_rate, "period": f"{hours}h"}
                    })
                    alerts_created.append(alert)
            
            # Analyze resource usage
            if "cpu_usage" in performance_data:
                cpu_usage = performance_data["cpu_usage"]
                if cpu_usage > 80:  # 80% CPU usage threshold
                    alert = await service.create_alert({
                        "alert_type": "resource_usage",
                        "severity": "high" if cpu_usage > 90 else "medium",
                        "message": f"High CPU usage: {cpu_usage}%",
                        "metadata": {"cpu_usage": cpu_usage, "period": f"{hours}h"}
                    })
                    alerts_created.append(alert)
            
            return {
                "analysis_period": f"{hours}h",
                "alerts_created": len(alerts_created),
                "performance_summary": performance_data,
                "analyzed_at": datetime.utcnow().isoformat(),
                "status": "completed"
            }
            
    except Exception as e:
        logger.error(f"Performance trends analysis failed: {e}")
        raise


@celery_app.task(bind=True, base=BaseTask, name="monitoring_tasks.update_rate_limit_stats")
def update_rate_limit_stats(self):
    """Update rate limiting statistics."""
    return asyncio.run(update_rate_limit_stats_async(self))


async def update_rate_limit_stats_async(task: Task):
    """Async rate limit stats update."""
    try:
        async with get_async_session() as db:
            service = MonitoringService(db)
            
            # Update rate limiting statistics
            stats = await service.update_rate_limit_statistics()
            
            return {
                "updated_policies": stats.get("updated_policies", 0),
                "blocked_requests": stats.get("blocked_requests", 0),
                "updated_at": datetime.utcnow().isoformat(),
                "status": "completed"
            }
            
    except Exception as e:
        logger.error(f"Rate limit stats update failed: {e}")
        raise


# File maintenance tasks
@celery_app.task(bind=True, base=BaseTask, name="maintenance_tasks.cleanup_orphaned_files")
def cleanup_orphaned_files(self):
    """Clean up orphaned files."""
    return asyncio.run(cleanup_orphaned_files_async(self))


async def cleanup_orphaned_files_async(task: Task):
    """Async cleanup of orphaned files."""
    try:
        async with get_async_session() as db:
            file_repo = FileRepository(db)
            
            # Find and clean up orphaned files
            cleaned_count = await file_repo.cleanup_orphaned_files()
            
            return {
                "cleaned_files": cleaned_count,
                "cleaned_at": datetime.utcnow().isoformat(),
                "status": "completed"
            }
            
    except Exception as e:
        logger.error(f"Orphaned files cleanup failed: {e}")
        raise


@celery_app.task(bind=True, base=BaseTask, name="maintenance_tasks.update_quota_usage")
def update_quota_usage(self):
    """Update user quota usage statistics."""
    return asyncio.run(update_quota_usage_async(self))


async def update_quota_usage_async(task: Task):
    """Async quota usage update."""
    try:
        async with get_async_session() as db:
            quota_repo = FileQuotaRepository(db)
            
            # Update quota usage for all users
            updated_users = await quota_repo.update_all_quotas()
            
            return {
                "updated_users": updated_users,
                "updated_at": datetime.utcnow().isoformat(),
                "status": "completed"
            }
            
    except Exception as e:
        logger.error(f"Quota usage update failed: {e}")
        raise


@celery_app.task(bind=True, base=BaseTask, name="maintenance_tasks.execute_retention_policies")
def execute_retention_policies(self, dry_run: bool = False):
    """Execute data retention policies."""
    return asyncio.run(execute_retention_policies_async(self, dry_run))


async def execute_retention_policies_async(task: Task, dry_run: bool = False):
    """Async execution of retention policies."""
    try:
        async with get_async_session() as db:
            retention_repo = DataRetentionPolicyRepository(db)
            
            # Execute all active retention policies
            results = await retention_repo.execute_all_policies(dry_run)
            
            return {
                "executed_policies": len(results),
                "dry_run": dry_run,
                "results": results,
                "executed_at": datetime.utcnow().isoformat(),
                "status": "completed"
            }
            
    except Exception as e:
        logger.error(f"Retention policies execution failed: {e}")
        raise


@celery_app.task(bind=True, base=BaseTask, name="maintenance_tasks.backup_audit_logs")
def backup_audit_logs(self, days: int = 90):
    """Backup old audit logs."""
    return asyncio.run(backup_audit_logs_async(self, days))


async def backup_audit_logs_async(task: Task, days: int = 90):
    """Async backup of audit logs."""
    try:
        async with get_async_session() as db:
            audit_repo = AuditLogRepository(db)
            
            # Backup old audit logs
            backup_result = await audit_repo.backup_old_logs(days)
            
            return {
                "backed_up_logs": backup_result.get("backed_up_count", 0),
                "backup_file": backup_result.get("backup_file"),
                "backup_date": datetime.utcnow().isoformat(),
                "status": "completed"
            }
            
    except Exception as e:
        logger.error(f"Audit logs backup failed: {e}")
        raise


# Periodic monitoring tasks
@celery_app.task(bind=True, base=BaseTask, name="monitoring_tasks.periodic_health_check")
def periodic_health_check(self):
    """Periodic health check of all systems."""
    return check_services_health.delay()


@celery_app.task(bind=True, base=BaseTask, name="monitoring_tasks.periodic_metrics_collection")
def periodic_metrics_collection(self):
    """Periodic collection of system metrics."""
    return collect_system_metrics.delay()


@celery_app.task(bind=True, base=BaseTask, name="monitoring_tasks.periodic_performance_analysis")
def periodic_performance_analysis(self):
    """Periodic performance analysis."""
    return analyze_performance_trends.delay(hours=24)


@celery_app.task(bind=True, base=BaseTask, name="maintenance_tasks.daily_maintenance")
def daily_maintenance(self):
    """Daily maintenance tasks."""
    tasks = [
        cleanup_orphaned_files.delay(),
        update_quota_usage.delay(),
        cleanup_old_metrics.delay(days=30),
        execute_retention_policies.delay(dry_run=False),
    ]
    
    return {
        "scheduled_tasks": len(tasks),
        "task_ids": [task.id for task in tasks],
        "scheduled_at": datetime.utcnow().isoformat()
    }


@celery_app.task(bind=True, base=BaseTask, name="maintenance_tasks.weekly_maintenance")
def weekly_maintenance(self):
    """Weekly maintenance tasks."""
    tasks = [
        backup_audit_logs.delay(days=90),
        generate_dashboard_data.delay(period="7d"),
    ]
    
    return {
        "scheduled_tasks": len(tasks),
        "task_ids": [task.id for task in tasks],
        "scheduled_at": datetime.utcnow().isoformat()
    }
