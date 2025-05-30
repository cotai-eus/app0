"""
Celery models for async task processing, worker management, and job queuing.
Based on the database architecture plan.
"""
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Float, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.shared.common.base_models import BaseModel, TimestampMixin


class TaskStatus(str, Enum):
    """Status of Celery tasks."""
    PENDING = "pending"
    RECEIVED = "received"
    STARTED = "started"
    SUCCESS = "success"
    FAILURE = "failure"
    RETRY = "retry"
    REVOKED = "revoked"


class TaskPriority(str, Enum):
    """Priority levels for tasks."""
    LOW = "low"
    NORMAL = "normal" 
    HIGH = "high"
    CRITICAL = "critical"


class WorkerStatus(str, Enum):
    """Status of Celery workers."""
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    IDLE = "idle"
    SHUTDOWN = "shutdown"


class CeleryTask(BaseModel, TimestampMixin):
    """Celery task tracking and management."""
    __tablename__ = "celery_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Task identification
    task_id = Column(String(155), unique=True, nullable=False)  # Celery task ID
    task_name = Column(String(255), nullable=False)  # Task function name
    
    # Task details
    status = Column(String(50), nullable=False, default=TaskStatus.PENDING)
    priority = Column(String(20), default=TaskPriority.NORMAL)
    queue_name = Column(String(100), default="default")
    
    # Execution context
    args = Column(JSON)  # Task arguments
    kwargs = Column(JSON)  # Task keyword arguments
    result = Column(JSON)  # Task result
    traceback = Column(Text)  # Error traceback if failed
    
    # Timing
    eta = Column(DateTime)  # Estimated time of arrival
    expires = Column(DateTime)  # Task expiration time
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    runtime_seconds = Column(Float)
    
    # Retry handling
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    retry_delay_seconds = Column(Integer, default=60)
    
    # Worker information
    worker_id = Column(String(255))
    worker_hostname = Column(String(255))
    worker_pid = Column(Integer)
    
    # User context
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    
    # Progress tracking
    progress_percent = Column(Integer, default=0)
    progress_message = Column(String(500))
    current_step = Column(String(255))
    total_steps = Column(Integer)
    
    # Resource usage
    memory_usage_mb = Column(Integer)
    cpu_time_seconds = Column(Float)
    
    # Related entities
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"))  # For document processing
    ai_job_id = Column(UUID(as_uuid=True), ForeignKey("ai_processing_jobs.id"))  # For AI processing
    
    # Grouping and dependencies
    group_id = Column(String(155))  # Task group ID
    chain_id = Column(String(155))  # Task chain ID
    parent_task_id = Column(String(155))  # Parent task for subtasks
    
    # Relationships
    user = relationship("User")
    company = relationship("Company")
    document = relationship("Document")
    ai_job = relationship("AIProcessingJob")

    __table_args__ = (
        Index('idx_celery_tasks_task_id', 'task_id'),
        Index('idx_celery_tasks_status', 'status'),
        Index('idx_celery_tasks_task_name', 'task_name'),
        Index('idx_celery_tasks_priority', 'priority'),
        Index('idx_celery_tasks_queue_name', 'queue_name'),
        Index('idx_celery_tasks_created_at', 'created_at'),
        Index('idx_celery_tasks_user_id', 'user_id'),
        Index('idx_celery_tasks_company_id', 'company_id'),
        Index('idx_celery_tasks_worker_id', 'worker_id'),
        Index('idx_celery_tasks_eta', 'eta'),
        Index('idx_celery_tasks_expires', 'expires'),
        # Composite indexes for common queries
        Index('idx_celery_tasks_status_created', 'status', 'created_at'),
        Index('idx_celery_tasks_queue_priority', 'queue_name', 'priority', 'created_at'),
    )


class CeleryWorker(BaseModel, TimestampMixin):
    """Celery worker monitoring and management."""
    __tablename__ = "celery_workers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Worker identification
    worker_id = Column(String(255), unique=True, nullable=False)
    hostname = Column(String(255), nullable=False)
    pid = Column(Integer)
    
    # Worker status
    status = Column(String(50), nullable=False, default=WorkerStatus.OFFLINE)
    is_active = Column(Boolean, default=True)
    
    # Configuration
    queues = Column(JSON)  # Array of queues this worker processes
    concurrency = Column(Integer, default=1)  # Number of concurrent tasks
    max_tasks_per_child = Column(Integer)  # Max tasks before worker restart
    
    # Performance metrics
    active_tasks = Column(Integer, default=0)
    processed_tasks = Column(Integer, default=0)
    failed_tasks = Column(Integer, default=0)
    avg_task_duration_seconds = Column(Float)
    
    # Resource usage
    cpu_usage_percent = Column(Float)
    memory_usage_mb = Column(Integer)
    memory_limit_mb = Column(Integer)
    
    # Health monitoring
    last_heartbeat = Column(DateTime, default=datetime.utcnow)
    heartbeat_interval_seconds = Column(Integer, default=30)
    consecutive_failures = Column(Integer, default=0)
    
    # Version information
    celery_version = Column(String(50))
    python_version = Column(String(50))
    platform = Column(String(100))
    
    # Load balancing
    load_average = Column(Float)  # Current load average
    preferred_queues = Column(JSON)  # Preferred queue order
    
    # Shutdown tracking
    shutdown_requested = Column(Boolean, default=False)
    shutdown_at = Column(DateTime)
    restart_count = Column(Integer, default=0)

    __table_args__ = (
        Index('idx_celery_workers_worker_id', 'worker_id'),
        Index('idx_celery_workers_status', 'status'),
        Index('idx_celery_workers_hostname', 'hostname'),
        Index('idx_celery_workers_is_active', 'is_active'),
        Index('idx_celery_workers_last_heartbeat', 'last_heartbeat'),
        Index('idx_celery_workers_load_average', 'load_average'),
    )


