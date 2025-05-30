"""
Serviços para domínio de Relatórios e Analytics
"""

import json
import secrets
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.reports.models import (
    Report, ReportExecution, ReportSchedule, ReportShare,
    Dashboard, DashboardWidget, KPI, KPIHistory, DataExport,
    ReportStatus, ReportFormat
)
from app.domains.reports.repository import (
    ReportRepository, ReportExecutionRepository, ReportScheduleRepository,
    ReportShareRepository, DashboardRepository, DashboardWidgetRepository,
    KPIRepository, KPIHistoryRepository, DataExportRepository
)
from app.domains.reports.schemas import (
    ReportCreate, ReportUpdate, ReportExecuteRequest,
    ReportScheduleCreate, ReportScheduleUpdate,
    ReportShareCreate, ReportShareUpdate,
    DashboardCreate, DashboardUpdate, DashboardCopyRequest,
    DashboardWidgetCreate, DashboardWidgetUpdate,
    KPICreate, KPIUpdate, KPICalculateRequest,
    DataExportCreate
)
from app.shared.common.exceptions import BusinessException


class ReportService:
    """Serviço para relatórios"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = ReportRepository(session)
        self.execution_repository = ReportExecutionRepository(session)

    async def create_report(
        self,
        company_id: UUID,
        user_id: UUID,
        report_data: ReportCreate
    ) -> Report:
        """Cria novo relatório"""
        
        # Validar configuração da query
        await self._validate_query_config(report_data.query_config, report_data.data_source)
        
        report = Report(
            **report_data.model_dump(),
            company_id=company_id,
            created_by=user_id
        )
        
        return await self.repository.create(report)

    async def update_report(
        self,
        report_id: UUID,
        user_id: UUID,
        company_id: UUID,
        update_data: ReportUpdate
    ) -> Report:
        """Atualiza relatório"""
        report = await self.repository.get_by_id(report_id)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Relatório não encontrado"
            )
        
        if report.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para atualizar este relatório"
            )
        
        # Validar nova configuração se fornecida
        if update_data.query_config is not None:
            data_source = update_data.data_source or report.data_source
            await self._validate_query_config(update_data.query_config, data_source)
        
        update_dict = update_data.model_dump(exclude_unset=True)
        return await self.repository.update(report_id, update_dict)

    async def delete_report(
        self,
        report_id: UUID,
        user_id: UUID,
        company_id: UUID
    ) -> None:
        """Remove relatório"""
        report = await self.repository.get_by_id(report_id)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Relatório não encontrado"
            )
        
        if report.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para remover este relatório"
            )
        
        await self.repository.delete(report_id)

    async def execute_report(
        self,
        report_id: UUID,
        user_id: UUID,
        company_id: UUID,
        execute_request: ReportExecuteRequest
    ) -> Tuple[Dict[str, Any], UUID]:
        """Executa relatório e retorna dados"""
        report = await self.repository.get_by_id(report_id)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Relatório não encontrado"
            )
        
        if report.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para executar este relatório"
            )
        
        if report.status != ReportStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Relatório não está ativo"
            )
        
        # Criar registro de execução
        execution_start = datetime.utcnow()
        execution = ReportExecution(
            report_id=report_id,
            executed_by=user_id,
            execution_start=execution_start,
            filters_used=execute_request.filters,
            parameters_used=execute_request.parameters,
            status="running"
        )
        
        execution = await self.execution_repository.create(execution)
        
        try:
            # Verificar cache se não for override
            if not execute_request.cache_override and report.last_cached_at:
                cache_age = datetime.utcnow() - report.last_cached_at
                if cache_age.total_seconds() < (report.cache_duration_minutes * 60):
                    # Usar dados em cache (simulado)
                    result_data = await self._get_cached_data(report_id)
                    if result_data:
                        await self._complete_execution(execution.id, result_data)
                        return result_data, execution.id
            
            # Executar query
            result_data = await self._execute_query(
                report, 
                execute_request.filters, 
                execute_request.parameters
            )
            
            # Atualizar cache
            if not execute_request.cache_override:
                await self.repository.update_cache_timestamp(report_id)
            
            # Completar execução
            await self._complete_execution(execution.id, result_data)
            
            return result_data, execution.id
            
        except Exception as e:
            # Marcar execução como falha
            await self._fail_execution(execution.id, str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao executar relatório: {str(e)}"
            )

    async def copy_report(
        self,
        report_id: UUID,
        user_id: UUID,
        company_id: UUID,
        new_name: str
    ) -> Report:
        """Copia relatório"""
        original = await self.repository.get_by_id(report_id)
        if not original:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Relatório não encontrado"
            )
        
        if original.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para copiar este relatório"
            )
        
        # Criar cópia
        copy_data = {
            "name": new_name,
            "description": f"Cópia de {original.name}",
            "company_id": company_id,
            "created_by": user_id,
            "report_type": original.report_type,
            "data_source": original.data_source,
            "query_config": original.query_config.copy() if original.query_config else {},
            "filters": original.filters.copy() if original.filters else {},
            "aggregations": original.aggregations.copy() if original.aggregations else {},
            "chart_config": original.chart_config.copy() if original.chart_config else {},
            "layout_config": original.layout_config.copy() if original.layout_config else {},
            "status": ReportStatus.DRAFT,
            "is_public": False,
            "is_embedded": False,
            "cache_duration_minutes": original.cache_duration_minutes,
            "metadata": original.metadata.copy() if original.metadata else {}
        }
        
        report_copy = Report(**copy_data)
        return await self.repository.create(report_copy)

    async def get_report_analytics(
        self,
        company_id: UUID,
        days: int = 30
    ) -> Dict[str, Any]:
        """Obtém analytics de relatórios"""
        # Estatísticas básicas
        reports = await self.repository.get_by_company(company_id, limit=1000)
        
        total_reports = len(reports)
        active_reports = len([r for r in reports if r.status == ReportStatus.ACTIVE])
        draft_reports = len([r for r in reports if r.status == ReportStatus.DRAFT])
        archived_reports = len([r for r in reports if r.status == ReportStatus.ARCHIVED])
        
        # Estatísticas de execução
        execution_stats = await self.execution_repository.get_execution_stats(company_id, days)
        
        # Relatórios mais usados
        most_used = await self.repository.get_most_executed(company_id, days)
        
        return {
            "total_reports": total_reports,
            "active_reports": active_reports,
            "draft_reports": draft_reports,
            "archived_reports": archived_reports,
            "total_executions": execution_stats["total_executions"],
            "avg_execution_time_ms": execution_stats["avg_duration_ms"],
            "most_used_reports": most_used,
            "execution_trends": []  # TODO: Implementar tendências
        }

    async def _validate_query_config(self, query_config: Dict[str, Any], data_source: str) -> None:
        """Valida configuração da query"""
        if not query_config:
            raise BusinessException("Configuração de query é obrigatória")
        
        # Validações específicas por fonte de dados
        if data_source == "forms":
            if "form_id" not in query_config:
                raise BusinessException("form_id é obrigatório para relatórios de formulários")
        elif data_source == "tasks":
            if "project_id" not in query_config and "board_id" not in query_config:
                raise BusinessException("project_id ou board_id é obrigatório para relatórios de tarefas")
        # Adicionar mais validações conforme necessário

    async def _execute_query(
        self,
        report: Report,
        filters: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Executa query do relatório"""
        # Simulação - implementar integração real com fontes de dados
        return {
            "data": [
                {"id": 1, "name": "Item 1", "value": 100},
                {"id": 2, "name": "Item 2", "value": 200},
                {"id": 3, "name": "Item 3", "value": 300}
            ],
            "total_rows": 3,
            "execution_time_ms": 150
        }

    async def _get_cached_data(self, report_id: UUID) -> Optional[Dict[str, Any]]:
        """Obtém dados em cache"""
        # Implementar sistema de cache real
        return None

    async def _complete_execution(
        self,
        execution_id: UUID,
        result_data: Dict[str, Any]
    ) -> None:
        """Completa execução com sucesso"""
        execution_end = datetime.utcnow()
        
        update_data = {
            "execution_end": execution_end,
            "duration_ms": result_data.get("execution_time_ms", 0),
            "status": "completed",
            "result_data": result_data,
            "row_count": result_data.get("total_rows", 0)
        }
        
        await self.execution_repository.update(execution_id, update_data)

    async def _fail_execution(self, execution_id: UUID, error_message: str) -> None:
        """Marca execução como falha"""
        execution_end = datetime.utcnow()
        
        update_data = {
            "execution_end": execution_end,
            "status": "failed",
            "error_message": error_message
        }
        
        await self.execution_repository.update(execution_id, update_data)


