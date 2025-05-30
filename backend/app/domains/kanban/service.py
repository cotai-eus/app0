"""
Service do domínio Kanban
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.domains.kanban.models import (
    Board, BoardColumn, Task, TaskComment, TaskAttachment, 
    TaskTimeLog, BoardMember, TaskStatus, TaskPriority
)
from app.domains.kanban.repository import (
    BoardRepository, BoardColumnRepository, TaskRepository,
    TaskCommentRepository, TaskAttachmentRepository, 
    TaskTimeLogRepository, BoardMemberRepository
)
from app.domains.kanban.schemas import (
    BoardCreate, BoardUpdate, BoardColumnCreate, BoardColumnUpdate,
    TaskCreate, TaskUpdate, TaskCommentCreate, TaskAttachmentCreate,
    TaskTimeLogCreate, BoardMemberCreate
)
from app.shared.common.exceptions import (
    NotFoundException, ValidationException, 
    PermissionDeniedException, ConflictException
)


class BoardService:
    """Service para Board"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = BoardRepository(session)
        self.column_repository = BoardColumnRepository(session)
        self.member_repository = BoardMemberRepository(session)
    
    async def create_board(
        self, 
        board_data: BoardCreate, 
        user_id: UUID
    ) -> Board:
        """Cria um novo board"""
        # Criar board
        board = Board(
            **board_data.model_dump(),
            created_by=user_id
        )
        
        board = await self.repository.create(board)
        
        # Adicionar criador como admin
        member = BoardMember(
            board_id=board.id,
            user_id=user_id,
            role="admin",
            created_by=user_id
        )
        await self.member_repository.create(member)
        
        # Criar colunas padrão
        default_columns = [
            {"title": "To Do", "position": 0, "color": "#f87171"},
            {"title": "In Progress", "position": 1, "color": "#fbbf24"},
            {"title": "Done", "position": 2, "color": "#34d399"}
        ]
        
        for col_data in default_columns:
            column = BoardColumn(
                board_id=board.id,
                title=col_data["title"],
                position=col_data["position"],
                color=col_data["color"],
                created_by=user_id
            )
            await self.column_repository.create(column)
        
        return board
    
    async def get_board(self, board_id: UUID, user_id: UUID) -> Board:
        """Busca board por ID"""
        board = await self.repository.get_by_id(board_id)
        if not board:
            raise NotFoundException("Board não encontrado")
        
        # Verificar permissão
        await self._check_board_access(board_id, user_id)
        
        return board
    
    async def get_board_with_columns(self, board_id: UUID, user_id: UUID) -> Board:
        """Busca board com colunas"""
        await self._check_board_access(board_id, user_id)
        
        board = await self.repository.get_with_columns(board_id)
        if not board:
            raise NotFoundException("Board não encontrado")
        
        return board
    
    async def update_board(
        self, 
        board_id: UUID, 
        board_data: BoardUpdate, 
        user_id: UUID
    ) -> Board:
        """Atualiza board"""
        await self._check_board_permission(board_id, user_id, ["admin", "editor"])
        
        board = await self.repository.get_by_id(board_id)
        if not board:
            raise NotFoundException("Board não encontrado")
        
        update_data = board_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(board, field, value)
        
        return await self.repository.update(board)
    
    async def delete_board(self, board_id: UUID, user_id: UUID) -> None:
        """Remove board"""
        await self._check_board_permission(board_id, user_id, ["admin"])
        
        board = await self.repository.get_by_id(board_id)
        if not board:
            raise NotFoundException("Board não encontrado")
        
        await self.repository.delete(board)
    
    async def get_company_boards(
        self, 
        company_id: UUID, 
        user_id: UUID,
        include_inactive: bool = False
    ) -> List[Board]:
        """Busca boards da empresa"""
        return await self.repository.get_by_company_id(
            company_id, 
            include_inactive
        )
    
    async def search_boards(
        self, 
        company_id: UUID,
        search_term: str,
        user_id: UUID,
        board_type: Optional[str] = None
    ) -> List[Board]:
        """Busca boards por termo"""
        return await self.repository.search_boards(
            company_id, 
            search_term, 
            board_type
        )
    
    async def add_member(
        self, 
        board_id: UUID, 
        member_data: BoardMemberCreate,
        user_id: UUID
    ) -> BoardMember:
        """Adiciona membro ao board"""
        await self._check_board_permission(board_id, user_id, ["admin"])
        
        # Verificar se já é membro
        existing = await self.member_repository.is_member(
            board_id, 
            member_data.user_id
        )
        if existing:
            raise ConflictException("Usuário já é membro do board")
        
        member = BoardMember(
            **member_data.model_dump(),
            board_id=board_id,
            created_by=user_id
        )
        
        return await self.member_repository.create(member)
    
    async def remove_member(
        self, 
        board_id: UUID, 
        member_user_id: UUID,
        user_id: UUID
    ) -> None:
        """Remove membro do board"""
        await self._check_board_permission(board_id, user_id, ["admin"])
        
        members = await self.member_repository.get_by_board_id(board_id)
        member_to_remove = None
        
        for member in members:
            if member.user_id == member_user_id:
                member_to_remove = member
                break
        
        if not member_to_remove:
            raise NotFoundException("Membro não encontrado")
        
        await self.member_repository.delete(member_to_remove)
    
    async def get_board_analytics(
        self, 
        board_id: UUID, 
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Análise do board"""
        await self._check_board_access(board_id, user_id)
        
        task_repository = TaskRepository(self.session)
        return await task_repository.get_tasks_analytics(
            board_id, 
            start_date, 
            end_date
        )
    
    async def _check_board_access(self, board_id: UUID, user_id: UUID) -> None:
        """Verifica se usuário tem acesso ao board"""
        # Verificar se é membro ou se o board é público
        is_member = await self.member_repository.is_member(board_id, user_id)
        
        if not is_member:
            board = await self.repository.get_by_id(board_id)
            if not board or not board.is_public:
                raise PermissionDeniedException(
                    "Acesso negado ao board"
                )
    
    async def _check_board_permission(
        self, 
        board_id: UUID, 
        user_id: UUID, 
        required_roles: List[str]
    ) -> None:
        """Verifica permissão específica no board"""
        role = await self.member_repository.get_member_role(board_id, user_id)
        
        if not role or role not in required_roles:
            raise PermissionDeniedException(
                "Permissão insuficiente para esta operação"
            )


class TaskService:
    """Service para Task"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = TaskRepository(session)
        self.board_repository = BoardRepository(session)
        self.column_repository = BoardColumnRepository(session)
        self.member_repository = BoardMemberRepository(session)
        self.board_service = BoardService(session)
    
    async def create_task(
        self, 
        task_data: TaskCreate, 
        user_id: UUID
    ) -> Task:
        """Cria nova tarefa"""
        # Verificar acesso à coluna
        column = await self.column_repository.get_by_id(task_data.column_id)
        if not column:
            raise NotFoundException("Coluna não encontrada")
        
        await self.board_service._check_board_permission(
            column.board_id, 
            user_id, 
            ["admin", "editor", "member"]
        )
        
        # Buscar próxima posição
        tasks = await self.repository.get_by_column_id(task_data.column_id)
        next_position = len(tasks)
        
        task = Task(
            **task_data.model_dump(),
            position=next_position,
            created_by=user_id
        )
        
        return await self.repository.create(task)
    
    async def get_task(self, task_id: UUID, user_id: UUID) -> Task:
        """Busca tarefa por ID"""
        task = await self.repository.get_by_id(task_id)
        if not task:
            raise NotFoundException("Tarefa não encontrada")
        
        # Verificar acesso via board
        column = await self.column_repository.get_by_id(task.column_id)
        await self.board_service._check_board_access(column.board_id, user_id)
        
        return task
    
    async def get_task_with_details(self, task_id: UUID, user_id: UUID) -> Task:
        """Busca tarefa com detalhes completos"""
        task = await self.repository.get_with_details(task_id)
        if not task:
            raise NotFoundException("Tarefa não encontrada")
        
        # Verificar acesso
        column = await self.column_repository.get_by_id(task.column_id)
        await self.board_service._check_board_access(column.board_id, user_id)
        
        return task
    
    async def update_task(
        self, 
        task_id: UUID, 
        task_data: TaskUpdate, 
        user_id: UUID
    ) -> Task:
        """Atualiza tarefa"""
        task = await self.repository.get_by_id(task_id)
        if not task:
            raise NotFoundException("Tarefa não encontrada")
        
        # Verificar permissão
        column = await self.column_repository.get_by_id(task.column_id)
        await self.board_service._check_board_permission(
            column.board_id, 
            user_id, 
            ["admin", "editor", "member"]
        )
        
        update_data = task_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)
        
        return await self.repository.update(task)
    
    async def delete_task(self, task_id: UUID, user_id: UUID) -> None:
        """Remove tarefa"""
        task = await self.repository.get_by_id(task_id)
        if not task:
            raise NotFoundException("Tarefa não encontrada")
        
        # Verificar permissão
        column = await self.column_repository.get_by_id(task.column_id)
        await self.board_service._check_board_permission(
            column.board_id, 
            user_id, 
            ["admin", "editor", "member"]
        )
        
        await self.repository.delete(task)
    
    async def move_task(
        self, 
        task_id: UUID, 
        new_column_id: UUID, 
        new_position: int,
        user_id: UUID
    ) -> Task:
        """Move tarefa para nova coluna/posição"""
        task = await self.repository.get_by_id(task_id)
        if not task:
            raise NotFoundException("Tarefa não encontrada")
        
        # Verificar acesso às colunas
        old_column = await self.column_repository.get_by_id(task.column_id)
        new_column = await self.column_repository.get_by_id(new_column_id)
        
        if not new_column:
            raise NotFoundException("Nova coluna não encontrada")
        
        # Verificar se as colunas pertencem ao mesmo board
        if old_column.board_id != new_column.board_id:
            raise ValidationException(
                "Não é possível mover tarefa entre boards diferentes"
            )
        
        await self.board_service._check_board_permission(
            old_column.board_id, 
            user_id, 
            ["admin", "editor", "member"]
        )
        
        # Mover tarefa
        await self.repository.move_task(task_id, new_column_id, new_position)
        
        # Atualizar status se necessário
        if new_column.title.lower() == "done":
            task.status = TaskStatus.DONE
        elif new_column.title.lower() == "in progress":
            task.status = TaskStatus.IN_PROGRESS
        else:
            task.status = TaskStatus.TODO
        
        return await self.repository.update(task)
    
    async def assign_task(
        self, 
        task_id: UUID, 
        assignee_id: UUID, 
        user_id: UUID
    ) -> Task:
        """Atribui tarefa a usuário"""
        task = await self.repository.get_by_id(task_id)
        if not task:
            raise NotFoundException("Tarefa não encontrada")
        
        # Verificar permissão
        column = await self.column_repository.get_by_id(task.column_id)
        await self.board_service._check_board_permission(
            column.board_id, 
            user_id, 
            ["admin", "editor", "member"]
        )
        
        # Verificar se assignee é membro do board
        is_member = await self.member_repository.is_member(
            column.board_id, 
            assignee_id
        )
        if not is_member:
            raise ValidationException(
                "Usuário não é membro do board"
            )
        
        task.assigned_to = assignee_id
        return await self.repository.update(task)
    
    async def get_user_tasks(
        self, 
        user_id: UUID,
        status: Optional[TaskStatus] = None,
        company_id: Optional[UUID] = None
    ) -> List[Task]:
        """Busca tarefas do usuário"""
        return await self.repository.get_by_assignee(
            user_id, 
            status, 
            company_id
        )
    
    async def get_overdue_tasks(
        self, 
        user_id: UUID,
        company_id: Optional[UUID] = None
    ) -> List[Task]:
        """Busca tarefas em atraso"""
        return await self.repository.get_overdue_tasks(company_id)