class TaskQueue(BaseModel, TimestampMixin):
    """Task queue monitoring and statistics."""
    __tablename__ = "task_queues"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Queue identification
    queue_name = Column(String(100), unique=True, nullable=False)
    
    # Queue configuration
    priority = Column(Integer, default=100)  # Queue priority
    max_length = Column(Integer)  # Maximum queue length
    message_ttl_seconds = Column(Integer)  # Message time-to-live
    
    # Current status
    pending_tasks = Column(Integer, default=0)
    active_tasks = Column(Integer, default=0)
    scheduled_tasks = Column(Integer, default=0)
    
    # Statistics
    total_processed = Column(Integer, default=0)
    total_failed = Column(Integer, default=0)
    avg_processing_time_seconds = Column(Float)
    
    # Performance metrics
    throughput_per_minute = Column(Float)  # Tasks processed per minute
    error_rate_percent = Column(Float)  # Percentage of failed tasks
    
    # Resource allocation
    assigned_workers = Column(JSON)  # Array of worker IDs processing this queue
    max_workers = Column(Integer)  # Maximum workers for this queue
    
    # Health status
    is_healthy = Column(Boolean, default=True)
    is_paused = Column(Boolean, default=False)
    last_task_at = Column(DateTime)  # When last task was processed
    
    # Alerting thresholds
    warning_threshold = Column(Integer, default=100)  # Warn when queue exceeds this
    critical_threshold = Column(Integer, default=500)  # Critical when queue exceeds this
    
    # Auto-scaling
    auto_scale_enabled = Column(Boolean, default=False)
    min_workers = Column(Integer, default=1)
    scale_up_threshold = Column(Integer, default=50)  # Scale up when queue exceeds this
    scale_down_threshold = Column(Integer, default=10)  # Scale down when queue below this

    __table_args__ = (
        Index('idx_task_queues_queue_name', 'queue_name'),
        Index('idx_task_queues_priority', 'priority'),
        Index('idx_task_queues_pending_tasks', 'pending_tasks'),
        Index('idx_task_queues_is_healthy', 'is_healthy'),
        Index('idx_task_queues_is_paused', 'is_paused'),
    )


class TaskSchedule(BaseModel, TimestampMixin):
    """Scheduled task configuration (similar to crontab)."""
    __tablename__ = "task_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Schedule identification
    name = Column(String(200), unique=True, nullable=False)
    task_name = Column(String(255), nullable=False)
    
    # Schedule configuration
    cron_expression = Column(String(100))  # Cron expression
    interval_seconds = Column(Integer)  # Alternative: run every N seconds
    
    # Task configuration
    args = Column(JSON)  # Task arguments
    kwargs = Column(JSON)  # Task keyword arguments
    queue_name = Column(String(100), default="default")
    priority = Column(String(20), default=TaskPriority.NORMAL)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_paused = Column(Boolean, default=False)
    
    # Execution tracking
    last_run_at = Column(DateTime)
    next_run_at = Column(DateTime)
    total_runs = Column(Integer, default=0)
    successful_runs = Column(Integer, default=0)
    failed_runs = Column(Integer, default=0)
    
    # Constraints
    max_runs = Column(Integer)  # Maximum number of runs (null = unlimited)
    expires_at = Column(DateTime)  # When schedule expires
    
    # Error handling
    max_consecutive_failures = Column(Integer, default=3)
    consecutive_failures = Column(Integer, default=0)
    failure_action = Column(String(50), default="pause")  # pause, disable, continue
    
    # User context
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    
    # Relationships
    creator = relationship("User")
    company = relationship("Company")

    __table_args__ = (
        Index('idx_task_schedules_name', 'name'),
        Index('idx_task_schedules_task_name', 'task_name'),
        Index('idx_task_schedules_is_active', 'is_active'),
        Index('idx_task_schedules_next_run_at', 'next_run_at'),
        Index('idx_task_schedules_company_id', 'company_id'),
    )
