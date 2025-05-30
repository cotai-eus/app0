"""
Monitoring and Analytics API endpoints.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session, get_current_user
from app.domains.auth.models import User
from app.domains.monitoring.service import MonitoringService
from app.domains.monitoring.schemas import (
    APIMetricsResponse,
    SystemMetricsResponse,
    ServiceHealthResponse,
    SecurityEventResponse,
    SecurityEventCreate,
    RateLimitPolicyResponse,
    RateLimitPolicyCreate,
    DashboardDataResponse,
    AlertCreate,
    AlertResponse,
)

router = APIRouter()


# System Health endpoints
@router.get("/health", response_model=Dict[str, Any])
async def get_system_health(
    db: AsyncSession = Depends(get_db_session),
):
    """Get overall system health status."""
    service = MonitoringService(db)
    health_data = await service.get_system_health()
    return health_data


@router.get("/health/services", response_model=List[ServiceHealthResponse])
async def get_services_health(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get health status of all services."""
    service = MonitoringService(db)
    services = await service.get_services_health()
    return [ServiceHealthResponse.model_validate(srv) for srv in services]


@router.post("/health/check/{service_name}")
async def check_service_health(
    service_name: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Perform health check on a specific service."""
    service = MonitoringService(db)
    result = await service.check_service_health(service_name)
    return result


# Metrics endpoints
@router.get("/metrics/api", response_model=List[APIMetricsResponse])
async def get_api_metrics(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    endpoint: Optional[str] = None,
    method: Optional[str] = None,
    status_code: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get API metrics with filtering."""
    service = MonitoringService(db)
    
    filters = {}
    if endpoint:
        filters["endpoint"] = endpoint
    if method:
        filters["method"] = method
    if status_code:
        filters["status_code"] = status_code
    if start_time:
        filters["start_time"] = start_time
    if end_time:
        filters["end_time"] = end_time
        
    metrics = await service.get_api_metrics(
        skip=skip, 
        limit=limit, 
        filters=filters
    )
    return [APIMetricsResponse.model_validate(metric) for metric in metrics]


@router.get("/metrics/system", response_model=List[SystemMetricsResponse])
async def get_system_metrics(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    metric_type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get system metrics."""
    service = MonitoringService(db)
    
    filters = {}
    if metric_type:
        filters["metric_type"] = metric_type
    if start_time:
        filters["start_time"] = start_time
    if end_time:
        filters["end_time"] = end_time
        
    metrics = await service.get_system_metrics(
        skip=skip, 
        limit=limit, 
        filters=filters
    )
    return [SystemMetricsResponse.model_validate(metric) for metric in metrics]


@router.get("/metrics/summary")
async def get_metrics_summary(
    period: str = "1h",
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get metrics summary for a time period."""
    service = MonitoringService(db)
    summary = await service.get_metrics_summary(period)
    return summary


@router.get("/metrics/performance")
async def get_performance_dashboard(
    hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get performance dashboard data."""
    service = MonitoringService(db)
    dashboard_data = await service.get_performance_dashboard(hours)
    return dashboard_data


# Security Events endpoints
@router.post("/security/events", response_model=SecurityEventResponse)
async def create_security_event(
    event_data: SecurityEventCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Create a security event."""
    service = MonitoringService(db)
    event = await service.create_security_event(event_data)
    return SecurityEventResponse.model_validate(event)


@router.get("/security/events", response_model=List[SecurityEventResponse])
async def get_security_events(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    user_id: Optional[UUID] = None,
    ip_address: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get security events with filtering."""
    service = MonitoringService(db)
    
    filters = {}
    if event_type:
        filters["event_type"] = event_type
    if severity:
        filters["severity"] = severity
    if user_id:
        filters["user_id"] = user_id
    if ip_address:
        filters["ip_address"] = ip_address
    if start_time:
        filters["start_time"] = start_time
    if end_time:
        filters["end_time"] = end_time
        
    events = await service.get_security_events(
        skip=skip, 
        limit=limit, 
        filters=filters
    )
    return [SecurityEventResponse.model_validate(event) for event in events]


@router.get("/security/events/{event_id}", response_model=SecurityEventResponse)
async def get_security_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get a specific security event."""
    service = MonitoringService(db)
    event = await service.get_security_event(event_id)
    
    if not event:
        raise HTTPException(status_code=404, detail="Security event not found")
        
    return SecurityEventResponse.model_validate(event)


@router.get("/security/summary")
async def get_security_summary(
    hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get security events summary."""
    service = MonitoringService(db)
    summary = await service.get_security_summary(hours)
    return summary


# Rate Limiting endpoints
@router.post("/rate-limits/policies", response_model=RateLimitPolicyResponse)
async def create_rate_limit_policy(
    policy_data: RateLimitPolicyCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Create a rate limit policy."""
    service = MonitoringService(db)
    policy = await service.create_rate_limit_policy(policy_data)
    return RateLimitPolicyResponse.model_validate(policy)


@router.get("/rate-limits/policies", response_model=List[RateLimitPolicyResponse])
async def get_rate_limit_policies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get rate limit policies."""
    service = MonitoringService(db)
    policies = await service.get_rate_limit_policies(skip=skip, limit=limit)
    return [RateLimitPolicyResponse.model_validate(policy) for policy in policies]


@router.get("/rate-limits/policies/{policy_id}", response_model=RateLimitPolicyResponse)
async def get_rate_limit_policy(
    policy_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get a specific rate limit policy."""
    service = MonitoringService(db)
    policy = await service.get_rate_limit_policy(policy_id)
    
    if not policy:
        raise HTTPException(status_code=404, detail="Rate limit policy not found")
        
    return RateLimitPolicyResponse.model_validate(policy)


@router.put("/rate-limits/policies/{policy_id}", response_model=RateLimitPolicyResponse)
async def update_rate_limit_policy(
    policy_id: UUID,
    policy_data: RateLimitPolicyCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Update a rate limit policy."""
    service = MonitoringService(db)
    policy = await service.update_rate_limit_policy(policy_id, policy_data)
    
    if not policy:
        raise HTTPException(status_code=404, detail="Rate limit policy not found")
        
    return RateLimitPolicyResponse.model_validate(policy)


@router.delete("/rate-limits/policies/{policy_id}")
async def delete_rate_limit_policy(
    policy_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Delete a rate limit policy."""
    service = MonitoringService(db)
    success = await service.delete_rate_limit_policy(policy_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Rate limit policy not found")
        
    return {"message": "Rate limit policy deleted successfully"}


@router.get("/rate-limits/status/{identifier}")
async def get_rate_limit_status(
    identifier: str,
    policy_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get rate limit status for an identifier."""
    service = MonitoringService(db)
    status = await service.get_rate_limit_status(identifier, policy_name)
    return status


# Dashboard endpoints
@router.get("/dashboard", response_model=DashboardDataResponse)
async def get_dashboard_data(
    period: str = "24h",
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get dashboard data."""
    service = MonitoringService(db)
    dashboard_data = await service.get_dashboard_data(period)
    return dashboard_data


@router.get("/dashboard/real-time")
async def get_real_time_metrics(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get real-time metrics."""
    service = MonitoringService(db)
    metrics = await service.get_real_time_metrics()
    return metrics


# Alerts endpoints
@router.post("/alerts", response_model=AlertResponse)
async def create_alert(
    alert_data: AlertCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Create a monitoring alert."""
    service = MonitoringService(db)
    alert = await service.create_alert(alert_data)
    return AlertResponse.model_validate(alert)


@router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
    severity: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get monitoring alerts."""
    service = MonitoringService(db)
    
    filters = {}
    if status:
        filters["status"] = status
    if severity:
        filters["severity"] = severity
        
    alerts = await service.get_alerts(skip=skip, limit=limit, filters=filters)
    return [AlertResponse.model_validate(alert) for alert in alerts]


@router.put("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Acknowledge an alert."""
    service = MonitoringService(db)
    success = await service.acknowledge_alert(alert_id, current_user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    return {"message": "Alert acknowledged"}


@router.put("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: UUID,
    resolution_notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Resolve an alert."""
    service = MonitoringService(db)
    success = await service.resolve_alert(alert_id, current_user.id, resolution_notes)
    
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    return {"message": "Alert resolved"}


# Maintenance endpoints
@router.post("/cleanup")
async def cleanup_old_data(
    days: int = Query(30, ge=1, le=365),
    data_types: Optional[List[str]] = Query(None),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Clean up old monitoring data."""
    service = MonitoringService(db)
    cleaned_counts = await service.cleanup_old_data(days, data_types)
    return {
        "message": "Cleanup completed",
        "cleaned_records": cleaned_counts
    }


@router.post("/export")
async def export_metrics(
    start_time: datetime,
    end_time: datetime,
    export_format: str = "csv",
    data_types: Optional[List[str]] = Query(None),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Export metrics data."""
    service = MonitoringService(db)
    export_data = await service.export_metrics(
        start_time, end_time, export_format, data_types
    )
    return export_data
