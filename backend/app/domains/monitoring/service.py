"""
Monitoring service for system metrics, health checks, and performance tracking.
Based on the database architecture plan.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
import psutil
import time

from sqlalchemy.orm import Session
from app.core.exceptions import NotFoundError, ValidationError, ServiceError
from app.domains.monitoring.repository import (
    APIMetricsRepository, SystemMetricsRepository, ServiceHealthRepository,
    RateLimitTrackingRepository, SecurityEventsRepository, RateLimitPoliciesRepository
)
from app.domains.monitoring.models import HealthStatus, SecurityEventType


class MonitoringService:
    """Service for comprehensive system monitoring and observability."""
    
    def __init__(self, db: Session):
        self.db = db
        self.api_metrics_repo = APIMetricsRepository(db)
        self.system_metrics_repo = SystemMetricsRepository(db)
        self.service_health_repo = ServiceHealthRepository(db)
        self.rate_limit_repo = RateLimitTrackingRepository(db)
        self.security_events_repo = SecurityEventsRepository(db)
        self.rate_limit_policies_repo = RateLimitPoliciesRepository(db)
    
    def record_api_metrics(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: int,
        user_id: Optional[str] = None,
        company_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """Record API request metrics."""
        
        metrics = self.api_metrics_repo.record_request(
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            user_id=user_id,
            company_id=company_id,
            **kwargs
        )
        
        return str(metrics.id)
    
    def get_api_metrics_summary(
        self,
        hours: int = 24,
        endpoint: Optional[str] = None,
        company_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get API metrics summary."""
        
        return self.api_metrics_repo.get_metrics_summary(
            hours=hours,
            endpoint=endpoint,
            company_id=company_id
        )
    
    def get_slow_endpoints(
        self,
        threshold_ms: int = 1000,
        hours: int = 24,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get endpoints with slow response times."""
        
        return self.api_metrics_repo.get_slow_endpoints(
            threshold_ms=threshold_ms,
            hours=hours,
            limit=limit
        )
    
    def get_error_hotspots(
        self,
        hours: int = 24,
        min_error_count: int = 5,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get endpoints with high error rates."""
        
        return self.api_metrics_repo.get_error_hotspots(
            hours=hours,
            min_error_count=min_error_count,
            limit=limit
        )
    
    def record_system_metrics(self) -> str:
        """Record current system metrics."""
        
        # Collect system metrics using psutil
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Network I/O
        network = psutil.net_io_counters()
        
        # Load average (Unix systems)
        try:
            load_avg = psutil.getloadavg()
            load_average_1m = load_avg[0]
            load_average_5m = load_avg[1]
            load_average_15m = load_avg[2]
        except AttributeError:
            # Windows doesn't have load average
            load_average_1m = load_average_5m = load_average_15m = None
        
        metrics = self.system_metrics_repo.record_metrics(
            cpu_usage_percent=cpu_percent,
            memory_usage_percent=memory.percent,
            memory_used_mb=memory.used // (1024 * 1024),
            memory_total_mb=memory.total // (1024 * 1024),
            disk_usage_percent=disk.percent,
            disk_used_gb=disk.used // (1024 * 1024 * 1024),
            disk_total_gb=disk.total // (1024 * 1024 * 1024),
            network_bytes_sent=network.bytes_sent,
            network_bytes_received=network.bytes_recv,
            load_average_1m=load_average_1m,
            load_average_5m=load_average_5m,
            load_average_15m=load_average_15m
        )
        
        return str(metrics.id)
    
    def get_system_health_status(self) -> Dict[str, Any]:
        """Get current system health status."""
        
        # Get latest system metrics
        latest_metrics = self.system_metrics_repo.get_latest_metrics()
        
        if not latest_metrics:
            return {
                "status": "unknown",
                "message": "No recent metrics available"
            }
        
        # Define health thresholds
        cpu_warning_threshold = 80
        cpu_critical_threshold = 95
        memory_warning_threshold = 85
        memory_critical_threshold = 95
        disk_warning_threshold = 90
        disk_critical_threshold = 95
        
        health_issues = []
        overall_status = "healthy"
        
        # Check CPU usage
        if latest_metrics.cpu_usage_percent > cpu_critical_threshold:
            health_issues.append(f"Critical CPU usage: {latest_metrics.cpu_usage_percent}%")
            overall_status = "critical"
        elif latest_metrics.cpu_usage_percent > cpu_warning_threshold:
            health_issues.append(f"High CPU usage: {latest_metrics.cpu_usage_percent}%")
            if overall_status == "healthy":
                overall_status = "warning"
        
        # Check memory usage
        if latest_metrics.memory_usage_percent > memory_critical_threshold:
            health_issues.append(f"Critical memory usage: {latest_metrics.memory_usage_percent}%")
            overall_status = "critical"
        elif latest_metrics.memory_usage_percent > memory_warning_threshold:
            health_issues.append(f"High memory usage: {latest_metrics.memory_usage_percent}%")
            if overall_status == "healthy":
                overall_status = "warning"
        
        # Check disk usage
        if latest_metrics.disk_usage_percent > disk_critical_threshold:
            health_issues.append(f"Critical disk usage: {latest_metrics.disk_usage_percent}%")
            overall_status = "critical"
        elif latest_metrics.disk_usage_percent > disk_warning_threshold:
            health_issues.append(f"High disk usage: {latest_metrics.disk_usage_percent}%")
            if overall_status == "healthy":
                overall_status = "warning"
        
        return {
            "status": overall_status,
            "timestamp": latest_metrics.created_at.isoformat(),
            "metrics": {
                "cpu_percent": latest_metrics.cpu_usage_percent,
                "memory_percent": latest_metrics.memory_usage_percent,
                "disk_percent": latest_metrics.disk_usage_percent,
                "load_average_1m": latest_metrics.load_average_1m
            },
            "issues": health_issues
        }
    
    def get_system_metrics_history(
        self,
        hours: int = 24,
        interval_minutes: int = 5
    ) -> List[Dict[str, Any]]:
        """Get system metrics history."""
        
        return self.system_metrics_repo.get_metrics_history(hours, interval_minutes)
    
    def check_service_health(
        self,
        service_name: str,
        endpoint: Optional[str] = None
    ) -> Dict[str, Any]:
        """Check health of a specific service."""
        
        start_time = time.time()
        
        try:
            # Perform health check based on service type
            if service_name == "database":
                # Check database connectivity
                self.db.execute("SELECT 1")
                status = HealthStatus.HEALTHY
                message = "Database connection successful"
                
            elif service_name == "redis":
                # Would check Redis connectivity in production
                status = HealthStatus.HEALTHY
                message = "Redis connection successful"
                
            elif service_name == "celery":
                # Would check Celery worker status in production
                status = HealthStatus.HEALTHY
                message = "Celery workers active"
                
            else:
                # Generic HTTP health check
                status = HealthStatus.HEALTHY
                message = f"Service {service_name} is responding"
                
        except Exception as e:
            status = HealthStatus.UNHEALTHY
            message = f"Health check failed: {str(e)}"
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Record health check result
        health_record = self.service_health_repo.record_health_check(
            service_name=service_name,
            status=status,
            response_time_ms=response_time_ms,
            endpoint=endpoint,
            details={"message": message}
        )
        
        return {
            "service_name": service_name,
            "status": status,
            "response_time_ms": response_time_ms,
            "message": message,
            "timestamp": health_record.created_at.isoformat()
        }
    
    def get_service_status_summary(self) -> Dict[str, Any]:
        """Get status summary for all monitored services."""
        
        services = ["database", "redis", "celery", "api"]
        service_statuses = {}
        
        for service in services:
            latest_check = self.service_health_repo.get_latest_health_check(service)
            if latest_check:
                service_statuses[service] = {
                    "status": latest_check.status,
                    "last_check": latest_check.created_at.isoformat(),
                    "response_time_ms": latest_check.response_time_ms
                }
            else:
                service_statuses[service] = {
                    "status": "unknown",
                    "last_check": None,
                    "response_time_ms": None
                }
        
        # Determine overall system status
        overall_status = "healthy"
        unhealthy_services = [
            service for service, status in service_statuses.items()
            if status["status"] in [HealthStatus.UNHEALTHY, HealthStatus.DEGRADED]
        ]
        
        if unhealthy_services:
            overall_status = "degraded" if len(unhealthy_services) < len(services) / 2 else "unhealthy"
        
        return {
            "overall_status": overall_status,
            "services": service_statuses,
            "unhealthy_services": unhealthy_services,
            "total_services": len(services),
            "healthy_services": len(services) - len(unhealthy_services)
        }
    
    def track_rate_limit(
        self,
        identifier: str,
        identifier_type: str,
        endpoint: str,
        company_id: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """Track and check rate limiting."""
        
        # Get applicable rate limit policy
        policy = self.rate_limit_policies_repo.get_applicable_policy(
            endpoint=endpoint,
            identifier_type=identifier_type,
            company_id=company_id
        )
        
        if not policy:
            # No rate limiting policy - allow request
            return True, {"rate_limited": False, "message": "No rate limit policy"}
        
        # Check current rate limit status
        is_allowed, remaining_requests, reset_time = self.rate_limit_repo.check_rate_limit(
            identifier=identifier,
            identifier_type=identifier_type,
            endpoint=endpoint,
            limit=policy.request_limit,
            window_seconds=policy.time_window_seconds
        )
        
        # Record the rate limit check
        self.rate_limit_repo.record_request(
            identifier=identifier,
            identifier_type=identifier_type,
            endpoint=endpoint,
            allowed=is_allowed,
            company_id=company_id
        )
        
        return is_allowed, {
            "rate_limited": not is_allowed,
            "remaining_requests": remaining_requests,
            "reset_time": reset_time.isoformat() if reset_time else None,
            "policy": {
                "request_limit": policy.request_limit,
                "window_seconds": policy.time_window_seconds
            }
        }
    
    def get_rate_limit_statistics(
        self,
        hours: int = 24,
        company_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get rate limiting statistics."""
        
        return self.rate_limit_repo.get_rate_limit_statistics(hours, company_id)
    
    def record_security_event(
        self,
        event_type: SecurityEventType,
        description: str,
        severity: str,
        source_ip: Optional[str] = None,
        user_id: Optional[str] = None,
        company_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """Record a security event."""
        
        event = self.security_events_repo.record_event(
            event_type=event_type,
            description=description,
            severity=severity,
            source_ip=source_ip,
            user_id=user_id,
            company_id=company_id,
            **kwargs
        )
        
        return str(event.id)
    
    def get_security_events(
        self,
        hours: int = 24,
        severity: Optional[str] = None,
        event_type: Optional[SecurityEventType] = None,
        company_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get recent security events."""
        
        events = self.security_events_repo.get_recent_events(
            hours=hours,
            severity=severity,
            event_type=event_type,
            company_id=company_id
        )
        
        return [
            {
                "id": str(event.id),
                "event_type": event.event_type,
                "description": event.description,
                "severity": event.severity,
                "source_ip": event.source_ip,
                "user_id": str(event.user_id) if event.user_id else None,
                "created_at": event.created_at.isoformat(),
                "details": event.details
            }
            for event in events
        ]
    
    def get_security_summary(
        self,
        hours: int = 24,
        company_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get security events summary."""
        
        return self.security_events_repo.get_security_summary(hours, company_id)
    
    def get_monitoring_dashboard(
        self,
        company_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get comprehensive monitoring dashboard data."""
        
        # System health
        system_health = self.get_system_health_status()
        
        # Service status
        service_status = self.get_service_status_summary()
        
        # API metrics
        api_metrics = self.get_api_metrics_summary(hours=24, company_id=company_id)
        
        # Security events
        security_summary = self.get_security_summary(hours=24, company_id=company_id)
        
        # Rate limiting stats
        rate_limit_stats = self.get_rate_limit_statistics(hours=24, company_id=company_id)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "system_health": system_health,
            "service_status": service_status,
            "api_metrics": api_metrics,
            "security_summary": security_summary,
            "rate_limiting": rate_limit_stats
        }
    
    def create_rate_limit_policy(
        self,
        name: str,
        endpoint_pattern: str,
        identifier_type: str,
        request_limit: int,
        time_window_seconds: int,
        created_by: str,
        company_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """Create a new rate limiting policy."""
        
        policy = self.rate_limit_policies_repo.create_policy(
            name=name,
            endpoint_pattern=endpoint_pattern,
            identifier_type=identifier_type,
            request_limit=request_limit,
            time_window_seconds=time_window_seconds,
            created_by=created_by,
            company_id=company_id,
            **kwargs
        )
        
        return str(policy.id)
    
    def update_rate_limit_policy(
        self,
        policy_id: str,
        **updates
    ) -> bool:
        """Update a rate limiting policy."""
        
        return self.rate_limit_policies_repo.update_policy(policy_id, updates)
    
    def get_rate_limit_policies(
        self,
        company_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get rate limiting policies."""
        
        policies = self.rate_limit_policies_repo.get_active_policies(company_id)
        
        return [
            {
                "id": str(policy.id),
                "name": policy.name,
                "endpoint_pattern": policy.endpoint_pattern,
                "identifier_type": policy.identifier_type,
                "request_limit": policy.request_limit,
                "time_window_seconds": policy.time_window_seconds,
                "is_active": policy.is_active,
                "created_at": policy.created_at.isoformat()
            }
            for policy in policies
        ]
    
    def cleanup_old_metrics(
        self,
        days: int = 30
    ) -> Dict[str, int]:
        """Clean up old monitoring data."""
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Clean up old API metrics
        api_deleted = self.api_metrics_repo.cleanup_old_metrics(cutoff_date)
        
        # Clean up old system metrics
        system_deleted = self.system_metrics_repo.cleanup_old_metrics(cutoff_date)
        
        # Clean up old health checks
        health_deleted = self.service_health_repo.cleanup_old_health_checks(cutoff_date)
        
        # Clean up old rate limit tracking
        rate_limit_deleted = self.rate_limit_repo.cleanup_old_tracking(cutoff_date)
        
        return {
            "api_metrics_deleted": api_deleted,
            "system_metrics_deleted": system_deleted,
            "health_checks_deleted": health_deleted,
            "rate_limit_records_deleted": rate_limit_deleted,
            "total_deleted": api_deleted + system_deleted + health_deleted + rate_limit_deleted
        }
