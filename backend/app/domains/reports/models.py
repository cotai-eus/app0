"""
Modelos de Relatórios e Analytics
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import Text, String, Boolean, Integer, JSON, ForeignKey, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID

from app.shared.common.base_models import BaseModel, TimestampMixin


class ReportType(str, Enum):
    """Tipo de relatório"""
    DASHBOARD = "dashboard"
    TABLE = "table"
    CHART = "chart"
    KPI = "kpi"
    FORM_ANALYTICS = "form_analytics"
    TASK_ANALYTICS = "task_analytics"
    FINANCIAL = "financial"
    TENDER_ANALYTICS = "tender_analytics"
    CUSTOM = "custom"


class ReportFormat(str, Enum):
    """Formato do relatório"""
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"
    HTML = "html"


class ChartType(str, Enum):
    """Tipo de gráfico"""
    LINE = "line"
    BAR = "bar"
    COLUMN = "column"
    PIE = "pie"
    DOUGHNUT = "doughnut"
    AREA = "area"
    SCATTER = "scatter"
    GAUGE = "gauge"
    FUNNEL = "funnel"
    HEATMAP = "heatmap"


class ScheduleFrequency(str, Enum):
    """Frequência de agendamento"""
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class ReportStatus(str, Enum):
    """Status do relatório"""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    ERROR = "error"


class Report(BaseModel, TimestampMixin):
    """Relatório"""
    
    __tablename__ = "reports"
    
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relacionamentos
    company_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        nullable=False
    )
    created_by: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        nullable=False
    )
    
    # Configuração do relatório
    report_type: Mapped[ReportType] = mapped_column(default=ReportType.TABLE)
    data_source: Mapped[str] = mapped_column(String(100), nullable=False)  # forms, tasks, tenders, etc.
    
    # Configuração de dados
    query_config: Mapped[dict] = mapped_column(JSON, nullable=False)  # Configuração da consulta
    filters: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    aggregations: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    
    # Configuração visual
    chart_config: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    layout_config: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    
    # Status e permissões
    status: Mapped[ReportStatus] = mapped_column(default=ReportStatus.DRAFT)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    is_embedded: Mapped[bool] = mapped_column(Boolean, default=False)
      # Cache e performance
    cache_duration_minutes: Mapped[int] = mapped_column(Integer, default=60)
    last_cached_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Metadados
    report_metadata: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    
    # Relacionamentos
    executions = relationship("ReportExecution", back_populates="report", cascade="all, delete-orphan")
    schedules = relationship("ReportSchedule", back_populates="report", cascade="all, delete-orphan")
    shares = relationship("ReportShare", back_populates="report", cascade="all, delete-orphan")


class ReportExecution(BaseModel, TimestampMixin):
    """Execução de relatório"""
    
    __tablename__ = "report_executions"
    
    report_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("reports.id"),
        nullable=False
    )
    executed_by: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        nullable=False
    )
    
    # Dados da execução
    execution_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    execution_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Status e resultado
    status: Mapped[str] = mapped_column(String(50), default="running")  # running, completed, failed
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Dados do resultado
    result_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    row_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Configurações usadas na execução
    filters_used: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    parameters_used: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    
    # Relacionamentos
    report = relationship("Report", back_populates="executions")


class ReportSchedule(BaseModel, TimestampMixin):
    """Agendamento de relatórios"""
    
    __tablename__ = "report_schedules"
    
    report_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("reports.id"),
        nullable=False
    )
    created_by: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        nullable=False
    )
    
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Configuração de agendamento
    frequency: Mapped[ScheduleFrequency] = mapped_column(nullable=False)
    cron_expression: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Configuração de entrega
    delivery_method: Mapped[str] = mapped_column(String(50), default="email")  # email, webhook, storage
    delivery_config: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # Formato de saída
    output_format: Mapped[ReportFormat] = mapped_column(default=ReportFormat.PDF)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    next_execution: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_execution: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    execution_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Configurações especiais
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    max_executions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Relacionamentos
    report = relationship("Report", back_populates="schedules")


class ReportShare(BaseModel, TimestampMixin):
    """Compartilhamento de relatórios"""
    
    __tablename__ = "report_shares"
    
    report_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("reports.id"),
        nullable=False
    )
    shared_with_user_id: Mapped[Optional[UUID]] = mapped_column(
        PostgresUUID(as_uuid=True),
        nullable=True  # Pode ser compartilhamento público
    )
    shared_by_user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        nullable=False
    )
    
    # Token para acesso público
    share_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True)
    
    # Permissões
    can_view: Mapped[bool] = mapped_column(Boolean, default=True)
    can_export: Mapped[bool] = mapped_column(Boolean, default=False)
    can_edit: Mapped[bool] = mapped_column(Boolean, default=False)
    can_share: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Configurações de acesso
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    access_count: Mapped[int] = mapped_column(Integer, default=0)
    max_access_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relacionamentos
    report = relationship("Report", back_populates="shares")


class Dashboard(BaseModel, TimestampMixin):
    """Dashboard com múltiplos relatórios"""
    
    __tablename__ = "dashboards"
    
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relacionamentos
    company_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        nullable=False
    )
    created_by: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        nullable=False
    )
    
    # Configuração do layout
    layout_config: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # Configurações visuais
    theme: Mapped[str] = mapped_column(String(50), default="default")
    background_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    
    # Status e permissões
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Configurações de atualização
    auto_refresh_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Relacionamentos
    widgets = relationship("DashboardWidget", back_populates="dashboard", cascade="all, delete-orphan")


class DashboardWidget(BaseModel, TimestampMixin):
    """Widget do dashboard"""
    
    __tablename__ = "dashboard_widgets"
    
    dashboard_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("dashboards.id"),
        nullable=False
    )
    report_id: Mapped[Optional[UUID]] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("reports.id"),
        nullable=True  # Pode ser widget customizado
    )
    
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    widget_type: Mapped[str] = mapped_column(String(50), nullable=False)  # report, metric, text, image
    
    # Posicionamento no grid
    position_x: Mapped[int] = mapped_column(Integer, default=0)
    position_y: Mapped[int] = mapped_column(Integer, default=0)
    width: Mapped[int] = mapped_column(Integer, default=6)
    height: Mapped[int] = mapped_column(Integer, default=4)
    
    # Configurações do widget
    widget_config: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    
    # Configurações visuais
    background_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    border_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    
    # Status
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relacionamentos
    dashboard = relationship("Dashboard", back_populates="widgets")


class KPI(BaseModel, TimestampMixin):
    """Indicadores-chave de performance"""
    
    __tablename__ = "kpis"
    
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relacionamentos
    company_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        nullable=False
    )
    created_by: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        nullable=False
    )
    
    # Configuração do KPI
    data_source: Mapped[str] = mapped_column(String(100), nullable=False)
    calculation_method: Mapped[str] = mapped_column(String(50), nullable=False)  # sum, avg, count, etc.
    calculation_config: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # Metas e limites
    target_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    warning_threshold: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    critical_threshold: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Formatação
    value_format: Mapped[str] = mapped_column(String(50), default="number")  # number, percentage, currency
    decimal_places: Mapped[int] = mapped_column(Integer, default=2)
    
    # Configurações de atualização
    update_frequency_minutes: Mapped[int] = mapped_column(Integer, default=60)
    last_calculated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    current_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    previous_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relacionamentos
    history = relationship("KPIHistory", back_populates="kpi", cascade="all, delete-orphan")


class KPIHistory(BaseModel, TimestampMixin):
    """Histórico de valores do KPI"""
    
    __tablename__ = "kpi_history"
    
    kpi_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("kpis.id"),
        nullable=False
    )
    
    value: Mapped[float] = mapped_column(Float, nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Metadados da calculação
    calculation_metadata: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    
    # Relacionamentos
    kpi = relationship("KPI", back_populates="history")


class DataExport(BaseModel, TimestampMixin):
    """Exportação de dados"""
    
    __tablename__ = "data_exports"
    
    # Relacionamentos
    company_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        nullable=False
    )
    requested_by: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        nullable=False
    )
    
    # Configuração da exportação
    data_source: Mapped[str] = mapped_column(String(100), nullable=False)
    export_format: Mapped[ReportFormat] = mapped_column(nullable=False)
    
    # Filtros e configurações
    filters: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    columns: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Status da exportação
    status: Mapped[str] = mapped_column(String(50), default="queued")  # queued, processing, completed, failed
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Datas
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Estatísticas
    total_rows: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
