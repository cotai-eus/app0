"""
Repository para domínio de Relatórios e Analytics
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, func, desc, asc, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.domains.reports.models import (
    Report, ReportExecution, ReportSchedule, ReportShare,
    Dashboard, DashboardWidget, KPI, KPIHistory, DataExport,
    ReportStatus, ReportType
)
from app.shared.common.repository import BaseRepository


class ReportRepository(BaseRepository[Report]):
    """Repository para relatórios"""

    def __init__(self, session: AsyncSession):
        super().__init__(Report, session)

    async def get_by_company(
        self,
        company_id: UUID,
        skip: int = 0,
        limit: int = 100,
        status: Optional[ReportStatus] = None,
        report_type: Optional[ReportType] = None,
        data_source: Optional[str] = None,
        is_public: Optional[bool] = None
    ) -> List[Report]:
        """Busca relatórios por empresa com filtros"""
        query = select(self.model).where(self.model.company_id == company_id)
        
        if status is not None:
            query = query.where(self.model.status == status)
        
        if report_type is not None:
            query = query.where(self.model.report_type == report_type)
            
        if data_source is not None:
            query = query.where(self.model.data_source == data_source)
            
        if is_public is not None:
            query = query.where(self.model.is_public == is_public)
        
        query = query.order_by(desc(self.model.updated_at)).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def search_reports(
        self,
        company_id: UUID,
        search_term: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[Report]:
        """Busca relatórios por termo"""
        query = select(self.model).where(
            and_(
                self.model.company_id == company_id,
                or_(
                    self.model.name.ilike(f"%{search_term}%"),
                    self.model.description.ilike(f"%{search_term}%")
                )
            )
        ).order_by(desc(self.model.updated_at)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_public_reports(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Report]:
        """Busca relatórios públicos"""
        query = select(self.model).where(
            and_(
                self.model.is_public == True,
                self.model.status == ReportStatus.ACTIVE
            )
        ).order_by(desc(self.model.updated_at)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_embedded_reports(
        self,
        company_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Report]:
        """Busca relatórios embarcados"""
        query = select(self.model).where(
            and_(
                self.model.company_id == company_id,
                self.model.is_embedded == True,
                self.model.status == ReportStatus.ACTIVE
            )
        ).order_by(desc(self.model.updated_at)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_most_executed(
        self,
        company_id: UUID,
        days: int = 30,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Busca relatórios mais executados"""
        since_date = datetime.utcnow() - timedelta(days=days)
        
        query = select(
            self.model.id,
            self.model.name,
            func.count(ReportExecution.id).label('execution_count')
        ).join(
            ReportExecution, 
            and_(
                ReportExecution.report_id == self.model.id,
                ReportExecution.created_at >= since_date
            )
        ).where(
            self.model.company_id == company_id
        ).group_by(
            self.model.id, self.model.name
        ).order_by(
            desc('execution_count')
        ).limit(limit)
        
        result = await self.session.execute(query)
        return [
            {
                'report_id': row.id,
                'report_name': row.name,
                'execution_count': row.execution_count
            }
            for row in result
        ]

    async def update_cache_timestamp(self, report_id: UUID) -> None:
        """Atualiza timestamp do cache"""
        await self.session.execute(
            text("UPDATE reports SET last_cached_at = NOW() WHERE id = :report_id"),
            {"report_id": report_id}
        )
        await self.session.commit()