class ReportScheduleService:
    """Serviço para agendamentos de relatórios"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = ReportScheduleRepository(session)
        self.report_repository = ReportRepository(session)

    async def create_schedule(
        self,
        user_id: UUID,
        company_id: UUID,
        schedule_data: ReportScheduleCreate
    ) -> ReportSchedule:
        """Cria agendamento"""
        # Verificar se relatório existe e pertence à empresa
        report = await self.report_repository.get_by_id(schedule_data.report_id)
        if not report or report.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Relatório não encontrado"
            )
        
        # Validar configuração de entrega
        await self._validate_delivery_config(
            schedule_data.delivery_method,
            schedule_data.delivery_config
        )
        
        # Calcular próxima execução
        next_execution = self._calculate_next_execution(
            schedule_data.frequency,
            schedule_data.cron_expression,
            schedule_data.timezone
        )
        
        schedule = ReportSchedule(
            **schedule_data.model_dump(),
            created_by=user_id,
            next_execution=next_execution
        )
        
        return await self.repository.create(schedule)

    async def update_schedule(
        self,
        schedule_id: UUID,
        user_id: UUID,
        company_id: UUID,
        update_data: ReportScheduleUpdate
    ) -> ReportSchedule:
        """Atualiza agendamento"""
        schedule = await self.repository.get_by_id(schedule_id)
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agendamento não encontrado"
            )
        
        # Verificar permissão através do relatório
        report = await self.report_repository.get_by_id(schedule.report_id)
        if not report or report.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para atualizar este agendamento"
            )
        
        update_dict = update_data.model_dump(exclude_unset=True)
        
        # Recalcular próxima execução se frequência mudou
        if "frequency" in update_dict or "cron_expression" in update_dict:
            frequency = update_dict.get("frequency", schedule.frequency)
            cron_expr = update_dict.get("cron_expression", schedule.cron_expression)
            timezone = update_dict.get("timezone", schedule.timezone)
            
            update_dict["next_execution"] = self._calculate_next_execution(
                frequency, cron_expr, timezone
            )
        
        return await self.repository.update(schedule_id, update_dict)

    async def process_due_schedules(self) -> List[Dict[str, Any]]:
        """Processa agendamentos que devem ser executados"""
        due_schedules = await self.repository.get_due_schedules()
        results = []
        
        for schedule in due_schedules:
            try:
                # Executar relatório agendado
                result = await self._execute_scheduled_report(schedule)
                results.append({"schedule_id": schedule.id, "success": True, "result": result})
                
                # Calcular próxima execução
                next_execution = self._calculate_next_execution(
                    schedule.frequency,
                    schedule.cron_expression,
                    schedule.timezone
                )
                
                # Atualizar informações de execução
                await self.repository.update_execution_info(schedule.id, next_execution)
                
            except Exception as e:
                results.append({
                    "schedule_id": schedule.id,
                    "success": False,
                    "error": str(e)
                })
        
        return results

    async def _validate_delivery_config(
        self,
        delivery_method: str,
        delivery_config: Dict[str, Any]
    ) -> None:
        """Valida configuração de entrega"""
        if delivery_method == "email":
            if "recipients" not in delivery_config:
                raise BusinessException("Lista de destinatários é obrigatória para entrega por email")
        elif delivery_method == "webhook":
            if "url" not in delivery_config:
                raise BusinessException("URL é obrigatória para entrega por webhook")
        # Adicionar mais validações

    def _calculate_next_execution(
        self,
        frequency: str,
        cron_expression: Optional[str],
        timezone: str
    ) -> datetime:
        """Calcula próxima execução"""
        # Implementação simplificada - usar biblioteca como croniter para produção
        now = datetime.utcnow()
        
        if frequency == "daily":
            return now + timedelta(days=1)
        elif frequency == "weekly":
            return now + timedelta(weeks=1)
        elif frequency == "monthly":
            return now + timedelta(days=30)
        else:
            return now + timedelta(hours=1)  # Default

    async def _execute_scheduled_report(self, schedule: ReportSchedule) -> Dict[str, Any]:
        """Executa relatório agendado"""
        # Implementar execução e entrega do relatório
        return {"status": "executed", "delivery_method": schedule.delivery_method}


class ReportShareService:
    """Serviço para compartilhamento de relatórios"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = ReportShareRepository(session)
        self.report_repository = ReportRepository(session)

    async def create_share(
        self,
        user_id: UUID,
        company_id: UUID,
        share_data: ReportShareCreate
    ) -> ReportShare:
        """Cria compartilhamento"""
        # Verificar se relatório existe e pertence à empresa
        report = await self.report_repository.get_by_id(share_data.report_id)
        if not report or report.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Relatório não encontrado"
            )
        
        # Gerar token se for compartilhamento público
        share_token = None
        if share_data.shared_with_user_id is None:
            share_token = self._generate_share_token()
        
        share = ReportShare(
            **share_data.model_dump(),
            shared_by_user_id=user_id,
            share_token=share_token
        )
        
        return await self.repository.create(share)

    async def access_shared_report(
        self,
        share_token: str,
        user_id: Optional[UUID] = None
    ) -> Tuple[ReportShare, Report]:
        """Acessa relatório compartilhado"""
        share = await self.repository.get_by_token(share_token)
        if not share:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Compartilhamento não encontrado"
            )
        
        # Verificar se compartilhamento está ativo
        if not share.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Compartilhamento não está ativo"
            )
        
        # Verificar expiração
        if share.expires_at and share.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Compartilhamento expirado"
            )
        
        # Verificar limite de acessos
        if share.max_access_count and share.access_count >= share.max_access_count:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Limite de acessos atingido"
            )
        
        # Incrementar contador de acesso
        await self.repository.increment_access_count(share.id)
        
        return share, share.report

    def _generate_share_token(self) -> str:
        """Gera token de compartilhamento"""
        return secrets.token_urlsafe(32)


