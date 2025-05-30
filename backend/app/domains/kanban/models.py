"""
Modelos de Kanban para gestão de projetos e tarefas
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import Text, String, Boolean, Integer, JSON, ForeignKey, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, JSONB

from app.shared.common.base_models import BaseModel, TimestampMixin, SoftDeleteMixin, UserTrackingMixin


class TaskPriority(str, Enum):
    """Prioridade da tarefa"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class TaskStatus(str, Enum):
    """Status da tarefa"""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    TESTING = "testing"
    DONE = "done"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class BoardType(str, Enum):
    """Tipo de board"""
    KANBAN = "kanban"
    SCRUM = "scrum"
    CUSTOM = "custom"
    AGILE = "agile"


class TaskComplexity(str, Enum):
    """Complexidade da tarefa (para IA)"""
    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


class AutomationTrigger(str, Enum):
    """Triggers de automação"""
    STATUS_CHANGE = "status_change"
    DUE_DATE_APPROACHING = "due_date_approaching"
    OVERDUE = "overdue"
    ASSIGNED = "assigned"
    COMPLETED = "completed"
    HIGH_PRIORITY = "high_priority"


class Board(BaseModel, TimestampMixin, SoftDeleteMixin, UserTrackingMixin):
    """Board do Kanban"""
    
    __tablename__ = "kanban_boards"
    
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    board_type: Mapped[BoardType] = mapped_column(default=BoardType.KANBAN)
    
    # Relacionamento com empresa
    company_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=False,
        index=True
    )
    
    # Configurações
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    is_template: Mapped[bool] = mapped_column(Boolean, default=False)
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)  # Hex color
    
    # IA e Automação
    ai_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_assign_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    smart_notifications: Mapped[bool] = mapped_column(Boolean, default=True)
    ai_suggestions: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    automation_rules: Mapped[Optional[List[dict]]] = mapped_column(JSONB, default=list)
    
    # Métricas e Analytics
    total_tasks: Mapped[int] = mapped_column(Integer, default=0)
    completed_tasks: Mapped[int] = mapped_column(Integer, default=0)
    average_completion_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    team_velocity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Configurações avançadas
    settings: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    integrations: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    
    # Relacionamentos    columns = relationship("BoardColumn", back_populates="board", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="board")
    members = relationship("BoardMember", back_populates="board", cascade="all, delete-orphan")
    automations = relationship("BoardAutomation", back_populates="board", cascade="all, delete-orphan")
    analytics = relationship("BoardAnalytics", back_populates="board", cascade="all, delete-orphan")


class BoardColumn(BaseModel, TimestampMixin):
    """Colunas do board"""
    
    __tablename__ = "kanban_columns"
    
    board_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("kanban_boards.id"),
        nullable=False
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Configurações
    position: Mapped[int] = mapped_column(Integer, default=0)
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True)
    task_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # WIP limit
    
    # Status padrão para tarefas nesta coluna
    default_status: Mapped[TaskStatus] = mapped_column(default=TaskStatus.TODO)
    
    # Metadados
    settings: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    
    # Relacionamentos
    board = relationship("Board", back_populates="columns")
    tasks = relationship("Task", back_populates="column")


class Task(BaseModel, TimestampMixin, SoftDeleteMixin, UserTrackingMixin):
    """Tarefa do Kanban"""
    
    __tablename__ = "kanban_tasks"
    
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relacionamentos
    board_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("kanban_boards.id"),
        nullable=False,
        index=True
    )
    column_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("kanban_columns.id"),
        nullable=False,
        index=True
    )
    assigned_to: Mapped[Optional[UUID]] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True
    )
    parent_task_id: Mapped[Optional[UUID]] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("kanban_tasks.id"),
        nullable=True
    )
    
    # Status e prioridade
    status: Mapped[TaskStatus] = mapped_column(default=TaskStatus.TODO, index=True)
    priority: Mapped[TaskPriority] = mapped_column(default=TaskPriority.MEDIUM, index=True)
    complexity: Mapped[TaskComplexity] = mapped_column(default=TaskComplexity.SIMPLE)
    
    # Posicionamento
    position: Mapped[int] = mapped_column(Integer, default=0)
    
    # Datas
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Estimativas e tracking
    estimated_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    story_points: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    progress_percentage: Mapped[int] = mapped_column(Integer, default=0)
    
    # IA e Automação
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_priority_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ai_complexity_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ai_suggestions: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    auto_assigned: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Bloqueios e dependências
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    blocked_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    blocked_by_task_id: Mapped[Optional[UUID]] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("kanban_tasks.id"),
        nullable=True
    )
    
    # Tags e categorização
    tags: Mapped[Optional[List[str]]] = mapped_column(JSONB, default=list)
    labels: Mapped[Optional[List[str]]] = mapped_column(JSONB, default=list)
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
      # Metadados e configurações
    settings: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    task_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    
    # Relacionamentos    board = relationship("Board", back_populates="tasks")
    column = relationship("BoardColumn", back_populates="tasks")
    subtasks = relationship("Task", backref="parent_task", remote_side="Task.id")
    comments = relationship("TaskComment", back_populates="task", cascade="all, delete-orphan")
    attachments = relationship("TaskAttachment", back_populates="task", cascade="all, delete-orphan")
    time_logs = relationship("TaskTimeLog", back_populates="task", cascade="all, delete-orphan")
    dependencies = relationship("TaskDependency", 
                              foreign_keys="TaskDependency.task_id", 
                              back_populates="task",
                              cascade="all, delete-orphan")
    ai_analyses = relationship("TaskAIAnalysis", back_populates="task", cascade="all, delete-orphan")


