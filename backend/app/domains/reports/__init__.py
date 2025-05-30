"""
Domínio de Relatórios e Analytics

Este domínio fornece funcionalidades completas para:
- Criação e execução de relatórios
- Dashboards interativos com widgets
- KPIs e métricas de negócio
- Agendamento de relatórios
- Compartilhamento de relatórios
- Exportação de dados
- Analytics e insights
"""

from app.domains.reports.models import (
    Report,
    ReportExecution,
    ReportSchedule,
    ReportShare,
    Dashboard,
    DashboardWidget,
    KPI,
    KPIHistory,
    DataExport,
    ReportType,
    ReportFormat,
    ChartType,
    ScheduleFrequency,
    ReportStatus
)

from app.domains.reports.schemas import (
    ReportResponse,
    ReportCreate,
    ReportUpdate,
    ReportExecuteRequest,
    ReportExecutionResponse,
    ReportAnalyticsResponse,
    ReportScheduleResponse,
    ReportScheduleCreate,
    ReportScheduleUpdate,
    ReportShareResponse,
    ReportShareCreate,
    ReportShareUpdate,
    DashboardResponse,
    DashboardCreate,
    DashboardUpdate,
    DashboardWithWidgetsResponse,
    DashboardAnalyticsResponse,
    DashboardWidgetResponse,
    DashboardWidgetCreate,
    DashboardWidgetUpdate,
    KPIResponse,
    KPICreate,
    KPIUpdate,
    KPIHistoryResponse,
    KPIWithHistoryResponse,
    DataExportResponse,
    DataExportCreate
)

from app.domains.reports.repository import (
    ReportRepository,
    ReportExecutionRepository,
    ReportScheduleRepository,
    ReportShareRepository,
    DashboardRepository,
    DashboardWidgetRepository,
    KPIRepository,
    KPIHistoryRepository,
    DataExportRepository
)

from app.domains.reports.service import (
    ReportService,
    ReportScheduleService,
    ReportShareService,
    DashboardService,
    KPIService,
    DataExportService
)

__all__ = [
    # Models
    "Report",
    "ReportExecution", 
    "ReportSchedule",
    "ReportShare",
    "Dashboard",
    "DashboardWidget",
    "KPI",
    "KPIHistory",
    "DataExport",
    "ReportType",
    "ReportFormat",
    "ChartType",
    "ScheduleFrequency",
    "ReportStatus",
    
    # Schemas
    "ReportResponse",
    "ReportCreate",
    "ReportUpdate",
    "ReportExecuteRequest",
    "ReportExecutionResponse",
    "ReportAnalyticsResponse",
    "ReportScheduleResponse",
    "ReportScheduleCreate",
    "ReportScheduleUpdate",
    "ReportShareResponse",
    "ReportShareCreate",
    "ReportShareUpdate",
    "DashboardResponse",
    "DashboardCreate",
    "DashboardUpdate",
    "DashboardWithWidgetsResponse",
    "DashboardAnalyticsResponse",
    "DashboardWidgetResponse",
    "DashboardWidgetCreate",
    "DashboardWidgetUpdate",
    "KPIResponse",
    "KPICreate",
    "KPIUpdate",
    "KPIHistoryResponse",
    "KPIWithHistoryResponse",
    "DataExportResponse",
    "DataExportCreate",
    
    # Repositories
    "ReportRepository",
    "ReportExecutionRepository",
    "ReportScheduleRepository",
    "ReportShareRepository",
    "DashboardRepository",
    "DashboardWidgetRepository",
    "KPIRepository",
    "KPIHistoryRepository",
    "DataExportRepository",
    
    # Services
    "ReportService",
    "ReportScheduleService",
    "ReportShareService",
    "DashboardService",
    "KPIService",
    "DataExportService"
]
