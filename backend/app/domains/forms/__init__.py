"""
Forms domain module for dynamic form creation and management.
"""

from app.domains.forms.models import Form, FormField, FormAnalytics, FormFieldType, FormStatus
from app.domains.forms.schemas import (
    FormCreate,
    FormUpdate,
    FormResponse,
    FormFieldCreate,
    FormFieldUpdate,
    FormFieldResponse,
    FormAnalyticsResponse,
    FormSummary,
)
from app.domains.forms.repository import (
    FormRepository,
    FormFieldRepository,
    FormAnalyticsRepository,
)
from app.domains.forms.service import (
    FormService,
    FormFieldService,
    FormAnalyticsService,
)

__all__ = [
    # Models
    "Form",
    "FormField", 
    "FormSubmission",
    "FormAnalytics",
    "FormFieldType",
    "FormStatus",
      # Schemas
    "FormCreate",
    "FormUpdate", 
    "FormResponse",
    "FormFieldCreate",
    "FormFieldUpdate",
    "FormFieldResponse",
    "FormSubmissionCreate",
    "FormSubmissionUpdate",
    "FormSubmissionResponse",
    "FormAnalyticsResponse",
    "FormSummary",
    
    # Repositories
    "FormRepository",
    "FormFieldRepository",
    "FormSubmissionRepository", 
    "FormAnalyticsRepository",
    
    # Services
    "FormService",
    "FormFieldService",
    "FormSubmissionService",
    "FormAnalyticsService",
]