class TaskComment(BaseModel, TimestampMixin):
    """Comentários das tarefas"""
    
    __tablename__ = "kanban_task_comments"
    
    task_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("kanban_tasks.id"),
        nullable=False
    )
    author_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Relacionamentos
    task = relationship("Task", back_populates="comments")


class TaskAttachment(BaseModel, TimestampMixin):
    """Anexos das tarefas"""
    
    __tablename__ = "kanban_task_attachments"
    
    task_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("kanban_tasks.id"),
        nullable=False
    )
    uploaded_by: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        nullable=False
    )
    
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Relacionamentos
    task = relationship("Task", back_populates="attachments")


class TaskTimeLog(BaseModel, TimestampMixin):
    """Log de tempo das tarefas"""
    
    __tablename__ = "kanban_task_time_logs"
    
    task_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("kanban_tasks.id"),
        nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        nullable=False
    )
    
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hours_spent: Mapped[int] = mapped_column(Integer, nullable=False)  # em minutos
    date_logged: Mapped[datetime] = mapped_column(nullable=False)
    
    # Relacionamentos
    task = relationship("Task", back_populates="time_logs")


class BoardMember(BaseModel, TimestampMixin):
    """Membros do board"""
    
    __tablename__ = "kanban_board_members"
    
    board_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("kanban_boards.id"),
        nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        nullable=False
    )
    role: Mapped[str] = mapped_column(String(50), default="member")  # admin, member, viewer
    
    # Configurações
    can_edit: Mapped[bool] = mapped_column(Boolean, default=True)
    can_delete: Mapped[bool] = mapped_column(Boolean, default=False)
    can_assign: Mapped[bool] = mapped_column(Boolean, default=True)
      # Relacionamentos
    board = relationship("Board", back_populates="members")


class TaskDependency(BaseModel, TimestampMixin):
    """Dependências entre tarefas"""
    
    __tablename__ = "kanban_task_dependencies"
    
    task_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("kanban_tasks.id"),
        nullable=False
    )
    depends_on_task_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("kanban_tasks.id"),
        nullable=False
    )
    dependency_type: Mapped[str] = mapped_column(String(50), default="blocks")  # blocks, finish_to_start, etc
    
    # Relacionamentos
    task = relationship("Task", foreign_keys=[task_id], back_populates="dependencies")
    depends_on_task = relationship("Task", foreign_keys=[depends_on_task_id])


class TaskAIAnalysis(BaseModel, TimestampMixin):
    """Análises de IA das tarefas"""
    
    __tablename__ = "kanban_task_ai_analysis"
    
    task_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("kanban_tasks.id"),
        nullable=False
    )
    
    # Análises de IA
    complexity_analysis: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    priority_analysis: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    time_estimation: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    skill_requirements: Mapped[Optional[List[str]]] = mapped_column(JSONB, default=list)
    suggested_assignees: Mapped[Optional[List[str]]] = mapped_column(JSONB, default=list)
    risk_factors: Mapped[Optional[List[str]]] = mapped_column(JSONB, default=list)
    
    # Scores de IA
    complexity_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    priority_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    completion_probability: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Metadados
    ai_model_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    analysis_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Relacionamentos
    task = relationship("Task", back_populates="ai_analyses")


class BoardAutomation(BaseModel, TimestampMixin):
    """Automações do board"""
    
    __tablename__ = "kanban_board_automations"
    
    board_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("kanban_boards.id"),
        nullable=False
    )
    
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Configuração da automação
    trigger_type: Mapped[AutomationTrigger] = mapped_column(nullable=False)
    trigger_conditions: Mapped[dict] = mapped_column(JSONB, nullable=False)
    actions: Mapped[List[dict]] = mapped_column(JSONB, nullable=False)
    
    # Estado
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    execution_count: Mapped[int] = mapped_column(Integer, default=0)
    last_executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relacionamentos
    board = relationship("Board", back_populates="automations")


class BoardAnalytics(BaseModel, TimestampMixin):
    """Analytics do board"""
    
    __tablename__ = "kanban_board_analytics"
    
    board_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("kanban_boards.id"),
        nullable=False
    )
    
    # Período da análise
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Métricas de tarefas
    tasks_created: Mapped[int] = mapped_column(Integer, default=0)
    tasks_completed: Mapped[int] = mapped_column(Integer, default=0)
    tasks_cancelled: Mapped[int] = mapped_column(Integer, default=0)
    
    # Métricas de tempo
    avg_cycle_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # horas
    avg_lead_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)   # horas
    avg_time_in_progress: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Métricas de qualidade
    bugs_reported: Mapped[int] = mapped_column(Integer, default=0)
    rework_tasks: Mapped[int] = mapped_column(Integer, default=0)
    blocked_tasks: Mapped[int] = mapped_column(Integer, default=0)
    
    # Métricas de equipe
    team_velocity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    team_productivity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Dados detalhados
    detailed_metrics: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    
    # Relacionamentos
    board = relationship("Board", back_populates="analytics")
