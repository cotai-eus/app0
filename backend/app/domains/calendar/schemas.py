"""
Schemas do domínio Calendar
"""

from datetime import datetime, date, time
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, EmailStr

from app.domains.calendar.models import (
    EventStatus, EventPriority, ReminderType, AttendeeStatus,
    CalendarType, AvailabilityType, RecurrenceType, SharePermission
)
from app.shared.common.base_schemas import BaseResponse, TimestampSchema


# Calendar Schemas
class CalendarBase(BaseModel):
    """Base schema for Calendar"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    calendar_type: CalendarType = CalendarType.PERSONAL
    is_public: bool = False
    timezone: str = Field(default="UTC", max_length=50)
    settings: Optional[Dict[str, Any]] = None


class CalendarCreate(CalendarBase):
    """Schema for creating a calendar"""
    pass


class CalendarUpdate(BaseModel):
    """Schema for updating a calendar"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    calendar_type: Optional[CalendarType] = None
    is_public: Optional[bool] = None
    timezone: Optional[str] = Field(None, max_length=50)
    settings: Optional[Dict[str, Any]] = None


class CalendarResponse(CalendarBase, BaseResponse, TimestampSchema):
    """Schema for calendar response"""
    owner_id: UUID
    
    model_config = ConfigDict(from_attributes=True)


# Event Schemas
class EventBase(BaseModel):
    """Base schema for Event"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    location: Optional[str] = None
    start_datetime: datetime
    end_datetime: datetime
    is_all_day: bool = False
    status: EventStatus = EventStatus.CONFIRMED
    priority: EventPriority = EventPriority.MEDIUM
    is_private: bool = False
    meeting_url: Optional[str] = None
    timezone: str = Field(default="UTC", max_length=50)
    metadata: Optional[Dict[str, Any]] = None


class EventCreate(EventBase):
    """Schema for creating an event"""
    calendar_id: UUID
    
    # Recurrence fields
    is_recurring: bool = False
    recurrence_type: Optional[RecurrenceType] = None
    recurrence_interval: Optional[int] = Field(None, ge=1)
    recurrence_end_date: Optional[date] = None
    recurrence_count: Optional[int] = Field(None, ge=1)
    recurrence_days: Optional[List[int]] = Field(None, min_items=1, max_items=7)


class EventUpdate(BaseModel):
    """Schema for updating an event"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    location: Optional[str] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    is_all_day: Optional[bool] = None
    status: Optional[EventStatus] = None
    priority: Optional[EventPriority] = None
    is_private: Optional[bool] = None
    meeting_url: Optional[str] = None
    timezone: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class EventResponse(EventBase, BaseResponse, TimestampSchema):
    """Schema for event response"""
    calendar_id: UUID
    created_by: UUID
    
    # Recurrence fields
    is_recurring: bool
    recurrence_type: Optional[RecurrenceType] = None
    recurrence_interval: Optional[int] = None
    recurrence_end_date: Optional[date] = None
    recurrence_count: Optional[int] = None
    recurrence_days: Optional[List[int]] = None
    parent_event_id: Optional[UUID] = None
    
    model_config = ConfigDict(from_attributes=True)


# Event Attendee Schemas
class EventAttendeeBase(BaseModel):
    """Base schema for EventAttendee"""
    email: EmailStr
    name: Optional[str] = None
    status: AttendeeStatus = AttendeeStatus.PENDING
    is_organizer: bool = False
    response_comment: Optional[str] = None


class EventAttendeeCreate(EventAttendeeBase):
    """Schema for creating an event attendee"""
    user_id: Optional[UUID] = None


class EventAttendeeUpdate(BaseModel):
    """Schema for updating an event attendee"""
    status: AttendeeStatus
    response_comment: Optional[str] = None


class EventAttendeeResponse(EventAttendeeBase, BaseResponse, TimestampSchema):
    """Schema for event attendee response"""
    event_id: UUID
    user_id: Optional[UUID] = None
    invited_by: UUID
    
    model_config = ConfigDict(from_attributes=True)


# Event Reminder Schemas
class EventReminderBase(BaseModel):
    """Base schema for EventReminder"""
    reminder_type: ReminderType = ReminderType.EMAIL
    minutes_before: int = Field(..., ge=0)
    is_sent: bool = False


class EventReminderCreate(EventReminderBase):
    """Schema for creating an event reminder"""
    pass


class EventReminderResponse(EventReminderBase, BaseResponse, TimestampSchema):
    """Schema for event reminder response"""
    event_id: UUID
    user_id: UUID
    sent_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


# Event Attachment Schemas
class EventAttachmentBase(BaseModel):
    """Base schema for EventAttachment"""
    filename: str
    original_filename: str
    file_size: int
    content_type: str


class EventAttachmentCreate(EventAttachmentBase):
    """Schema for creating an event attachment"""
    pass