class DashboardService:
    """Serviço para dashboards"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = DashboardRepository(session)
        self.widget_repository = DashboardWidgetRepository(session)

    async def create_dashboard(
        self,
        company_id: UUID,
        user_id: UUID,
        dashboard_data: DashboardCreate
    ) -> Dashboard:
        """Cria dashboard"""
        dashboard = Dashboard(
            **dashboard_data.model_dump(),
            company_id=company_id,
            created_by=user_id
        )
        
        return await self.repository.create(dashboard)

    async def copy_dashboard(
        self,
        dashboard_id: UUID,
        user_id: UUID,
        company_id: UUID,
        copy_request: DashboardCopyRequest
    ) -> Dashboard:
        """Copia dashboard"""
        original = await self.repository.get_with_widgets(dashboard_id)
        if not original or original.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dashboard não encontrado"
            )
        
        # Criar cópia do dashboard
        dashboard_copy = Dashboard(
            name=copy_request.new_name,
            description=f"Cópia de {original.name}",
            company_id=company_id,
            created_by=user_id,
            layout_config=original.layout_config.copy() if original.layout_config else {},
            theme=original.theme,
            background_color=original.background_color,
            auto_refresh_minutes=original.auto_refresh_minutes
        )
        
        dashboard_copy = await self.repository.create(dashboard_copy)
        
        # Copiar widgets se solicitado
        if copy_request.copy_widgets and original.widgets:
            for widget in original.widgets:
                widget_copy = DashboardWidget(
                    dashboard_id=dashboard_copy.id,
                    report_id=widget.report_id,
                    title=widget.title,
                    widget_type=widget.widget_type,
                    position_x=widget.position_x,
                    position_y=widget.position_y,
                    width=widget.width,
                    height=widget.height,
                    widget_config=widget.widget_config.copy() if widget.widget_config else {},
                    background_color=widget.background_color,
                    border_color=widget.border_color
                )
                await self.widget_repository.create(widget_copy)
        
        return dashboard_copy

    async def set_default_dashboard(
        self,
        dashboard_id: UUID,
        user_id: UUID,
        company_id: UUID
    ) -> None:
        """Define dashboard como padrão"""
        dashboard = await self.repository.get_by_id(dashboard_id)
        if not dashboard or dashboard.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dashboard não encontrado"
            )
        
        await self.repository.set_as_default(dashboard_id, company_id)


class KPIService:
    """Serviço para KPIs"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = KPIRepository(session)
        self.history_repository = KPIHistoryRepository(session)

    async def create_kpi(
        self,
        company_id: UUID,
        user_id: UUID,
        kpi_data: KPICreate
    ) -> KPI:
        """Cria KPI"""
        kpi = KPI(
            **kpi_data.model_dump(),
            company_id=company_id,
            created_by=user_id
        )
        
        return await self.repository.create(kpi)

    async def calculate_kpi(
        self,
        kpi_id: UUID,
        user_id: UUID,
        company_id: UUID,
        calculate_request: KPICalculateRequest
    ) -> Dict[str, Any]:
        """Calcula valor do KPI"""
        kpi = await self.repository.get_by_id(kpi_id)
        if not kpi or kpi.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="KPI não encontrado"
            )
        
        # Verificar se precisa recalcular
        if not calculate_request.force_recalculate and kpi.last_calculated_at:
            time_since_calc = datetime.utcnow() - kpi.last_calculated_at
            if time_since_calc.total_seconds() < (kpi.update_frequency_minutes * 60):
                return {
                    "value": kpi.current_value,
                    "calculated_at": kpi.last_calculated_at,
                    "from_cache": True
                }
        
        # Calcular novo valor
        new_value = await self._calculate_kpi_value(kpi)
        calculation_metadata = {
            "calculated_by": str(user_id),
            "method": kpi.calculation_method,
            "config": kpi.calculation_config
        }
        
        # Salvar no histórico se solicitado
        if calculate_request.save_to_history:
            history_entry = KPIHistory(
                kpi_id=kpi_id,
                value=new_value,
                calculated_at=datetime.utcnow(),
                calculation_metadata=calculation_metadata
            )
            await self.history_repository.create(history_entry)
        
        # Atualizar KPI
        await self.repository.update_value(kpi_id, new_value, calculation_metadata)
        
        return {
            "value": new_value,
            "calculated_at": datetime.utcnow(),
            "from_cache": False
        }

    async def process_kpi_calculations(self) -> List[Dict[str, Any]]:
        """Processa cálculos de KPIs que estão em atraso"""
        due_kpis = await self.repository.get_due_for_calculation()
        results = []
        
        for kpi in due_kpis:
            try:
                new_value = await self._calculate_kpi_value(kpi)
                
                # Salvar histórico
                history_entry = KPIHistory(
                    kpi_id=kpi.id,
                    value=new_value,
                    calculated_at=datetime.utcnow(),
                    calculation_metadata={"automated": True}
                )
                await self.history_repository.create(history_entry)
                
                # Atualizar KPI
                await self.repository.update_value(kpi.id, new_value)
                
                results.append({
                    "kpi_id": kpi.id,
                    "success": True,
                    "value": new_value
                })
                
            except Exception as e:
                results.append({
                    "kpi_id": kpi.id,
                    "success": False,
                    "error": str(e)
                })
        
        return results

    async def _calculate_kpi_value(self, kpi: KPI) -> float:
        """Calcula valor do KPI baseado na configuração"""
        # Implementação simplificada - integrar com fontes de dados reais
        import random
        return round(random.uniform(0, 1000), 2)


