"""
Endpoints do domínio Kanban
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.domains.auth.service import get_current_user
from app.domains.auth.models import User
from app.domains.kanban.service import (
    BoardService, TaskService, TaskTimeLogService, TaskCommentService
)
from app.domains.kanban.schemas import (
    BoardResponse, BoardCreate, BoardUpdate, BoardColumnResponse,
    BoardColumnCreate, BoardColumnUpdate, TaskResponse, TaskCreate, 
    TaskUpdate, TaskCommentResponse, TaskCommentCreate, TaskTimeLogResponse,
    TaskTimeLogCreate, BoardMemberResponse, BoardMemberCreate,
    BoardAnalyticsResponse, TaskMoveRequest, TaskAssignRequest
)
from app.shared.common.responses import SuccessResponse

router = APIRouter(prefix="/kanban", tags=["Kanban"])


# Board Endpoints
@router.post("/boards", response_model=BoardResponse, status_code=status.HTTP_201_CREATED)
async def create_board(
    board_data: BoardCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Cria um novo board"""
    service = BoardService(session)
    board = await service.create_board(board_data, current_user.id)
    return board


@router.get("/boards/{board_id}", response_model=BoardResponse)
async def get_board(
    board_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Busca board por ID"""
    service = BoardService(session)
    return await service.get_board(board_id, current_user.id)


@router.get("/boards/{board_id}/full", response_model=BoardResponse)
async def get_board_with_columns(
    board_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Busca board com todas as colunas e tarefas"""
    service = BoardService(session)
    return await service.get_board_with_columns(board_id, current_user.id)


@router.put("/boards/{board_id}", response_model=BoardResponse)
async def update_board(
    board_id: UUID,
    board_data: BoardUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Atualiza board"""
    service = BoardService(session)
    return await service.update_board(board_id, board_data, current_user.id)


@router.delete("/boards/{board_id}", response_model=SuccessResponse)
async def delete_board(
    board_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Remove board"""
    service = BoardService(session)
    await service.delete_board(board_id, current_user.id)
    return SuccessResponse(message="Board removido com sucesso")


@router.get("/companies/{company_id}/boards", response_model=List[BoardResponse])
async def get_company_boards(
    company_id: UUID,
    include_inactive: bool = Query(False),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Lista boards da empresa"""
    service = BoardService(session)
    return await service.get_company_boards(
        company_id, 
        current_user.id, 
        include_inactive
    )


@router.get("/companies/{company_id}/boards/search", response_model=List[BoardResponse])
async def search_boards(
    company_id: UUID,
    q: str = Query(..., min_length=2),
    board_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Busca boards por termo"""
    service = BoardService(session)
    return await service.search_boards(
        company_id, 
        q, 
        current_user.id, 
        board_type
    )


@router.get("/boards/{board_id}/analytics", response_model=BoardAnalyticsResponse)
async def get_board_analytics(
    board_id: UUID,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Análise do board"""
    service = BoardService(session)
    return await service.get_board_analytics(
        board_id, 
        current_user.id, 
        start_date, 
        end_date
    )


# Board Members Endpoints
@router.post("/boards/{board_id}/members", response_model=BoardMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_board_member(
    board_id: UUID,
    member_data: BoardMemberCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Adiciona membro ao board"""
    service = BoardService(session)
    return await service.add_member(board_id, member_data, current_user.id)


@router.delete("/boards/{board_id}/members/{user_id}", response_model=SuccessResponse)
async def remove_board_member(
    board_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Remove membro do board"""
    service = BoardService(session)
    await service.remove_member(board_id, user_id, current_user.id)
    return SuccessResponse(message="Membro removido com sucesso")


# Task Endpoints
@router.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Cria nova tarefa"""
    service = TaskService(session)
    return await service.create_task(task_data, current_user.id)


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    include_details: bool = Query(False),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Busca tarefa por ID"""
    service = TaskService(session)
    
    if include_details:
        return await service.get_task_with_details(task_id, current_user.id)
    else:
        return await service.get_task(task_id, current_user.id)


@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    task_data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Atualiza tarefa"""
    service = TaskService(session)
    return await service.update_task(task_id, task_data, current_user.id)


@router.delete("/tasks/{task_id}", response_model=SuccessResponse)
async def delete_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Remove tarefa"""
    service = TaskService(session)
    await service.delete_task(task_id, current_user.id)
    return SuccessResponse(message="Tarefa removida com sucesso")


@router.post("/tasks/{task_id}/move", response_model=TaskResponse)
async def move_task(
    task_id: UUID,
    move_data: TaskMoveRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Move tarefa para nova coluna/posição"""
    service = TaskService(session)
    return await service.move_task(
        task_id, 
        move_data.column_id, 
        move_data.position, 
        current_user.id
    )


@router.post("/tasks/{task_id}/assign", response_model=TaskResponse)
async def assign_task(
    task_id: UUID,
    assign_data: TaskAssignRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Atribui tarefa a usuário"""
    service = TaskService(session)
    return await service.assign_task(
        task_id, 
        assign_data.assignee_id, 
        current_user.id
    )


@router.get("/users/tasks", response_model=List[TaskResponse])
async def get_user_tasks(
    status: Optional[str] = Query(None),
    company_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Busca tarefas do usuário atual"""
    service = TaskService(session)
    
    task_status = None
    if status:
        from app.domains.kanban.models import TaskStatus
        try:
            task_status = TaskStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Status inválido"
            )
    
    return await service.get_user_tasks(
        current_user.id, 
        task_status, 
        company_id
    )


@router.get("/tasks/overdue", response_model=List[TaskResponse])
async def get_overdue_tasks(
    company_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Busca tarefas em atraso"""
    service = TaskService(session)
    return await service.get_overdue_tasks(current_user.id, company_id)


# Task Comments Endpoints
@router.post("/tasks/{task_id}/comments", response_model=TaskCommentResponse, status_code=status.HTTP_201_CREATED)
async def create_task_comment(
    task_id: UUID,
    comment_data: TaskCommentCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Adiciona comentário à tarefa"""
    # Garantir que o task_id do path seja usado
    comment_data.task_id = task_id
    
    service = TaskCommentService(session)
    return await service.create_comment(comment_data, current_user.id)


@router.get("/tasks/{task_id}/comments", response_model=List[TaskCommentResponse])
async def get_task_comments(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Lista comentários da tarefa"""
    service = TaskCommentService(session)
    return await service.get_task_comments(task_id, current_user.id)


# Task Time Log Endpoints
@router.post("/tasks/{task_id}/time-logs/start", response_model=TaskTimeLogResponse, status_code=status.HTTP_201_CREATED)
async def start_time_log(
    task_id: UUID,
    time_log_data: TaskTimeLogCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Inicia contagem de tempo para tarefa"""
    # Garantir que o task_id do path seja usado
    time_log_data.task_id = task_id
    
    service = TaskTimeLogService(session)
    return await service.start_time_log(time_log_data, current_user.id)


@router.post("/tasks/{task_id}/time-logs/stop", response_model=TaskTimeLogResponse)
async def stop_time_log(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Para contagem de tempo para tarefa"""
    service = TaskTimeLogService(session)
    return await service.stop_time_log(task_id, current_user.id)


@router.get("/tasks/{task_id}/time-summary", response_model=Dict[str, Any])
async def get_task_time_summary(
    task_id: UUID,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Resumo de tempo gasto na tarefa"""
    service = TaskTimeLogService(session)
    return await service.get_task_time_summary(
        task_id, 
        current_user.id, 
        start_date, 
        end_date
    )
