"""
Monitoring repository for system metrics and health tracking.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, and_, func, desc, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.common.repository import BaseRepository
from app.domains.monitoring.models import (
    APIMetrics,
    SystemMetrics,
    ServiceHealth,
    RateLimitTracking,
    SecurityEvents,
    RateLimitPolicies,
    HealthStatus,
    MetricType
)


class APIMetricsRepository(BaseRepository[APIMetrics]):
    """Repository for API metrics operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(APIMetrics, session)
    
    async def record_api_call(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: int,
        user_id: Optional[UUID] = None,
        company_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> APIMetrics:
        """Record an API call metric."""
        metric = APIMetrics(
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            user_id=user_id,
            company_id=company_id,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.utcnow()
        )
        
        return await self.create(metric)
    
    async def get_endpoint_metrics(
        self,
        endpoint: str,
        start_time: datetime,
        end_time: datetime,
        method: Optional[str] = None
    ) -> List[APIMetrics]:
        """Get metrics for a specific endpoint."""
        query = select(APIMetrics).where(
            and_(
                APIMetrics.endpoint == endpoint,
                APIMetrics.timestamp >= start_time,
                APIMetrics.timestamp <= end_time
            )
        )
        
        if method:
            query = query.where(APIMetrics.method == method)
            
        query = query.order_by(APIMetrics.timestamp)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_performance_summary(
        self,
        start_time: datetime,
        end_time: datetime,
        company_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get performance summary for time period."""
        query = select(APIMetrics).where(
            and_(
                APIMetrics.timestamp >= start_time,
                APIMetrics.timestamp <= end_time
            )
        )
        
        if company_id:
            query = query.where(APIMetrics.company_id == company_id)
        
        # Get basic stats
        total_requests = await self.session.execute(
            select(func.count(APIMetrics.id)).select_from(query.subquery())
        )
        
        avg_response_time = await self.session.execute(
            select(func.avg(APIMetrics.response_time_ms)).select_from(query.subquery())
        )
        
        error_rate = await self.session.execute(
            select(func.count(APIMetrics.id)).select_from(
                query.where(APIMetrics.status_code >= 400).subquery()
            )
        )
        
        # Get top endpoints
        top_endpoints = await self.session.execute(
            select(
                APIMetrics.endpoint,
                func.count(APIMetrics.id).label('request_count'),
                func.avg(APIMetrics.response_time_ms).label('avg_response_time')
            ).select_from(query.subquery()).group_by(
                APIMetrics.endpoint
            ).order_by(desc('request_count')).limit(10)
        )
        
        total_count = total_requests.scalar() or 0
        error_count = error_rate.scalar() or 0
        
        return {
            'total_requests': total_count,
            'avg_response_time_ms': round(avg_response_time.scalar() or 0, 2),
            'error_rate_percent': round((error_count / total_count * 100) if total_count > 0 else 0, 2),
            'top_endpoints': [
                {
                    'endpoint': row.endpoint,
                    'request_count': row.request_count,
                    'avg_response_time_ms': round(row.avg_response_time, 2)
                }
                for row in top_endpoints.all()
            ]
        }
    
    async def get_error_analysis(
        self,
        start_time: datetime,
        end_time: datetime,
        status_code: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get error analysis for time period."""
        query = select(
            APIMetrics.endpoint,
            APIMetrics.status_code,
            func.count(APIMetrics.id).label('error_count'),
            func.max(APIMetrics.timestamp).label('last_occurrence')
        ).where(
            and_(
                APIMetrics.timestamp >= start_time,
                APIMetrics.timestamp <= end_time,
                APIMetrics.status_code >= 400
            )
        )
        
        if status_code:
            query = query.where(APIMetrics.status_code == status_code)
            
        query = query.group_by(
            APIMetrics.endpoint, APIMetrics.status_code
        ).order_by(desc('error_count'))
        
        result = await self.session.execute(query)
        return [
            {
                'endpoint': row.endpoint,
                'status_code': row.status_code,
                'error_count': row.error_count,
                'last_occurrence': row.last_occurrence
            }
            for row in result.all()
        ]


class SystemMetricsRepository(BaseRepository[SystemMetrics]):
    """Repository for system metrics operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(SystemMetrics, session)
    
    async def record_system_metric(
        self,
        metric_type: MetricType,
        value: float,
        service_metadata: Optional[Dict[str, Any]] = None
    ) -> SystemMetrics:
        """Record a system metric."""
        metric = SystemMetrics(
            metric_type=metric_type,
            value=value,
            service_metadata=service_metadata or {},
            timestamp=datetime.utcnow()
        )
        
        return await self.create(metric)
    
    async def get_metrics_by_type(
        self,
        metric_type: MetricType,
        start_time: datetime,
        end_time: datetime,
        limit: int = 1000
    ) -> List[SystemMetrics]:
        """Get metrics by type for time period."""
        query = select(SystemMetrics).where(
            and_(
                SystemMetrics.metric_type == metric_type,
                SystemMetrics.timestamp >= start_time,
                SystemMetrics.timestamp <= end_time
            )
        ).order_by(SystemMetrics.timestamp).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_latest_metrics(
        self,
        metric_types: Optional[List[MetricType]] = None,
        minutes: int = 60
    ) -> List[SystemMetrics]:
        """Get latest metrics for specified types."""
        start_time = datetime.utcnow() - timedelta(minutes=minutes)
        
        query = select(SystemMetrics).where(
            SystemMetrics.timestamp >= start_time
        )
        
        if metric_types:
            query = query.where(SystemMetrics.metric_type.in_(metric_types))
            
        query = query.order_by(desc(SystemMetrics.timestamp))
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_aggregated_metrics(
        self,
        metric_type: MetricType,
        start_time: datetime,
        end_time: datetime,
        interval_minutes: int = 5
    ) -> List[Dict[str, Any]]:
        """Get aggregated metrics by time intervals."""
        # PostgreSQL specific query for time bucket aggregation
        interval_sql = f"'{interval_minutes} minutes'"
        
        query = text(f"""
            SELECT 
                date_trunc('minute', timestamp) + 
                (EXTRACT(minute FROM timestamp)::int / {interval_minutes}) * 
                interval '{interval_minutes} minute' as time_bucket,
                AVG(value) as avg_value,
                MIN(value) as min_value,
                MAX(value) as max_value,
                COUNT(*) as data_points
            FROM system_metrics 
            WHERE metric_type = :metric_type 
                AND timestamp >= :start_time 
                AND timestamp <= :end_time
            GROUP BY time_bucket
            ORDER BY time_bucket
        """)
        
        result = await self.session.execute(
            query,
            {
                'metric_type': metric_type.value,
                'start_time': start_time,
                'end_time': end_time
            }
        )
        
        return [
            {
                'time_bucket': row.time_bucket,
                'avg_value': float(row.avg_value),
                'min_value': float(row.min_value),
                'max_value': float(row.max_value),
                'data_points': row.data_points
            }
            for row in result.all()
        ]


class ServiceHealthRepository(BaseRepository[ServiceHealth]):
    """Repository for service health operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(ServiceHealth, session)
    
    async def record_health_check(
        self,
        service_name: str,
        status: HealthStatus,
        response_time_ms: Optional[int] = None,
        error_message: Optional[str] = None,
        service_metadata: Optional[Dict[str, Any]] = None
    ) -> ServiceHealth:
        """Record a service health check."""
        health = ServiceHealth(
            service_name=service_name,
            status=status,
            response_time_ms=response_time_ms,
            error_message=error_message,
            service_metadata=service_metadata or {},
            timestamp=datetime.utcnow()
        )
        
        return await self.create(health)
    
    async def get_service_status(self, service_name: str) -> Optional[ServiceHealth]:
        """Get latest status for a service."""
        query = select(ServiceHealth).where(
            ServiceHealth.service_name == service_name
        ).order_by(desc(ServiceHealth.timestamp)).limit(1)
        
        result = await self.session.execute(query)
        return result.scalars().first()
    
    async def get_all_service_statuses(self) -> List[ServiceHealth]:
        """Get latest status for all services."""
        # Get latest record for each service
        subquery = select(
            ServiceHealth.service_name,
            func.max(ServiceHealth.timestamp).label('max_timestamp')
        ).group_by(ServiceHealth.service_name).subquery()
        
        query = select(ServiceHealth).join(
            subquery,
            and_(
                ServiceHealth.service_name == subquery.c.service_name,
                ServiceHealth.timestamp == subquery.c.max_timestamp
            )
        ).order_by(ServiceHealth.service_name)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_service_uptime(
        self,
        service_name: str,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Calculate service uptime for time period."""
        total_checks = await self.session.execute(
            select(func.count(ServiceHealth.id)).where(
                and_(
                    ServiceHealth.service_name == service_name,
                    ServiceHealth.timestamp >= start_time,
                    ServiceHealth.timestamp <= end_time
                )
            )
        )
        
        healthy_checks = await self.session.execute(
            select(func.count(ServiceHealth.id)).where(
                and_(
                    ServiceHealth.service_name == service_name,
                    ServiceHealth.status == HealthStatus.HEALTHY,
                    ServiceHealth.timestamp >= start_time,
                    ServiceHealth.timestamp <= end_time
                )
            )
        )
        
        total_count = total_checks.scalar() or 0
        healthy_count = healthy_checks.scalar() or 0
        
        uptime_percent = (healthy_count / total_count * 100) if total_count > 0 else 0
        
        return {
            'service_name': service_name,
            'total_checks': total_count,
            'healthy_checks': healthy_count,
            'uptime_percent': round(uptime_percent, 2),
            'period_start': start_time,
            'period_end': end_time
        }


class RateLimitTrackingRepository(BaseRepository[RateLimitTracking]):
    """Repository for rate limit tracking operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(RateLimitTracking, session)
    
    async def record_rate_limit_event(
        self,
        identifier: str,
        endpoint: str,
        current_count: int,
        limit_value: int,
        window_start: datetime,
        window_end: datetime,
        blocked: bool = False,
        user_id: Optional[UUID] = None,
        company_id: Optional[UUID] = None
    ) -> RateLimitTracking:
        """Record a rate limit tracking event."""
        event = RateLimitTracking(
            identifier=identifier,
            endpoint=endpoint,
            current_count=current_count,
            limit_value=limit_value,
            window_start=window_start,
            window_end=window_end,
            blocked=blocked,
            user_id=user_id,
            company_id=company_id,
            timestamp=datetime.utcnow()
        )
        
        return await self.create(event)
    
    async def get_current_usage(
        self,
        identifier: str,
        endpoint: str,
        window_start: datetime,
        window_end: datetime
    ) -> int:
        """Get current usage count for identifier and endpoint in time window."""
        result = await self.session.execute(
            select(func.count(RateLimitTracking.id)).where(
                and_(
                    RateLimitTracking.identifier == identifier,
                    RateLimitTracking.endpoint == endpoint,
                    RateLimitTracking.timestamp >= window_start,
                    RateLimitTracking.timestamp <= window_end
                )
            )
        )
        
        return result.scalar() or 0
    
    async def get_blocked_requests(
        self,
        start_time: datetime,
        end_time: datetime,
        endpoint: Optional[str] = None
    ) -> List[RateLimitTracking]:
        """Get blocked requests for time period."""
        query = select(RateLimitTracking).where(
            and_(
                RateLimitTracking.blocked == True,
                RateLimitTracking.timestamp >= start_time,
                RateLimitTracking.timestamp <= end_time
            )
        )
        
        if endpoint:
            query = query.where(RateLimitTracking.endpoint == endpoint)
            
        query = query.order_by(desc(RateLimitTracking.timestamp))
        result = await self.session.execute(query)
        return result.scalars().all()


class SecurityEventsRepository(BaseRepository[SecurityEvents]):
    """Repository for security events operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(SecurityEvents, session)
    
    async def record_security_event(
        self,
        event_type: str,
        severity: str,
        description: str,
        source_ip: str,
        user_id: Optional[UUID] = None,
        company_id: Optional[UUID] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> SecurityEvents:
        """Record a security event."""
        event = SecurityEvents(
            event_type=event_type,
            severity=severity,
            description=description,
            source_ip=source_ip,
            user_id=user_id,
            company_id=company_id,
            additional_data=additional_data or {},
            timestamp=datetime.utcnow()
        )
        
        return await self.create(event)
    
    async def get_security_events(
        self,
        start_time: datetime,
        end_time: datetime,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        source_ip: Optional[str] = None,
        user_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[SecurityEvents]:
        """Get security events with filtering."""
        query = select(SecurityEvents).where(
            and_(
                SecurityEvents.timestamp >= start_time,
                SecurityEvents.timestamp <= end_time
            )
        )
        
        if event_type:
            query = query.where(SecurityEvents.event_type == event_type)
            
        if severity:
            query = query.where(SecurityEvents.severity == severity)
            
        if source_ip:
            query = query.where(SecurityEvents.source_ip == source_ip)
            
        if user_id:
            query = query.where(SecurityEvents.user_id == user_id)
            
        query = query.order_by(desc(SecurityEvents.timestamp)).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_security_summary(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Get security events summary for time period."""
        # Total events
        total_events = await self.session.execute(
            select(func.count(SecurityEvents.id)).where(
                and_(
                    SecurityEvents.timestamp >= start_time,
                    SecurityEvents.timestamp <= end_time
                )
            )
        )
        
        # Events by severity
        severity_stats = await self.session.execute(
            select(
                SecurityEvents.severity,
                func.count(SecurityEvents.id).label('count')
            ).where(
                and_(
                    SecurityEvents.timestamp >= start_time,
                    SecurityEvents.timestamp <= end_time
                )
            ).group_by(SecurityEvents.severity)
        )
        
        # Top event types
        event_type_stats = await self.session.execute(
            select(
                SecurityEvents.event_type,
                func.count(SecurityEvents.id).label('count')
            ).where(
                and_(
                    SecurityEvents.timestamp >= start_time,
                    SecurityEvents.timestamp <= end_time
                )
            ).group_by(SecurityEvents.event_type).order_by(desc('count')).limit(10)
        )
        
        # Top source IPs
        source_ip_stats = await self.session.execute(
            select(
                SecurityEvents.source_ip,
                func.count(SecurityEvents.id).label('count')
            ).where(
                and_(
                    SecurityEvents.timestamp >= start_time,
                    SecurityEvents.timestamp <= end_time
                )
            ).group_by(SecurityEvents.source_ip).order_by(desc('count')).limit(10)
        )
        
        return {
            'total_events': total_events.scalar() or 0,
            'severity_breakdown': {
                row.severity: row.count for row in severity_stats.all()
            },
            'top_event_types': [
                {'event_type': row.event_type, 'count': row.count}
                for row in event_type_stats.all()
            ],
            'top_source_ips': [
                {'source_ip': row.source_ip, 'count': row.count}
                for row in source_ip_stats.all()
            ]
        }


class RateLimitPoliciesRepository(BaseRepository[RateLimitPolicies]):
    """Repository for rate limit policies operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(RateLimitPolicies, session)
    
    async def get_active_policies(
        self,
        endpoint: Optional[str] = None,
        user_type: Optional[str] = None
    ) -> List[RateLimitPolicies]:
        """Get active rate limit policies."""
        query = select(RateLimitPolicies).where(
            RateLimitPolicies.is_active == True
        )
        
        if endpoint:
            query = query.where(RateLimitPolicies.endpoint == endpoint)
            
        if user_type:
            query = query.where(RateLimitPolicies.user_type == user_type)
            
        query = query.order_by(RateLimitPolicies.priority)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_policy_for_request(
        self,
        endpoint: str,
        user_type: str
    ) -> Optional[RateLimitPolicies]:
        """Get most specific rate limit policy for a request."""
        # Try exact endpoint match first
        exact_match = await self.session.execute(
            select(RateLimitPolicies).where(
                and_(
                    RateLimitPolicies.endpoint == endpoint,
                    RateLimitPolicies.user_type == user_type,
                    RateLimitPolicies.is_active == True
                )
            ).order_by(RateLimitPolicies.priority).limit(1)
        )
        
        policy = exact_match.scalars().first()
        if policy:
            return policy
        
        # Try wildcard endpoint match
        wildcard_match = await self.session.execute(
            select(RateLimitPolicies).where(
                and_(
                    RateLimitPolicies.endpoint == "*",
                    RateLimitPolicies.user_type == user_type,
                    RateLimitPolicies.is_active == True
                )
            ).order_by(RateLimitPolicies.priority).limit(1)
        )
        
        return wildcard_match.scalars().first()
