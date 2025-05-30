"""
Celery task management repositories for async processing, worker monitoring, and scheduling.
Based on the database architecture plan.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import desc, asc, func, and_, or_, text
from sqlalchemy.orm import Session, joinedload

from app.shared.common.repository import BaseRepository
from app.core.exceptions import NotFoundError, ValidationError
from .models import (
    CeleryTask, CeleryWorker, TaskQueue, TaskSchedule,
    TaskStatus, TaskPriority, WorkerStatus
)


class CeleryTaskRepository(BaseRepository[CeleryTask]):
    """Repository for Celery task tracking and management."""
    
    def __init__(self, db: Session):
        super().__init__(db, CeleryTask)
    
    def create_task(
        self,
        task_id: str,
        task_name: str,
        status: TaskStatus = TaskStatus.PENDING,
        priority: TaskPriority = TaskPriority.NORMAL,
        queue_name: str = "default",
        **kwargs
    ) -> CeleryTask:
        """Create a new task record."""
        task = CeleryTask(
            task_id=task_id,
            task_name=task_name,
            status=status,
            priority=priority,
            queue_name=queue_name,
            **kwargs
        )
        return self.create(task)
    
    def get_by_task_id(self, task_id: str) -> Optional[CeleryTask]:
        """Get task by Celery task ID."""
        return self.db.query(CeleryTask).filter(
            CeleryTask.task_id == task_id
        ).first()
    
    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        result: Optional[Dict] = None,
        traceback: Optional[str] = None,
        worker_info: Optional[Dict] = None
    ) -> bool:
        """Update task status and related information."""
        task = self.get_by_task_id(task_id)
        if not task:
            return False
        
        task.status = status
        
        if result is not None:
            task.result = result
        
        if traceback:
            task.traceback = traceback
        
        if worker_info:
            task.worker_id = worker_info.get('worker_id')
            task.worker_hostname = worker_info.get('hostname')
            task.worker_pid = worker_info.get('pid')
        
        # Update timing based on status
        now = datetime.utcnow()
        if status == TaskStatus.STARTED and not task.started_at:
            task.started_at = now
        elif status in [TaskStatus.SUCCESS, TaskStatus.FAILURE] and not task.completed_at:
            task.completed_at = now
            if task.started_at:
                task.runtime_seconds = (now - task.started_at).total_seconds()
        
        self.db.commit()
        return True
    
    def update_task_progress(
        self,
        task_id: str,
        progress_percent: int,
        progress_message: Optional[str] = None,
        current_step: Optional[str] = None
    ) -> bool:
        """Update task progress information."""
        task = self.get_by_task_id(task_id)
        if not task:
            return False
        
        task.progress_percent = max(0, min(100, progress_percent))
        if progress_message:
            task.progress_message = progress_message
        if current_step:
            task.current_step = current_step
        
        self.db.commit()
        return True
    
    def get_pending_tasks(
        self,
        queue_name: Optional[str] = None,
        priority: Optional[TaskPriority] = None,
        limit: int = 100
    ) -> List[CeleryTask]:
        """Get pending tasks."""
        query = self.db.query(CeleryTask).filter(
            CeleryTask.status == TaskStatus.PENDING
        )
        
        if queue_name:
            query = query.filter(CeleryTask.queue_name == queue_name)
        
        if priority:
            query = query.filter(CeleryTask.priority == priority)
        
        # Order by priority and creation time
        priority_order = {
            TaskPriority.CRITICAL: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.NORMAL: 2,
            TaskPriority.LOW: 3
        }
        
        return query.order_by(
            func.array_position(
                [TaskPriority.CRITICAL, TaskPriority.HIGH, TaskPriority.NORMAL, TaskPriority.LOW],
                CeleryTask.priority
            ),
            CeleryTask.created_at
        ).limit(limit).all()
    
    def get_running_tasks(
        self,
        worker_id: Optional[str] = None
    ) -> List[CeleryTask]:
        """Get currently running tasks."""
        query = self.db.query(CeleryTask).filter(
            CeleryTask.status == TaskStatus.STARTED
        )
        
        if worker_id:
            query = query.filter(CeleryTask.worker_id == worker_id)
        
        return query.order_by(CeleryTask.started_at).all()
    
    def get_failed_tasks(
        self,
        hours: int = 24,
        include_retries: bool = False
    ) -> List[CeleryTask]:
        """Get failed tasks within specified timeframe."""
        since = datetime.utcnow() - timedelta(hours=hours)
        
        query = self.db.query(CeleryTask).filter(
            CeleryTask.status == TaskStatus.FAILURE,
            CeleryTask.created_at >= since
        )
        
        if not include_retries:
            query = query.filter(CeleryTask.retry_count == 0)
        
        return query.order_by(desc(CeleryTask.created_at)).all()
    
    def get_user_tasks(
        self,
        user_id: str,
        company_id: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        limit: int = 50
    ) -> List[CeleryTask]:
        """Get tasks for a specific user."""
        query = self.db.query(CeleryTask).filter(
            CeleryTask.user_id == user_id
        )
        
        if company_id:
            query = query.filter(CeleryTask.company_id == company_id)
        
        if status:
            query = query.filter(CeleryTask.status == status)
        
        return query.order_by(desc(CeleryTask.created_at)).limit(limit).all()
    
    def get_task_statistics(
        self,
        hours: int = 24,
        company_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get task execution statistics."""
        since = datetime.utcnow() - timedelta(hours=hours)
        
        query = self.db.query(CeleryTask).filter(
            CeleryTask.created_at >= since
        )
        
        if company_id:
            query = query.filter(CeleryTask.company_id == company_id)
        
        # Status distribution
        status_stats = self.db.query(
            CeleryTask.status,
            func.count(CeleryTask.id).label('count')
        ).filter(
            CeleryTask.created_at >= since
        ).group_by(CeleryTask.status).all()
        
        # Task type distribution
        task_type_stats = self.db.query(
            CeleryTask.task_name,
            func.count(CeleryTask.id).label('count'),
            func.avg(CeleryTask.runtime_seconds).label('avg_runtime')
        ).filter(
            CeleryTask.created_at >= since
        ).group_by(CeleryTask.task_name).all()
        
        # Queue distribution
        queue_stats = self.db.query(
            CeleryTask.queue_name,
            func.count(CeleryTask.id).label('count')
        ).filter(
            CeleryTask.created_at >= since
        ).group_by(CeleryTask.queue_name).all()
        
        return {
            'total_tasks': query.count(),
            'status_distribution': {stat.status: stat.count for stat in status_stats},
            'task_types': [
                {
                    'task_name': stat.task_name,
                    'count': stat.count,
                    'avg_runtime_seconds': float(stat.avg_runtime) if stat.avg_runtime else 0
                }
                for stat in task_type_stats
            ],
            'queue_distribution': {stat.queue_name: stat.count for stat in queue_stats}
        }
    
    def retry_failed_task(
        self,
        task_id: str,
        max_retries: Optional[int] = None
    ) -> bool:
        """Retry a failed task."""
        task = self.get_by_task_id(task_id)
        if not task or task.status != TaskStatus.FAILURE:
            return False
        
        if max_retries and task.retry_count >= max_retries:
            return False
        
        task.status = TaskStatus.PENDING
        task.retry_count += 1
        task.traceback = None
        task.started_at = None
        task.completed_at = None
        task.runtime_seconds = None
        
        self.db.commit()
        return True
    
    def cleanup_old_tasks(
        self,
        days: int = 30,
        keep_failed: bool = True
    ) -> int:
        """Clean up old completed tasks."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = self.db.query(CeleryTask).filter(
            CeleryTask.created_at < cutoff_date,
            CeleryTask.status.in_([TaskStatus.SUCCESS])
        )
        
        if not keep_failed:
            query = query.filter(
                CeleryTask.status.in_([TaskStatus.SUCCESS, TaskStatus.FAILURE])
            )
        
        count = query.count()
        query.delete(synchronize_session=False)
        self.db.commit()
        
        return count


class CeleryWorkerRepository(BaseRepository[CeleryWorker]):
    """Repository for Celery worker monitoring and management."""
    
    def __init__(self, db: Session):
        super().__init__(db, CeleryWorker)
    
    def register_worker(
        self,
        worker_id: str,
        hostname: str,
        pid: int,
        queues: List[str],
        concurrency: int = 1,
        **kwargs
    ) -> CeleryWorker:
        """Register a new worker."""
        # Check if worker already exists
        existing_worker = self.get_by_worker_id(worker_id)
        if existing_worker:
            # Update existing worker
            existing_worker.hostname = hostname
            existing_worker.pid = pid
            existing_worker.queues = queues
            existing_worker.concurrency = concurrency
            existing_worker.status = WorkerStatus.ONLINE
            existing_worker.is_active = True
            existing_worker.last_heartbeat = datetime.utcnow()
            existing_worker.restart_count += 1
            
            for key, value in kwargs.items():
                setattr(existing_worker, key, value)
            
            self.db.commit()
            return existing_worker
        
        worker = CeleryWorker(
            worker_id=worker_id,
            hostname=hostname,
            pid=pid,
            queues=queues,
            concurrency=concurrency,
            status=WorkerStatus.ONLINE,
            **kwargs
        )
        return self.create(worker)
    
    def get_by_worker_id(self, worker_id: str) -> Optional[CeleryWorker]:
        """Get worker by worker ID."""
        return self.db.query(CeleryWorker).filter(
            CeleryWorker.worker_id == worker_id
        ).first()
    
    def update_heartbeat(
        self,
        worker_id: str,
        status: Optional[WorkerStatus] = None,
        active_tasks: Optional[int] = None,
        resource_usage: Optional[Dict] = None
    ) -> bool:
        """Update worker heartbeat and status."""
        worker = self.get_by_worker_id(worker_id)
        if not worker:
            return False
        
        worker.last_heartbeat = datetime.utcnow()
        worker.consecutive_failures = 0  # Reset failure count on successful heartbeat
        
        if status:
            worker.status = status
        
        if active_tasks is not None:
            worker.active_tasks = active_tasks
        
        if resource_usage:
            worker.cpu_usage_percent = resource_usage.get('cpu_percent')
            worker.memory_usage_mb = resource_usage.get('memory_mb')
            worker.load_average = resource_usage.get('load_average')
        
        self.db.commit()
        return True
    
    def get_active_workers(
        self,
        queue_name: Optional[str] = None
    ) -> List[CeleryWorker]:
        """Get active workers."""
        query = self.db.query(CeleryWorker).filter(
            CeleryWorker.is_active == True,
            CeleryWorker.status != WorkerStatus.OFFLINE
        )
        
        if queue_name:
            query = query.filter(
                CeleryWorker.queues.contains([queue_name])
            )
        
        return query.order_by(CeleryWorker.load_average).all()
    
    def get_offline_workers(
        self,
        minutes: int = 5
    ) -> List[CeleryWorker]:
        """Get workers that haven't sent heartbeat recently."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        
        return self.db.query(CeleryWorker).filter(
            CeleryWorker.is_active == True,
            CeleryWorker.last_heartbeat < cutoff_time
        ).all()
    
    def mark_worker_offline(self, worker_id: str) -> bool:
        """Mark a worker as offline."""
        worker = self.get_by_worker_id(worker_id)
        if not worker:
            return False
        
        worker.status = WorkerStatus.OFFLINE
        worker.is_active = False
        worker.consecutive_failures += 1
        
        self.db.commit()
        return True
    
    def shutdown_worker(
        self,
        worker_id: str,
        graceful: bool = True
    ) -> bool:
        """Request worker shutdown."""
        worker = self.get_by_worker_id(worker_id)
        if not worker:
            return False
        
        worker.shutdown_requested = True
        if not graceful:
            worker.status = WorkerStatus.SHUTDOWN
            worker.is_active = False
        
        self.db.commit()
        return True
    
    def get_worker_load_distribution(self) -> List[Dict[str, Any]]:
        """Get load distribution across workers."""
        workers = self.get_active_workers()
        
        return [
            {
                'worker_id': worker.worker_id,
                'hostname': worker.hostname,
                'active_tasks': worker.active_tasks,
                'concurrency': worker.concurrency,
                'utilization_percent': (
                    (worker.active_tasks / worker.concurrency * 100) 
                    if worker.concurrency > 0 else 0
                ),
                'cpu_usage_percent': worker.cpu_usage_percent,
                'memory_usage_mb': worker.memory_usage_mb,
                'load_average': worker.load_average,
                'queues': worker.queues
            }
            for worker in workers
        ]
    
    def get_worker_statistics(self) -> Dict[str, Any]:
        """Get worker statistics."""
        total_workers = self.db.query(CeleryWorker).count()
        active_workers = self.db.query(CeleryWorker).filter(
            CeleryWorker.is_active == True
        ).count()
        
        online_workers = self.db.query(CeleryWorker).filter(
            CeleryWorker.status == WorkerStatus.ONLINE
        ).count()
        
        # Average metrics for active workers
        active_worker_stats = self.db.query(
            func.avg(CeleryWorker.active_tasks).label('avg_active_tasks'),
            func.avg(CeleryWorker.cpu_usage_percent).label('avg_cpu'),
            func.avg(CeleryWorker.memory_usage_mb).label('avg_memory'),
            func.sum(CeleryWorker.processed_tasks).label('total_processed'),
            func.sum(CeleryWorker.failed_tasks).label('total_failed')
        ).filter(CeleryWorker.is_active == True).first()
        
        return {
            'total_workers': total_workers,
            'active_workers': active_workers,
            'online_workers': online_workers,
            'offline_workers': total_workers - online_workers,
            'avg_active_tasks': float(active_worker_stats.avg_active_tasks or 0),
            'avg_cpu_usage': float(active_worker_stats.avg_cpu or 0),
            'avg_memory_usage': float(active_worker_stats.avg_memory or 0),
            'total_processed_tasks': int(active_worker_stats.total_processed or 0),
            'total_failed_tasks': int(active_worker_stats.total_failed or 0)
        }


