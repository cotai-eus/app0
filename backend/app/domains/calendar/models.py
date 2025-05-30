"""
Modelos de Calendário para gestão de eventos e agendamentos
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import Text, String, Boolean, Integer, JSON, ForeignKey, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, JSONB

from app.shared.common.base_models import BaseModel, TimestampMixin, SoftDeleteMixin, UserTrackingMixin


class EventType(str, Enum):
    """Tipo de evento"""
    MEETING = "meeting"
    TASK = "task"
    REMINDER = "reminder"
    APPOINTMENT = "appointment"
    DEADLINE = "deadline"
    MILESTONE = "milestone"
    PERSONAL = "personal"
    COMPANY = "company"
    TRAINING = "training"
    INTERVIEW = "interview"
    REVIEW = "review"
    BREAK = "break"


class EventStatus(str, Enum):
    """Status do evento"""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"
    IN_PROGRESS = "in_progress"
    POSTPONED = "postponed"


class EventPriority(str, Enum):
    """Prioridade do evento"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class RecurrenceType(str, Enum):
    """Tipo de recorrência"""
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class AttendeeStatus(str, Enum):
    """Status do participante"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    TENTATIVE = "tentative"
    NO_RESPONSE = "no_response"


class AISchedulingPriority(str, Enum):
    """Prioridade para agendamento inteligente"""
    FLEXIBLE = "flexible"
    PREFERRED = "preferred"
    FIXED = "fixed"
    CRITICAL = "critical"


class ConflictResolutionStrategy(str, Enum):
    """Estratégia de resolução de conflitos"""
    ASK_USER = "ask_user"
    AUTO_RESCHEDULE = "auto_reschedule"
    SUGGEST_ALTERNATIVES = "suggest_alternatives"
    BLOCK_CONFLICTING = "block_conflicting"


class MeetingOptimizationType(str, Enum):
    """Tipo de otimização de reunião"""
    TIME_EFFICIENCY = "time_efficiency"
    ATTENDEE_AVAILABILITY = "attendee_availability"
    RESOURCE_OPTIMIZATION = "resource_optimization"
    ENERGY_LEVELS = "energy_levels"
    COMMUTE_TIME = "commute_time"


class Calendar(BaseModel, TimestampMixin):
    """Calendário"""
    
    __tablename__ = "calendars"
    
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)  # Hex color
    
    # Relacionamentos
    company_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        nullable=False
    )
    owner_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        nullable=False
    )
    
    # Configurações
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    
    # Configurações de acesso
    allow_booking: Mapped[bool] = mapped_column(Boolean, default=False)
    booking_advance_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # AI Integration
    ai_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    smart_scheduling: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_optimization: Mapped[bool] = mapped_column(Boolean, default=False)
    conflict_resolution_strategy: Mapped[ConflictResolutionStrategy] = mapped_column(
        default=ConflictResolutionStrategy.ASK_USER
    )
    
    # AI Preferences and Learning
    ai_preferences: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    learning_data: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    optimization_history: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    
    # Working Hours and Patterns
    working_hours: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    break_patterns: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    commute_preferences: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    
    # Performance Metrics
    scheduling_efficiency_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    meeting_satisfaction_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    time_utilization_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Metadados
    settings: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    
    # Relacionamentos
    events = relationship("Event", back_populates="calendar")
    shares = relationship("CalendarShare", back_populates="calendar", cascade="all, delete-orphan")
    ai_insights = relationship("CalendarAIInsight", back_populates="calendar", cascade="all, delete-orphan")
    optimization_reports = relationship("ScheduleOptimizationReport", back_populates="calendar", cascade="all, delete-orphan")


class Event(BaseModel, TimestampMixin):
    """Evento do calendário"""
    
    __tablename__ = "calendar_events"
    
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    
    # Relacionamentos
    calendar_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("calendars.id"),
        nullable=False
    )
    created_by: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        nullable=False
    )
    
    # Datas e horários
    start_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_all_day: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Classificação
    event_type: Mapped[EventType] = mapped_column(default=EventType.MEETING)
    status: Mapped[EventStatus] = mapped_column(default=EventStatus.SCHEDULED)
    priority: Mapped[EventPriority] = mapped_column(default=EventPriority.MEDIUM)
    
    # AI Integration
    ai_scheduled: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_optimized: Mapped[bool] = mapped_column(Boolean, default=False)
    scheduling_priority: Mapped[AISchedulingPriority] = mapped_column(default=AISchedulingPriority.FLEXIBLE)
    optimization_type: Mapped[Optional[MeetingOptimizationType]] = mapped_column(nullable=True)
    
    # AI Analysis and Suggestions
    ai_analysis: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    ai_suggestions: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    preparation_requirements: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    
    # Smart Features
    auto_agenda_generation: Mapped[bool] = mapped_column(Boolean, default=False)
    smart_duration_adjustment: Mapped[bool] = mapped_column(Boolean, default=False)
    intelligent_reminders: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Performance Tracking
    actual_duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    effectiveness_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    attendee_satisfaction: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    productivity_impact: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Configurações visuais
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    
    # Recorrência
    recurrence_type: Mapped[RecurrenceType] = mapped_column(default=RecurrenceType.NONE)
    recurrence_interval: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    recurrence_end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    recurrence_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Relacionamento com evento pai (para eventos recorrentes)
    parent_event_id: Mapped[Optional[UUID]] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("calendar_events.id"),
        nullable=True
    )
    
    # Configurações
    is_private: Mapped[bool] = mapped_column(Boolean, default=False)
    allow_guests: Mapped[bool] = mapped_column(Boolean, default=True)
    send_notifications: Mapped[bool] = mapped_column(Boolean, default=True)
      # Links e recursos
    meeting_link: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    external_links: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    
    # Metadados
    event_metadata: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    
    # Relacionamentos
    calendar = relationship("Calendar", back_populates="events")
    parent_event = relationship("Event", remote_side="Event.id", backref="child_events")
    attendees = relationship("EventAttendee", back_populates="event", cascade="all, delete-orphan")
    reminders = relationship("EventReminder", back_populates="event", cascade="all, delete-orphan")
    attachments = relationship("EventAttachment", back_populates="event", cascade="all, delete-orphan")
    ai_analysis_logs = relationship("EventAIAnalysis", back_populates="event", cascade="all, delete-orphan")


class EventAttendee(BaseModel, TimestampMixin):
    """Participantes do evento"""
    
    __tablename__ = "calendar_event_attendees"
    
    event_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("calendar_events.id"),
        nullable=False
    )
    user_id: Mapped[Optional[UUID]] = mapped_column(
        PostgresUUID(as_uuid=True),
        nullable=True  # Pode ser convidado externo
    )
    
    # Dados do participante
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Status
    status: Mapped[AttendeeStatus] = mapped_column(default=AttendeeStatus.PENDING)
    is_organizer: Mapped[bool] = mapped_column(Boolean, default=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Datas de resposta
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Observações
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relacionamentos
    event = relationship("Event", back_populates="attendees")


class EventReminder(BaseModel, TimestampMixin):
    """Lembretes do evento"""
    
    __tablename__ = "calendar_event_reminders"
    
    event_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("calendar_events.id"),
        nullable=False
    )
    
    # Configuração do lembrete
    minutes_before: Mapped[int] = mapped_column(Integer, nullable=False)
    method: Mapped[str] = mapped_column(String(50), default="email")  # email, popup, sms
    
    # Status
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relacionamentos
    event = relationship("Event", back_populates="reminders")


class EventAttachment(BaseModel, TimestampMixin):
    """Anexos do evento"""
    
    __tablename__ = "calendar_event_attachments"
    
    event_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("calendar_events.id"),
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
    event = relationship("Event", back_populates="attachments")


class CalendarShare(BaseModel, TimestampMixin):
    """Compartilhamento de calendários"""
    
    __tablename__ = "calendar_shares"
    
    calendar_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("calendars.id"),
        nullable=False
    )
    shared_with_user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        nullable=False
    )
    shared_by_user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        nullable=False
    )
    
    # Permissões
    can_view: Mapped[bool] = mapped_column(Boolean, default=True)
    can_edit: Mapped[bool] = mapped_column(Boolean, default=False)
    can_delete: Mapped[bool] = mapped_column(Boolean, default=False)
    can_share: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Configurações
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relacionamentos
    calendar = relationship("Calendar", back_populates="shares")


class AvailabilitySlot(BaseModel, TimestampMixin):
    """Slots de disponibilidade para agendamentos"""
    
    __tablename__ = "calendar_availability_slots"
    
    calendar_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("calendars.id"),
        nullable=False
    )
    
    # Configuração do slot
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0-6 (segunda a domingo)
    start_time: Mapped[str] = mapped_column(String(5), nullable=False)  # HH:MM
    end_time: Mapped[str] = mapped_column(String(5), nullable=False)    # HH:MM
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
      # Configurações especiais
    max_bookings_per_slot: Mapped[int] = mapped_column(Integer, default=1)
    buffer_minutes: Mapped[int] = mapped_column(Integer, default=0)  # Tempo entre agendamentos
    
    # Metadados
    slot_metadata: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)


class CalendarAIInsight(BaseModel, TimestampMixin):
    """Insights de IA para calendário"""
    
    __tablename__ = "calendar_ai_insights"
    
    calendar_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("calendars.id"),
        nullable=False
    )
    
    # Tipo e conteúdo do insight
    insight_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Métricas e dados
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    impact_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    data_points: Mapped[dict] = mapped_column(JSONB, default=dict)
    
    # Recommendations
    recommendations: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    action_items: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_implemented: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relacionamentos
    calendar = relationship("Calendar", back_populates="ai_insights")


class EventAIAnalysis(BaseModel, TimestampMixin):
    """Análise de IA para eventos específicos"""
    
    __tablename__ = "calendar_event_ai_analysis"
    
    event_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("calendar_events.id"),
        nullable=False
    )
    
    # Tipo de análise
    analysis_type: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Resultados da análise
    results: Mapped[dict] = mapped_column(JSONB, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Sugestões
    suggestions: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    optimizations: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    
    # Status de processamento
    processing_status: Mapped[str] = mapped_column(String(50), default="completed")
    error_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relacionamentos
    event = relationship("Event", back_populates="ai_analysis_logs")


class ScheduleOptimizationReport(BaseModel, TimestampMixin):
    """Relatório de otimização de agenda"""
    
    __tablename__ = "schedule_optimization_reports"
    
    calendar_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("calendars.id"),
        nullable=False
    )
    
    # Período do relatório
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Métricas de performance
    total_events: Mapped[int] = mapped_column(Integer, nullable=False)
    optimized_events: Mapped[int] = mapped_column(Integer, default=0)
    time_saved_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    efficiency_improvement: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Análise detalhada
    optimization_summary: Mapped[dict] = mapped_column(JSONB, nullable=False)
    pattern_analysis: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    recommendations: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    
    # Status
    report_status: Mapped[str] = mapped_column(String(50), default="completed")
    
    # Relacionamentos
    calendar = relationship("Calendar", back_populates="optimization_reports")


class SmartEventSuggestion(BaseModel, TimestampMixin):
    """Sugestões inteligentes de eventos"""
    
    __tablename__ = "smart_event_suggestions"
    
    calendar_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("calendars.id"),
        nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        nullable=False
    )
    
    # Detalhes da sugestão
    suggestion_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Dados do evento sugerido
    suggested_event_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    priority_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Status
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, accepted, rejected, expired
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # User feedback
    user_feedback: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    
    # AI Context
    ai_context: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)


class MeetingPattern(BaseModel, TimestampMixin):
    """Padrões de reunião detectados pela IA"""
    
    __tablename__ = "meeting_patterns"
    
    calendar_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("calendars.id"),
        nullable=False
    )
    
    # Detalhes do padrão
    pattern_type: Mapped[str] = mapped_column(String(100), nullable=False)
    pattern_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Dados do padrão
    pattern_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    frequency: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Estatísticas
    occurrence_count: Mapped[int] = mapped_column(Integer, default=1)
    confidence_level: Mapped[float] = mapped_column(Float, nullable=False)
    effectiveness_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Período de detecção
    first_detected: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_occurrence: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relacionamento
    calendar = relationship("Calendar")


class ConflictResolution(BaseModel, TimestampMixin):
    """Resoluções de conflito de agenda"""
    
    __tablename__ = "calendar_conflict_resolutions"
    
    calendar_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("calendars.id"),
        nullable=False
    )
    
    # Eventos conflitantes
    conflicting_event_ids: Mapped[List[UUID]] = mapped_column(JSON, nullable=False)
    
    # Detalhes do conflito
    conflict_type: Mapped[str] = mapped_column(String(100), nullable=False)
    conflict_description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Resolução aplicada
    resolution_strategy: Mapped[ConflictResolutionStrategy] = mapped_column(nullable=False)
    resolution_details: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    # Resultados
    resolution_status: Mapped[str] = mapped_column(String(50), default="pending")
    user_approval_required: Mapped[bool] = mapped_column(Boolean, default=True)
    user_approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Efetividade
    effectiveness_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    user_satisfaction: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
