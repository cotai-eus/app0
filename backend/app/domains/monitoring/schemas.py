"""
Schemas for the monitoring domain.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domains.monitoring.models import HealthStatus, MetricType


# Base schemas
class APIMetricsBase(BaseModel):
    """Base schema for API metrics."""
    model_config = ConfigDict(from_attributes=True)
    
    endpoint: str = Field(..., description="Endpoint da API")
    method: str = Field(..., description="Método HTTP")
    status_code: int = Field(..., description="Código de status")
    response_time_ms: int = Field(..., description="Tempo de resposta em ms")
    user_id: Optional[UUID] = Field(default=None, description="ID do usuário")
    company_id: Optional[UUID] = Field(default=None, description="ID da empresa")
    request_size_bytes: Optional[int] = Field(default=None, description="Tamanho da requisição")
    response_size_bytes: Optional[int] = Field(default=None, description="Tamanho da resposta")
    user_agent: Optional[str] = Field(default=None, description="User agent")
    ip_address: Optional[str] = Field(default=None, description="Endereço IP")
    error_message: Optional[str] = Field(default=None, description="Mensagem de erro")
    request_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadados da requisição")


class APIMetricsCreate(APIMetricsBase):
    """Schema for creating API metrics."""
    pass


class APIMetricsResponse(APIMetricsBase):
    """Schema for API metrics responses."""
    id: UUID
    timestamp: datetime
    created_at: datetime


# System Metrics schemas
class SystemMetricsBase(BaseModel):
    """Base schema for system metrics."""
    model_config = ConfigDict(from_attributes=True)
    
    metric_type: MetricType = Field(..., description="Tipo da métrica")
    metric_name: str = Field(..., description="Nome da métrica")
    metric_value: float = Field(..., description="Valor da métrica")
    unit: Optional[str] = Field(default=None, description="Unidade da métrica")
    hostname: Optional[str] = Field(default=None, description="Nome do host")
    service_name: Optional[str] = Field(default=None, description="Nome do serviço")
    tags: Optional[Dict[str, str]] = Field(default=None, description="Tags da métrica")
    metric_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadados da métrica")


class SystemMetricsCreate(SystemMetricsBase):
    """Schema for creating system metrics."""
    pass


class SystemMetricsResponse(SystemMetricsBase):
    """Schema for system metrics responses."""
    id: UUID
    timestamp: datetime
    created_at: datetime


# Service Health schemas
class ServiceHealthBase(BaseModel):
    """Base schema for service health."""
    model_config = ConfigDict(from_attributes=True)
    
    service_name: str = Field(..., description="Nome do serviço")
    status: HealthStatus = Field(..., description="Status de saúde")
    version: Optional[str] = Field(default=None, description="Versão do serviço")
    uptime_seconds: Optional[int] = Field(default=None, description="Uptime em segundos")
    last_check_at: Optional[datetime] = Field(default=None, description="Último check")
    error_message: Optional[str] = Field(default=None, description="Mensagem de erro")
    dependencies: Optional[List[str]] = Field(default=None, description="Dependências")
    service_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadados do serviço")


class ServiceHealthCreate(ServiceHealthBase):
    """Schema for creating service health."""
    pass


class ServiceHealthUpdate(BaseModel):
    """Schema for updating service health."""
    model_config = ConfigDict(from_attributes=True)
    
    status: Optional[HealthStatus] = None
    version: Optional[str] = None
    uptime_seconds: Optional[int] = None
    last_check_at: Optional[datetime] = None
    error_message: Optional[str] = None
    dependencies: Optional[List[str]] = None
    service_metadata: Optional[Dict[str, Any]] = None


class ServiceHealthResponse(ServiceHealthBase):
    """Schema for service health responses."""
    id: UUID
    created_at: datetime
    updated_at: datetime


# Rate Limit Tracking schemas
class RateLimitTrackingBase(BaseModel):
    """Base schema for rate limit tracking."""
    model_config = ConfigDict(from_attributes=True)
    
    endpoint: str = Field(..., description="Endpoint")
    user_id: Optional[UUID] = Field(default=None, description="ID do usuário")
    ip_address: Optional[str] = Field(default=None, description="Endereço IP")
    company_id: Optional[UUID] = Field(default=None, description="ID da empresa")
    request_count: int = Field(default=1, description="Contador de requisições")
    window_start: datetime = Field(..., description="Início da janela")
    window_end: datetime = Field(..., description="Fim da janela")
    rate_limit_exceeded: bool = Field(default=False, description="Limite excedido")
    tracking_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadados do tracking")


class RateLimitTrackingCreate(RateLimitTrackingBase):
    """Schema for creating rate limit tracking."""
    pass


class RateLimitTrackingResponse(RateLimitTrackingBase):
    """Schema for rate limit tracking responses."""
    id: UUID
    created_at: datetime
    updated_at: datetime


# Security Events schemas
class SecurityEventsBase(BaseModel):
    """Base schema for security events."""
    model_config = ConfigDict(from_attributes=True)
    
    event_type: str = Field(..., description="Tipo do evento")
    severity: str = Field(..., description="Severidade")
    user_id: Optional[UUID] = Field(default=None, description="ID do usuário")
    ip_address: Optional[str] = Field(default=None, description="Endereço IP")
    user_agent: Optional[str] = Field(default=None, description="User agent")
    endpoint: Optional[str] = Field(default=None, description="Endpoint")
    description: str = Field(..., description="Descrição do evento")
    blocked: bool = Field(default=False, description="Se foi bloqueado")
    event_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadados do evento")


class SecurityEventsCreate(SecurityEventsBase):
    """Schema for creating security events."""
    pass


class SecurityEventsResponse(SecurityEventsBase):
    """Schema for security events responses."""
    id: UUID
    timestamp: datetime
    created_at: datetime


# Rate Limit Policies schemas
class RateLimitPoliciesBase(BaseModel):
    """Base schema for rate limit policies."""
    model_config = ConfigDict(from_attributes=True)
    
    policy_name: str = Field(..., description="Nome da política")
    endpoint_pattern: str = Field(..., description="Padrão do endpoint")
    requests_per_minute: int = Field(..., description="Requisições por minuto")
    requests_per_hour: int = Field(..., description="Requisições por hora")
    requests_per_day: int = Field(..., description="Requisições por dia")
    applies_to_users: bool = Field(default=True, description="Aplica a usuários")
    applies_to_ips: bool = Field(default=True, description="Aplica a IPs")
    applies_to_companies: bool = Field(default=False, description="Aplica a empresas")
    bypass_roles: Optional[List[str]] = Field(default=None, description="Roles que fazem bypass")
    enabled: bool = Field(default=True, description="Política ativa")
    policy_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadados da política")


class RateLimitPoliciesCreate(RateLimitPoliciesBase):
    """Schema for creating rate limit policies."""
    pass


class RateLimitPoliciesUpdate(BaseModel):
    """Schema for updating rate limit policies."""
    model_config = ConfigDict(from_attributes=True)
    
    policy_name: Optional[str] = None
    endpoint_pattern: Optional[str] = None
    requests_per_minute: Optional[int] = None
    requests_per_hour: Optional[int] = None
    requests_per_day: Optional[int] = None
    applies_to_users: Optional[bool] = None
    applies_to_ips: Optional[bool] = None
    applies_to_companies: Optional[bool] = None
    bypass_roles: Optional[List[str]] = None
    enabled: Optional[bool] = None
    policy_metadata: Optional[Dict[str, Any]] = None


class RateLimitPoliciesResponse(RateLimitPoliciesBase):
    """Schema for rate limit policies responses."""
    id: UUID
    created_at: datetime
    updated_at: datetime


# Analytics and Aggregation schemas
class MetricsAggregationRequest(BaseModel):
    """Schema for metrics aggregation request."""
    model_config = ConfigDict(from_attributes=True)
    
    metric_type: MetricType = Field(..., description="Tipo da métrica")
    start_date: datetime = Field(..., description="Data inicial")
    end_date: datetime = Field(..., description="Data final")
    interval: str = Field(default="1h", description="Intervalo de agregação")
    group_by: Optional[List[str]] = Field(default=None, description="Campos para agrupar")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Filtros")


class MetricsAggregationResponse(BaseModel):
    """Schema for metrics aggregation response."""
    model_config = ConfigDict(from_attributes=True)
    
    data_points: List[Dict[str, Any]] = Field(..., description="Pontos de dados")
    total_records: int = Field(..., description="Total de registros")
    start_date: datetime = Field(..., description="Data inicial")
    end_date: datetime = Field(..., description="Data final")
    interval: str = Field(..., description="Intervalo usado")


class HealthCheckSummaryResponse(BaseModel):
    """Schema for health check summary."""
    model_config = ConfigDict(from_attributes=True)
    
    overall_status: HealthStatus = Field(..., description="Status geral")
    services: List[ServiceHealthResponse] = Field(..., description="Status dos serviços")
    last_updated: datetime = Field(..., description="Última atualização")
    total_services: int = Field(..., description="Total de serviços")
    healthy_services: int = Field(..., description="Serviços saudáveis")
    unhealthy_services: int = Field(..., description="Serviços não saudáveis")


class PerformanceReportRequest(BaseModel):
    """Schema for performance report request."""
    model_config = ConfigDict(from_attributes=True)
    
    start_date: datetime = Field(..., description="Data inicial")
    end_date: datetime = Field(..., description="Data final")
    endpoints: Optional[List[str]] = Field(default=None, description="Filtro por endpoints")
    company_id: Optional[UUID] = Field(default=None, description="Filtro por empresa")
    include_errors: bool = Field(default=True, description="Incluir erros")


class PerformanceReportResponse(BaseModel):
    """Schema for performance report response."""
    model_config = ConfigDict(from_attributes=True)
    
    total_requests: int = Field(..., description="Total de requisições")
    average_response_time: float = Field(..., description="Tempo médio de resposta")
    error_rate: float = Field(..., description="Taxa de erro")
    slowest_endpoints: List[Dict[str, Any]] = Field(..., description="Endpoints mais lentos")
    most_used_endpoints: List[Dict[str, Any]] = Field(..., description="Endpoints mais usados")
    error_breakdown: Dict[str, int] = Field(..., description="Breakdown de erros")
    timeline_data: List[Dict[str, Any]] = Field(..., description="Dados da timeline")
