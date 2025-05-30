"""
Schemas para domínio de Relatórios e Analytics
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.domains.reports.models import (
    ReportType, ReportFormat, ChartType, ScheduleFrequency, 
    ReportStatus
)


# Base schemas
class ReportBase(BaseModel):
    """Schema base para relatórios"""
    model_config = ConfigDict(from_attributes=True)
    
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    report_type: ReportType = ReportType.TABLE
    data_source: str = Field(..., min_length=1, max_length=100)
    query_config: Dict[str, Any] = Field(default_factory=dict)
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    aggregations: Optional[Dict[str, Any]] = Field(default_factory=dict)
    chart_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    layout_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    status: ReportStatus = ReportStatus.DRAFT
    is_public: bool = False
    is_embedded: bool = False
    cache_duration_minutes: int = Field(default=60, ge=1, le=1440)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ReportCreate(ReportBase):
    """Schema para criação de relatório"""
    pass


class ReportUpdate(BaseModel):
    """Schema para atualização de relatório"""
    model_config = ConfigDict(from_attributes=True)
    
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    report_type: Optional[ReportType] = None
    data_source: Optional[str] = Field(None, min_length=1, max_length=100)
    query_config: Optional[Dict[str, Any]] = None
    filters: Optional[Dict[str, Any]] = None
    aggregations: Optional[Dict[str, Any]] = None
    chart_config: Optional[Dict[str, Any]] = None
    layout_config: Optional[Dict[str, Any]] = None
    status: Optional[ReportStatus] = None
    is_public: Optional[bool] = None
    is_embedded: Optional[bool] = None
    cache_duration_minutes: Optional[int] = Field(None, ge=1, le=1440)
    metadata: Optional[Dict[str, Any]] = None


class ReportResponse(ReportBase):
    """Schema de resposta para relatório"""
    id: UUID
    company_id: UUID
    created_by: UUID
    last_cached_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# Report Execution schemas
class ReportExecutionBase(BaseModel):
    """Schema base para execução de relatório"""
    model_config = ConfigDict(from_attributes=True)
    
    filters_used: Optional[Dict[str, Any]] = Field(default_factory=dict)
    parameters_used: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ReportExecutionCreate(ReportExecutionBase):
    """Schema para criação de execução"""
    report_id: UUID


class ReportExecutionResponse(ReportExecutionBase):
    """Schema de resposta para execução"""
    id: UUID
    report_id: UUID
    executed_by: UUID
    execution_start: datetime
    execution_end: Optional[datetime] = None
    duration_ms: Optional[int] = None
    status: str
    error_message: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None
    row_count: Optional[int] = None
    created_at: datetime


# Report Schedule schemas
class ReportScheduleBase(BaseModel):
    """Schema base para agendamento"""
    model_config = ConfigDict(from_attributes=True)
    
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    frequency: ScheduleFrequency
    cron_expression: Optional[str] = Field(None, max_length=100)
    delivery_method: str = Field(default="email", max_length=50)
    delivery_config: Dict[str, Any] = Field(default_factory=dict)
    output_format: ReportFormat = ReportFormat.PDF
    is_active: bool = True
    timezone: str = Field(default="UTC", max_length=50)
    max_executions: Optional[int] = Field(None, ge=1)


class ReportScheduleCreate(ReportScheduleBase):
    """Schema para criação de agendamento"""
    report_id: UUID


class ReportScheduleUpdate(BaseModel):
    """Schema para atualização de agendamento"""
    model_config = ConfigDict(from_attributes=True)
    
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    frequency: Optional[ScheduleFrequency] = None
    cron_expression: Optional[str] = Field(None, max_length=100)
    delivery_method: Optional[str] = Field(None, max_length=50)
    delivery_config: Optional[Dict[str, Any]] = None
    output_format: Optional[ReportFormat] = None
    is_active: Optional[bool] = None
    timezone: Optional[str] = Field(None, max_length=50)
    max_executions: Optional[int] = Field(None, ge=1)


class ReportScheduleResponse(ReportScheduleBase):
    """Schema de resposta para agendamento"""
    id: UUID
    report_id: UUID
    created_by: UUID
    next_execution: Optional[datetime] = None
    last_execution: Optional[datetime] = None
    execution_count: int
    created_at: datetime
    updated_at: datetime


# Report Share schemas
class ReportShareBase(BaseModel):
    """Schema base para compartilhamento"""
    model_config = ConfigDict(from_attributes=True)
    
    shared_with_user_id: Optional[UUID] = None
    can_view: bool = True
    can_export: bool = False
    can_edit: bool = False
    can_share: bool = False
    expires_at: Optional[datetime] = None
    max_access_count: Optional[int] = Field(None, ge=1)


class ReportShareCreate(ReportShareBase):
    """Schema para criação de compartilhamento"""
    report_id: UUID


class ReportShareUpdate(BaseModel):
    """Schema para atualização de compartilhamento"""
    model_config = ConfigDict(from_attributes=True)
    
    can_view: Optional[bool] = None
    can_export: Optional[bool] = None
    can_edit: Optional[bool] = None
    can_share: Optional[bool] = None
    expires_at: Optional[datetime] = None
    max_access_count: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None


class ReportShareResponse(ReportShareBase):
    """Schema de resposta para compartilhamento"""
    id: UUID
    report_id: UUID
    shared_by_user_id: UUID
    share_token: Optional[str] = None
    access_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


# Dashboard schemas
class DashboardBase(BaseModel):
    """Schema base para dashboard"""
    model_config = ConfigDict(from_attributes=True)
    
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    layout_config: Dict[str, Any] = Field(default_factory=dict)
    theme: str = Field(default="default", max_length=50)
    background_color: Optional[str] = Field(None, max_length=7)
    is_public: bool = False
    is_default: bool = False
    auto_refresh_minutes: Optional[int] = Field(None, ge=1, le=1440)


class DashboardCreate(DashboardBase):
    """Schema para criação de dashboard"""
    pass


class DashboardUpdate(BaseModel):
    """Schema para atualização de dashboard"""
    model_config = ConfigDict(from_attributes=True)
    
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    layout_config: Optional[Dict[str, Any]] = None
    theme: Optional[str] = Field(None, max_length=50)
    background_color: Optional[str] = Field(None, max_length=7)
    is_public: Optional[bool] = None
    is_default: Optional[bool] = None
    auto_refresh_minutes: Optional[int] = Field(None, ge=1, le=1440)


class DashboardResponse(DashboardBase):
    """Schema de resposta para dashboard"""
    id: UUID
    company_id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: datetime


# Dashboard Widget schemas
class DashboardWidgetBase(BaseModel):
    """Schema base para widget"""
    model_config = ConfigDict(from_attributes=True)
    
    title: str = Field(..., min_length=1, max_length=200)
    widget_type: str = Field(..., max_length=50)
    position_x: int = Field(default=0, ge=0)
    position_y: int = Field(default=0, ge=0)
    width: int = Field(default=6, ge=1, le=12)
    height: int = Field(default=4, ge=1, le=12)
    widget_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    background_color: Optional[str] = Field(None, max_length=7)
    border_color: Optional[str] = Field(None, max_length=7)
    is_visible: bool = True


class DashboardWidgetCreate(DashboardWidgetBase):
    """Schema para criação de widget"""
    dashboard_id: UUID
    report_id: Optional[UUID] = None


class DashboardWidgetUpdate(BaseModel):
    """Schema para atualização de widget"""
    model_config = ConfigDict(from_attributes=True)
    
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    widget_type: Optional[str] = Field(None, max_length=50)
    position_x: Optional[int] = Field(None, ge=0)
    position_y: Optional[int] = Field(None, ge=0)
    width: Optional[int] = Field(None, ge=1, le=12)
    height: Optional[int] = Field(None, ge=1, le=12)
    widget_config: Optional[Dict[str, Any]] = None
    background_color: Optional[str] = Field(None, max_length=7)
    border_color: Optional[str] = Field(None, max_length=7)
    is_visible: Optional[bool] = None
    report_id: Optional[UUID] = None


class DashboardWidgetResponse(DashboardWidgetBase):
    """Schema de resposta para widget"""
    id: UUID
    dashboard_id: UUID
    report_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime


# KPI schemas
class KPIBase(BaseModel):
    """Schema base para KPI"""
    model_config = ConfigDict(from_attributes=True)
    
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    data_source: str = Field(..., min_length=1, max_length=100)
    calculation_method: str = Field(..., max_length=50)
    calculation_config: Dict[str, Any] = Field(default_factory=dict)
    target_value: Optional[float] = None
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    value_format: str = Field(default="number", max_length=50)
    decimal_places: int = Field(default=2, ge=0, le=10)
    update_frequency_minutes: int = Field(default=60, ge=1, le=1440)
    is_active: bool = True


class KPICreate(KPIBase):
    """Schema para criação de KPI"""
    pass


class KPIUpdate(BaseModel):
    """Schema para atualização de KPI"""
    model_config = ConfigDict(from_attributes=True)
    
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    data_source: Optional[str] = Field(None, min_length=1, max_length=100)
    calculation_method: Optional[str] = Field(None, max_length=50)
    calculation_config: Optional[Dict[str, Any]] = None
    target_value: Optional[float] = None
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    value_format: Optional[str] = Field(None, max_length=50)
    decimal_places: Optional[int] = Field(None, ge=0, le=10)
    update_frequency_minutes: Optional[int] = Field(None, ge=1, le=1440)
    is_active: Optional[bool] = None


class KPIResponse(KPIBase):
    """Schema de resposta para KPI"""
    id: UUID
    company_id: UUID
    created_by: UUID
    last_calculated_at: Optional[datetime] = None
    current_value: Optional[float] = None
    previous_value: Optional[float] = None
    created_at: datetime
    updated_at: datetime


class KPIHistoryResponse(BaseModel):
    """Schema de resposta para histórico de KPI"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    kpi_id: UUID
    value: float
    calculated_at: datetime
    calculation_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime


# Data Export schemas
class DataExportBase(BaseModel):
    """Schema base para exportação"""
    model_config = ConfigDict(from_attributes=True)
    
    data_source: str = Field(..., min_length=1, max_length=100)
    export_format: ReportFormat
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    columns: Optional[List[str]] = None


class DataExportCreate(DataExportBase):
    """Schema para criação de exportação"""
    pass


class DataExportResponse(DataExportBase):
    """Schema de resposta para exportação"""
    id: UUID
    company_id: UUID
    requested_by: UUID
    status: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    total_rows: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# Analytics schemas
class ReportAnalyticsResponse(BaseModel):
    """Schema para analytics de relatórios"""
    model_config = ConfigDict(from_attributes=True)
    
    total_reports: int
    active_reports: int
    draft_reports: int
    archived_reports: int
    total_executions: int
    avg_execution_time_ms: Optional[float] = None
    most_used_reports: List[Dict[str, Any]]
    execution_trends: List[Dict[str, Any]]


class DashboardAnalyticsResponse(BaseModel):
    """Schema para analytics de dashboards"""
    model_config = ConfigDict(from_attributes=True)
    
    total_dashboards: int
    public_dashboards: int
    private_dashboards: int
    total_widgets: int
    avg_widgets_per_dashboard: Optional[float] = None
    popular_dashboards: List[Dict[str, Any]]


