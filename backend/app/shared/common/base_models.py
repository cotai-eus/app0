"""
Modelos base para SQLAlchemy
"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID

from app.core.database import Base


class TimestampMixin:
    """Mixin para timestamps automáticos"""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


class BaseModel(Base):
    """Modelo base com funcionalidades comuns"""
    
    __abstract__ = True
    
    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False
    )
    
    @declared_attr
    def __tablename__(cls) -> str:
        """Gera nome da tabela automaticamente"""
        return cls.__name__.lower()
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte modelo para dicionário"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    async def save(self, session: AsyncSession) -> None:
        """Salva o modelo no banco"""
        session.add(self)
        await session.commit()
        await session.refresh(self)
    
    async def delete(self, session: AsyncSession) -> None:
        """Remove o modelo do banco"""
        await session.delete(self)
        await session.commit()
    
    def __repr__(self) -> str:
        """Representação string do modelo"""
        attrs = []
        for column in self.__table__.columns:
            if column.primary_key:
                value = getattr(self, column.name, None)
                attrs.append(f"{column.name}={value}")
        
        attrs_str = ", ".join(attrs)
        return f"<{self.__class__.__name__}({attrs_str})>"


class SoftDeleteMixin:
    """Mixin para soft delete"""
    
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None
    )
    
    def soft_delete(self) -> None:
        """Marca o registro como deletado"""
        self.deleted_at = datetime.utcnow()
    
    def restore(self) -> None:
        """Restaura o registro"""
        self.deleted_at = None
    
    @property
    def is_deleted(self) -> bool:
        """Verifica se o registro está deletado"""
        return self.deleted_at is not None


class UserTrackingMixin:
    """Mixin para rastreamento de usuário"""
    
    created_by: Mapped[Optional[str]] = mapped_column(nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(nullable=True)


class VersionMixin:
    """Mixin para controle de versão otimista"""
    
    version: Mapped[int] = mapped_column(default=1, nullable=False)
    
    def increment_version(self) -> None:
        """Incrementa a versão"""
        self.version += 1
