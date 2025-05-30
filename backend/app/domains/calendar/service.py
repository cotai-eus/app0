"""
Service do domínio Calendar
"""

import uuid
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.domains.calendar.models import (
    Calendar, Event, EventAttendee, EventReminder, EventAttachment,
    CalendarShare, AvailabilitySlot, EventStatus, EventPriority,
    AttendeeStatus, CalendarType, AvailabilityType, RecurrenceType
)
from app.domains.calendar.repository import (
    CalendarRepository, EventRepository, EventAttendeeRepository,
    EventReminderRepository, CalendarShareRepository, AvailabilitySlotRepository
)
from app.domains.calendar.schemas import (
    CalendarCreate, CalendarUpdate, EventCreate, EventUpdate,
    EventAttendeeCreate, EventAttendeeUpdate, EventReminderCreate,
    CalendarShareCreate, CalendarShareUpdate, AvailabilitySlotCreate,
    AvailabilitySlotUpdate, BookingRequest
)
from app.shared.common.exceptions import (
    NotFoundException, ValidationException, 
    PermissionDeniedException, ConflictException
)


class CalendarService:
    """Service para Calendar"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = CalendarRepository(session)
        self.share_repository = CalendarShareRepository(session)
    
    async def create_calendar(
        self, 
        calendar_data: CalendarCreate, 
        user_id: UUID
    ) -> Calendar:
        """Cria um novo calendário"""
        calendar = Calendar(
            **calendar_data.model_dump(),
            owner_id=user_id
        )
        
        return await self.repository.create(calendar)
    
    async def get_calendar(self, calendar_id: UUID, user_id: UUID) -> Calendar:
        """Busca calendário por ID"""
        calendar = await self.repository.get_by_id(calendar_id)
        if not calendar:
            raise NotFoundException("Calendário não encontrado")
        
        # Verificar permissão
        await self._check_calendar_access(calendar_id, user_id)
        
        return calendar
    
    async def update_calendar(
        self, 
        calendar_id: UUID, 
        calendar_data: CalendarUpdate, 
        user_id: UUID
    ) -> Calendar:
        """Atualiza calendário"""
        await self._check_calendar_permission(
            calendar_id, 
            user_id, 
            require_owner=True
        )
        
        calendar = await self.repository.get_by_id(calendar_id)
        if not calendar:
            raise NotFoundException("Calendário não encontrado")
        
        update_data = calendar_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(calendar, field, value)
        
        return await self.repository.update(calendar)
    
    async def delete_calendar(self, calendar_id: UUID, user_id: UUID) -> None:
        """Remove calendário"""
        await self._check_calendar_permission(
            calendar_id, 
            user_id, 
            require_owner=True
        )
        
        calendar = await self.repository.get_by_id(calendar_id)
        if not calendar:
            raise NotFoundException("Calendário não encontrado")
        
        await self.repository.delete(calendar)
    
    async def get_user_calendars(self, user_id: UUID) -> List[Calendar]:
        """Busca calendários do usuário (próprios + compartilhados)"""
        owned = await self.repository.get_by_owner_id(user_id)
        shared = await self.repository.get_shared_calendars(user_id)
        
        # Remover duplicatas
        calendars = {cal.id: cal for cal in owned + shared}
        return list(calendars.values())
    
    async def search_calendars(
        self, 
        search_term: str,
        calendar_type: Optional[CalendarType] = None,
        user_id: Optional[UUID] = None
    ) -> List[Calendar]:
        """Busca calendários por termo"""
        return await self.repository.search_calendars(
            search_term, 
            calendar_type, 
            user_id
        )
    
    async def share_calendar(
        self, 
        calendar_id: UUID, 
        share_data: CalendarShareCreate,
        user_id: UUID
    ) -> CalendarShare:
        """Compartilha calendário com usuário"""
        await self._check_calendar_permission(
            calendar_id, 
            user_id, 
            require_owner=True
        )
        
        # Verificar se já está compartilhado
        existing = await self.share_repository.get_permission(
            calendar_id, 
            share_data.user_id
        )
        if existing:
            raise ConflictException("Calendário já compartilhado com este usuário")
        
        share = CalendarShare(
            **share_data.model_dump(),
            calendar_id=calendar_id,
            shared_by=user_id
        )
        
        return await self.share_repository.create(share)
    
    async def update_calendar_share(
        self, 
        calendar_id: UUID, 
        shared_user_id: UUID,
        share_data: CalendarShareUpdate,
        user_id: UUID
    ) -> CalendarShare:
        """Atualiza permissões de compartilhamento"""
        await self._check_calendar_permission(
            calendar_id, 
            user_id, 
            require_owner=True
        )
        
        share = await self.share_repository.get_permission(
            calendar_id, 
            shared_user_id
        )
        if not share:
            raise NotFoundException("Compartilhamento não encontrado")
        
        update_data = share_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(share, field, value)
        
        return await self.share_repository.update(share)
    
    async def remove_calendar_share(
        self, 
        calendar_id: UUID, 
        shared_user_id: UUID,
        user_id: UUID
    ) -> None:
        """Remove compartilhamento"""
        await self._check_calendar_permission(
            calendar_id, 
            user_id, 
            require_owner=True
        )
        
        share = await self.share_repository.get_permission(
            calendar_id, 
            shared_user_id
        )
        if not share:
            raise NotFoundException("Compartilhamento não encontrado")
        
        await self.share_repository.delete(share)
    
    async def get_calendar_analytics(
        self, 
        calendar_id: UUID, 
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Análise do calendário"""
        await self._check_calendar_access(calendar_id, user_id)
        
        event_repository = EventRepository(self.session)
        return await event_repository.get_events_analytics(
            calendar_id, 
            start_date, 
            end_date
        )
    
    async def _check_calendar_access(self, calendar_id: UUID, user_id: UUID) -> None:
        """Verifica se usuário tem acesso ao calendário"""
        calendar = await self.repository.get_by_id(calendar_id)
        if not calendar:
            raise NotFoundException("Calendário não encontrado")
        
        # Proprietário sempre tem acesso
        if calendar.owner_id == user_id:
            return
        
        # Verificar se é público
        if calendar.is_public:
            return
        
        # Verificar se está compartilhado
        share = await self.share_repository.get_permission(calendar_id, user_id)
        if not share:
            raise PermissionDeniedException("Acesso negado ao calendário")
    
    async def _check_calendar_permission(
        self, 
        calendar_id: UUID, 
        user_id: UUID,
        require_owner: bool = False,
        require_edit: bool = False
    ) -> None:
        """Verifica permissão específica no calendário"""
        calendar = await self.repository.get_by_id(calendar_id)
        if not calendar:
            raise NotFoundException("Calendário não encontrado")
        
        # Proprietário sempre tem todas as permissões
        if calendar.owner_id == user_id:
            return
        
        if require_owner:
            raise PermissionDeniedException(
                "Apenas o proprietário pode realizar esta operação"
            )
        
        # Verificar compartilhamento
        share = await self.share_repository.get_permission(calendar_id, user_id)
        if not share:
            raise PermissionDeniedException("Acesso negado ao calendário")
        
        if require_edit and share.permission == "view":
            raise PermissionDeniedException(
                "Permissão de edição necessária"
            )