class EventAttachmentResponse(EventAttachmentBase, BaseResponse, TimestampSchema):
    """Schema for event attachment response"""
    event_id: UUID
    uploaded_by: UUID
    
    model_config = ConfigDict(from_attributes=True)


# Calendar Share Schemas
class CalendarShareBase(BaseModel):
    """Base schema for CalendarShare"""
    permission: SharePermission = SharePermission.VIEW
    can_edit_events: bool = False
    can_invite_others: bool = False


class CalendarShareCreate(CalendarShareBase):
    """Schema for creating a calendar share"""
    user_id: UUID


class CalendarShareUpdate(BaseModel):
    """Schema for updating a calendar share"""
    permission: Optional[SharePermission] = None
    can_edit_events: Optional[bool] = None
    can_invite_others: Optional[bool] = None


class CalendarShareResponse(CalendarShareBase, BaseResponse, TimestampSchema):
    """Schema for calendar share response"""
    calendar_id: UUID
    user_id: UUID
    shared_by: UUID
    
    model_config = ConfigDict(from_attributes=True)


# Availability Slot Schemas
class AvailabilitySlotBase(BaseModel):
    """Base schema for AvailabilitySlot"""
    day_of_week: int = Field(..., ge=0, le=6)  # 0=Monday, 6=Sunday
    start_time: time
    end_time: time
    availability_type: AvailabilityType = AvailabilityType.AVAILABLE
    is_recurring: bool = True
    metadata: Optional[Dict[str, Any]] = None


class AvailabilitySlotCreate(AvailabilitySlotBase):
    """Schema for creating an availability slot"""
    calendar_id: UUID


class AvailabilitySlotUpdate(BaseModel):
    """Schema for updating an availability slot"""
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    availability_type: Optional[AvailabilityType] = None
    is_recurring: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class AvailabilitySlotResponse(AvailabilitySlotBase, BaseResponse, TimestampSchema):
    """Schema for availability slot response"""
    calendar_id: UUID
    created_by: UUID
    
    model_config = ConfigDict(from_attributes=True)


# Complex Schemas
class EventWithDetails(EventResponse):
    """Event with additional details"""
    attendees: List[EventAttendeeResponse] = []
    reminders: List[EventReminderResponse] = []
    attachments: List[EventAttachmentResponse] = []


class CalendarWithEvents(CalendarResponse):
    """Calendar with events"""
    events: List[EventResponse] = []
    shared_users: List[CalendarShareResponse] = []


class CalendarSummary(BaseModel):
    """Calendar summary with statistics"""
    calendar: CalendarResponse
    total_events: int
    upcoming_events: int
    events_today: int
    events_this_week: int
    events_this_month: int


class EventConflict(BaseModel):
    """Schema for event conflicts"""
    event: EventResponse
    conflict_type: str  # "overlap", "double_booking", "availability"
    conflicting_event: Optional[EventResponse] = None
    message: str


class AvailabilityCheck(BaseModel):
    """Schema for availability check"""
    calendar_id: UUID
    start_datetime: datetime
    end_datetime: datetime
    check_conflicts: bool = True


class AvailabilityResponse(BaseModel):
    """Schema for availability response"""
    is_available: bool
    conflicts: List[EventConflict] = []
    available_slots: List[Dict[str, datetime]] = []


# Bulk Operations
class EventBulkCreate(BaseModel):
    """Schema for bulk creating events"""
    events: List[EventCreate]


class EventBulkUpdate(BaseModel):
    """Schema for bulk updating events"""
    event_ids: List[UUID]
    updates: EventUpdate


class CalendarEventFilter(BaseModel):
    """Schema for filtering calendar events"""
    calendar_ids: Optional[List[UUID]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[EventStatus] = None
    priority: Optional[EventPriority] = None
    search_term: Optional[str] = None
    include_private: bool = False
    attendee_email: Optional[str] = None


# Analytics Schemas
class CalendarAnalytics(BaseModel):
    """Calendar analytics response"""
    calendar_id: UUID
    period_start: datetime
    period_end: datetime
    total_events: int
    completed_events: int
    cancelled_events: int
    average_event_duration: float  # em horas
    busiest_day: str
    busiest_hour: int
    events_by_priority: Dict[str, int]
    events_by_status: Dict[str, int]
    attendance_rate: float  # percentage


# Booking Schemas
class BookingRequest(BaseModel):
    """Schema for booking a time slot"""
    calendar_id: UUID
    title: str
    description: Optional[str] = None
    start_datetime: datetime
    end_datetime: datetime
    attendee_email: EmailStr
    attendee_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BookingResponse(BaseModel):
    """Schema for booking response"""
    booking_id: UUID
    event: EventResponse
    confirmation_code: str
    is_confirmed: bool
    booking_url: Optional[str] = None
