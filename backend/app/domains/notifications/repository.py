"""
Repositórios para domínio de Notificações e Comunicação
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.shared.common.base_repository import BaseRepository
from app.domains.notifications.models import (
    Notification, NotificationDelivery, NotificationTemplate,
    NotificationPreference, NotificationDigest, WebhookEndpoint,
    WebhookDelivery, DeviceToken, NotificationStatus,
    NotificationChannel, NotificationType, Priority
)
from app.domains.notifications.schemas import (
    NotificationCreate, NotificationUpdate, NotificationTemplateCreate,
    NotificationTemplateUpdate, NotificationPreferenceCreate,
    NotificationPreferenceUpdate, WebhookEndpointCreate,
    WebhookEndpointUpdate
)


class NotificationRepository(BaseRepository[Notification]):
    """Repositório para notificações"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Notification, session)
    
    async def get_with_deliveries(self, notification_id: UUID) -> Optional[Notification]:
        """Busca notificação com entregas"""
        result = await self.session.execute(
            select(Notification)
            .options(selectinload(Notification.deliveries))
            .where(Notification.id == notification_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_recipient(
        self,
        recipient_id: UUID,
        skip: int = 0,
        limit: int = 100,
        status: Optional[NotificationStatus] = None,
        notification_type: Optional[NotificationType] = None,
        priority: Optional[Priority] = None,
        unread_only: bool = False
    ) -> List[Notification]:
        """Busca notificações por destinatário"""
        query = select(Notification).where(Notification.recipient_id == recipient_id)
        
        if status:
            query = query.where(Notification.status == status)
        
        if notification_type:
            query = query.where(Notification.notification_type == notification_type)
        
        if priority:
            query = query.where(Notification.priority == priority)
        
        if unread_only:
            query = query.where(Notification.read_at.is_(None))
        
        query = query.order_by(desc(Notification.created_at)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_company(
        self,
        company_id: UUID,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Notification]:
        """Busca notificações por empresa"""
        query = select(Notification).where(Notification.company_id == company_id)
        
        if filters:
            if "status" in filters:
                query = query.where(Notification.status == filters["status"])
            if "notification_type" in filters:
                query = query.where(Notification.notification_type == filters["notification_type"])
            if "priority" in filters:
                query = query.where(Notification.priority == filters["priority"])
            if "date_from" in filters:
                query = query.where(Notification.created_at >= filters["date_from"])
            if "date_to" in filters:
                query = query.where(Notification.created_at <= filters["date_to"])
        
        query = query.order_by(desc(Notification.created_at)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_pending_scheduled(self, before: datetime) -> List[Notification]:
        """Busca notificações agendadas pendentes"""
        result = await self.session.execute(
            select(Notification)
            .where(
                and_(
                    Notification.status == NotificationStatus.PENDING,
                    Notification.scheduled_at.isnot(None),
                    Notification.scheduled_at <= before
                )
            )
            .order_by(asc(Notification.scheduled_at))
        )
        return result.scalars().all()
    
    async def get_expired(self, before: datetime) -> List[Notification]:
        """Busca notificações expiradas"""
        result = await self.session.execute(
            select(Notification)
            .where(
                and_(
                    Notification.expires_at.isnot(None),
                    Notification.expires_at <= before,
                    Notification.status != NotificationStatus.CANCELLED
                )
            )
        )
        return result.scalars().all()
    
    async def mark_as_read(self, notification_id: UUID) -> bool:
        """Marca notificação como lida"""
        notification = await self.get(notification_id)
        if notification and notification.read_at is None:
            notification.read_at = datetime.utcnow()
            notification.status = NotificationStatus.READ
            await self.session.flush()
            return True
        return False
    
    async def mark_multiple_as_read(self, notification_ids: List[UUID]) -> int:
        """Marca múltiplas notificações como lidas"""
        from sqlalchemy import update
        
        result = await self.session.execute(
            update(Notification)
            .where(
                and_(
                    Notification.id.in_(notification_ids),
                    Notification.read_at.is_(None)
                )
            )
            .values(
                read_at=datetime.utcnow(),
                status=NotificationStatus.READ
            )
        )
        return result.rowcount or 0
    
    async def count_unread_by_recipient(self, recipient_id: UUID) -> int:
        """Conta notificações não lidas por destinatário"""
        result = await self.session.execute(
            select(func.count(Notification.id))
            .where(
                and_(
                    Notification.recipient_id == recipient_id,
                    Notification.read_at.is_(None)
                )
            )
        )
        return result.scalar() or 0
    
    async def get_for_digest(
        self,
        recipient_id: UUID,
        period_start: datetime,
        period_end: datetime
    ) -> List[Notification]:
        """Busca notificações para digest"""
        result = await self.session.execute(
            select(Notification)
            .where(
                and_(
                    Notification.recipient_id == recipient_id,
                    Notification.allow_digest == True,
                    Notification.created_at >= period_start,
                    Notification.created_at <= period_end
                )
            )
            .order_by(desc(Notification.created_at))
        )
        return result.scalars().all()


class NotificationDeliveryRepository(BaseRepository[NotificationDelivery]):
    """Repositório para entregas de notificação"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(NotificationDelivery, session)
    
    async def get_by_notification(self, notification_id: UUID) -> List[NotificationDelivery]:
        """Busca entregas por notificação"""
        result = await self.session.execute(
            select(NotificationDelivery)
            .where(NotificationDelivery.notification_id == notification_id)
            .order_by(desc(NotificationDelivery.created_at))
        )
        return result.scalars().all()
    
    async def get_failed_for_retry(self, before: datetime) -> List[NotificationDelivery]:
        """Busca entregas falhadas para tentar novamente"""
        result = await self.session.execute(
            select(NotificationDelivery)
            .where(
                and_(
                    NotificationDelivery.status == NotificationStatus.FAILED,
                    NotificationDelivery.attempt_count < NotificationDelivery.max_attempts,
                    NotificationDelivery.next_retry_at <= before
                )
            )
            .order_by(asc(NotificationDelivery.next_retry_at))
        )
        return result.scalars().all()
    
    async def get_by_channel(
        self,
        channel: NotificationChannel,
        status: Optional[NotificationStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[NotificationDelivery]:
        """Busca entregas por canal"""
        query = select(NotificationDelivery).where(NotificationDelivery.channel == channel)
        
        if status:
            query = query.where(NotificationDelivery.status == status)
        
        query = query.order_by(desc(NotificationDelivery.created_at)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()


class NotificationTemplateRepository(BaseRepository[NotificationTemplate]):
    """Repositório para templates de notificação"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(NotificationTemplate, session)
    
    async def get_by_code(self, code: str) -> Optional[NotificationTemplate]:
        """Busca template por código"""
        result = await self.session.execute(
            select(NotificationTemplate).where(NotificationTemplate.code == code)
        )
        return result.scalar_one_or_none()
    
    async def get_by_company(
        self,
        company_id: UUID,
        template_type: Optional[str] = None,
        is_active: Optional[bool] = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[NotificationTemplate]:
        """Busca templates por empresa"""
        query = select(NotificationTemplate).where(NotificationTemplate.company_id == company_id)
        
        if template_type:
            query = query.where(NotificationTemplate.template_type == template_type)
        
        if is_active is not None:
            query = query.where(NotificationTemplate.is_active == is_active)
        
        query = query.order_by(desc(NotificationTemplate.created_at)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_system_templates(
        self,
        template_type: Optional[str] = None,
        is_active: bool = True
    ) -> List[NotificationTemplate]:
        """Busca templates do sistema"""
        query = select(NotificationTemplate).where(NotificationTemplate.is_system == True)
        
        if template_type:
            query = query.where(NotificationTemplate.template_type == template_type)
        
        if is_active is not None:
            query = query.where(NotificationTemplate.is_active == is_active)
        
        result = await self.session.execute(query)
        return result.scalars().all()


class NotificationPreferenceRepository(BaseRepository[NotificationPreference]):
    """Repositório para preferências de notificação"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(NotificationPreference, session)
    
    async def get_by_user(self, user_id: UUID) -> Optional[NotificationPreference]:
        """Busca preferências por usuário"""
        result = await self.session.execute(
            select(NotificationPreference).where(NotificationPreference.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def create_default_preferences(self, user_id: UUID) -> NotificationPreference:
        """Cria preferências padrão para usuário"""
        preferences = NotificationPreference(user_id=user_id)
        self.session.add(preferences)
        await self.session.flush()
        await self.session.refresh(preferences)
        return preferences
    
    async def get_users_for_digest(
        self,
        frequency: str,
        current_time: str
    ) -> List[NotificationPreference]:
        """Busca usuários que devem receber digest"""
        result = await self.session.execute(
            select(NotificationPreference)
            .where(
                and_(
                    NotificationPreference.digest_enabled == True,
                    NotificationPreference.digest_frequency == frequency,
                    NotificationPreference.digest_time == current_time
                )
            )
        )
        return result.scalars().all()


class WebhookEndpointRepository(BaseRepository[WebhookEndpoint]):
    """Repositório para endpoints de webhook"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(WebhookEndpoint, session)
    
    async def get_by_company(
        self,
        company_id: UUID,
        is_active: Optional[bool] = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[WebhookEndpoint]:
        """Busca webhooks por empresa"""
        query = select(WebhookEndpoint).where(WebhookEndpoint.company_id == company_id)
        
        if is_active is not None:
            query = query.where(WebhookEndpoint.is_active == is_active)
        
        query = query.order_by(desc(WebhookEndpoint.created_at)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_active_for_event(self, event_type: str) -> List[WebhookEndpoint]:
        """Busca webhooks ativos para tipo de evento"""
        result = await self.session.execute(
            select(WebhookEndpoint)
            .where(
                and_(
                    WebhookEndpoint.is_active == True,
                    or_(
                        WebhookEndpoint.event_types.is_(None),
                        func.json_array_length(WebhookEndpoint.event_types) == 0,
                        WebhookEndpoint.event_types.contains([event_type])
                    )
                )
            )
        )
        return result.scalars().all()


class WebhookDeliveryRepository(BaseRepository[WebhookDelivery]):
    """Repositório para entregas de webhook"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(WebhookDelivery, session)
    
    async def get_by_endpoint(
        self,
        endpoint_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[WebhookDelivery]:
        """Busca entregas por endpoint"""
        result = await self.session.execute(
            select(WebhookDelivery)
            .where(WebhookDelivery.endpoint_id == endpoint_id)
            .order_by(desc(WebhookDelivery.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_failed_for_retry(self, before: datetime) -> List[WebhookDelivery]:
        """Busca entregas falhadas para tentar novamente"""
        result = await self.session.execute(
            select(WebhookDelivery)
            .where(
                and_(
                    WebhookDelivery.status == "failed",
                    WebhookDelivery.attempt_count < WebhookDelivery.max_attempts,
                    WebhookDelivery.next_retry_at <= before
                )
            )
            .order_by(asc(WebhookDelivery.next_retry_at))
        )
        return result.scalars().all()


class DeviceTokenRepository(BaseRepository[DeviceToken]):
    """Repositório para tokens de dispositivo"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(DeviceToken, session)
    
    async def get_by_user(
        self,
        user_id: UUID,
        platform: Optional[str] = None,
        is_active: bool = True
    ) -> List[DeviceToken]:
        """Busca tokens por usuário"""
        query = select(DeviceToken).where(DeviceToken.user_id == user_id)
        
        if platform:
            query = query.where(DeviceToken.platform == platform)
        
        if is_active is not None:
            query = query.where(DeviceToken.is_active == is_active)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_token(self, token: str) -> Optional[DeviceToken]:
        """Busca token específico"""
        result = await self.session.execute(
            select(DeviceToken).where(DeviceToken.token == token)
        )
        return result.scalar_one_or_none()
    
    async def deactivate_old_tokens(
        self,
        user_id: UUID,
        platform: str,
        keep_token: str
    ) -> int:
        """Desativa tokens antigos do usuário na plataforma, exceto o especificado"""
        from sqlalchemy import update
        
        result = await self.session.execute(
            update(DeviceToken)
            .where(
                and_(
                    DeviceToken.user_id == user_id,
                    DeviceToken.platform == platform,
                    DeviceToken.token != keep_token
                )
            )
            .values(is_active=False)
        )
        return result.rowcount or 0


class NotificationDigestRepository(BaseRepository[NotificationDigest]):
    """Repositório para digests de notificação"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(NotificationDigest, session)
    
    async def get_by_user(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[NotificationDigest]:
        """Busca digests por usuário"""
        result = await self.session.execute(
            select(NotificationDigest)
            .where(NotificationDigest.user_id == user_id)
            .order_by(desc(NotificationDigest.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_pending_to_send(self) -> List[NotificationDigest]:
        """Busca digests pendentes de envio"""
        result = await self.session.execute(
            select(NotificationDigest)
            .where(NotificationDigest.is_sent == False)
            .order_by(asc(NotificationDigest.created_at))
        )
        return result.scalars().all()
