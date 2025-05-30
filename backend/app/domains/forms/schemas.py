"""
Schemas para formulários
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.domains.forms.models import FormFieldType, FormStatus


# Base schemas
class FormFieldBase(BaseModel):
    """Base para campos de formulário"""
    label: str = Field(..., max_length=200)
    field_type: FormFieldType
    name: str = Field(..., max_length=100)
    placeholder: Optional[str] = Field(None, max_length=200)
    help_text: Optional[str] = None
    is_required: bool = False
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    pattern: Optional[str] = Field(None, max_length=500)
    options: List[str] = Field(default_factory=list)
    default_value: Optional[str] = None
    order: int = 0
    is_visible: bool = True
    settings: Dict[str, Any] = Field(default_factory=dict)


class FormFieldCreate(FormFieldBase):
    """Schema para criação de campo"""
    pass


class FormFieldUpdate(BaseModel):
    """Schema para atualização de campo"""
    label: Optional[str] = Field(None, max_length=200)
    field_type: Optional[FormFieldType] = None
    placeholder: Optional[str] = Field(None, max_length=200)
    help_text: Optional[str] = None
    is_required: Optional[bool] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    pattern: Optional[str] = Field(None, max_length=500)
    options: Optional[List[str]] = None
    default_value: Optional[str] = None
    order: Optional[int] = None
    is_visible: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None


class FormFieldResponse(FormFieldBase):
    """Schema de resposta de campo"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    form_id: UUID
    created_at: datetime
    updated_at: datetime


# Form schemas
class FormBase(BaseModel):
    """Base para formulários"""
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    is_public: bool = False
    allow_multiple_submissions: bool = True
    submission_limit: Optional[int] = None
    close_date: Optional[datetime] = None
    settings: Dict[str, Any] = Field(default_factory=dict)


class FormCreate(FormBase):
    """Schema para criação de formulário"""
    fields: List[FormFieldCreate] = Field(default_factory=list)


class FormUpdate(BaseModel):
    """Schema para atualização de formulário"""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    status: Optional[FormStatus] = None
    is_public: Optional[bool] = None
    allow_multiple_submissions: Optional[bool] = None
    submission_limit: Optional[int] = None
    close_date: Optional[datetime] = None
    settings: Optional[Dict[str, Any]] = None


class FormResponse(FormBase):
    """Schema de resposta de formulário"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    status: FormStatus
    company_id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    fields: List[FormFieldResponse] = Field(default_factory=list)


class FormWithFields(FormResponse):
    """Form with included fields"""
    fields: List[FormFieldResponse] = Field(default_factory=list)


class FormSummary(BaseModel):
    """Resumo do formulário"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    title: str
    description: Optional[str]
    status: FormStatus
    is_public: bool
    submission_count: int = 0
    created_at: datetime
    updated_at: datetime


# Submission schemas
class FormSubmissionBase(BaseModel):
    """Base para submissão"""
    data: Dict[str, Any]
    is_draft: bool = False


class FormSubmissionCreate(FormSubmissionBase):
    """Schema para criação de submissão"""
    pass


class FormSubmissionUpdate(BaseModel):
    """Schema para atualização de submissão"""
    data: Optional[Dict[str, Any]] = None
    is_draft: Optional[bool] = None


class FormSubmissionResponse(FormSubmissionBase):
    """Schema de resposta de submissão"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    form_id: UUID
    submitted_by: Optional[UUID]
    ip_address: Optional[str]
    user_agent: Optional[str]
    submission_source: Optional[str]
    submitted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


# Analytics schemas
class FormAnalyticsResponse(BaseModel):
    """Analytics do formulário"""
    model_config = ConfigDict(from_attributes=True)
    
    form_id: UUID
    date: datetime
    views: int
    submissions: int
    completions: int
    abandons: int
    avg_completion_time: Optional[int]
    analytics_data: Dict[str, Any]


class FormStats(BaseModel):
    """Estatísticas gerais do formulário"""
    total_views: int = 0
    total_submissions: int = 0
    total_completions: int = 0
    completion_rate: float = 0.0
    avg_completion_time: Optional[int] = None
    last_submission: Optional[datetime] = None


# Validation schemas
class FormValidationResult(BaseModel):
    """Resultado da validação de formulário"""
    is_valid: bool
    errors: Dict[str, List[str]] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


class FieldValidationError(BaseModel):
    """Erro de validação de campo"""
    field_name: str
    message: str
    code: str


class FieldReorder(BaseModel):
    """Schema for reordering form fields"""
    field_id: UUID
    order: int


# Form summary schemas
class FormSummary(BaseModel):
    """Comprehensive form summary with analytics"""
    form: FormWithFields
    analytics: FormAnalyticsResponse
    data_summary: Dict[str, Any] = Field(default_factory=dict)
