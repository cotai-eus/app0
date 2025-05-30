"""
Schemas do domínio Kanban
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.domains.kanban.models import TaskPriority, TaskStatus, BoardType
from app.shared.common.base_schemas import BaseResponseSchema, TimestampSchema


# Board Schemas
class BoardBase(BaseModel):
    """Base schema for Board"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    board_type: BoardType = BoardType.KANBAN
    is_active: bool = True
    is_public: bool = False
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    settings: Optional[Dict[str, Any]] = None


class BoardCreate(BoardBase):
    """Schema for creating a board"""
    company_id: UUID


class BoardUpdate(BaseModel):
    """Schema for updating a board"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    board_type: Optional[BoardType] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    settings: Optional[Dict[str, Any]] = None


class BoardResponse(BoardBase, BaseResponseSchema, TimestampSchema):
    """Schema for board response"""
    company_id: UUID
    created_by: UUID
    
    model_config = ConfigDict(from_attributes=True)


# Board Column Schemas
class BoardColumnBase(BaseModel):
    """Base schema for BoardColumn"""
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    position: int = 0
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    is_visible: bool = True
    task_limit: Optional[int] = Field(None, ge=0)
    default_status: TaskStatus = TaskStatus.TODO
    settings: Optional[Dict[str, Any]] = None


class BoardColumnCreate(BoardColumnBase):
    """Schema for creating a board column"""
    pass


class BoardColumnUpdate(BaseModel):
    """Schema for updating a board column"""
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    position: Optional[int] = None
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    is_visible: Optional[bool] = None
    task_limit: Optional[int] = Field(None, ge=0)
    default_status: Optional[TaskStatus] = None
    settings: Optional[Dict[str, Any]] = None


class BoardColumnResponse(BoardColumnBase, BaseResponseSchema, TimestampSchema):
    """Schema for board column response"""
    board_id: UUID
    task_count: Optional[int] = 0
    
    model_config = ConfigDict(from_attributes=True)


# Task Schemas
class TaskBase(BaseModel):
    """Base schema for Task"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    position: int = 0
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    estimated_hours: Optional[int] = Field(None, ge=0)
    story_points: Optional[int] = Field(None, ge=0)
    tags: Optional[List[str]] = None
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    settings: Optional[Dict[str, Any]] = None


class TaskCreate(TaskBase):
    """Schema for creating a task"""
    column_id: UUID
    assigned_to: Optional[UUID] = None
    parent_task_id: Optional[UUID] = None


