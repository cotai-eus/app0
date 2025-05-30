"""
Schemas para domínio de Notificações e Comunicação
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, EmailStr

from app.domains.notifications.models import (
    NotificationType, NotificationChannel, NotificationStatus,
    TemplateType, Priority
)


# Base schemas
class NotificationBase(BaseModel):
    """Schema base para notificações"""
    model_config = ConfigDict(from_attributes=True)
    
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1)
    notification_type: NotificationType = NotificationType.INFO
    priority: Priority = Priority.MEDIUM
    channels: List[str] = Field(default_factory=lambda: [NotificationChannel.IN_APP])
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    action_url: Optional[str] = None
    action_label: Optional[str] = Field(None, max_length=100)
    related_object_type: Optional[str] = Field(None, max_length=50)
    related_object_id: Optional[UUID] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    is_persistent: bool = True
    allow_digest: bool = True


class NotificationCreate(NotificationBase):
    """Schema para criação de notificação"""
    recipient_id: UUID
    sender_id: Optional[UUID] = None


class NotificationUpdate(BaseModel):
    """Schema para atualização de notificação"""
    model_config = ConfigDict(from_attributes=True)
    
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    message: Optional[str] = Field(None, min_length=1)
    notification_type: Optional[NotificationType] = None
    priority: Optional[Priority] = None
    channels: Optional[List[str]] = None
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    action_url: Optional[str] = None
    action_label: Optional[str] = Field(None, max_length=100)
    metadata: Optional[Dict[str, Any]] = None


class NotificationResponse(NotificationBase):
    """Schema de resposta para notificação"""
    id: UUID
    recipient_id: UUID
    sender_id: Optional[UUID] = None
    company_id: UUID
    status: NotificationStatus
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# Notification Delivery schemas
class NotificationDeliveryBase(BaseModel):
    """Schema base para entrega de notificação"""
    model_config = ConfigDict(from_attributes=True)
    
    channel: NotificationChannel
    recipient_address: str = Field(..., max_length=255)
    max_attempts: int = Field(default=3, ge=1, le=10)


class NotificationDeliveryCreate(NotificationDeliveryBase):
    """Schema para criação de entrega"""
    notification_id: UUID


class NotificationDeliveryResponse(NotificationDeliveryBase):
    """Schema de resposta para entrega"""
    id: UUID
    notification_id: UUID
    status: NotificationStatus
    attempt_count: int
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    next_retry_at: Optional[datetime] = None
    provider_id: Optional[str] = None
    provider_response: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime


# Template schemas
class NotificationTemplateBase(BaseModel):
    """Schema base para template"""
    model_config = ConfigDict(from_attributes=True)
    
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    template_type: TemplateType
    default_channels: List[str] = Field(default_factory=list)
    subject_template: Optional[str] = Field(None, max_length=255)
    content_template: str = Field(..., min_length=1)
    html_template: Optional[str] = None
    css_styles: Optional[str] = None
    available_variables: Optional[List[str]] = Field(default_factory=list)
    is_active: bool = True
    is_system: bool = False
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class NotificationTemplateCreate(NotificationTemplateBase):
    """Schema para criação de template"""
    pass


class NotificationTemplateUpdate(BaseModel):
    """Schema para atualização de template"""
    model_config = ConfigDict(from_attributes=True)
    
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    default_channels: Optional[List[str]] = None
    subject_template: Optional[str] = Field(None, max_length=255)
    content_template: Optional[str] = Field(None, min_length=1)
    html_template: Optional[str] = None
    css_styles: Optional[str] = None
    available_variables: Optional[List[str]] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class NotificationTemplateResponse(NotificationTemplateBase):
    """Schema de resposta para template"""
    id: UUID
    company_id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: datetime


# Preferences schemas
class NotificationPreferenceBase(BaseModel):
    """Schema base para preferências"""
    model_config = ConfigDict(from_attributes=True)
    
    # Preferências por tipo
    info_enabled: bool = True
    success_enabled: bool = True
    warning_enabled: bool = True
    error_enabled: bool = True
    reminder_enabled: bool = True
    invitation_enabled: bool = True
    approval_enabled: bool = True
    mention_enabled: bool = True
    system_enabled: bool = True
    
    # Preferências por canal
    in_app_enabled: bool = True
    email_enabled: bool = True
    sms_enabled: bool = False
    push_enabled: bool = True
    
    # Configurações de digest
    digest_enabled: bool = True
    digest_frequency: str = Field(default="daily", max_length=20)
    digest_time: str = Field(default="09:00", max_length=5)
    
    # Horários de silêncio
    quiet_hours_enabled: bool = False
    quiet_start_time: Optional[str] = Field(None, max_length=5)
    quiet_end_time: Optional[str] = Field(None, max_length=5)
    
    # Configurações avançadas
    timezone: str = Field(default="UTC", max_length=50)
    language: str = Field(default="pt-BR", max_length=10)
    custom_settings: Optional[Dict[str, Any]] = Field(default_factory=dict)


class NotificationPreferenceCreate(NotificationPreferenceBase):
    """Schema para criação de preferências"""
    user_id: UUID


class NotificationPreferenceUpdate(NotificationPreferenceBase):
    """Schema para atualização de preferências"""
    pass


class NotificationPreferenceResponse(NotificationPreferenceBase):
    """Schema de resposta para preferências"""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime


# Digest schemas
class NotificationDigestResponse(BaseModel):
    """Schema de resposta para digest"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    user_id: UUID
    period_start: datetime
    period_end: datetime
    frequency: str
    title: str
    content: str
    html_content: Optional[str] = None
    notification_count: int
    unread_count: int
    is_sent: bool
    sent_at: Optional[datetime] = None
    notification_ids: List[UUID]
    created_at: datetime