class TaskTimeLogService:
    """Service para TaskTimeLog"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = TaskTimeLogRepository(session)
        self.task_service = TaskService(session)
    
    async def start_time_log(
        self, 
        time_log_data: TaskTimeLogCreate, 
        user_id: UUID
    ) -> TaskTimeLog:
        """Inicia log de tempo"""
        # Verificar acesso à tarefa
        await self.task_service.get_task(time_log_data.task_id, user_id)
        
        # Verificar se já tem log ativo
        active_log = await self.repository.get_active_log(
            time_log_data.task_id, 
            user_id
        )
        if active_log:
            raise ConflictException("Já existe um log de tempo ativo para esta tarefa")
        
        time_log = TaskTimeLog(
            **time_log_data.model_dump(),
            user_id=user_id,
            start_time=datetime.utcnow()
        )
        
        return await self.repository.create(time_log)
    
    async def stop_time_log(self, task_id: UUID, user_id: UUID) -> TaskTimeLog:
        """Para log de tempo ativo"""
        active_log = await self.repository.get_active_log(task_id, user_id)
        if not active_log:
            raise NotFoundException("Nenhum log ativo encontrado")
        
        active_log.end_time = datetime.utcnow()
        return await self.repository.update(active_log)
    
    async def get_task_time_summary(
        self, 
        task_id: UUID, 
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Resumo de tempo da tarefa"""
        # Verificar acesso à tarefa
        await self.task_service.get_task(task_id, user_id)
        
        return await self.repository.get_time_summary(
            task_id, 
            start_date, 
            end_date
        )


class TaskCommentService:
    """Service para TaskComment"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = TaskCommentRepository(session)
        self.task_service = TaskService(session)
    
    async def create_comment(
        self, 
        comment_data: TaskCommentCreate, 
        user_id: UUID
    ) -> TaskComment:
        """Cria comentário"""
        # Verificar acesso à tarefa
        await self.task_service.get_task(comment_data.task_id, user_id)
        
        comment = TaskComment(
            **comment_data.model_dump(),
            created_by=user_id
        )
        
        return await self.repository.create(comment)
    
    async def get_task_comments(
        self, 
        task_id: UUID, 
        user_id: UUID
    ) -> List[TaskComment]:
        """Busca comentários da tarefa"""
        # Verificar acesso à tarefa
        await self.task_service.get_task(task_id, user_id)
        
        return await self.repository.get_by_task_id(task_id)