class TaskUpdate(BaseModel):
    """Schema for updating a task"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    column_id: Optional[UUID] = None
    assigned_to: Optional[UUID] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    position: Optional[int] = None
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_hours: Optional[int] = Field(None, ge=0)
    actual_hours: Optional[int] = Field(None, ge=0)
    story_points: Optional[int] = Field(None, ge=0)
    tags: Optional[List[str]] = None
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    settings: Optional[Dict[str, Any]] = None


class TaskResponse(TaskBase, BaseResponseSchema, TimestampSchema):
    """Schema for task response"""
    board_id: UUID
    column_id: UUID
    assigned_to: Optional[UUID] = None
    created_by: UUID
    parent_task_id: Optional[UUID] = None
    completed_at: Optional[datetime] = None
    actual_hours: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


# Action Schemas
class TaskMoveRequest(BaseModel):
    """Schema for moving a task"""
    column_id: UUID
    position: int


class TaskAssignRequest(BaseModel):
    """Schema for assigning a task"""
    assignee_id: UUID


class BoardAnalyticsResponse(BaseModel):
    """Schema for board analytics response"""
    status_distribution: Dict[str, int]
    priority_distribution: Dict[str, int]
    average_completion_hours: float
    period: Dict[str, str]


class TaskAttachmentCreate(BaseModel):
    """Schema for creating task attachment"""
    filename: str
    original_filename: str
    file_size: int
    content_type: str


class TaskMove(BaseModel):
    """Schema for moving a task"""
    task_id: UUID
    column_id: UUID
    position: int


class TaskPositionUpdate(BaseModel):
    """Schema for updating task positions"""
    task_id: UUID
    position: int


# Task Comment Schemas
class TaskCommentBase(BaseModel):
    """Base schema for TaskComment"""
    content: str = Field(..., min_length=1)


class TaskCommentCreate(TaskCommentBase):
    """Schema for creating a task comment"""
    pass


class TaskCommentUpdate(BaseModel):
    """Schema for updating a task comment"""
    content: str = Field(..., min_length=1)


class TaskCommentResponse(TaskCommentBase, BaseResponseSchema, TimestampSchema):
    """Schema for task comment response"""
    task_id: UUID
    author_id: UUID
    
    model_config = ConfigDict(from_attributes=True)


# Task Attachment Schemas
class TaskAttachmentResponse(BaseResponseSchema, TimestampSchema):
    """Schema for task attachment response"""
    task_id: UUID
    uploaded_by: UUID
    filename: str
    original_filename: str
    file_size: int
    content_type: str
    
    model_config = ConfigDict(from_attributes=True)


# Task Time Log Schemas
class TaskTimeLogBase(BaseModel):
    """Base schema for TaskTimeLog"""
    description: Optional[str] = None
    hours_spent: int = Field(..., ge=1)  # em minutos
    date_logged: datetime


class TaskTimeLogCreate(TaskTimeLogBase):
    """Schema for creating a task time log"""
    pass


class TaskTimeLogUpdate(BaseModel):
    """Schema for updating a task time log"""
    description: Optional[str] = None
    hours_spent: Optional[int] = Field(None, ge=1)
    date_logged: Optional[datetime] = None


class TaskTimeLogResponse(TaskTimeLogBase, BaseResponseSchema, TimestampSchema):
    """Schema for task time log response"""
    task_id: UUID
    user_id: UUID
    
    model_config = ConfigDict(from_attributes=True)


# Board Member Schemas
class BoardMemberBase(BaseModel):
    """Base schema for BoardMember"""
    role: str = "member"
    can_edit: bool = True
    can_delete: bool = False
    can_assign: bool = True


class BoardMemberCreate(BoardMemberBase):
    """Schema for creating a board member"""
    user_id: UUID


class BoardMemberUpdate(BaseModel):
    """Schema for updating a board member"""
    role: Optional[str] = None
    can_edit: Optional[bool] = None
    can_delete: Optional[bool] = None
    can_assign: Optional[bool] = None


class BoardMemberResponse(BoardMemberBase, BaseResponseSchema, TimestampSchema):
    """Schema for board member response"""
    board_id: UUID
    user_id: UUID
    
    model_config = ConfigDict(from_attributes=True)


# Complex Schemas
class TaskWithDetails(TaskResponse):
    """Task with additional details"""
    subtasks: List[TaskResponse] = []
    comments: List[TaskCommentResponse] = []
    attachments: List[TaskAttachmentResponse] = []
    time_logs: List[TaskTimeLogResponse] = []


class BoardColumnWithTasks(BoardColumnResponse):
    """Board column with tasks"""
    tasks: List[TaskResponse] = []


class BoardWithDetails(BoardResponse):
    """Board with columns and tasks"""
    columns: List[BoardColumnWithTasks] = []
    members: List[BoardMemberResponse] = []


class BoardSummary(BaseModel):
    """Board summary with statistics"""
    board: BoardResponse
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    overdue_tasks: int
    total_hours_logged: int
    total_estimated_hours: int
    completion_rate: float
    productivity_metrics: Dict[str, Any]


class KanbanMetrics(BaseModel):
    """Kanban metrics and analytics"""
    board_id: UUID
    period_days: int
    cycle_time_avg: Optional[float] = None  # em dias
    lead_time_avg: Optional[float] = None   # em dias
    throughput: int  # tarefas completadas no período
    wip_violations: int  # violações de Work in Progress
    tasks_by_status: Dict[str, int]
    tasks_by_priority: Dict[str, int]
    burndown_data: List[Dict[str, Any]]
    velocity_data: List[Dict[str, Any]]


# Bulk Operations
class TaskBulkMove(BaseModel):
    """Schema for bulk moving tasks"""
    tasks: List[TaskMove]


class TaskBulkUpdate(BaseModel):
    """Schema for bulk updating tasks"""
    task_ids: List[UUID]
    updates: TaskUpdate


class ColumnReorder(BaseModel):
    """Schema for reordering columns"""
    column_id: UUID
    position: int


class ColumnBulkReorder(BaseModel):
    """Schema for bulk reordering columns"""
    columns: List[ColumnReorder]
