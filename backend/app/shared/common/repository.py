"""
Base repository classes for data access patterns.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from app.shared.common.base_models import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    """Repository base para operações CRUD."""
    
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session
    
    async def get_by_id(self, id: UUID) -> Optional[ModelType]:
        """Busca um registro por ID."""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """Busca todos os registros com paginação."""
        query = select(self.model)
        
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)
        
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def create(self, obj_in: Dict[str, Any]) -> ModelType:
        """Cria um novo registro."""
        db_obj = self.model(**obj_in)
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj
    
    async def update(self, id: UUID, obj_in: Dict[str, Any]) -> Optional[ModelType]:
        """Atualiza um registro existente."""
        await self.session.execute(
            update(self.model)
            .where(self.model.id == id)
            .values(**obj_in)
        )
        await self.session.commit()
        return await self.get_by_id(id)
    
    async def delete(self, id: UUID) -> bool:
        """Remove um registro."""
        result = await self.session.execute(
            delete(self.model).where(self.model.id == id)
        )
        await self.session.commit()
        return result.rowcount > 0
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Conta o número de registros."""
        query = select(func.count(self.model.id))
        
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)
        
        result = await self.session.execute(query)
        return result.scalar()


class AsyncRepository(BaseRepository[ModelType]):
    """Repository assíncrono especializado."""
    
    async def exists(self, id: UUID) -> bool:
        """Verifica se um registro existe."""
        result = await self.session.execute(
            select(func.count(self.model.id)).where(self.model.id == id)
        )
        return result.scalar() > 0
    
    async def get_or_create(
        self,
        defaults: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> tuple[ModelType, bool]:
        """Busca ou cria um registro."""
        # Busca primeiro
        query = select(self.model)
        for field, value in kwargs.items():
            if hasattr(self.model, field):
                query = query.where(getattr(self.model, field) == value)
        
        result = await self.session.execute(query)
        instance = result.scalar_one_or_none()
        
        if instance:
            return instance, False
        
        # Se não encontrou, cria
        create_data = {**kwargs, **(defaults or {})}
        instance = await self.create(create_data)
        return instance, True
