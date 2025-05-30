"""
Service base para lógica de negócio
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ValidationException
from app.shared.common.base_repository import BaseRepository

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")
RepositoryType = TypeVar("RepositoryType", bound=BaseRepository)


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType], ABC):
    """Service base com operações CRUD e lógica de negócio"""
    
    def __init__(self, repository: RepositoryType):
        self.repository = repository
    
    @property
    @abstractmethod
    def entity_name(self) -> str:
        """Nome da entidade para mensagens de erro"""
        pass
    
    async def get_by_id(self, id: Any) -> ModelType:
        """Busca entidade por ID com validação"""
        entity = await self.repository.get(id)
        if not entity:
            raise NotFoundException(self.entity_name, id)
        return entity
    
    async def get_by_id_optional(self, id: Any) -> Optional[ModelType]:
        """Busca entidade por ID sem validação"""
        return await self.repository.get(id)
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False,
    ) -> List[ModelType]:
        """Lista entidades com filtros e paginação"""
        return await self.repository.get_multi(
            skip=skip,
            limit=limit,
            filters=filters,
            order_by=order_by,
            order_desc=order_desc
        )
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Conta entidades com filtros"""
        return await self.repository.count(filters)
    
    async def create(
        self, 
        obj_in: CreateSchemaType,
        current_user_id: Optional[str] = None
    ) -> ModelType:
        """Cria nova entidade com validações"""
        
        # Validações de negócio antes da criação
        await self.validate_create(obj_in)
        
        # Adiciona informações do usuário se disponível
        if current_user_id and hasattr(obj_in, 'created_by'):
            obj_in.created_by = current_user_id
        
        # Cria a entidade
        entity = await self.repository.create(obj_in)
        
        # Hook pós-criação
        await self.after_create(entity, obj_in)
        
        return entity
    
    async def update(
        self, 
        id: Any, 
        obj_in: UpdateSchemaType,
        current_user_id: Optional[str] = None
    ) -> ModelType:
        """Atualiza entidade existente com validações"""
        
        # Busca entidade existente
        entity = await self.get_by_id(id)
        
        # Validações de negócio antes da atualização
        await self.validate_update(entity, obj_in)
        
        # Adiciona informações do usuário se disponível
        if current_user_id and hasattr(obj_in, 'updated_by'):
            obj_in.updated_by = current_user_id
        
        # Atualiza a entidade
        updated_entity = await self.repository.update(entity, obj_in)
        
        # Hook pós-atualização
        await self.after_update(updated_entity, obj_in)
        
        return updated_entity
    
    async def delete(self, id: Any) -> bool:
        """Remove entidade por ID com validações"""
        
        # Busca entidade existente
        entity = await self.get_by_id(id)
        
        # Validações de negócio antes da remoção
        await self.validate_delete(entity)
        
        # Hook pré-remoção
        await self.before_delete(entity)
        
        # Remove a entidade
        result = await self.repository.delete(id)
        
        # Hook pós-remoção
        if result:
            await self.after_delete(entity)
        
        return result
    
    async def exists(self, id: Any) -> bool:
        """Verifica se entidade existe"""
        return await self.repository.exists(id)
    
    async def search(
        self,
        query: str,
        search_fields: List[str],
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """Busca entidades por texto"""
        if not query.strip():
            return []
        
        return await self.repository.search(
            search_term=query,
            search_fields=search_fields,
            skip=skip,
            limit=limit
        )
    
    # Hooks para validações e ações personalizadas
    
    async def validate_create(self, obj_in: CreateSchemaType) -> None:
        """Validações específicas para criação"""
        pass
    
    async def validate_update(
        self, 
        entity: ModelType, 
        obj_in: UpdateSchemaType
    ) -> None:
        """Validações específicas para atualização"""
        pass
    
    async def validate_delete(self, entity: ModelType) -> None:
        """Validações específicas para remoção"""
        pass
    
    async def after_create(
        self, 
        entity: ModelType, 
        obj_in: CreateSchemaType
    ) -> None:
        """Hook executado após criação"""
        pass
    
    async def after_update(
        self, 
        entity: ModelType, 
        obj_in: UpdateSchemaType
    ) -> None:
        """Hook executado após atualização"""
        pass
    
    async def before_delete(self, entity: ModelType) -> None:
        """Hook executado antes da remoção"""
        pass
    
    async def after_delete(self, entity: ModelType) -> None:
        """Hook executado após remoção"""
        pass
    
    # Métodos utilitários
    
    async def get_by_field(
        self, 
        field: str, 
        value: Any,
        required: bool = False
    ) -> Optional[ModelType]:
        """Busca entidade por campo específico"""
        entity = await self.repository.get_by_field(field, value)
        
        if required and not entity:
            raise NotFoundException(f"{self.entity_name} by {field}", value)
        
        return entity
    
    async def get_multi_by_field(
        self, 
        field: str, 
        value: Any,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """Busca múltiplas entidades por campo específico"""
        return await self.repository.get_multi_by_field(
            field=field,
            value=value,
            skip=skip,
            limit=limit
        )
    
    async def bulk_create(
        self, 
        objects: List[CreateSchemaType],
        current_user_id: Optional[str] = None
    ) -> List[ModelType]:
        """Cria múltiplas entidades em lote"""
        
        # Validações para cada objeto
        for obj_in in objects:
            await self.validate_create(obj_in)
            if current_user_id and hasattr(obj_in, 'created_by'):
                obj_in.created_by = current_user_id
        
        # Cria em lote
        entities = await self.repository.bulk_create(objects)
        
        # Hook pós-criação para cada entidade
        for i, entity in enumerate(entities):
            await self.after_create(entity, objects[i])
        
        return entities
    
    async def validate_unique_field(
        self, 
        field: str, 
        value: Any, 
        exclude_id: Optional[Any] = None
    ) -> None:
        """Valida se um campo é único"""
        existing = await self.repository.get_by_field(field, value)
        
        if existing and (not exclude_id or existing.id != exclude_id):
            raise ValidationException(
                f"{field} must be unique",
                field=field,
                details={"value": str(value)}
            )
