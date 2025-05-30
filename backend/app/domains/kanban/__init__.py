"""
Domínio Kanban
"""

from .models import (
    Board, BoardColumn, Task, TaskComment, TaskAttachment,
    TaskTimeLog, BoardMember, TaskStatus, TaskPriority, BoardType
)
from .schemas import (
    BoardResponse, BoardCreate, BoardUpdate,
    BoardColumnResponse, BoardColumnCreate, BoardColumnUpdate,
    TaskResponse, TaskCreate, TaskUpdate,
    TaskCommentResponse, TaskCommentCreate,
    TaskAttachmentResponse, TaskAttachmentCreate,
    TaskTimeLogResponse, TaskTimeLogCreate,
    BoardMemberResponse, BoardMemberCreate,
    BoardAnalyticsResponse, TaskMoveRequest, TaskAssignRequest
)
from .repository import (
    BoardRepository, BoardColumnRepository, TaskRepository,
    TaskCommentRepository, TaskAttachmentRepository,
    TaskTimeLogRepository, BoardMemberRepository
)
from .service import (
    BoardService, TaskService, TaskTimeLogService, TaskCommentService
)

__all__ = [
    # Models
    "Board", "BoardColumn", "Task", "TaskComment", "TaskAttachment",
    "TaskTimeLog", "BoardMember", "TaskStatus", "TaskPriority", "BoardType",
    
    # Schemas
    "BoardResponse", "BoardCreate", "BoardUpdate",
    "BoardColumnResponse", "BoardColumnCreate", "BoardColumnUpdate",
    "TaskResponse", "TaskCreate", "TaskUpdate",
    "TaskCommentResponse", "TaskCommentCreate",
    "TaskAttachmentResponse", "TaskAttachmentCreate",
    "TaskTimeLogResponse", "TaskTimeLogCreate",
    "BoardMemberResponse", "BoardMemberCreate",
    "BoardAnalyticsResponse", "TaskMoveRequest", "TaskAssignRequest",
    
    # Repositories
    "BoardRepository", "BoardColumnRepository", "TaskRepository",
    "TaskCommentRepository", "TaskAttachmentRepository",
    "TaskTimeLogRepository", "BoardMemberRepository",
    
    # Services
    "BoardService", "TaskService", "TaskTimeLogService", "TaskCommentService"
]
