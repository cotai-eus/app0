"""
Endpoints do domínio Calendar
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.domains.auth.service import get_current_user
from app.domains.auth.models import User
from app.domains.calendar.service import (
    CalendarService, EventService, EventAttendeeService
)
from app.domains.calendar.schemas import (
    CalendarResponse, CalendarCreate, CalendarUpdate,
    EventResponse, EventCreate, EventUpdate, EventWithDetails,
    EventAttendeeResponse, EventAttendeeCreate, EventAttendeeUpdate,
    CalendarShareResponse, CalendarShareCreate, CalendarShareUpdate,
    AvailabilitySlotResponse, AvailabilitySlotCreate, AvailabilitySlotUpdate,
    CalendarAnalytics, AvailabilityResponse, AvailabilityCheck,
    BookingRequest, BookingResponse
)
from app.domains.calendar.models import EventStatus, EventPriority, CalendarType
from app.shared.common.responses import SuccessResponse

router = APIRouter(prefix="/calendar", tags=["Calendar"])


# Calendar Endpoints
@router.post("/calendars", response_model=CalendarResponse, status_code=status.HTTP_201_CREATED)
async def create_calendar(
    calendar_data: CalendarCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Cria um novo calendário"""
    service = CalendarService(session)
    calendar = await service.create_calendar(calendar_data, current_user.id)
    return calendar