class TaskQueueRepository(BaseRepository[TaskQueue]):
    """Repository for task queue monitoring and management."""
    
    def __init__(self, db: Session):
        super().__init__(db, TaskQueue)
    
    def get_or_create_queue(
        self,
        queue_name: str,
        priority: int = 100,
        **kwargs
    ) -> TaskQueue:
        """Get existing queue or create new one."""
        queue = self.db.query(TaskQueue).filter(
            TaskQueue.queue_name == queue_name
        ).first()
        
        if queue:
            return queue
        
        queue = TaskQueue(
            queue_name=queue_name,
            priority=priority,
            **kwargs
        )
        return self.create(queue)
    
    def update_queue_stats(
        self,
        queue_name: str,
        pending_tasks: int,
        active_tasks: int,
        scheduled_tasks: int = 0
    ) -> bool:
        """Update queue statistics."""
        queue = self.get_or_create_queue(queue_name)
        
        queue.pending_tasks = pending_tasks
        queue.active_tasks = active_tasks
        queue.scheduled_tasks = scheduled_tasks
        queue.last_task_at = datetime.utcnow() if active_tasks > 0 else queue.last_task_at
        
        # Update health status based on thresholds
        if pending_tasks >= queue.critical_threshold:
            queue.is_healthy = False
        elif pending_tasks >= queue.warning_threshold:
            queue.is_healthy = True  # Warning but still healthy
        else:
            queue.is_healthy = True
        
        self.db.commit()
        return True
    
    def increment_processed_tasks(
        self,
        queue_name: str,
        success: bool = True,
        processing_time: Optional[float] = None
    ) -> bool:
        """Increment processed task counters."""
        queue = self.get_or_create_queue(queue_name)
        
        queue.total_processed += 1
        if not success:
            queue.total_failed += 1
        
        # Update average processing time
        if processing_time and success:
            if queue.avg_processing_time_seconds:
                # Weighted average
                total_successful = queue.total_processed - queue.total_failed
                queue.avg_processing_time_seconds = (
                    (queue.avg_processing_time_seconds * (total_successful - 1) + processing_time)
                    / total_successful
                )
            else:
                queue.avg_processing_time_seconds = processing_time
        
        # Update error rate
        if queue.total_processed > 0:
            queue.error_rate_percent = (queue.total_failed / queue.total_processed) * 100
        
        self.db.commit()
        return True
    
    def get_unhealthy_queues(self) -> List[TaskQueue]:
        """Get queues that are not healthy."""
        return self.db.query(TaskQueue).filter(
            TaskQueue.is_healthy == False
        ).all()
    
    def get_overloaded_queues(self) -> List[TaskQueue]:
        """Get queues that exceed warning thresholds."""
        return self.db.query(TaskQueue).filter(
            TaskQueue.pending_tasks >= TaskQueue.warning_threshold
        ).all()
    
    def pause_queue(self, queue_name: str) -> bool:
        """Pause a queue."""
        queue = self.get_or_create_queue(queue_name)
        queue.is_paused = True
        self.db.commit()
        return True
    
    def resume_queue(self, queue_name: str) -> bool:
        """Resume a paused queue."""
        queue = self.get_or_create_queue(queue_name)
        queue.is_paused = False
        self.db.commit()
        return True
    
    def get_queue_performance_metrics(self) -> List[Dict[str, Any]]:
        """Get performance metrics for all queues."""
        queues = self.db.query(TaskQueue).order_by(TaskQueue.priority).all()
        
        return [
            {
                'queue_name': queue.queue_name,
                'priority': queue.priority,
                'pending_tasks': queue.pending_tasks,
                'active_tasks': queue.active_tasks,
                'total_processed': queue.total_processed,
                'total_failed': queue.total_failed,
                'error_rate_percent': queue.error_rate_percent,
                'avg_processing_time_seconds': queue.avg_processing_time_seconds,
                'throughput_per_minute': queue.throughput_per_minute,
                'is_healthy': queue.is_healthy,
                'is_paused': queue.is_paused,
                'assigned_workers': queue.assigned_workers
            }
            for queue in queues
        ]


