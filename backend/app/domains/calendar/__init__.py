"""
Calendar domain initialization.
"""

from app.domains.calendar.models import (
    Calendar,
    Event,
    EventAttendee,
    EventReminder,
    EventAttachment,
    CalendarShare,
    AvailabilitySlot,
    CalendarAIInsight,
    EventAIAnalysis,
    ScheduleOptimizationReport,
    SmartEventSuggestion,
    MeetingPattern,
    ConflictResolution,
    EventType,
    EventStatus,
    EventPriority,
    RecurrenceType,
    AttendeeStatus,
    AISchedulingPriority,
    ConflictResolutionStrategy,
    MeetingOptimizationType,
)

__all__ = [
    # Models
    "Calendar",
    "Event",
    "EventAttendee",
    "EventReminder",
    "EventAttachment",
    "CalendarShare",
    "AvailabilitySlot",
    "CalendarAIInsight",
    "EventAIAnalysis",
    "ScheduleOptimizationReport",
    "SmartEventSuggestion",
    "MeetingPattern",
    "ConflictResolution",
    # Enums
    "EventType",
    "EventStatus",
    "EventPriority",
    "RecurrenceType",
    "AttendeeStatus",
    "AISchedulingPriority",
    "ConflictResolutionStrategy",
    "MeetingOptimizationType",
]
