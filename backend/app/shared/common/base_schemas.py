"""
Schemas base para Pydantic
"""

from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field, ConfigDict


class BaseSchema(BaseModel):
    """Schema base para todos os modelos Pydantic"""
    
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        arbitrary_types_allowed=True,
        str_strip_whitespace=True,
    )


class TimestampSchema(BaseSchema):
    """Schema base com timestamps"""
    
    created_at: datetime
    updated_at: datetime


class BaseCreateSchema(BaseSchema):
    """Schema base para criação"""
    pass


class BaseUpdateSchema(BaseSchema):
    """Schema base para atualização"""
    pass


class BaseResponseSchema(TimestampSchema):
    """Schema base para resposta"""
    
    id: str | int


class SoftDeleteSchema(BaseSchema):
    """Schema para soft delete"""
    
    deleted_at: Optional[datetime] = None
    
    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


class UserTrackingSchema(BaseSchema):
    """Schema para rastreamento de usuário"""
    
    created_by: Optional[str] = None
    updated_by: Optional[str] = None


class VersionSchema(BaseSchema):
    """Schema para controle de versão"""
    
    version: int = Field(default=1, ge=1)


# Generic schemas para paginação
T = TypeVar('T')


class PaginatedResponse(BaseSchema, Generic[T]):
    """Resposta paginada genérica"""
    
    items: List[T]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    size: int = Field(ge=1)
    pages: int = Field(ge=0)
    
    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        size: int
    ) -> "PaginatedResponse[T]":
        """Cria resposta paginada"""
        pages = (total + size - 1) // size if total > 0 else 0
        
        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )


class ErrorDetail(BaseSchema):
    """Detalhe do erro"""
    
    code: str
    message: str
    field: Optional[str] = None


class ErrorResponse(BaseSchema):
    """Resposta de erro padronizada"""
    
    error: ErrorDetail
    request_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SuccessResponse(BaseSchema):
    """Resposta de sucesso padronizada"""
    
    message: str
    data: Optional[dict[str, Any]] = None
    request_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseSchema):
    """Resposta do health check"""
    
    status: str = Field(description="Status da aplicação")
    version: str = Field(description="Versão da aplicação")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: dict[str, str] = Field(default_factory=dict)
    uptime: float = Field(description="Tempo de funcionamento em segundos")


class MetricsResponse(BaseSchema):
    """Resposta das métricas"""
    
    requests_total: int
    requests_per_second: float
    average_response_time: float
    active_connections: int
    memory_usage: dict[str, Any]
    database_connections: dict[str, Any]