class TaskScheduleRepository(BaseRepository[TaskSchedule]):
    """Repository for scheduled task management."""
    
    def __init__(self, db: Session):
        super().__init__(db, TaskSchedule)
    
    def create_schedule(
        self,
        name: str,
        task_name: str,
        created_by: str,
        company_id: str,
        cron_expression: Optional[str] = None,
        interval_seconds: Optional[int] = None,
        **kwargs
    ) -> TaskSchedule:
        """Create a new task schedule."""
        if not cron_expression and not interval_seconds:
            raise ValidationError("Either cron_expression or interval_seconds must be provided")
        
        schedule = TaskSchedule(
            name=name,
            task_name=task_name,
            created_by=created_by,
            company_id=company_id,
            cron_expression=cron_expression,
            interval_seconds=interval_seconds,
            **kwargs
        )
        return self.create(schedule)
    
    def get_active_schedules(self) -> List[TaskSchedule]:
        """Get all active schedules."""
        now = datetime.utcnow()
        
        return self.db.query(TaskSchedule).filter(
            TaskSchedule.is_active == True,
            TaskSchedule.is_paused == False,
            or_(
                TaskSchedule.expires_at.is_(None),
                TaskSchedule.expires_at > now
            )
        ).all()
    
    def get_due_schedules(self, buffer_minutes: int = 1) -> List[TaskSchedule]:
        """Get schedules that are due for execution."""
        now = datetime.utcnow()
        buffer_time = now + timedelta(minutes=buffer_minutes)
        
        return self.db.query(TaskSchedule).filter(
            TaskSchedule.is_active == True,
            TaskSchedule.is_paused == False,
            TaskSchedule.next_run_at <= buffer_time,
            or_(
                TaskSchedule.expires_at.is_(None),
                TaskSchedule.expires_at > now
            )
        ).all()
    
    def update_execution(
        self,
        schedule_id: str,
        success: bool,
        next_run_at: datetime,
        error_message: Optional[str] = None
    ) -> bool:
        """Update schedule after execution."""
        schedule = self.get_by_id(schedule_id)
        if not schedule:
            return False
        
        schedule.last_run_at = datetime.utcnow()
        schedule.next_run_at = next_run_at
        schedule.total_runs += 1
        
        if success:
            schedule.successful_runs += 1
            schedule.consecutive_failures = 0
        else:
            schedule.failed_runs += 1
            schedule.consecutive_failures += 1
        
        # Check if schedule should be disabled due to failures
        if (schedule.max_consecutive_failures and 
            schedule.consecutive_failures >= schedule.max_consecutive_failures):
            
            if schedule.failure_action == "pause":
                schedule.is_paused = True
            elif schedule.failure_action == "disable":
                schedule.is_active = False
        
        # Check if max runs reached
        if (schedule.max_runs and 
            schedule.total_runs >= schedule.max_runs):
            schedule.is_active = False
        
        self.db.commit()
        return True
    
    def get_company_schedules(
        self,
        company_id: str,
        active_only: bool = True
    ) -> List[TaskSchedule]:
        """Get schedules for a company."""
        query = self.db.query(TaskSchedule).filter(
            TaskSchedule.company_id == company_id
        )
        
        if active_only:
            query = query.filter(TaskSchedule.is_active == True)
        
        return query.order_by(TaskSchedule.next_run_at).all()
    
    def pause_schedule(self, schedule_id: str) -> bool:
        """Pause a schedule."""
        schedule = self.get_by_id(schedule_id)
        if not schedule:
            return False
        
        schedule.is_paused = True
        self.db.commit()
        return True
    
    def resume_schedule(self, schedule_id: str) -> bool:
        """Resume a paused schedule."""
        schedule = self.get_by_id(schedule_id)
        if not schedule:
            return False
        
        schedule.is_paused = False
        self.db.commit()
        return True
    
    def disable_schedule(self, schedule_id: str) -> bool:
        """Disable a schedule."""
        schedule = self.get_by_id(schedule_id)
        if not schedule:
            return False
        
        schedule.is_active = False
        self.db.commit()
        return True
    
    def get_schedule_statistics(self) -> Dict[str, Any]:
        """Get schedule execution statistics."""
        total_schedules = self.db.query(TaskSchedule).count()
        active_schedules = self.db.query(TaskSchedule).filter(
            TaskSchedule.is_active == True
        ).count()
        paused_schedules = self.db.query(TaskSchedule).filter(
            TaskSchedule.is_paused == True
        ).count()
        
        # Recent execution stats
        recent_executions = self.db.query(
            func.sum(TaskSchedule.total_runs).label('total_runs'),
            func.sum(TaskSchedule.successful_runs).label('successful_runs'),
            func.sum(TaskSchedule.failed_runs).label('failed_runs')
        ).first()
        
        return {
            'total_schedules': total_schedules,
            'active_schedules': active_schedules,
            'paused_schedules': paused_schedules,
            'disabled_schedules': total_schedules - active_schedules,
            'total_executions': int(recent_executions.total_runs or 0),
            'successful_executions': int(recent_executions.successful_runs or 0),
            'failed_executions': int(recent_executions.failed_runs or 0),
            'success_rate_percent': (
                (recent_executions.successful_runs / recent_executions.total_runs * 100)
                if recent_executions.total_runs and recent_executions.total_runs > 0
                else 0
            )
        }
