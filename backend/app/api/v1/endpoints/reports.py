"""
API endpoints para domínio de Relatórios e Analytics
"""

from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.domains.auth.models import User
from app.domains.reports.service import (
    ReportService, ReportScheduleService, ReportShareService,
    DashboardService, KPIService, DataExportService
)
from app.domains.reports.repository import (
    ReportRepository, ReportExecutionRepository, ReportScheduleRepository,
    ReportShareRepository, DashboardRepository, DashboardWidgetRepository,
    KPIRepository, KPIHistoryRepository, DataExportRepository
)
from app.domains.reports.schemas import (
    ReportResponse, ReportCreate, ReportUpdate, ReportExecuteRequest,
    ReportExecutionResponse, ReportAnalyticsResponse,
    ReportScheduleResponse, ReportScheduleCreate, ReportScheduleUpdate,
    ReportShareResponse, ReportShareCreate, ReportShareUpdate,
    DashboardResponse, DashboardCreate, DashboardUpdate, DashboardCopyRequest,
    DashboardWithWidgetsResponse, DashboardAnalyticsResponse,
    DashboardWidgetResponse, DashboardWidgetCreate, DashboardWidgetUpdate,
    KPIResponse, KPICreate, KPIUpdate, KPICalculateRequest,
    KPIHistoryResponse, KPIWithHistoryResponse,
    DataExportResponse, DataExportCreate,
    ReportCopyRequest
)

router = APIRouter()


# Reports endpoints
@router.post("/reports", response_model=ReportResponse)
async def create_report(
    report_data: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cria novo relatório"""
    service = ReportService(db)
    return await service.create_report(
        current_user.company_id,
        current_user.id,
        report_data
    )


@router.get("/reports", response_model=List[ReportResponse])
async def list_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    report_type: Optional[str] = Query(None),
    data_source: Optional[str] = Query(None),
    is_public: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lista relatórios da empresa"""
    repository = ReportRepository(db)
    
    if search:
        return await repository.search_reports(
            current_user.company_id,
            search,
            skip,
            limit
        )
    
    return await repository.get_by_company(
        current_user.company_id,
        skip,
        limit,
        status,
        report_type,
        data_source,
        is_public
    )


@router.get("/reports/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: UUID = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Obtém relatório por ID"""
    repository = ReportRepository(db)
    report = await repository.get_by_id(report_id)
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Relatório não encontrado"
        )
    
    if report.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para acessar este relatório"
        )
    
    return report