class ReportExecutionRepository(BaseRepository[ReportExecution]):
    """Repository para execuções de relatórios"""

    def __init__(self, session: AsyncSession):
        super().__init__(ReportExecution, session)

    async def get_by_report(
        self,
        report_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[ReportExecution]:
        """Busca execuções por relatório"""
        query = select(self.model).where(
            self.model.report_id == report_id
        ).order_by(desc(self.model.execution_start)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_user_executions(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[ReportExecution]:
        """Busca execuções por usuário"""
        query = select(self.model).options(
            joinedload(self.model.report)
        ).where(
            self.model.executed_by == user_id
        ).order_by(desc(self.model.execution_start)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_execution_stats(
        self,
        company_id: UUID,
        days: int = 30
    ) -> Dict[str, Any]:
        """Estatísticas de execuções"""
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Total de execuções
        total_query = select(func.count(self.model.id)).join(
            Report
        ).where(
            and_(
                Report.company_id == company_id,
                self.model.created_at >= since_date
            )
        )
        total_result = await self.session.execute(total_query)
        total_executions = total_result.scalar() or 0
        
        # Tempo médio de execução
        avg_query = select(func.avg(self.model.duration_ms)).join(
            Report
        ).where(
            and_(
                Report.company_id == company_id,
                self.model.created_at >= since_date,
                self.model.duration_ms.isnot(None)
            )
        )
        avg_result = await self.session.execute(avg_query)
        avg_duration = avg_result.scalar() or 0
        
        # Execuções por status
        status_query = select(
            self.model.status,
            func.count(self.model.id).label('count')
        ).join(
            Report
        ).where(
            and_(
                Report.company_id == company_id,
                self.model.created_at >= since_date
            )
        ).group_by(self.model.status)
        
        status_result = await self.session.execute(status_query)
        status_counts = {row.status: row.count for row in status_result}
        
        return {
            'total_executions': total_executions,
            'avg_duration_ms': float(avg_duration) if avg_duration else None,
            'status_counts': status_counts
        }


class ReportScheduleRepository(BaseRepository[ReportSchedule]):
    """Repository para agendamentos de relatórios"""

    def __init__(self, session: AsyncSession):
        super().__init__(ReportSchedule, session)

    async def get_by_company(
        self,
        company_id: UUID,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[ReportSchedule]:
        """Busca agendamentos por empresa"""
        query = select(self.model).join(Report).where(
            Report.company_id == company_id
        )
        
        if is_active is not None:
            query = query.where(self.model.is_active == is_active)
            
        query = query.order_by(desc(self.model.created_at)).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_due_schedules(self) -> List[ReportSchedule]:
        """Busca agendamentos que devem ser executados"""
        now = datetime.utcnow()
        
        query = select(self.model).where(
            and_(
                self.model.is_active == True,
                self.model.next_execution <= now
            )
        ).order_by(asc(self.model.next_execution))
        
        result = await self.session.execute(query)
        return result.scalars().all()

    async def update_execution_info(
        self,
        schedule_id: UUID,
        next_execution: Optional[datetime] = None
    ) -> None:
        """Atualiza informações de execução"""
        update_data = {
            'last_execution': datetime.utcnow(),
            'execution_count': self.model.execution_count + 1
        }
        
        if next_execution:
            update_data['next_execution'] = next_execution
            
        await self.session.execute(
            text("""
                UPDATE report_schedules 
                SET last_execution = :last_execution,
                    execution_count = execution_count + 1,
                    next_execution = COALESCE(:next_execution, next_execution)
                WHERE id = :schedule_id
            """),
            {
                'schedule_id': schedule_id,
                'last_execution': update_data['last_execution'],
                'next_execution': next_execution
            }
        )
        await self.session.commit()


class ReportShareRepository(BaseRepository[ReportShare]):
    """Repository para compartilhamentos de relatórios"""

    def __init__(self, session: AsyncSession):
        super().__init__(ReportShare, session)

    async def get_by_report(
        self,
        report_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[ReportShare]:
        """Busca compartilhamentos por relatório"""
        query = select(self.model).where(
            self.model.report_id == report_id
        ).order_by(desc(self.model.created_at)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_token(self, share_token: str) -> Optional[ReportShare]:
        """Busca compartilhamento por token"""
        query = select(self.model).options(
            joinedload(self.model.report)
        ).where(
            and_(
                self.model.share_token == share_token,
                self.model.is_active == True
            )
        )
        
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_user_shares(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[ReportShare]:
        """Busca compartilhamentos do usuário"""
        query = select(self.model).options(
            joinedload(self.model.report)
        ).where(
            self.model.shared_with_user_id == user_id
        ).order_by(desc(self.model.created_at)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()

    async def increment_access_count(self, share_id: UUID) -> None:
        """Incrementa contador de acesso"""
        await self.session.execute(
            text("UPDATE report_shares SET access_count = access_count + 1 WHERE id = :share_id"),
            {"share_id": share_id}
        )
        await self.session.commit()


class DashboardRepository(BaseRepository[Dashboard]):
    """Repository para dashboards"""

    def __init__(self, session: AsyncSession):
        super().__init__(Dashboard, session)

    async def get_by_company(
        self,
        company_id: UUID,
        skip: int = 0,
        limit: int = 100,
        is_public: Optional[bool] = None
    ) -> List[Dashboard]:
        """Busca dashboards por empresa"""
        query = select(self.model).where(self.model.company_id == company_id)
        
        if is_public is not None:
            query = query.where(self.model.is_public == is_public)
            
        query = query.order_by(desc(self.model.updated_at)).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_with_widgets(self, dashboard_id: UUID) -> Optional[Dashboard]:
        """Busca dashboard com widgets"""
        query = select(self.model).options(
            selectinload(self.model.widgets)
        ).where(self.model.id == dashboard_id)
        
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_default_dashboard(self, company_id: UUID) -> Optional[Dashboard]:
        """Busca dashboard padrão da empresa"""
        query = select(self.model).where(
            and_(
                self.model.company_id == company_id,
                self.model.is_default == True
            )
        )
        
        result = await self.session.execute(query)
        return result.scalars().first()

    async def set_as_default(self, dashboard_id: UUID, company_id: UUID) -> None:
        """Define dashboard como padrão"""
        # Remove flag de padrão de outros dashboards
        await self.session.execute(
            text("""
                UPDATE dashboards 
                SET is_default = FALSE 
                WHERE company_id = :company_id AND id != :dashboard_id
            """),
            {"company_id": company_id, "dashboard_id": dashboard_id}
        )
        
        # Define o dashboard atual como padrão
        await self.session.execute(
            text("UPDATE dashboards SET is_default = TRUE WHERE id = :dashboard_id"),
            {"dashboard_id": dashboard_id}
        )
        
        await self.session.commit()


class DashboardWidgetRepository(BaseRepository[DashboardWidget]):
    """Repository para widgets de dashboard"""

    def __init__(self, session: AsyncSession):
        super().__init__(DashboardWidget, session)

    async def get_by_dashboard(
        self,
        dashboard_id: UUID,
        visible_only: bool = True
    ) -> List[DashboardWidget]:
        """Busca widgets por dashboard"""
        query = select(self.model).where(self.model.dashboard_id == dashboard_id)
        
        if visible_only:
            query = query.where(self.model.is_visible == True)
            
        query = query.order_by(asc(self.model.position_y), asc(self.model.position_x))
        result = await self.session.execute(query)
        return result.scalars().all()

    async def reorder_widgets(
        self,
        dashboard_id: UUID,
        widget_positions: List[Dict[str, Any]]
    ) -> None:
        """Reordena widgets no dashboard"""
        for widget_pos in widget_positions:
            await self.session.execute(
                text("""
                    UPDATE dashboard_widgets 
                    SET position_x = :position_x, 
                        position_y = :position_y,
                        width = :width,
                        height = :height
                    WHERE id = :widget_id AND dashboard_id = :dashboard_id
                """),
                {
                    "widget_id": widget_pos["widget_id"],
                    "dashboard_id": dashboard_id,
                    "position_x": widget_pos["position_x"],
                    "position_y": widget_pos["position_y"],
                    "width": widget_pos["width"],
                    "height": widget_pos["height"]
                }
            )
        
        await self.session.commit()


class KPIRepository(BaseRepository[KPI]):
    """Repository para KPIs"""

    def __init__(self, session: AsyncSession):
        super().__init__(KPI, session)

    async def get_by_company(
        self,
        company_id: UUID,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[KPI]:
        """Busca KPIs por empresa"""
        query = select(self.model).where(self.model.company_id == company_id)
        
        if is_active is not None:
            query = query.where(self.model.is_active == is_active)
            
        query = query.order_by(desc(self.model.updated_at)).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_due_for_calculation(self) -> List[KPI]:
        """Busca KPIs que precisam ser calculados"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=60)  # Considera intervalo mínimo
        
        query = select(self.model).where(
            and_(
                self.model.is_active == True,
                or_(
                    self.model.last_calculated_at.is_(None),
                    self.model.last_calculated_at <= cutoff_time
                )
            )
        )
        
        result = await self.session.execute(query)
        return result.scalars().all()

    async def update_value(
        self,
        kpi_id: UUID,
        new_value: float,
        calculation_metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Atualiza valor do KPI"""
        now = datetime.utcnow()
        
        # Pega valor atual para mover para previous_value
        current_query = select(self.model.current_value).where(self.model.id == kpi_id)
        current_result = await self.session.execute(current_query)
        current_value = current_result.scalar()
        
        # Atualiza o KPI
        await self.session.execute(
            text("""
                UPDATE kpis 
                SET current_value = :new_value,
                    previous_value = :previous_value,
                    last_calculated_at = :calculated_at
                WHERE id = :kpi_id
            """),
            {
                "kpi_id": kpi_id,
                "new_value": new_value,
                "previous_value": current_value,
                "calculated_at": now
            }
        )
        
        await self.session.commit()


class KPIHistoryRepository(BaseRepository[KPIHistory]):
    """Repository para histórico de KPIs"""

    def __init__(self, session: AsyncSession):
        super().__init__(KPIHistory, session)

    async def get_by_kpi(
        self,
        kpi_id: UUID,
        days: int = 30,
        skip: int = 0,
        limit: int = 100
    ) -> List[KPIHistory]:
        """Busca histórico por KPI"""
        since_date = datetime.utcnow() - timedelta(days=days)
        
        query = select(self.model).where(
            and_(
                self.model.kpi_id == kpi_id,
                self.model.calculated_at >= since_date
            )
        ).order_by(desc(self.model.calculated_at)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_trend_data(
        self,
        kpi_id: UUID,
        days: int = 30
    ) -> Dict[str, Any]:
        """Calcula dados de tendência"""
        since_date = datetime.utcnow() - timedelta(days=days)
        
        query = select(
            self.model.value,
            self.model.calculated_at
        ).where(
            and_(
                self.model.kpi_id == kpi_id,
                self.model.calculated_at >= since_date
            )
        ).order_by(asc(self.model.calculated_at))
        
        result = await self.session.execute(query)
        values = [(row.value, row.calculated_at) for row in result]
        
        if len(values) < 2:
            return {'trend_direction': 'stable', 'trend_percentage': 0.0}
        
        first_value = values[0][0]
        last_value = values[-1][0]
        
        if first_value == 0:
            trend_percentage = 100.0 if last_value > 0 else 0.0
        else:
            trend_percentage = ((last_value - first_value) / first_value) * 100
        
        if trend_percentage > 5:
            trend_direction = 'up'
        elif trend_percentage < -5:
            trend_direction = 'down'
        else:
            trend_direction = 'stable'
        
        return {
            'trend_direction': trend_direction,
            'trend_percentage': round(trend_percentage, 2)
        }


class DataExportRepository(BaseRepository[DataExport]):
    """Repository para exportações de dados"""

    def __init__(self, session: AsyncSession):
        super().__init__(DataExport, session)

    async def get_by_company(
        self,
        company_id: UUID,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[DataExport]:
        """Busca exportações por empresa"""
        query = select(self.model).where(self.model.company_id == company_id)
        
        if status:
            query = query.where(self.model.status == status)
            
        query = query.order_by(desc(self.model.created_at)).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_user_exports(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[DataExport]:
        """Busca exportações por usuário"""
        query = select(self.model).where(
            self.model.requested_by == user_id
        ).order_by(desc(self.model.created_at)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()

    async def update_status(
        self,
        export_id: UUID,
        status: str,
        file_path: Optional[str] = None,
        file_size: Optional[int] = None,
        total_rows: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Atualiza status da exportação"""
        update_data = {"export_id": export_id, "status": status}
        
        set_clauses = ["status = :status"]
        
        if status == "processing" and not file_path:
            set_clauses.append("started_at = NOW()")
        elif status == "completed":
            set_clauses.append("completed_at = NOW()")
            if file_path:
                update_data["file_path"] = file_path
                set_clauses.append("file_path = :file_path")
            if file_size:
                update_data["file_size"] = file_size
                set_clauses.append("file_size = :file_size")
            if total_rows:
                update_data["total_rows"] = total_rows
                set_clauses.append("total_rows = :total_rows")
        elif status == "failed" and error_message:
            update_data["error_message"] = error_message
            set_clauses.append("error_message = :error_message")
            
        query = f"UPDATE data_exports SET {', '.join(set_clauses)} WHERE id = :export_id"
        
        await self.session.execute(text(query), update_data)
        await self.session.commit()

    async def cleanup_expired_exports(self) -> int:
        """Remove exportações expiradas"""
        now = datetime.utcnow()
        
        result = await self.session.execute(
            text("DELETE FROM data_exports WHERE expires_at < :now"),
            {"now": now}
        )
        
        await self.session.commit()
        return result.rowcount
