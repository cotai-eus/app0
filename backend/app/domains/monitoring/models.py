"""
Monitoring models for system metrics, API performance, and observability.
Based on the database architecture plan.
"""
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Float, BigInteger, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.shared.common.base_models import BaseModel, TimestampMixin, UserTrackingMixin


class MetricType(str, Enum):
    """Types of metrics collected."""
    API_REQUEST = "api_request"
    SYSTEM_RESOURCE = "system_resource"
    DATABASE_QUERY = "database_query"
    AI_PROCESSING = "ai_processing"
    USER_ACTION = "user_action"
    ERROR_RATE = "error_rate"
    BUSINESS_KPI = "business_kpi"


class ServiceStatus(str, Enum):
    """Health status of services."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class AlertSeverity(str, Enum):
    """Severity levels for alerts."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class APIMetrics(BaseModel, TimestampMixin):
    """API request metrics and performance data."""
    __tablename__ = "api_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Request identification
    request_id = Column(String(100))
    endpoint = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)
    path = Column(String(500))
    query_params = Column(JSON)
    
    # Response metrics
    status_code = Column(Integer, nullable=False)
    response_time_ms = Column(Integer, nullable=False)
    response_size_bytes = Column(Integer)
    
    # User context
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    session_id = Column(String(100))
    
    # Request context
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    referer = Column(String(500))
    
    # Performance details
    db_queries_count = Column(Integer, default=0)
    db_query_time_ms = Column(Integer, default=0)
    cache_hits = Column(Integer, default=0)
    cache_misses = Column(Integer, default=0)
    
    # Error tracking
    error_type = Column(String(100))
    error_message = Column(Text)
    stack_trace = Column(Text)
    
    # Rate limiting
    rate_limit_bucket = Column(String(100))
    rate_limit_remaining = Column(Integer)
    
    # Relationships
    user = relationship("User")
    company = relationship("Company")

    __table_args__ = (
        Index('idx_api_metrics_endpoint', 'endpoint'),
        Index('idx_api_metrics_status_code', 'status_code'),
        Index('idx_api_metrics_created_at', 'created_at'),
        Index('idx_api_metrics_user_id', 'user_id'),
        Index('idx_api_metrics_company_id', 'company_id'),
        Index('idx_api_metrics_response_time', 'response_time_ms'),
        # Composite indexes for common queries
        Index('idx_api_metrics_endpoint_date', 'endpoint', 'created_at'),
        Index('idx_api_metrics_company_date', 'company_id', 'created_at'),
    )


class SystemMetrics(BaseModel, TimestampMixin):
    """System resource metrics and performance data."""
    __tablename__ = "system_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Metric identification
    metric_type = Column(String(50), nullable=False)
    metric_name = Column(String(100), nullable=False)
    source = Column(String(100), nullable=False)  # hostname, service name, etc.
    
    # Metric values
    value = Column(Float, nullable=False)
    unit = Column(String(20))  # bytes, percent, count, etc.
    tags = Column(JSON)  # Additional metadata/labels
    
    # System context
    hostname = Column(String(255))
    service_name = Column(String(100))
    environment = Column(String(50))  # dev, staging, prod
    
    # Thresholds
    warning_threshold = Column(Float)
    critical_threshold = Column(Float)
    is_alert_triggered = Column(Boolean, default=False)
    
    # Aggregation support
    aggregation_period = Column(String(20))  # 1m, 5m, 1h, 1d
    sample_count = Column(Integer, default=1)

    __table_args__ = (
        Index('idx_system_metrics_type', 'metric_type'),
        Index('idx_system_metrics_name', 'metric_name'),
        Index('idx_system_metrics_source', 'source'),
        Index('idx_system_metrics_created_at', 'created_at'),
        Index('idx_system_metrics_value', 'value'),
        # Composite indexes for time-series queries
        Index('idx_system_metrics_source_name_date', 'source', 'metric_name', 'created_at'),
        Index('idx_system_metrics_type_date', 'metric_type', 'created_at'),
    )


class ServiceHealth(BaseModel, TimestampMixin):
    """Health status monitoring for services."""
    __tablename__ = "service_health"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Service identification
    service_name = Column(String(100), nullable=False)
    instance_id = Column(String(100))
    version = Column(String(50))
    hostname = Column(String(255))
    
    # Health status
    status = Column(String(20), nullable=False, default=ServiceStatus.UNKNOWN)
    health_score = Column(Integer)  # 0-100 health score
    
    # Check details
    check_type = Column(String(50))  # http, tcp, database, custom
    check_url = Column(String(500))
    response_time_ms = Column(Integer)
    
    # Dependencies
    dependencies = Column(JSON)  # List of dependent services and their status
    dependency_failures = Column(JSON)  # Failed dependencies
    
    # Resource usage
    cpu_usage_percent = Column(Float)
    memory_usage_percent = Column(Float)
    disk_usage_percent = Column(Float)
    
    # Error information
    error_count = Column(Integer, default=0)
    last_error = Column(Text)
    consecutive_failures = Column(Integer, default=0)
    
    # Alerting
    alert_sent = Column(Boolean, default=False)
    alert_severity = Column(String(20))
      # Additional metadata
    service_metadata = Column(JSON)
    tags = Column(JSON)

    __table_args__ = (
        Index('idx_service_health_service_name', 'service_name'),
        Index('idx_service_health_status', 'status'),
        Index('idx_service_health_created_at', 'created_at'),
        Index('idx_service_health_health_score', 'health_score'),
        # Composite index for latest status per service
        Index('idx_service_health_service_date', 'service_name', 'created_at'),
    )