# Request schemas para operações especiais
class ReportExecuteRequest(BaseModel):
    """Schema para executar relatório"""
    model_config = ConfigDict(from_attributes=True)
    
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    cache_override: bool = False


class ReportCopyRequest(BaseModel):
    """Schema para copiar relatório"""
    model_config = ConfigDict(from_attributes=True)
    
    new_name: str = Field(..., min_length=1, max_length=200)
    copy_schedules: bool = False
    copy_shares: bool = False


class DashboardCopyRequest(BaseModel):
    """Schema para copiar dashboard"""
    model_config = ConfigDict(from_attributes=True)
    
    new_name: str = Field(..., min_length=1, max_length=200)
    copy_widgets: bool = True


class KPICalculateRequest(BaseModel):
    """Schema para calcular KPI"""
    model_config = ConfigDict(from_attributes=True)
    
    force_recalculate: bool = False
    save_to_history: bool = True


# Response para dados agregados
class DashboardWithWidgetsResponse(DashboardResponse):
    """Dashboard com widgets incluídos"""
    widgets: List[DashboardWidgetResponse] = Field(default_factory=list)


class ReportWithExecutionsResponse(ReportResponse):
    """Relatório com execuções incluídas"""
    recent_executions: List[ReportExecutionResponse] = Field(default_factory=list)
    execution_count: int = 0


class KPIWithHistoryResponse(KPIResponse):
    """KPI com histórico incluído"""
    recent_history: List[KPIHistoryResponse] = Field(default_factory=list)
    trend_direction: Optional[str] = None  # up, down, stable
    trend_percentage: Optional[float] = None
