"""
Modelos de formulários dinâmicos
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from sqlalchemy import Text, String, Boolean, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID

from app.shared.common.base_models import BaseModel, TimestampMixin


class FormFieldType(str, Enum):
    """Tipos de campos de formulário"""
    TEXT = "text"
    TEXTAREA = "textarea"
    NUMBER = "number"
    EMAIL = "email"
    PASSWORD = "password"
    SELECT = "select"
    MULTISELECT = "multiselect"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    FILE = "file"
    DATE = "date"
    DATETIME = "datetime"
    CURRENCY = "currency"


class FormStatus(str, Enum):
    """Status do formulário"""
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class Form(BaseModel, TimestampMixin):
    """Modelo de formulário dinâmico"""
    
    __tablename__ = "forms"
    
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[FormStatus] = mapped_column(default=FormStatus.DRAFT)
    company_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), 
        nullable=False
    )
    created_by: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), 
        nullable=False
    )
    
    # Configurações do formulário
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    allow_multiple_submissions: Mapped[bool] = mapped_column(Boolean, default=True)
    submission_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    close_date: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    # Metadados
    settings: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
      # Relacionamentos
    fields = relationship("FormField", back_populates="form", cascade="all, delete-orphan")
    # submissions relationship moved to audit domain


class FormField(BaseModel, TimestampMixin):
    """Campo de formulário"""
    
    __tablename__ = "form_fields"
    
    form_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), 
        nullable=False
    )
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    field_type: Mapped[FormFieldType] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    placeholder: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    help_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Validações
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)
    min_length: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_length: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    min_value: Mapped[Optional[float]] = mapped_column(nullable=True)
    max_value: Mapped[Optional[float]] = mapped_column(nullable=True)
    pattern: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Configurações específicas do campo
    options: Mapped[Optional[list]] = mapped_column(JSON, default=list)  # Para select, radio, etc
    default_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Ordem e visibilidade
    order: Mapped[int] = mapped_column(Integer, default=0)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Metadados
    settings: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
      # Relacionamentos
    form = relationship("Form", back_populates="fields")


# FormSubmission moved to audit domain for compliance and advanced tracking

class FormAnalytics(BaseModel, TimestampMixin):
    """Analytics de formulários"""
    
    __tablename__ = "form_analytics"
    
    form_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), 
        nullable=False
    )
    date: Mapped[datetime] = mapped_column(nullable=False)
    
    # Métricas
    views: Mapped[int] = mapped_column(Integer, default=0)
    submissions: Mapped[int] = mapped_column(Integer, default=0)
    completions: Mapped[int] = mapped_column(Integer, default=0)
    abandons: Mapped[int] = mapped_column(Integer, default=0)
    
    # Tempo médio
    avg_completion_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # em segundos
    
    # Dados detalhados
    analytics_data: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