class RateLimitTracking(BaseModel, TimestampMixin):
    """Rate limiting tracking and statistics."""
    __tablename__ = "rate_limit_tracking"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Rate limit identification
    bucket_key = Column(String(255), nullable=False)  # user_id:endpoint or ip:endpoint
    rule_name = Column(String(100), nullable=False)
    
    # Request details
    endpoint = Column(String(255), nullable=False)
    method = Column(String(10))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    ip_address = Column(String(45))
    
    # Rate limit status
    request_count = Column(Integer, nullable=False)
    limit_value = Column(Integer, nullable=False)
    window_size_seconds = Column(Integer, nullable=False)
    remaining_requests = Column(Integer, nullable=False)
    
    # Violation tracking
    is_blocked = Column(Boolean, default=False)
    block_duration_seconds = Column(Integer)
    violation_count = Column(Integer, default=0)
    
    # Time windows
    window_start = Column(DateTime, nullable=False)
    window_end = Column(DateTime, nullable=False)
    blocked_until = Column(DateTime)
    
    # Context
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    user_agent = Column(Text)
    
    # Relationships
    user = relationship("User")
    company = relationship("Company")

    __table_args__ = (
        Index('idx_rate_limit_bucket_key', 'bucket_key'),
        Index('idx_rate_limit_user_id', 'user_id'),
        Index('idx_rate_limit_endpoint', 'endpoint'),
        Index('idx_rate_limit_is_blocked', 'is_blocked'),
        Index('idx_rate_limit_window_end', 'window_end'),
        # Composite indexes for rate limit lookups
        Index('idx_rate_limit_bucket_window', 'bucket_key', 'window_end'),
        Index('idx_rate_limit_user_endpoint', 'user_id', 'endpoint', 'window_end'),
    )


class SecurityEvents(BaseModel, TimestampMixin):
    """Security events and threat detection."""
    __tablename__ = "security_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Event identification
    event_type = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False, default=AlertSeverity.INFO)
    source = Column(String(100), nullable=False)
    
    # Event details
    title = Column(String(255), nullable=False)
    description = Column(Text)
    raw_data = Column(JSON)  # Original event data
    
    # User/session context
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    session_id = Column(String(100))
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Request context
    endpoint = Column(String(255))
    method = Column(String(10))
    request_id = Column(String(100))
    
    # Threat assessment
    risk_score = Column(Integer)  # 0-100 risk level
    threat_indicators = Column(JSON)  # Array of threat indicators
    false_positive_probability = Column(Float)  # 0.0-1.0
    
    # Response tracking
    is_investigated = Column(Boolean, default=False)
    investigation_notes = Column(Text)
    investigated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    investigated_at = Column(DateTime)
    
    # Actions taken
    action_taken = Column(String(100))  # blocked, warned, ignored, etc.
    automated_response = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    investigator = relationship("User", foreign_keys=[investigated_by])

    __table_args__ = (
        Index('idx_security_events_event_type', 'event_type'),
        Index('idx_security_events_severity', 'severity'),
        Index('idx_security_events_user_id', 'user_id'),
        Index('idx_security_events_ip_address', 'ip_address'),
        Index('idx_security_events_created_at', 'created_at'),
        Index('idx_security_events_risk_score', 'risk_score'),
        Index('idx_security_events_is_investigated', 'is_investigated'),
    )


class RateLimitPolicies(BaseModel, TimestampMixin, UserTrackingMixin):
    """Rate limiting policies and rules."""
    __tablename__ = "rate_limit_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Policy identification
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Rule definition
    endpoint_pattern = Column(String(255), nullable=False)  # Regex pattern for endpoints
    method = Column(String(10))  # HTTP method, null for all
    
    # Rate limiting rules
    requests_per_minute = Column(Integer)
    requests_per_hour = Column(Integer)
    requests_per_day = Column(Integer)
    concurrent_requests = Column(Integer)  # Max concurrent requests
    
    # Burst handling
    burst_limit = Column(Integer)  # Allow burst up to this limit
    burst_window_seconds = Column(Integer, default=60)
    
    # Scope
    applies_to = Column(String(50), nullable=False)  # USER, IP, COMPANY, GLOBAL
    user_roles = Column(JSON)  # Apply to specific user roles
    company_plans = Column(JSON)  # Apply to specific company plans
    
    # Actions
    block_duration_seconds = Column(Integer, default=300)  # 5 minutes default
    warning_threshold_percent = Column(Integer, default=80)  # Warn at 80% of limit
    
    # Status and priority
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=100)  # Lower number = higher priority
    
    # Organization
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))  # Company-specific policy
    is_global = Column(Boolean, default=False)  # Apply to all companies
    
    # Exemptions
    exempt_ips = Column(JSON)  # Array of exempt IP addresses/ranges
    exempt_users = Column(JSON)  # Array of exempt user IDs
    
    # Relationships
    company = relationship("Company")

    __table_args__ = (
        Index('idx_rate_limit_policies_endpoint_pattern', 'endpoint_pattern'),
        Index('idx_rate_limit_policies_is_active', 'is_active'),
        Index('idx_rate_limit_policies_applies_to', 'applies_to'),
        Index('idx_rate_limit_policies_priority', 'priority'),
        Index('idx_rate_limit_policies_is_global', 'is_global'),
    )
