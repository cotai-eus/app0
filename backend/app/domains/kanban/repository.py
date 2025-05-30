"""
Repository do domínio Kanban
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, func, text, desc, asc, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.sql import Select

from app.domains.kanban.models import (
    Board, BoardColumn, Task, TaskComment, TaskAttachment, 
    TaskTimeLog, BoardMember, TaskStatus, TaskPriority
)
from app.shared.common.base_repository import BaseRepository


class BoardRepository(BaseRepository[Board]):
    """Repository para Board"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Board, session)
    
    async def get_by_company_id(
        self, 
        company_id: UUID, 
        include_inactive: bool = False
    ) -> List[Board]:
        """Busca boards por empresa"""
        query = select(Board).where(Board.company_id == company_id)
        
        if not include_inactive:
            query = query.where(Board.is_active == True)
        
        query = query.order_by(Board.title)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_with_columns(self, board_id: UUID) -> Optional[Board]:
        """Busca board com suas colunas"""
        query = (
            select(Board)
            .options(selectinload(Board.columns))
            .where(Board.id == board_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_with_members(self, board_id: UUID) -> Optional[Board]:
        """Busca board com membros"""
        query = (
            select(Board)
            .options(selectinload(Board.members))
            .where(Board.id == board_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_public_boards(self, limit: int = 50) -> List[Board]:
        """Busca boards públicos"""
        query = (
            select(Board)
            .where(and_(Board.is_public == True, Board.is_active == True))
            .order_by(Board.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def search_boards(
        self, 
        company_id: UUID,
        search_term: str,
        board_type: Optional[str] = None
    ) -> List[Board]:
        """Busca boards por termo"""
        query = (
            select(Board)
            .where(
                and_(
                    Board.company_id == company_id,
                    or_(
                        Board.title.ilike(f"%{search_term}%"),
                        Board.description.ilike(f"%{search_term}%")
                    )
                )
            )
        )
        
        if board_type:
            query = query.where(Board.board_type == board_type)
        
        result = await self.session.execute(query)
        return result.scalars().all()


class BoardColumnRepository(BaseRepository[BoardColumn]):
    """Repository para BoardColumn"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(BoardColumn, session)
    
    async def get_by_board_id(self, board_id: UUID) -> List[BoardColumn]:
        """Busca colunas por board"""
        query = (
            select(BoardColumn)
            .where(BoardColumn.board_id == board_id)
            .order_by(BoardColumn.position)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_with_tasks(self, column_id: UUID) -> Optional[BoardColumn]:
        """Busca coluna com suas tarefas"""
        query = (
            select(BoardColumn)
            .options(selectinload(BoardColumn.tasks))
            .where(BoardColumn.id == column_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def reorder_columns(self, board_id: UUID, column_orders: List[Dict[str, Any]]) -> None:
        """Reordena colunas do board"""
        for order_data in column_orders:
            column_id = order_data["column_id"]
            position = order_data["position"]
            
            await self.session.execute(
                text("UPDATE boardcolumn SET position = :position WHERE id = :id AND board_id = :board_id"),
                {"position": position, "id": column_id, "board_id": board_id}
            )
        
        await self.session.commit()


class TaskRepository(BaseRepository[Task]):
    """Repository para Task"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Task, session)
    
    async def get_by_column_id(
        self, 
        column_id: UUID,
        status: Optional[TaskStatus] = None
    ) -> List[Task]:
        """Busca tarefas por coluna"""
        query = (
            select(Task)
            .where(Task.column_id == column_id)
            .order_by(Task.position)
        )
        
        if status:
            query = query.where(Task.status == status)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_board_id(
        self, 
        board_id: UUID,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        assigned_to: Optional[UUID] = None
    ) -> List[Task]:
        """Busca tarefas por board com filtros"""
        query = (
            select(Task)
            .join(BoardColumn)
            .where(BoardColumn.board_id == board_id)
            .order_by(Task.created_at.desc())
        )
        
        if status:
            query = query.where(Task.status == status)
        
        if priority:
            query = query.where(Task.priority == priority)
        
        if assigned_to:
            query = query.where(Task.assigned_to == assigned_to)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_with_details(self, task_id: UUID) -> Optional[Task]:
        """Busca tarefa com todos os detalhes"""
        query = (
            select(Task)
            .options(
                selectinload(Task.comments),
                selectinload(Task.attachments),
                selectinload(Task.time_logs)
            )
            .where(Task.id == task_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_assignee(
        self, 
        assignee_id: UUID,
        status: Optional[TaskStatus] = None,
        company_id: Optional[UUID] = None
    ) -> List[Task]:
        """Busca tarefas por responsável"""
        query = select(Task).where(Task.assigned_to == assignee_id)
        
        if status:
            query = query.where(Task.status == status)
        
        if company_id:
            query = (
                query.join(BoardColumn)
                .join(Board)
                .where(Board.company_id == company_id)
            )
        
        query = query.order_by(Task.due_date.asc().nullslast())
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_overdue_tasks(self, company_id: Optional[UUID] = None) -> List[Task]:
        """Busca tarefas em atraso"""
        now = datetime.utcnow()
        query = (
            select(Task)
            .where(
                and_(
                    Task.due_date < now,
                    Task.status != TaskStatus.DONE
                )
            )
        )
        
        if company_id:
            query = (
                query.join(BoardColumn)
                .join(Board)
                .where(Board.company_id == company_id)
            )
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def move_task(
        self, 
        task_id: UUID, 
        new_column_id: UUID, 
        new_position: int
    ) -> None:
        """Move tarefa para nova coluna/posição"""
        # Atualiza a tarefa
        await self.session.execute(
            text("""
                UPDATE task 
                SET column_id = :column_id, position = :position 
                WHERE id = :id
            """),
            {
                "column_id": new_column_id, 
                "position": new_position, 
                "id": task_id
            }
        )
        await self.session.commit()
    
    async def get_tasks_analytics(
        self, 
        board_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Análise de tarefas do board"""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Tasks por status
        status_query = (
            select(Task.status, func.count(Task.id).label('count'))
            .join(BoardColumn)
            .where(
                and_(
                    BoardColumn.board_id == board_id,
                    Task.created_at >= start_date,
                    Task.created_at <= end_date
                )
            )
            .group_by(Task.status)
        )
        status_result = await self.session.execute(status_query)
        status_counts = {row[0]: row[1] for row in status_result}
        
        # Tasks por prioridade
        priority_query = (
            select(Task.priority, func.count(Task.id).label('count'))
            .join(BoardColumn)
            .where(
                and_(
                    BoardColumn.board_id == board_id,
                    Task.created_at >= start_date,
                    Task.created_at <= end_date
                )
            )
            .group_by(Task.priority)
        )
        priority_result = await self.session.execute(priority_query)
        priority_counts = {row[0]: row[1] for row in priority_result}
        
        # Tempo médio de conclusão
        completion_query = (
            select(
                func.avg(
                    func.extract('epoch', Task.updated_at - Task.created_at) / 3600
                ).label('avg_hours')
            )
            .join(BoardColumn)
            .where(
                and_(
                    BoardColumn.board_id == board_id,
                    Task.status == TaskStatus.DONE,
                    Task.updated_at >= start_date,
                    Task.updated_at <= end_date
                )
            )
        )
        completion_result = await self.session.execute(completion_query)
        avg_completion_hours = completion_result.scalar() or 0
        
        return {
            "status_distribution": status_counts,
            "priority_distribution": priority_counts,
            "average_completion_hours": round(avg_completion_hours, 2),
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }


class TaskCommentRepository(BaseRepository[TaskComment]):
    """Repository para TaskComment"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(TaskComment, session)
    
    async def get_by_task_id(self, task_id: UUID) -> List[TaskComment]:
        """Busca comentários por tarefa"""
        query = (
            select(TaskComment)
            .where(TaskComment.task_id == task_id)
            .order_by(TaskComment.created_at.asc())
        )
        result = await self.session.execute(query)
        return result.scalars().all()


class TaskAttachmentRepository(BaseRepository[TaskAttachment]):
    """Repository para TaskAttachment"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(TaskAttachment, session)
    
    async def get_by_task_id(self, task_id: UUID) -> List[TaskAttachment]:
        """Busca anexos por tarefa"""
        query = (
            select(TaskAttachment)
            .where(TaskAttachment.task_id == task_id)
            .order_by(TaskAttachment.created_at.desc())
        )
        result = await self.session.execute(query)
        return result.scalars().all()


class TaskTimeLogRepository(BaseRepository[TaskTimeLog]):
    """Repository para TaskTimeLog"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(TaskTimeLog, session)
    
    async def get_by_task_id(self, task_id: UUID) -> List[TaskTimeLog]:
        """Busca logs de tempo por tarefa"""
        query = (
            select(TaskTimeLog)
            .where(TaskTimeLog.task_id == task_id)
            .order_by(TaskTimeLog.start_time.desc())
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_active_log(self, task_id: UUID, user_id: UUID) -> Optional[TaskTimeLog]:
        """Busca log ativo para usuário e tarefa"""
        query = (
            select(TaskTimeLog)
            .where(
                and_(
                    TaskTimeLog.task_id == task_id,
                    TaskTimeLog.user_id == user_id,
                    TaskTimeLog.end_time.is_(None)
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_time_summary(
        self, 
        task_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Resumo de tempo gasto na tarefa"""
        query = select(TaskTimeLog).where(TaskTimeLog.task_id == task_id)
        
        if start_date:
            query = query.where(TaskTimeLog.start_time >= start_date)
        if end_date:
            query = query.where(TaskTimeLog.start_time <= end_date)
        
        result = await self.session.execute(query)
        logs = result.scalars().all()
        
        total_minutes = 0
        for log in logs:
            if log.end_time:
                duration = log.end_time - log.start_time
                total_minutes += duration.total_seconds() / 60
        
        return {
            "total_minutes": round(total_minutes, 2),
            "total_hours": round(total_minutes / 60, 2),
            "log_count": len(logs),
            "period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            }
        }


class BoardMemberRepository(BaseRepository[BoardMember]):
    """Repository para BoardMember"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(BoardMember, session)
    
    async def get_by_board_id(self, board_id: UUID) -> List[BoardMember]:
        """Busca membros por board"""
        query = (
            select(BoardMember)
            .where(BoardMember.board_id == board_id)
            .order_by(BoardMember.created_at)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_user_id(self, user_id: UUID) -> List[BoardMember]:
        """Busca boards do usuário"""
        query = (
            select(BoardMember)
            .where(BoardMember.user_id == user_id)
            .order_by(BoardMember.created_at.desc())
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def is_member(self, board_id: UUID, user_id: UUID) -> bool:
        """Verifica se usuário é membro do board"""
        query = (
            select(BoardMember)
            .where(
                and_(
                    BoardMember.board_id == board_id,
                    BoardMember.user_id == user_id
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def get_member_role(self, board_id: UUID, user_id: UUID) -> Optional[str]:
        """Busca papel do membro no board"""
        query = (
            select(BoardMember.role)
            .where(
                and_(
                    BoardMember.board_id == board_id,
                    BoardMember.user_id == user_id
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
