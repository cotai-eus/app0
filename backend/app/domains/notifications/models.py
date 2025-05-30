"""
Modelos de Notificações e Comunicação
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import Text, String, Boolean, Integer, JSON, ForeignKey, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, JSONB

from app.shared.common.base_models import BaseModel, TimestampMixin, SoftDeleteMixin, UserTrackingMixin


class NotificationType(str, Enum):
    """Tipo de notificação"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    REMINDER = "reminder"
    INVITATION = "invitation"
    APPROVAL = "approval"
    MENTION = "mention"
    SYSTEM = "system"
    AI_INSIGHT = "ai_insight"
    DEADLINE_ALERT = "deadline_alert"
    TASK_UPDATE = "task_update"
    SECURITY_ALERT = "security_alert"


class NotificationChannel(str, Enum):
    """Canal de notificação"""
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"
    SLACK = "slack"
    TEAMS = "teams"
    DISCORD = "discord"
    WHATSAPP = "whatsapp"


class NotificationStatus(str, Enum):
    """Status da notificação"""
    PENDING = "pending"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BOUNCED = "bounced"


class TemplateType(str, Enum):
    """Tipo de template"""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"
    WEBHOOK = "webhook"


class Priority(str, Enum):
    """Prioridade da notificação"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class Notification(BaseModel, TimestampMixin, SoftDeleteMixin):
    """Notificação"""
    
    __tablename__ = "notifications"
    
    # Relacionamentos
    recipient_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )
    sender_id: Mapped[Optional[UUID]] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True  # Pode ser sistema
    )
    company_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=False,
        index=True
    )
    
    # Conteúdo
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    short_message: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Para SMS/Push
    
    # Classificação
    notification_type: Mapped[NotificationType] = mapped_column(default=NotificationType.INFO, index=True)
    priority: Mapped[Priority] = mapped_column(default=Priority.MEDIUM, index=True)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    
    # Canais e entrega
    channels: Mapped[List[str]] = mapped_column(JSONB, default=list)  # Lista de canais
    preferred_channel: Mapped[Optional[NotificationChannel]] = mapped_column(nullable=True)
    
    # Status e controle
    status: Mapped[NotificationStatus] = mapped_column(default=NotificationStatus.PENDING, index=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    
    # Datas importantes
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Ações e links
    action_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    action_label: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
      # Referências a outros objetos
    related_object_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    related_object_id: Mapped[Optional[UUID]] = mapped_column(PostgresUUID(as_uuid=True), nullable=True)
    
    # Metadados
    notification_metadata: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    
    # Configurações
    is_persistent: Mapped[bool] = mapped_column(Boolean, default=True)  # Se deve ser salva no banco
    allow_digest: Mapped[bool] = mapped_column(Boolean, default=True)   # Pode ser agrupada em digest
    
    # Relacionamentos
    deliveries = relationship("NotificationDelivery", back_populates="notification", cascade="all, delete-orphan")


class NotificationDelivery(BaseModel, TimestampMixin):
    """Entrega de notificação por canal"""
    
    __tablename__ = "notification_deliveries"
    
    notification_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("notifications.id"),
        nullable=False
    )
    
    # Canal de entrega
    channel: Mapped[NotificationChannel] = mapped_column(nullable=False)
    
    # Dados de entrega
    recipient_address: Mapped[str] = mapped_column(String(255), nullable=False)  # email, phone, etc.
    
    # Status da entrega
    status: Mapped[NotificationStatus] = mapped_column(default=NotificationStatus.PENDING)
    
    # Tentativas
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    
    # Datas
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Resposta do provedor
    provider_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    provider_response: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relacionamentos
    notification = relationship("Notification", back_populates="deliveries")


class NotificationTemplate(BaseModel, TimestampMixin):
    """Template de notificação"""
    
    __tablename__ = "notification_templates"
    
    # Identificação
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relacionamentos
    company_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        nullable=False
    )
    created_by: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        nullable=False
    )
    
    # Tipo e canal
    template_type: Mapped[TemplateType] = mapped_column(nullable=False)
    default_channels: Mapped[List[str]] = mapped_column(JSON, default=list)
    
    # Conteúdo do template
    subject_template: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    content_template: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Configurações visuais (para email)
    html_template: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    css_styles: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Variáveis disponíveis
    available_variables: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
      # Configurações
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)  # Template do sistema
    
    # Metadados
    template_metadata: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)


class NotificationPreference(BaseModel, TimestampMixin):
    """Preferências de notificação do usuário"""
    
    __tablename__ = "notification_preferences"
    
    user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        nullable=False,
        unique=True
    )
    
    # Preferências por tipo
    info_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    success_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    warning_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    error_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    reminder_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    invitation_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    approval_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    mention_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    system_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Preferências por canal
    in_app_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    sms_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Configurações de digest
    digest_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    digest_frequency: Mapped[str] = mapped_column(String(20), default="daily")  # hourly, daily, weekly
    digest_time: Mapped[str] = mapped_column(String(5), default="09:00")  # HH:MM
    
    # Horários de silêncio
    quiet_hours_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    quiet_start_time: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)  # HH:MM
    quiet_end_time: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)    # HH:MM
    
    # Configurações avançadas
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    language: Mapped[str] = mapped_column(String(10), default="pt-BR")
    
    # Metadados
    custom_settings: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)


class NotificationDigest(BaseModel, TimestampMixin):
    """Digest de notificações"""
    
    __tablename__ = "notification_digests"
    
    user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        nullable=False
    )
    
    # Período do digest
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    frequency: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Conteúdo
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    html_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Estatísticas
    notification_count: Mapped[int] = mapped_column(Integer, default=0)
    unread_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Status
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # IDs das notificações incluídas
    notification_ids: Mapped[List[UUID]] = mapped_column(JSON, default=list)


class WebhookEndpoint(BaseModel, TimestampMixin):
    """Endpoint de webhook para notificações"""
    
    __tablename__ = "webhook_endpoints"
    
    # Relacionamentos
    company_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        nullable=False
    )
    created_by: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        nullable=False
    )
    
    # Configuração do webhook
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Autenticação
    auth_type: Mapped[str] = mapped_column(String(50), default="none")  # none, bearer, basic, custom
    auth_config: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    
    # Configurações
    headers: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=30)
    retry_count: Mapped[int] = mapped_column(Integer, default=3)
    
    # Filtros
    event_types: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)  # Tipos de eventos para enviar
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Estatísticas
    total_calls: Mapped[int] = mapped_column(Integer, default=0)
    successful_calls: Mapped[int] = mapped_column(Integer, default=0)
    failed_calls: Mapped[int] = mapped_column(Integer, default=0)
    last_called_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relacionamentos
    deliveries = relationship("WebhookDelivery", back_populates="endpoint", cascade="all, delete-orphan")


class WebhookDelivery(BaseModel, TimestampMixin):
    """Entrega de webhook"""
    
    __tablename__ = "webhook_deliveries"
    
    endpoint_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("webhook_endpoints.id"),
        nullable=False
    )
    notification_id: Mapped[Optional[UUID]] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("notifications.id"),
        nullable=True
    )
    
    # Dados da entrega
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # Status da entrega
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, sent, failed
    
    # Tentativas
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    
    # Resposta
    response_status: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    response_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    response_headers: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Datas
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Erro
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relacionamentos
    endpoint = relationship("WebhookEndpoint", back_populates="deliveries")


class DeviceToken(BaseModel, TimestampMixin):
    """Token de dispositivo para push notifications"""
    
    __tablename__ = "device_tokens"
    
    user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        nullable=False
    )
    
    # Token e plataforma
    token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)  # ios, android, web
    
    # Informações do dispositivo
    device_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    device_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    app_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    os_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
      # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Metadados
    webhook_metadata: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)


class NotificationAnalytics(BaseModel, TimestampMixin):
    """Analytics de notificações"""
    
    __tablename__ = "notification_analytics"
    
    # Relacionamento
    company_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=False
    )
    
    # Período da análise
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_type: Mapped[str] = mapped_column(String(20), nullable=False)  # hourly, daily, weekly, monthly
    
    # Métricas gerais
    total_sent: Mapped[int] = mapped_column(Integer, default=0)
    total_delivered: Mapped[int] = mapped_column(Integer, default=0)
    total_read: Mapped[int] = mapped_column(Integer, default=0)
    total_failed: Mapped[int] = mapped_column(Integer, default=0)
    
    # Métricas por canal
    email_sent: Mapped[int] = mapped_column(Integer, default=0)
    email_delivered: Mapped[int] = mapped_column(Integer, default=0)
    email_opened: Mapped[int] = mapped_column(Integer, default=0)
    email_clicked: Mapped[int] = mapped_column(Integer, default=0)
    
    push_sent: Mapped[int] = mapped_column(Integer, default=0)
    push_delivered: Mapped[int] = mapped_column(Integer, default=0)
    push_opened: Mapped[int] = mapped_column(Integer, default=0)
    
    sms_sent: Mapped[int] = mapped_column(Integer, default=0)
    sms_delivered: Mapped[int] = mapped_column(Integer, default=0)
    
    # Taxas calculadas
    delivery_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    open_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    click_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Métricas avançadas
    avg_delivery_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # segundos
    avg_read_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)     # segundos
    bounce_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Dados detalhados
    detailed_metrics: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)


class SmartNotificationRule(BaseModel, TimestampMixin, UserTrackingMixin):
    """Regras inteligentes para notificações baseadas em IA"""
    
    __tablename__ = "smart_notification_rules"
    
    # Relacionamento
    company_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=False
    )
    
    # Configuração da regra
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Condições para ativação
    trigger_conditions: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    # Configurações de IA
    ai_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    ai_model_config: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    personalization_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Configurações de timing
    optimal_timing_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    timezone_aware: Mapped[bool] = mapped_column(Boolean, default=True)
    respect_quiet_hours: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Configurações de conteúdo
    dynamic_content: Mapped[bool] = mapped_column(Boolean, default=False)
    content_templates: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    
    # Configurações de canal
    smart_channel_selection: Mapped[bool] = mapped_column(Boolean, default=True)
    fallback_channels: Mapped[Optional[List[str]]] = mapped_column(JSONB, default=list)
    
    # Estado e controle
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=5)  # 1-10
    
    # Métricas
    execution_count: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    last_executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Dados de performance
    effectiveness_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    user_engagement_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


class NotificationAIInsight(BaseModel, TimestampMixin):
    """Insights de IA sobre notificações"""
    
    __tablename__ = "notification_ai_insights"
    
    # Relacionamento
    company_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=False
    )
    
    # Período da análise
    analysis_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    analysis_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Tipo de insight
    insight_type: Mapped[str] = mapped_column(String(50), nullable=False)  # performance, engagement, optimization
    insight_category: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Conteúdo do insight
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Dados e métricas
    metrics: Mapped[dict] = mapped_column(JSONB, nullable=False)
    recommendations: Mapped[List[dict]] = mapped_column(JSONB, default=list)
    
    # Scores
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0-1
    impact_score: Mapped[float] = mapped_column(Float, nullable=False)      # 0-1
    urgency_score: Mapped[float] = mapped_column(Float, nullable=False)     # 0-1
    
    # Estado
    is_actionable: Mapped[bool] = mapped_column(Boolean, default=True)
    is_implemented: Mapped[bool] = mapped_column(Boolean, default=False)
    implemented_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Metadados
    ai_model_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    analysis_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)


class NotificationABTest(BaseModel, TimestampMixin, UserTrackingMixin):
    """Testes A/B para notificações"""
    
    __tablename__ = "notification_ab_tests"
    
    # Relacionamento
    company_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=False
    )
    
    # Configuração do teste
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hypothesis: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Configurações das variantes
    control_config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    variant_configs: Mapped[List[dict]] = mapped_column(JSONB, nullable=False)
    
    # Configurações do teste
    traffic_allocation: Mapped[dict] = mapped_column(JSONB, nullable=False)  # % para cada variante
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence_level: Mapped[float] = mapped_column(Float, default=0.95)
    
    # Critérios de sucesso
    primary_metric: Mapped[str] = mapped_column(String(100), nullable=False)
    secondary_metrics: Mapped[Optional[List[str]]] = mapped_column(JSONB, default=list)
    success_criteria: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    # Período do teste
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Estado
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft, running, paused, completed, cancelled
    
    # Resultados
    current_results: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    final_results: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    winning_variant: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    statistical_significance: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Métricas de participação
    total_participants: Mapped[int] = mapped_column(Integer, default=0)
    control_participants: Mapped[int] = mapped_column(Integer, default=0)
    variant_participants: Mapped[dict] = mapped_column(JSONB, default=dict)


class UserNotificationScore(BaseModel, TimestampMixin):
    """Score de engajamento do usuário com notificações"""
    
    __tablename__ = "user_notification_scores"
    
    # Relacionamento
    user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        unique=True
    )
    
    # Scores de engajamento
    overall_engagement_score: Mapped[float] = mapped_column(Float, default=0.5)  # 0-1
    email_engagement_score: Mapped[float] = mapped_column(Float, default=0.5)
    push_engagement_score: Mapped[float] = mapped_column(Float, default=0.5)
    in_app_engagement_score: Mapped[float] = mapped_column(Float, default=0.5)
    
    # Padrões de comportamento
    preferred_time_slots: Mapped[Optional[List[str]]] = mapped_column(JSONB, default=list)  # horários preferenciais
    preferred_channels: Mapped[Optional[List[str]]] = mapped_column(JSONB, default=list)
    preferred_frequency: Mapped[str] = mapped_column(String(20), default="medium")  # low, medium, high
    
    # Estatísticas
    total_received: Mapped[int] = mapped_column(Integer, default=0)
    total_opened: Mapped[int] = mapped_column(Integer, default=0)
    total_clicked: Mapped[int] = mapped_column(Integer, default=0)
    total_unsubscribed: Mapped[int] = mapped_column(Integer, default=0)
    
    # Métricas calculadas
    open_rate: Mapped[float] = mapped_column(Float, default=0.0)
    click_rate: Mapped[float] = mapped_column(Float, default=0.0)
    avg_response_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # segundos
    
    # Última atualização e cálculo
    last_calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    calculation_period_days: Mapped[int] = mapped_column(Integer, default=30)