@router.get("/calendars/{calendar_id}", response_model=CalendarResponse)
async def get_calendar(
    calendar_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Busca calendário por ID"""
    service = CalendarService(session)
    return await service.get_calendar(calendar_id, current_user.id)


@router.put("/calendars/{calendar_id}", response_model=CalendarResponse)
async def update_calendar(
    calendar_id: UUID,
    calendar_data: CalendarUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Atualiza calendário"""
    service = CalendarService(session)
    return await service.update_calendar(calendar_id, calendar_data, current_user.id)


@router.delete("/calendars/{calendar_id}", response_model=SuccessResponse)
async def delete_calendar(
    calendar_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Remove calendário"""
    service = CalendarService(session)
    await service.delete_calendar(calendar_id, current_user.id)
    return SuccessResponse(message="Calendário removido com sucesso")


@router.get("/calendars", response_model=List[CalendarResponse])
async def get_user_calendars(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Lista calendários do usuário (próprios + compartilhados)"""
    service = CalendarService(session)
    return await service.get_user_calendars(current_user.id)


@router.get("/calendars/search", response_model=List[CalendarResponse])
async def search_calendars(
    q: str = Query(..., min_length=2),
    calendar_type: Optional[CalendarType] = Query(None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Busca calendários por termo"""
    service = CalendarService(session)
    return await service.search_calendars(q, calendar_type, current_user.id)


@router.get("/calendars/{calendar_id}/analytics", response_model=CalendarAnalytics)
async def get_calendar_analytics(
    calendar_id: UUID,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Análise do calendário"""
    service = CalendarService(session)
    return await service.get_calendar_analytics(
        calendar_id, 
        current_user.id, 
        start_date, 
        end_date
    )


# Calendar Sharing Endpoints
@router.post("/calendars/{calendar_id}/share", response_model=CalendarShareResponse, status_code=status.HTTP_201_CREATED)
async def share_calendar(
    calendar_id: UUID,
    share_data: CalendarShareCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Compartilha calendário com usuário"""
    service = CalendarService(session)
    return await service.share_calendar(calendar_id, share_data, current_user.id)


@router.put("/calendars/{calendar_id}/share/{user_id}", response_model=CalendarShareResponse)
async def update_calendar_share(
    calendar_id: UUID,
    user_id: UUID,
    share_data: CalendarShareUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Atualiza permissões de compartilhamento"""
    service = CalendarService(session)
    return await service.update_calendar_share(
        calendar_id, 
        user_id, 
        share_data, 
        current_user.id
    )


@router.delete("/calendars/{calendar_id}/share/{user_id}", response_model=SuccessResponse)
async def remove_calendar_share(
    calendar_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Remove compartilhamento"""
    service = CalendarService(session)
    await service.remove_calendar_share(calendar_id, user_id, current_user.id)
    return SuccessResponse(message="Compartilhamento removido com sucesso")


# Event Endpoints
@router.post("/events", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: EventCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Cria novo evento"""
    service = EventService(session)
    return await service.create_event(event_data, current_user.id)


@router.get("/events/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: UUID,
    include_details: bool = Query(False),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Busca evento por ID"""
    service = EventService(session)
    
    if include_details:
        return await service.get_event_with_details(event_id, current_user.id)
    else:
        return await service.get_event(event_id, current_user.id)


@router.put("/events/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: UUID,
    event_data: EventUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Atualiza evento"""
    service = EventService(session)
    return await service.update_event(event_id, event_data, current_user.id)


@router.delete("/events/{event_id}", response_model=SuccessResponse)
async def delete_event(
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Remove evento"""
    service = EventService(session)
    await service.delete_event(event_id, current_user.id)
    return SuccessResponse(message="Evento removido com sucesso")


@router.get("/calendars/{calendar_id}/events", response_model=List[EventResponse])
async def get_calendar_events(
    calendar_id: UUID,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    status: Optional[EventStatus] = Query(None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Lista eventos do calendário"""
    service = EventService(session)
    return await service.get_calendar_events(
        calendar_id, 
        current_user.id, 
        start_date, 
        end_date, 
        status
    )


@router.get("/events/range", response_model=List[EventResponse])
async def get_events_in_range(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    calendar_ids: Optional[List[UUID]] = Query(None),
    include_private: bool = Query(False),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Busca eventos em um período"""
    service = EventService(session)
    return await service.get_events_in_range(
        start_date,
        end_date,
        calendar_ids,
        current_user.id,
        include_private
    )


@router.get("/events/mine", response_model=List[EventResponse])
async def get_user_events(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    status: Optional[EventStatus] = Query(None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Busca eventos do usuário atual"""
    service = EventService(session)
    return await service.get_user_events(
        current_user.id, 
        start_date, 
        end_date, 
        status
    )


@router.get("/events/upcoming", response_model=List[EventResponse])
async def get_upcoming_events(
    days_ahead: int = Query(7, ge=1, le=365),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Busca próximos eventos do usuário"""
    service = EventService(session)
    return await service.get_upcoming_events(
        current_user.id, 
        days_ahead, 
        limit
    )


# Availability and Booking Endpoints
@router.post("/calendars/{calendar_id}/check-availability", response_model=AvailabilityResponse)
async def check_availability(
    calendar_id: UUID,
    availability_data: AvailabilityCheck,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Verifica disponibilidade para agendamento"""
    service = EventService(session)
    return await service.check_availability(
        calendar_id,
        availability_data.start_datetime,
        availability_data.end_datetime,
        current_user.id
    )


@router.post("/calendars/{calendar_id}/book", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def book_time_slot(
    calendar_id: UUID,
    booking_data: BookingRequest,
    current_user: Optional[User] = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Faz agendamento em calendário (público ou com permissão)"""
    # Garantir que calendar_id do path seja usado
    booking_data.calendar_id = calendar_id
    
    service = EventService(session)
    event = await service.book_time_slot(
        booking_data, 
        current_user.id if current_user else None
    )
    
    confirmation_code = event.metadata.get("confirmation_code", "")
    
    return BookingResponse(
        booking_id=event.id,
        event=event,
        confirmation_code=confirmation_code,
        is_confirmed=True,
        booking_url=f"/calendar/events/{event.id}"
    )


# Event Attendees Endpoints
@router.post("/events/{event_id}/attendees", response_model=EventAttendeeResponse, status_code=status.HTTP_201_CREATED)
async def add_event_attendee(
    event_id: UUID,
    attendee_data: EventAttendeeCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Adiciona participante ao evento"""
    service = EventAttendeeService(session)
    return await service.add_attendee(event_id, attendee_data, current_user.id)


@router.put("/events/{event_id}/attendees/{attendee_email}/status", response_model=EventAttendeeResponse)
async def update_attendee_status(
    event_id: UUID,
    attendee_email: str,
    status_data: EventAttendeeUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Atualiza status de participação no evento"""
    service = EventAttendeeService(session)
    return await service.update_attendee_status(
        event_id, 
        attendee_email, 
        status_data, 
        current_user.id
    )


# Public Endpoints (without authentication)
@router.get("/public/calendars", response_model=List[CalendarResponse])
async def get_public_calendars(
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_async_session)
):
    """Lista calendários públicos"""
    from app.domains.calendar.repository import CalendarRepository
    
    repository = CalendarRepository(session)
    return await repository.get_public_calendars(limit)


@router.get("/public/calendars/{calendar_id}/events", response_model=List[EventResponse])
async def get_public_calendar_events(
    calendar_id: UUID,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    session: AsyncSession = Depends(get_async_session)
):
    """Lista eventos de calendário público"""
    from app.domains.calendar.repository import CalendarRepository, EventRepository
    
    # Verificar se calendário é público
    cal_repo = CalendarRepository(session)
    calendar = await cal_repo.get_by_id(calendar_id)
    
    if not calendar or not calendar.is_public:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendário público não encontrado"
        )
    
    event_repo = EventRepository(session)
    return await event_repo.get_by_calendar_id(
        calendar_id, 
        start_date, 
        end_date, 
        EventStatus.CONFIRMED
    )


@router.post("/public/calendars/{calendar_id}/book", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def book_public_time_slot(
    calendar_id: UUID,
    booking_data: BookingRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """Faz agendamento em calendário público (sem autenticação)"""
    # Garantir que calendar_id do path seja usado
    booking_data.calendar_id = calendar_id
    
    service = EventService(session)
    event = await service.book_time_slot(booking_data, None)
    
    confirmation_code = event.metadata.get("confirmation_code", "")
    
    return BookingResponse(
        booking_id=event.id,
        event=event,
        confirmation_code=confirmation_code,
        is_confirmed=True,
        booking_url=f"/calendar/events/{event.id}"
    )