@router.put("/reports/{report_id}", response_model=ReportResponse)
async def update_report(
    report_id: UUID = Path(...),
    update_data: ReportUpdate = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Atualiza relatório"""
    service = ReportService(db)
    return await service.update_report(
        report_id,
        current_user.id,
        current_user.company_id,
        update_data
    )


@router.delete("/reports/{report_id}")
async def delete_report(
    report_id: UUID = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove relatório"""
    service = ReportService(db)
    await service.delete_report(
        report_id,
        current_user.id,
        current_user.company_id
    )
    return {"message": "Relatório removido com sucesso"}


@router.post("/reports/{report_id}/execute")
async def execute_report(
    report_id: UUID = Path(...),
    execute_request: ReportExecuteRequest = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Executa relatório"""
    service = ReportService(db)
    result_data, execution_id = await service.execute_report(
        report_id,
        current_user.id,
        current_user.company_id,
        execute_request
    )
    
    return {
        "execution_id": execution_id,
        "data": result_data
    }


@router.post("/reports/{report_id}/copy", response_model=ReportResponse)
async def copy_report(
    report_id: UUID = Path(...),
    copy_request: ReportCopyRequest = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Copia relatório"""
    service = ReportService(db)
    return await service.copy_report(
        report_id,
        current_user.id,
        current_user.company_id,
        copy_request.new_name
    )


@router.get("/reports/{report_id}/executions", response_model=List[ReportExecutionResponse])
async def get_report_executions(
    report_id: UUID = Path(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lista execuções do relatório"""
    # Verificar se relatório pertence à empresa
    report_repo = ReportRepository(db)
    report = await report_repo.get_by_id(report_id)
    
    if not report or report.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Relatório não encontrado"
        )
    
    execution_repo = ReportExecutionRepository(db)
    return await execution_repo.get_by_report(report_id, skip, limit)


# Report Analytics
@router.get("/reports/analytics", response_model=ReportAnalyticsResponse)
async def get_report_analytics(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Obtém analytics de relatórios"""
    service = ReportService(db)
    return await service.get_report_analytics(current_user.company_id, days)


# Report Schedules
@router.post("/schedules", response_model=ReportScheduleResponse)
async def create_schedule(
    schedule_data: ReportScheduleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cria agendamento de relatório"""
    service = ReportScheduleService(db)
    return await service.create_schedule(
        current_user.id,
        current_user.company_id,
        schedule_data
    )


@router.get("/schedules", response_model=List[ReportScheduleResponse])
async def list_schedules(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lista agendamentos da empresa"""
    repository = ReportScheduleRepository(db)
    return await repository.get_by_company(
        current_user.company_id,
        skip,
        limit,
        is_active
    )


@router.put("/schedules/{schedule_id}", response_model=ReportScheduleResponse)
async def update_schedule(
    schedule_id: UUID = Path(...),
    update_data: ReportScheduleUpdate = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Atualiza agendamento"""
    service = ReportScheduleService(db)
    return await service.update_schedule(
        schedule_id,
        current_user.id,
        current_user.company_id,
        update_data
    )


# Report Shares
@router.post("/shares", response_model=ReportShareResponse)
async def create_share(
    share_data: ReportShareCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cria compartilhamento de relatório"""
    service = ReportShareService(db)
    return await service.create_share(
        current_user.id,
        current_user.company_id,
        share_data
    )


@router.get("/shares/token/{share_token}")
async def access_shared_report(
    share_token: str = Path(...),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Acessa relatório compartilhado via token"""
    service = ReportShareService(db)
    share, report = await service.access_shared_report(
        share_token,
        current_user.id if current_user else None
    )
    
    return {
        "report": report,
        "share_permissions": {
            "can_view": share.can_view,
            "can_export": share.can_export,
            "can_edit": share.can_edit,
            "can_share": share.can_share
        }
    }


@router.get("/reports/{report_id}/shares", response_model=List[ReportShareResponse])
async def get_report_shares(
    report_id: UUID = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lista compartilhamentos do relatório"""
    # Verificar permissão
    report_repo = ReportRepository(db)
    report = await report_repo.get_by_id(report_id)
    
    if not report or report.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Relatório não encontrado"
        )
    
    repository = ReportShareRepository(db)
    return await repository.get_by_report(report_id)


# Dashboards
@router.post("/dashboards", response_model=DashboardResponse)
async def create_dashboard(
    dashboard_data: DashboardCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cria dashboard"""
    service = DashboardService(db)
    return await service.create_dashboard(
        current_user.company_id,
        current_user.id,
        dashboard_data
    )


@router.get("/dashboards", response_model=List[DashboardResponse])
async def list_dashboards(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_public: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lista dashboards da empresa"""
    repository = DashboardRepository(db)
    return await repository.get_by_company(
        current_user.company_id,
        skip,
        limit,
        is_public
    )


@router.get("/dashboards/{dashboard_id}", response_model=DashboardWithWidgetsResponse)
async def get_dashboard(
    dashboard_id: UUID = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Obtém dashboard com widgets"""
    repository = DashboardRepository(db)
    dashboard = await repository.get_with_widgets(dashboard_id)
    
    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard não encontrado"
        )
    
    if dashboard.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para acessar este dashboard"
        )
    
    return dashboard


@router.put("/dashboards/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(
    dashboard_id: UUID = Path(...),
    update_data: DashboardUpdate = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Atualiza dashboard"""
    repository = DashboardRepository(db)
    dashboard = await repository.get_by_id(dashboard_id)
    
    if not dashboard or dashboard.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard não encontrado"
        )
    
    update_dict = update_data.model_dump(exclude_unset=True)
    return await repository.update(dashboard_id, update_dict)


@router.post("/dashboards/{dashboard_id}/copy", response_model=DashboardResponse)
async def copy_dashboard(
    dashboard_id: UUID = Path(...),
    copy_request: DashboardCopyRequest = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Copia dashboard"""
    service = DashboardService(db)
    return await service.copy_dashboard(
        dashboard_id,
        current_user.id,
        current_user.company_id,
        copy_request
    )


@router.post("/dashboards/{dashboard_id}/set-default")
async def set_default_dashboard(
    dashboard_id: UUID = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Define dashboard como padrão"""
    service = DashboardService(db)
    await service.set_default_dashboard(
        dashboard_id,
        current_user.id,
        current_user.company_id
    )
    return {"message": "Dashboard definido como padrão"}


# Dashboard Widgets
@router.post("/dashboards/{dashboard_id}/widgets", response_model=DashboardWidgetResponse)
async def create_widget(
    dashboard_id: UUID = Path(...),
    widget_data: DashboardWidgetCreate = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cria widget no dashboard"""
    # Verificar se dashboard pertence à empresa
    dashboard_repo = DashboardRepository(db)
    dashboard = await dashboard_repo.get_by_id(dashboard_id)
    
    if not dashboard or dashboard.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard não encontrado"
        )
    
    widget_data.dashboard_id = dashboard_id
    
    widget_repo = DashboardWidgetRepository(db)
    widget = DashboardWidget(**widget_data.model_dump())
    return await widget_repo.create(widget)


@router.get("/dashboards/{dashboard_id}/widgets", response_model=List[DashboardWidgetResponse])
async def get_dashboard_widgets(
    dashboard_id: UUID = Path(...),
    visible_only: bool = Query(True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lista widgets do dashboard"""
    # Verificar permissão
    dashboard_repo = DashboardRepository(db)
    dashboard = await dashboard_repo.get_by_id(dashboard_id)
    
    if not dashboard or dashboard.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard não encontrado"
        )
    
    widget_repo = DashboardWidgetRepository(db)
    return await widget_repo.get_by_dashboard(dashboard_id, visible_only)


@router.put("/widgets/{widget_id}", response_model=DashboardWidgetResponse)
async def update_widget(
    widget_id: UUID = Path(...),
    update_data: DashboardWidgetUpdate = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Atualiza widget"""
    widget_repo = DashboardWidgetRepository(db)
    widget = await widget_repo.get_by_id(widget_id)
    
    if not widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Widget não encontrado"
        )
    
    # Verificar permissão através do dashboard
    dashboard_repo = DashboardRepository(db)
    dashboard = await dashboard_repo.get_by_id(widget.dashboard_id)
    
    if not dashboard or dashboard.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para atualizar este widget"
        )
    
    update_dict = update_data.model_dump(exclude_unset=True)
    return await widget_repo.update(widget_id, update_dict)


# KPIs
@router.post("/kpis", response_model=KPIResponse)
async def create_kpi(
    kpi_data: KPICreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cria KPI"""
    service = KPIService(db)
    return await service.create_kpi(
        current_user.company_id,
        current_user.id,
        kpi_data
    )


@router.get("/kpis", response_model=List[KPIResponse])
async def list_kpis(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lista KPIs da empresa"""
    repository = KPIRepository(db)
    return await repository.get_by_company(
        current_user.company_id,
        skip,
        limit,
        is_active
    )


@router.get("/kpis/{kpi_id}", response_model=KPIWithHistoryResponse)
async def get_kpi(
    kpi_id: UUID = Path(...),
    include_history: bool = Query(True),
    history_days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Obtém KPI com histórico"""
    kpi_repo = KPIRepository(db)
    kpi = await kpi_repo.get_by_id(kpi_id)
    
    if not kpi or kpi.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="KPI não encontrado"
        )
    
    result = KPIWithHistoryResponse.model_validate(kpi)
    
    if include_history:
        history_repo = KPIHistoryRepository(db)
        history = await history_repo.get_by_kpi(kpi_id, history_days)
        trend_data = await history_repo.get_trend_data(kpi_id, history_days)
        
        result.recent_history = history
        result.trend_direction = trend_data.get("trend_direction")
        result.trend_percentage = trend_data.get("trend_percentage")
    
    return result


@router.post("/kpis/{kpi_id}/calculate")
async def calculate_kpi(
    kpi_id: UUID = Path(...),
    calculate_request: KPICalculateRequest = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Calcula valor do KPI"""
    service = KPIService(db)
    return await service.calculate_kpi(
        kpi_id,
        current_user.id,
        current_user.company_id,
        calculate_request
    )


@router.put("/kpis/{kpi_id}", response_model=KPIResponse)
async def update_kpi(
    kpi_id: UUID = Path(...),
    update_data: KPIUpdate = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Atualiza KPI"""
    repository = KPIRepository(db)
    kpi = await repository.get_by_id(kpi_id)
    
    if not kpi or kpi.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="KPI não encontrado"
        )
    
    update_dict = update_data.model_dump(exclude_unset=True)
    return await repository.update(kpi_id, update_dict)


# Data Exports
@router.post("/exports", response_model=DataExportResponse)
async def create_export(
    export_data: DataExportCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cria exportação de dados"""
    service = DataExportService(db)
    return await service.create_export(
        current_user.company_id,
        current_user.id,
        export_data
    )


@router.get("/exports", response_model=List[DataExportResponse])
async def list_exports(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lista exportações do usuário"""
    repository = DataExportRepository(db)
    return await repository.get_user_exports(
        current_user.id,
        skip,
        limit
    )


@router.get("/exports/{export_id}", response_model=DataExportResponse)
async def get_export(
    export_id: UUID = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Obtém status da exportação"""
    repository = DataExportRepository(db)
    export = await repository.get_by_id(export_id)
    
    if not export:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exportação não encontrada"
        )
    
    if export.requested_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para acessar esta exportação"
        )
    
    return export


# Public endpoints (sem autenticação)
@router.get("/public/reports", response_model=List[ReportResponse])
async def list_public_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """Lista relatórios públicos"""
    repository = ReportRepository(db)
    return await repository.get_public_reports(skip, limit)


@router.get("/dashboards/analytics", response_model=DashboardAnalyticsResponse)
async def get_dashboard_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Obtém analytics de dashboards"""
    # Implementar analytics de dashboards
    return DashboardAnalyticsResponse(
        total_dashboards=0,
        public_dashboards=0,
        private_dashboards=0,
        total_widgets=0,
        avg_widgets_per_dashboard=0.0,
        popular_dashboards=[]
    )