class EventService:
    """Service para Event"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = EventRepository(session)
        self.calendar_service = CalendarService(session)
        self.attendee_repository = EventAttendeeRepository(session)
        self.reminder_repository = EventReminderRepository(session)
    
    async def create_event(
        self, 
        event_data: EventCreate, 
        user_id: UUID
    ) -> Event:
        """Cria novo evento"""
        # Verificar permissão no calendário
        await self.calendar_service._check_calendar_permission(
            event_data.calendar_id, 
            user_id, 
            require_edit=True
        )
        
        # Validar dados
        if event_data.end_datetime <= event_data.start_datetime:
            raise ValidationException(
                "Data de término deve ser posterior à data de início"
            )
        
        # Verificar conflitos
        conflicts = await self.repository.check_conflicts(
            event_data.calendar_id,
            event_data.start_datetime,
            event_data.end_datetime
        )
        
        if conflicts:
            raise ConflictException(
                f"Conflito de horário com {len(conflicts)} evento(s)"
            )
        
        # Criar evento principal
        event_dict = event_data.model_dump()
        
        # Remover campos de recorrência para o evento principal
        recurrence_fields = [
            'is_recurring', 'recurrence_type', 'recurrence_interval',
            'recurrence_end_date', 'recurrence_count', 'recurrence_days'
        ]
        
        for field in recurrence_fields:
            event_dict.pop(field, None)
        
        event = Event(
            **event_dict,
            created_by=user_id,
            is_recurring=event_data.is_recurring
        )
        
        event = await self.repository.create(event)
        
        # Criar instâncias recorrentes se necessário
        if event_data.is_recurring and event_data.recurrence_type:
            await self._create_recurring_instances(event, event_data, user_id)
        
        return event
    
    async def get_event(self, event_id: UUID, user_id: UUID) -> Event:
        """Busca evento por ID"""
        event = await self.repository.get_by_id(event_id)
        if not event:
            raise NotFoundException("Evento não encontrado")
        
        # Verificar acesso ao calendário
        await self.calendar_service._check_calendar_access(
            event.calendar_id, 
            user_id
        )
        
        # Verificar se é evento privado
        if event.is_private and event.created_by != user_id:
            # Verificar se é participante
            attendees = await self.attendee_repository.get_by_event_id(event_id)
            is_attendee = any(att.user_id == user_id for att in attendees)
            
            if not is_attendee:
                raise PermissionDeniedException("Evento privado")
        
        return event
    
    async def get_event_with_details(self, event_id: UUID, user_id: UUID) -> Event:
        """Busca evento com detalhes completos"""
        await self.get_event(event_id, user_id)  # Verificar permissões
        
        event = await self.repository.get_with_details(event_id)
        if not event:
            raise NotFoundException("Evento não encontrado")
        
        return event
    
    async def update_event(
        self, 
        event_id: UUID, 
        event_data: EventUpdate, 
        user_id: UUID
    ) -> Event:
        """Atualiza evento"""
        event = await self.repository.get_by_id(event_id)
        if not event:
            raise NotFoundException("Evento não encontrado")
        
        # Verificar permissão
        await self.calendar_service._check_calendar_permission(
            event.calendar_id, 
            user_id, 
            require_edit=True
        )
        
        # Validar se usuário pode editar (criador ou organizador)
        if event.created_by != user_id:
            attendees = await self.attendee_repository.get_by_event_id(event_id)
            is_organizer = any(
                att.user_id == user_id and att.is_organizer 
                for att in attendees
            )
            
            if not is_organizer:
                raise PermissionDeniedException(
                    "Apenas o criador ou organizador pode editar o evento"
                )
        
        # Validar datas se fornecidas
        update_data = event_data.model_dump(exclude_unset=True)
        
        if 'start_datetime' in update_data or 'end_datetime' in update_data:
            start_dt = update_data.get('start_datetime', event.start_datetime)
            end_dt = update_data.get('end_datetime', event.end_datetime)
            
            if end_dt <= start_dt:
                raise ValidationException(
                    "Data de término deve ser posterior à data de início"
                )
            
            # Verificar conflitos
            conflicts = await self.repository.check_conflicts(
                event.calendar_id,
                start_dt,
                end_dt,
                exclude_event_id=event_id
            )
            
            if conflicts:
                raise ConflictException(
                    f"Conflito de horário com {len(conflicts)} evento(s)"
                )
        
        # Atualizar evento
        for field, value in update_data.items():
            setattr(event, field, value)
        
        return await self.repository.update(event)
    
    async def delete_event(self, event_id: UUID, user_id: UUID) -> None:
        """Remove evento"""
        event = await self.repository.get_by_id(event_id)
        if not event:
            raise NotFoundException("Evento não encontrado")
        
        # Verificar permissão
        await self.calendar_service._check_calendar_permission(
            event.calendar_id, 
            user_id, 
            require_edit=True
        )
        
        # Apenas criador pode deletar
        if event.created_by != user_id:
            raise PermissionDeniedException(
                "Apenas o criador pode deletar o evento"
            )
        
        await self.repository.delete(event)
    
    async def get_calendar_events(
        self, 
        calendar_id: UUID, 
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[EventStatus] = None
    ) -> List[Event]:
        """Busca eventos do calendário"""
        await self.calendar_service._check_calendar_access(calendar_id, user_id)
        
        return await self.repository.get_by_calendar_id(
            calendar_id, 
            start_date, 
            end_date, 
            status
        )
    
    async def get_events_in_range(
        self, 
        start_date: datetime,
        end_date: datetime,
        calendar_ids: Optional[List[UUID]] = None,
        user_id: Optional[UUID] = None,
        include_private: bool = False
    ) -> List[Event]:
        """Busca eventos em um período"""
        return await self.repository.get_events_in_range(
            start_date,
            end_date,
            calendar_ids,
            user_id,
            include_private
        )
    
    async def get_user_events(
        self, 
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[EventStatus] = None
    ) -> List[Event]:
        """Busca eventos do usuário"""
        return await self.repository.get_user_events(
            user_id, 
            start_date, 
            end_date, 
            status
        )
    
    async def get_upcoming_events(
        self, 
        user_id: UUID,
        days_ahead: int = 7,
        limit: int = 10
    ) -> List[Event]:
        """Busca próximos eventos do usuário"""
        return await self.repository.get_upcoming_events(
            user_id, 
            days_ahead, 
            limit
        )
    
    async def check_availability(
        self, 
        calendar_id: UUID,
        start_datetime: datetime,
        end_datetime: datetime,
        user_id: UUID
    ) -> Dict[str, Any]:
        """Verifica disponibilidade para agendamento"""
        await self.calendar_service._check_calendar_access(calendar_id, user_id)
        
        # Verificar conflitos
        conflicts = await self.repository.check_conflicts(
            calendar_id,
            start_datetime,
            end_datetime
        )
        
        # Verificar slots de disponibilidade
        availability_repository = AvailabilitySlotRepository(self.session)
        available_slots = await availability_repository.check_availability(
            calendar_id,
            start_datetime,
            end_datetime
        )
        
        return {
            "is_available": len(conflicts) == 0 and len(available_slots) > 0,
            "conflicts": [
                {
                    "event_id": conflict.id,
                    "title": conflict.title,
                    "start_datetime": conflict.start_datetime.isoformat(),
                    "end_datetime": conflict.end_datetime.isoformat()
                }
                for conflict in conflicts
            ],
            "available_slots": len(available_slots) > 0
        }
    
    async def book_time_slot(
        self, 
        booking_data: BookingRequest,
        user_id: Optional[UUID] = None
    ) -> Event:
        """Faz agendamento em calendário público"""
        # Verificar se calendário é público ou se usuário tem acesso
        calendar = await CalendarRepository(self.session).get_by_id(
            booking_data.calendar_id
        )
        if not calendar:
            raise NotFoundException("Calendário não encontrado")
        
        if not calendar.is_public and user_id:
            await self.calendar_service._check_calendar_access(
                booking_data.calendar_id, 
                user_id
            )
        elif not calendar.is_public:
            raise PermissionDeniedException("Calendário não é público")
        
        # Verificar disponibilidade
        availability = await self.check_availability(
            booking_data.calendar_id,
            booking_data.start_datetime,
            booking_data.end_datetime,
            calendar.owner_id  # Usar owner para verificação
        )
        
        if not availability["is_available"]:
            raise ConflictException("Horário não disponível")
        
        # Criar evento
        event_create = EventCreate(
            calendar_id=booking_data.calendar_id,
            title=booking_data.title,
            description=booking_data.description,
            start_datetime=booking_data.start_datetime,
            end_datetime=booking_data.end_datetime,
            status=EventStatus.CONFIRMED,
            metadata=booking_data.metadata or {}
        )
        
        # Adicionar código de confirmação
        confirmation_code = str(uuid.uuid4())[:8].upper()
        event_create.metadata["confirmation_code"] = confirmation_code
        event_create.metadata["booked_by_email"] = booking_data.attendee_email
        
        event = await self.create_event(event_create, calendar.owner_id)
        
        # Adicionar participante
        attendee = EventAttendee(
            event_id=event.id,
            email=booking_data.attendee_email,
            name=booking_data.attendee_name,
            user_id=user_id,
            status=AttendeeStatus.ACCEPTED,
            invited_by=calendar.owner_id
        )
        
        await self.attendee_repository.create(attendee)
        
        return event
    
    async def _create_recurring_instances(
        self, 
        parent_event: Event, 
        event_data: EventCreate, 
        user_id: UUID
    ) -> None:
        """Cria instâncias de evento recorrente"""
        if not event_data.recurrence_type:
            return
        
        instances_created = 0
        max_instances = event_data.recurrence_count or 52  # Máximo 1 ano
        
        current_date = event_data.start_datetime
        delta = timedelta(days=1)
        
        # Configurar intervalo baseado no tipo de recorrência
        if event_data.recurrence_type == RecurrenceType.DAILY:
            delta = timedelta(days=event_data.recurrence_interval or 1)
        elif event_data.recurrence_type == RecurrenceType.WEEKLY:
            delta = timedelta(weeks=event_data.recurrence_interval or 1)
        elif event_data.recurrence_type == RecurrenceType.MONTHLY:
            delta = timedelta(days=30 * (event_data.recurrence_interval or 1))
        elif event_data.recurrence_type == RecurrenceType.YEARLY:
            delta = timedelta(days=365 * (event_data.recurrence_interval or 1))
        
        while instances_created < max_instances:
            current_date += delta
            
            # Verificar data limite
            if event_data.recurrence_end_date and current_date.date() > event_data.recurrence_end_date:
                break
            
            # Verificar dias da semana se especificado
            if event_data.recurrence_days and current_date.weekday() not in event_data.recurrence_days:
                continue
            
            # Calcular data de término
            duration = event_data.end_datetime - event_data.start_datetime
            end_datetime = current_date + duration
            
            # Criar instância
            instance = Event(
                calendar_id=parent_event.calendar_id,
                title=parent_event.title,
                description=parent_event.description,
                location=parent_event.location,
                start_datetime=current_date,
                end_datetime=end_datetime,
                is_all_day=parent_event.is_all_day,
                status=parent_event.status,
                priority=parent_event.priority,
                is_private=parent_event.is_private,
                meeting_url=parent_event.meeting_url,
                timezone=parent_event.timezone,
                metadata=parent_event.metadata,
                is_recurring=False,
                parent_event_id=parent_event.id,
                created_by=user_id
            )
            
            await self.repository.create(instance)
            instances_created += 1


class EventAttendeeService:
    """Service para EventAttendee"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = EventAttendeeRepository(session)
        self.event_service = EventService(session)
    
    async def add_attendee(
        self, 
        event_id: UUID,
        attendee_data: EventAttendeeCreate, 
        user_id: UUID
    ) -> EventAttendee:
        """Adiciona participante ao evento"""
        # Verificar acesso ao evento
        event = await self.event_service.get_event(event_id, user_id)
        
        # Verificar se pode adicionar participantes
        if event.created_by != user_id:
            existing_attendees = await self.repository.get_by_event_id(event_id)
            is_organizer = any(
                att.user_id == user_id and att.is_organizer 
                for att in existing_attendees
            )
            
            if not is_organizer:
                raise PermissionDeniedException(
                    "Apenas organizadores podem adicionar participantes"
                )
        
        # Verificar se já é participante
        existing = await self.repository.get_by_event_id(event_id)
        for att in existing:
            if att.email == attendee_data.email:
                raise ConflictException(
                    "Este email já é participante do evento"
                )
        
        attendee = EventAttendee(
            **attendee_data.model_dump(),
            event_id=event_id,
            invited_by=user_id
        )
        
        return await self.repository.create(attendee)
    
    async def update_attendee_status(
        self, 
        event_id: UUID,
        attendee_email: str,
        status_data: EventAttendeeUpdate,
        user_id: UUID
    ) -> EventAttendee:
        """Atualiza status de participação"""
        attendees = await self.repository.get_by_event_id(event_id)
        attendee = None
        
        for att in attendees:
            if att.email == attendee_email:
                attendee = att
                break
        
        if not attendee:
            raise NotFoundException("Participante não encontrado")
        
        # Verificar se pode atualizar (próprio usuário ou organizador)
        can_update = (
            attendee.user_id == user_id or  # Próprio usuário
            any(att.user_id == user_id and att.is_organizer for att in attendees)  # Organizador
        )
        
        if not can_update:
            raise PermissionDeniedException(
                "Não é possível atualizar status de outro participante"
            )
        
        attendee.status = status_data.status
        if status_data.response_comment:
            attendee.response_comment = status_data.response_comment
        
        return await self.repository.update(attendee)
