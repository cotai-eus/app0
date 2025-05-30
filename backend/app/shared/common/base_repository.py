"""
Repository base para acesso a dados
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.shared.common.base_models import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class BaseRepository(Generic[ModelType], ABC):
    """Repository base com operações CRUD genéricas"""
    
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session
    
    async def get(self, id: Any) -> Optional[ModelType]:
        """Busca registro por ID"""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False,
    ) -> List[ModelType]:
        """Busca múltiplos registros com filtros e paginação"""
        query = select(self.model)
        
        # Aplica filtros
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)
        
        # Aplica ordenação
        if order_by and hasattr(self.model, order_by):
            order_column = getattr(self.model, order_by)
            if order_desc:
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column)
        
        # Aplica paginação
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Conta registros com filtros opcionais"""
        query = select(func.count(self.model.id))
        
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)
        
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        """Cria novo registro"""
        if hasattr(obj_in, 'model_dump'):
            obj_data = obj_in.model_dump()
        elif hasattr(obj_in, 'dict'):
            obj_data = obj_in.dict()
        else:
            obj_data = dict(obj_in)
        
        db_obj = self.model(**obj_data)
        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj
    
    async def update(
        self, 
        db_obj: ModelType, 
        obj_in: UpdateSchemaType
    ) -> ModelType:
        """Atualiza registro existente"""
        if hasattr(obj_in, 'model_dump'):
            update_data = obj_in.model_dump(exclude_unset=True)
        elif hasattr(obj_in, 'dict'):
            update_data = obj_in.dict(exclude_unset=True)
        else:
            update_data = dict(obj_in)
        
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj
    
    async def delete(self, id: Any) -> bool:
        """Remove registro por ID"""
        result = await self.session.execute(
            delete(self.model).where(self.model.id == id)
        )
        return result.rowcount > 0
    
    async def delete_obj(self, db_obj: ModelType) -> bool:
        """Remove objeto específico"""
        await self.session.delete(db_obj)
        return True
    
    async def exists(self, id: Any) -> bool:
        """Verifica se registro existe"""
        result = await self.session.execute(
            select(func.count(self.model.id)).where(self.model.id == id)
        )
        count = result.scalar() or 0
        return count > 0
    
    async def get_by_field(
        self, 
        field: str, 
        value: Any
    ) -> Optional[ModelType]:
        """Busca registro por campo específico"""
        if not hasattr(self.model, field):
            return None
        
        result = await self.session.execute(
            select(self.model).where(getattr(self.model, field) == value)
        )
        return result.scalar_one_or_none()
    
    async def get_multi_by_field(
        self, 
        field: str, 
        value: Any,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """Busca múltiplos registros por campo específico"""
        if not hasattr(self.model, field):
            return []
        
        query = select(self.model).where(
            getattr(self.model, field) == value
        ).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def bulk_create(self, objects: List[CreateSchemaType]) -> List[ModelType]:
        """Cria múltiplos registros em lote"""
        db_objects = []
        
        for obj_in in objects:
            if hasattr(obj_in, 'model_dump'):
                obj_data = obj_in.model_dump()
            elif hasattr(obj_in, 'dict'):
                obj_data = obj_in.dict()
            else:
                obj_data = dict(obj_in)
            
            db_obj = self.model(**obj_data)
            db_objects.append(db_obj)
        
        self.session.add_all(db_objects)
        await self.session.flush()
        
        for db_obj in db_objects:
            await self.session.refresh(db_obj)
        
        return db_objects
    
    async def bulk_update(
        self, 
        filters: Dict[str, Any], 
        update_data: Dict[str, Any]
    ) -> int:
        """Atualiza múltiplos registros em lote"""
        query = update(self.model)
        
        for field, value in filters.items():
            if hasattr(self.model, field):
                query = query.where(getattr(self.model, field) == value)
        
        query = query.values(**update_data)
        result = await self.session.execute(query)
        return result.rowcount or 0
    
    async def search(
        self,
        search_term: str,
        search_fields: List[str],
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """Busca texto em múltiplos campos"""
        query = select(self.model)
        
        search_conditions = []
        for field in search_fields:
            if hasattr(self.model, field):
                field_column = getattr(self.model, field)
                search_conditions.append(
                    field_column.ilike(f"%{search_term}%")
                )
        
        if search_conditions:
            from sqlalchemy import or_
            query = query.where(or_(*search_conditions))
        
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()