# Webhook schemas
class WebhookEndpointBase(BaseModel):
    """Schema base para webhook"""
    model_config = ConfigDict(from_attributes=True)
    
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    url: str = Field(..., min_length=1)
    auth_type: str = Field(default="none", max_length=50)
    auth_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    headers: Optional[Dict[str, Any]] = Field(default_factory=dict)
    timeout_seconds: int = Field(default=30, ge=1, le=300)
    retry_count: int = Field(default=3, ge=0, le=10)
    event_types: Optional[List[str]] = Field(default_factory=list)
    is_active: bool = True


class WebhookEndpointCreate(WebhookEndpointBase):
    """Schema para criação de webhook"""
    pass


class WebhookEndpointUpdate(BaseModel):
    """Schema para atualização de webhook"""
    model_config = ConfigDict(from_attributes=True)
    
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    url: Optional[str] = Field(None, min_length=1)
    auth_type: Optional[str] = Field(None, max_length=50)
    auth_config: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, Any]] = None
    timeout_seconds: Optional[int] = Field(None, ge=1, le=300)
    retry_count: Optional[int] = Field(None, ge=0, le=10)
    event_types: Optional[List[str]] = None
    is_active: Optional[bool] = None


class WebhookEndpointResponse(WebhookEndpointBase):
    """Schema de resposta para webhook"""
    id: UUID
    company_id: UUID
    created_by: UUID
    total_calls: int
    successful_calls: int
    failed_calls: int
    last_called_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class WebhookDeliveryResponse(BaseModel):
    """Schema de resposta para entrega de webhook"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    endpoint_id: UUID
    notification_id: Optional[UUID] = None
    event_type: str
    payload: Dict[str, Any]
    status: str
    attempt_count: int
    max_attempts: int
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    response_headers: Optional[Dict[str, Any]] = None
    sent_at: Optional[datetime] = None
    next_retry_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime


# Device Token schemas
class DeviceTokenBase(BaseModel):
    """Schema base para token de dispositivo"""
    model_config = ConfigDict(from_attributes=True)
    
    token: str = Field(..., min_length=1, max_length=255)
    platform: str = Field(..., max_length=20)
    device_id: Optional[str] = Field(None, max_length=255)
    device_name: Optional[str] = Field(None, max_length=200)
    app_version: Optional[str] = Field(None, max_length=50)
    os_version: Optional[str] = Field(None, max_length=50)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class DeviceTokenCreate(DeviceTokenBase):
    """Schema para criação de token"""
    pass


class DeviceTokenUpdate(BaseModel):
    """Schema para atualização de token"""
    model_config = ConfigDict(from_attributes=True)
    
    device_name: Optional[str] = Field(None, max_length=200)
    app_version: Optional[str] = Field(None, max_length=50)
    os_version: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class DeviceTokenResponse(DeviceTokenBase):
    """Schema de resposta para token"""
    id: UUID
    user_id: UUID
    is_active: bool
    last_used_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# Request schemas para operações especiais
class SendNotificationRequest(BaseModel):
    """Schema para envio de notificação"""
    model_config = ConfigDict(from_attributes=True)
    
    template_code: Optional[str] = None
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    message: Optional[str] = Field(None, min_length=1)
    recipient_ids: List[UUID] = Field(..., min_items=1)
    notification_type: NotificationType = NotificationType.INFO
    priority: Priority = Priority.MEDIUM
    channels: List[str] = Field(default_factory=lambda: [NotificationChannel.IN_APP])
    template_variables: Optional[Dict[str, Any]] = Field(default_factory=dict)
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    action_url: Optional[str] = None
    action_label: Optional[str] = Field(None, max_length=100)
    related_object_type: Optional[str] = Field(None, max_length=50)
    related_object_id: Optional[UUID] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SendBulkNotificationRequest(BaseModel):
    """Schema para envio em lote"""
    model_config = ConfigDict(from_attributes=True)
    
    notifications: List[SendNotificationRequest] = Field(..., min_items=1, max_items=1000)
    
    
class MarkAsReadRequest(BaseModel):
    """Schema para marcar como lida"""
    model_config = ConfigDict(from_attributes=True)
    
    notification_ids: List[UUID] = Field(..., min_items=1)


class TestWebhookRequest(BaseModel):
    """Schema para testar webhook"""
    model_config = ConfigDict(from_attributes=True)
    
    test_payload: Optional[Dict[str, Any]] = Field(default_factory=dict)


# Response schemas para operações especiais
class NotificationStatsResponse(BaseModel):
    """Schema para estatísticas de notificações"""
    model_config = ConfigDict(from_attributes=True)
    
    total_notifications: int
    unread_notifications: int
    notifications_by_type: Dict[str, int]
    notifications_by_channel: Dict[str, int]
    recent_notifications: List[NotificationResponse]


class NotificationAnalyticsResponse(BaseModel):
    """Schema para analytics de notificações"""
    model_config = ConfigDict(from_attributes=True)
    
    total_sent: int
    total_delivered: int
    total_read: int
    delivery_rate: float
    read_rate: float
    avg_delivery_time_ms: Optional[float] = None
    channel_stats: Dict[str, Dict[str, Any]]
    trending_notifications: List[Dict[str, Any]]


class WebhookStatsResponse(BaseModel):
    """Schema para estatísticas de webhook"""
    model_config = ConfigDict(from_attributes=True)
    
    total_endpoints: int
    active_endpoints: int
    total_deliveries: int
    successful_deliveries: int
    failed_deliveries: int
    success_rate: float
    avg_response_time_ms: Optional[float] = None


# Response agregada
class NotificationWithDeliveriesResponse(NotificationResponse):
    """Notificação com entregas incluídas"""
    deliveries: List[NotificationDeliveryResponse] = Field(default_factory=list)


class TemplateWithUsageResponse(NotificationTemplateResponse):
    """Template com estatísticas de uso"""
    usage_count: int = 0
    last_used_at: Optional[datetime] = None