class DataExportService:
    """Serviço para exportação de dados"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = DataExportRepository(session)

    async def create_export(
        self,
        company_id: UUID,
        user_id: UUID,
        export_data: DataExportCreate
    ) -> DataExport:
        """Cria solicitação de exportação"""
        # Calcular data de expiração (7 dias)
        expires_at = datetime.utcnow() + timedelta(days=7)
        
        export = DataExport(
            **export_data.model_dump(),
            company_id=company_id,
            requested_by=user_id,
            expires_at=expires_at,
            status="queued"
        )
        
        export = await self.repository.create(export)
        
        # Adicionar à fila de processamento (implementar com Celery)
        # await self._queue_export_processing(export.id)
        
        return export

    async def process_export(self, export_id: UUID) -> Dict[str, Any]:
        """Processa exportação"""
        export = await self.repository.get_by_id(export_id)
        if not export:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exportação não encontrada"
            )
        
        try:
            # Marcar como processando
            await self.repository.update_status(export_id, "processing")
            
            # Processar dados (implementação simplificada)
            file_path, file_size, total_rows = await self._generate_export_file(export)
            
            # Marcar como completa
            await self.repository.update_status(
                export_id, "completed", file_path, file_size, total_rows
            )
            
            return {
                "status": "completed",
                "file_path": file_path,
                "total_rows": total_rows
            }
            
        except Exception as e:
            await self.repository.update_status(export_id, "failed", error_message=str(e))
            raise

    async def _generate_export_file(
        self,
        export: DataExport
    ) -> Tuple[str, int, int]:
        """Gera arquivo de exportação"""
        # Implementação simplificada
        file_path = f"/exports/{export.id}.{export.export_format.value}"
        file_size = 1024  # bytes
        total_rows = 100
        
        return file_path, file_size, total_rows
