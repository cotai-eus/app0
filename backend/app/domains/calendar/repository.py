"""
Repository do domínio Calendar
"""

from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, func, text, desc, asc, and_, or_, between
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.sql import Select

from app.domains.calendar.models import (
    Calendar, Event, EventAttendee, EventReminder, EventAttachment,
    CalendarShare, AvailabilitySlot, EventStatus, EventPriority,
    AttendeeStatus, CalendarType, AvailabilityType
)
from app.shared.common.base_repository import BaseRepository


class CalendarRepository(BaseRepository[Calendar]):
    """Repository para Calendar"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Calendar, session)
    
    async def get_by_owner_id(self, owner_id: UUID) -> List[Calendar]:
        """Busca calendários por proprietário"""
        query = (
            select(Calendar)
            .where(Calendar.owner_id == owner_id)
            .order_by(Calendar.name)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_shared_calendars(self, user_id: UUID) -> List[Calendar]:
        """Busca calendários compartilhados com o usuário"""
        query = (
            select(Calendar)
            .join(CalendarShare)
            .where(CalendarShare.user_id == user_id)
            .order_by(Calendar.name)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_public_calendars(self, limit: int = 50) -> List[Calendar]:
        """Busca calendários públicos"""
        query = (
            select(Calendar)
            .where(Calendar.is_public == True)
            .order_by(Calendar.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def search_calendars(
        self, 
        search_term: str,
        calendar_type: Optional[CalendarType] = None,
        user_id: Optional[UUID] = None
    ) -> List[Calendar]:
        """Busca calendários por termo"""
        query = (
            select(Calendar)
            .where(
                or_(
                    Calendar.name.ilike(f"%{search_term}%"),
                    Calendar.description.ilike(f"%{search_term}%")
                )
            )
        )
        
        if calendar_type:
            query = query.where(Calendar.calendar_type == calendar_type)
        
        if user_id:
            # Incluir calendários próprios e compartilhados
            query = query.where(
                or_(
                    Calendar.owner_id == user_id,
                    Calendar.is_public == True,
                    Calendar.id.in_(
                        select(CalendarShare.calendar_id)
                        .where(CalendarShare.user_id == user_id)
                    )
                )
            )
        
        result = await self.session.execute(query)
        return result.scalars().all()


class EventRepository(BaseRepository[Event]):
    """Repository para Event"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Event, session)
    
    async def get_by_calendar_id(
        self, 
        calendar_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[EventStatus] = None
    ) -> List[Event]:
        """Busca eventos por calendário"""
        query = select(Event).where(Event.calendar_id == calendar_id)
        
        if start_date:
            query = query.where(Event.end_datetime >= start_date)
        
        if end_date:
            query = query.where(Event.start_datetime <= end_date)
        
        if status:
            query = query.where(Event.status == status)
        
        query = query.order_by(Event.start_datetime)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_events_in_range(
        self, 
        start_date: datetime,
        end_date: datetime,
        calendar_ids: Optional[List[UUID]] = None,
        user_id: Optional[UUID] = None,
        include_private: bool = False
    ) -> List[Event]:
        """Busca eventos em um período"""
        query = (
            select(Event)
            .where(
                and_(
                    Event.start_datetime <= end_date,
                    Event.end_datetime >= start_date
                )
            )
        )
        
        if calendar_ids:
            query = query.where(Event.calendar_id.in_(calendar_ids))
        
        if user_id and not include_private:
            # Excluir eventos privados que não são do usuário
            query = query.where(
                or_(
                    Event.is_private == False,
                    Event.created_by == user_id
                )
            )
        
        query = query.order_by(Event.start_datetime)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_with_details(self, event_id: UUID) -> Optional[Event]:
        """Busca evento com detalhes completos"""
        query = (
            select(Event)
            .options(
                selectinload(Event.attendees),
                selectinload(Event.reminders),
                selectinload(Event.attachments)
            )
            .where(Event.id == event_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_recurring_events(
        self, 
        parent_event_id: UUID
    ) -> List[Event]:
        """Busca instâncias de evento recorrente"""
        query = (
            select(Event)
            .where(Event.parent_event_id == parent_event_id)
            .order_by(Event.start_datetime)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_user_events(
        self, 
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[EventStatus] = None
    ) -> List[Event]:
        """Busca eventos do usuário (como criador ou participante)"""
        # Eventos criados pelo usuário
        created_query = select(Event).where(Event.created_by == user_id)
        
        # Eventos onde é participante
        attendee_query = (
            select(Event)
            .join(EventAttendee)
            .where(EventAttendee.user_id == user_id)
        )
        
        # Combinar as queries
        query = created_query.union(attendee_query)
        
        if start_date:
            query = query.where(Event.end_datetime >= start_date)
        
        if end_date:
            query = query.where(Event.start_datetime <= end_date)
        
        if status:
            query = query.where(Event.status == status)
        
        query = query.order_by(Event.start_datetime)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_upcoming_events(
        self, 
        user_id: UUID,
        days_ahead: int = 7,
        limit: int = 10
    ) -> List[Event]:
        """Busca próximos eventos do usuário"""
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=days_ahead)
        
        events = await self.get_user_events(
            user_id, 
            start_date, 
            end_date, 
            EventStatus.CONFIRMED
        )
        
        return events[:limit]
    
    async def check_conflicts(
        self, 
        calendar_id: UUID,
        start_datetime: datetime,
        end_datetime: datetime,
        exclude_event_id: Optional[UUID] = None
    ) -> List[Event]:
        """Verifica conflitos de horário"""
        query = (
            select(Event)
            .where(
                and_(
                    Event.calendar_id == calendar_id,
                    Event.status == EventStatus.CONFIRMED,
                    Event.start_datetime < end_datetime,
                    Event.end_datetime > start_datetime
                )
            )
        )
        
        if exclude_event_id:
            query = query.where(Event.id != exclude_event_id)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_events_analytics(
        self, 
        calendar_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Análise de eventos do calendário"""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Eventos por status
        status_query = (
            select(Event.status, func.count(Event.id).label('count'))
            .where(
                and_(
                    Event.calendar_id == calendar_id,
                    Event.start_datetime >= start_date,
                    Event.start_datetime <= end_date
                )
            )
            .group_by(Event.status)
        )
        status_result = await self.session.execute(status_query)
        status_counts = {row[0]: row[1] for row in status_result}
        
        # Eventos por prioridade
        priority_query = (
            select(Event.priority, func.count(Event.id).label('count'))
            .where(
                and_(
                    Event.calendar_id == calendar_id,
                    Event.start_datetime >= start_date,
                    Event.start_datetime <= end_date
                )
            )
            .group_by(Event.priority)
        )
        priority_result = await self.session.execute(priority_query)
        priority_counts = {row[0]: row[1] for row in priority_result}
        
        # Duração média dos eventos
        duration_query = (
            select(
                func.avg(
                    func.extract('epoch', Event.end_datetime - Event.start_datetime) / 3600
                ).label('avg_hours')
            )
            .where(
                and_(
                    Event.calendar_id == calendar_id,
                    Event.start_datetime >= start_date,
                    Event.start_datetime <= end_date
                )
            )
        )
        duration_result = await self.session.execute(duration_query)
        avg_duration_hours = duration_result.scalar() or 0
        
        # Dia mais ocupado
        busiest_day_query = (
            select(
                func.date_trunc('day', Event.start_datetime).label('day'),
                func.count(Event.id).label('count')
            )
            .where(
                and_(
                    Event.calendar_id == calendar_id,
                    Event.start_datetime >= start_date,
                    Event.start_datetime <= end_date
                )
            )
            .group_by(func.date_trunc('day', Event.start_datetime))
            .order_by(desc('count'))
            .limit(1)
        )
        busiest_day_result = await self.session.execute(busiest_day_query)
        busiest_day_row = busiest_day_result.first()
        busiest_day = busiest_day_row[0].strftime('%Y-%m-%d') if busiest_day_row else None
        
        return {
            "status_distribution": status_counts,
            "priority_distribution": priority_counts,
            "average_duration_hours": round(avg_duration_hours, 2),
            "busiest_day": busiest_day,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }


class EventAttendeeRepository(BaseRepository[EventAttendee]):
    """Repository para EventAttendee"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(EventAttendee, session)
    
    async def get_by_event_id(self, event_id: UUID) -> List[EventAttendee]:
        """Busca participantes por evento"""
        query = (
            select(EventAttendee)
            .where(EventAttendee.event_id == event_id)
            .order_by(EventAttendee.created_at)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_user_id(
        self, 
        user_id: UUID,
        status: Optional[AttendeeStatus] = None
    ) -> List[EventAttendee]:
        """Busca eventos do usuário como participante"""
        query = select(EventAttendee).where(EventAttendee.user_id == user_id)
        
        if status:
            query = query.where(EventAttendee.status == status)
        
        query = query.order_by(EventAttendee.created_at.desc())
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_email(self, email: str) -> List[EventAttendee]:
        """Busca participações por email"""
        query = (
            select(EventAttendee)
            .where(EventAttendee.email == email)
            .order_by(EventAttendee.created_at.desc())
        )
        result = await self.session.execute(query)
        return result.scalars().all()


class EventReminderRepository(BaseRepository[EventReminder]):
    """Repository para EventReminder"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(EventReminder, session)
    
    async def get_by_event_id(self, event_id: UUID) -> List[EventReminder]:
        """Busca lembretes por evento"""
        query = (
            select(EventReminder)
            .where(EventReminder.event_id == event_id)
            .order_by(EventReminder.minutes_before)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_pending_reminders(
        self, 
        check_time: Optional[datetime] = None
    ) -> List[EventReminder]:
        """Busca lembretes pendentes"""
        if not check_time:
            check_time = datetime.utcnow()
        
        # Subquery para buscar eventos que precisam de lembrete
        events_subquery = (
            select(Event.id, Event.start_datetime)
            .where(Event.status == EventStatus.CONFIRMED)
            .subquery()
        )
        
        query = (
            select(EventReminder)
            .join(events_subquery, EventReminder.event_id == events_subquery.c.id)
            .where(
                and_(
                    EventReminder.is_sent == False,
                    events_subquery.c.start_datetime - func.interval(f'{EventReminder.minutes_before} minutes') <= check_time
                )
            )
        )
        
        result = await self.session.execute(query)
        return result.scalars().all()


class CalendarShareRepository(BaseRepository[CalendarShare]):
    """Repository para CalendarShare"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(CalendarShare, session)
    
    async def get_by_calendar_id(self, calendar_id: UUID) -> List[CalendarShare]:
        """Busca compartilhamentos por calendário"""
        query = (
            select(CalendarShare)
            .where(CalendarShare.calendar_id == calendar_id)
            .order_by(CalendarShare.created_at)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_user_id(self, user_id: UUID) -> List[CalendarShare]:
        """Busca calendários compartilhados com o usuário"""
        query = (
            select(CalendarShare)
            .where(CalendarShare.user_id == user_id)
            .order_by(CalendarShare.created_at.desc())
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_permission(
        self, 
        calendar_id: UUID, 
        user_id: UUID
    ) -> Optional[CalendarShare]:
        """Busca permissão específica"""
        query = (
            select(CalendarShare)
            .where(
                and_(
                    CalendarShare.calendar_id == calendar_id,
                    CalendarShare.user_id == user_id
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class AvailabilitySlotRepository(BaseRepository[AvailabilitySlot]):
    """Repository para AvailabilitySlot"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(AvailabilitySlot, session)
    
    async def get_by_calendar_id(self, calendar_id: UUID) -> List[AvailabilitySlot]:
        """Busca slots de disponibilidade por calendário"""
        query = (
            select(AvailabilitySlot)
            .where(AvailabilitySlot.calendar_id == calendar_id)
            .order_by(AvailabilitySlot.day_of_week, AvailabilitySlot.start_time)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_day_of_week(
        self, 
        calendar_id: UUID, 
        day_of_week: int
    ) -> List[AvailabilitySlot]:
        """Busca slots por dia da semana"""
        query = (
            select(AvailabilitySlot)
            .where(
                and_(
                    AvailabilitySlot.calendar_id == calendar_id,
                    AvailabilitySlot.day_of_week == day_of_week
                )
            )
            .order_by(AvailabilitySlot.start_time)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def check_availability(
        self, 
        calendar_id: UUID,
        start_datetime: datetime,
        end_datetime: datetime
    ) -> List[AvailabilitySlot]:
        """Verifica disponibilidade em um período"""
        day_of_week = start_datetime.weekday()  # 0=Monday
        start_time = start_datetime.time()
        end_time = end_datetime.time()
        
        query = (
            select(AvailabilitySlot)
            .where(
                and_(
                    AvailabilitySlot.calendar_id == calendar_id,
                    AvailabilitySlot.day_of_week == day_of_week,
                    AvailabilitySlot.availability_type == AvailabilityType.AVAILABLE,
                    AvailabilitySlot.start_time <= start_time,
                    AvailabilitySlot.end_time >= end_time
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalars().all()
