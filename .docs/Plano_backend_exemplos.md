# Exemplos Práticos de Implementação - Backend

Este documento complementa o `Plano_backend.md` com exemplos concretos de implementação dos padrões e arquiteturas descritos.

## 1. Exemplo Completo de Domínio: Tenders

### 1.1. Model (SQLAlchemy)

```python
# app/domains/tenders/models.py
import uuid
from enum import Enum
from decimal import Decimal
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Numeric, ForeignKey, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship
from app.shared.common.base_models import TimestampMixin, UUIDMixin

class TenderStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ANALYZING = "ANALYZING"
    READY = "READY"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"

class Tender(UUIDMixin, TimestampMixin):
    __tablename__ = "tenders"
    
    # Campos básicos
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=True)
    tender_number = Column(String(100), unique=True, nullable=False, index=True)
    
    # Status e datas
    status = Column(ENUM(TenderStatus), default=TenderStatus.DRAFT, nullable=False, index=True)
    publication_date = Column(DateTime(timezone=True), nullable=True)
    opening_date = Column(DateTime(timezone=True), nullable=False)
    closing_date = Column(DateTime(timezone=True), nullable=False)
    
    # Valores
    estimated_value = Column(Numeric(15, 2), nullable=True)
    minimum_value = Column(Numeric(15, 2), nullable=True)
    
    # Metadados e configurações
    requirements = Column(JSON, default=list)  # Lista de requisitos
    evaluation_criteria = Column(JSON, default=dict)  # Critérios de avaliação
    attachments = Column(JSON, default=list)  # Lista de anexos
    
    # Análise de IA
    ai_analysis = Column(JSON, default=dict)  # Resultado da análise
    risk_score = Column(Numeric(3, 2), nullable=True)  # 0.00 a 1.00
    confidence_score = Column(Numeric(3, 2), nullable=True)  # 0.00 a 1.00
    
    # Relacionamentos
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relacionamentos ORM
    company = relationship("Company", back_populates="tenders")
    created_by = relationship("User", back_populates="created_tenders")
    items = relationship("TenderItem", back_populates="tender", cascade="all, delete-orphan")
    quotes = relationship("Quote", back_populates="tender")
    
    def __repr__(self):
        return f"<Tender {self.tender_number}: {self.title}>"

class TenderItem(UUIDMixin, TimestampMixin):
    __tablename__ = "tender_items"
    
    tender_id = Column(UUID(as_uuid=True), ForeignKey("tenders.id"), nullable=False, index=True)
    item_number = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    quantity = Column(Numeric(10, 3), nullable=False)
    unit = Column(String(50), nullable=False)
    estimated_unit_price = Column(Numeric(10, 2), nullable=True)
    specifications = Column(JSON, default=dict)
    
    # Relacionamentos
    tender = relationship("Tender", back_populates="items")
    quote_items = relationship("QuoteItem", back_populates="tender_item")
```

### 1.2. Schemas (Pydantic)

```python
# app/domains/tenders/schemas.py
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
import uuid
from pydantic import BaseModel, Field, validator
from app.domains.tenders.models import TenderStatus

class TenderItemBase(BaseModel):
    item_number: str = Field(..., min_length=1, max_length=50)
    description: str = Field(..., min_length=1)
    quantity: Decimal = Field(..., gt=0)
    unit: str = Field(..., min_length=1, max_length=50)
    estimated_unit_price: Optional[Decimal] = Field(None, ge=0)
    specifications: Dict[str, Any] = Field(default_factory=dict)

class TenderItemCreate(TenderItemBase):
    pass

class TenderItemUpdate(BaseModel):
    item_number: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, min_length=1)
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit: Optional[str] = Field(None, min_length=1, max_length=50)
    estimated_unit_price: Optional[Decimal] = Field(None, ge=0)
    specifications: Optional[Dict[str, Any]] = None

class TenderItem(TenderItemBase):
    id: uuid.UUID
    tender_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class TenderBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    opening_date: datetime
    closing_date: datetime
    estimated_value: Optional[Decimal] = Field(None, ge=0)
    minimum_value: Optional[Decimal] = Field(None, ge=0)
    requirements: List[str] = Field(default_factory=list)
    evaluation_criteria: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('closing_date')
    def closing_after_opening(cls, v, values):
        if 'opening_date' in values and v <= values['opening_date']:
            raise ValueError('Closing date must be after opening date')
        return v
    
    @validator('minimum_value')
    def minimum_less_than_estimated(cls, v, values):
        if v is not None and 'estimated_value' in values and values['estimated_value'] is not None:
            if v > values['estimated_value']:
                raise ValueError('Minimum value cannot be greater than estimated value')
        return v

class TenderCreate(TenderBase):
    items: List[TenderItemCreate] = Field(default_factory=list)

class TenderUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    opening_date: Optional[datetime] = None
    closing_date: Optional[datetime] = None
    estimated_value: Optional[Decimal] = Field(None, ge=0)
    minimum_value: Optional[Decimal] = Field(None, ge=0)
    requirements: Optional[List[str]] = None
    evaluation_criteria: Optional[Dict[str, Any]] = None
    status: Optional[TenderStatus] = None

class TenderInDB(TenderBase):
    id: uuid.UUID
    tender_number: str
    status: TenderStatus
    company_id: uuid.UUID
    created_by_id: uuid.UUID
    publication_date: Optional[datetime]
    ai_analysis: Dict[str, Any]
    risk_score: Optional[Decimal]
    confidence_score: Optional[Decimal]
    created_at: datetime
    updated_at: datetime

class Tender(TenderInDB):
    items: List[TenderItem] = Field(default_factory=list)
    
    class Config:
        from_attributes = True

class TenderSummary(BaseModel):
    """Schema para listagens com dados resumidos"""
    id: uuid.UUID
    title: str
    tender_number: str
    status: TenderStatus
    opening_date: datetime
    closing_date: datetime
    estimated_value: Optional[Decimal]
    risk_score: Optional[Decimal]
    items_count: int
    quotes_count: int
    
    class Config:
        from_attributes = True

class TenderAnalysisResult(BaseModel):
    """Resultado da análise de IA"""
    summary: str
    key_requirements: List[str]
    potential_risks: List[Dict[str, Any]]
    estimated_complexity: str  # "LOW", "MEDIUM", "HIGH"
    recommended_actions: List[str]
    confidence_score: Decimal
    processing_time_seconds: float
```

### 1.3. Repository

```python
# app/domains/tenders/repository.py
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from app.shared.common.base_repository import SQLAlchemyRepository
from app.domains.tenders.models import Tender, TenderItem, TenderStatus

class TenderRepository(SQLAlchemyRepository[Tender]):
    """Repository específico para Tenders"""
    
    def __init__(self):
        super().__init__(Tender)
    
    async def get_with_items(self, db: AsyncSession, tender_id: UUID) -> Optional[Tender]:
        """Buscar tender com items eager loaded"""
        stmt = (
            select(Tender)
            .options(selectinload(Tender.items))
            .where(Tender.id == tender_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_company(
        self, 
        db: AsyncSession, 
        company_id: UUID,
        *,
        status: Optional[TenderStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Tender]:
        """Buscar tenders por empresa com filtros"""
        
        stmt = select(Tender).where(Tender.company_id == company_id)
        
        if status:
            stmt = stmt.where(Tender.status == status)
        
        stmt = stmt.offset(skip).limit(limit).order_by(Tender.created_at.desc())
        
        result = await db.execute(stmt)
        return result.scalars().all()
    
    async def get_summary_by_company(
        self, 
        db: AsyncSession, 
        company_id: UUID,
        **filters
    ) -> List[Dict[str, Any]]:
        """Buscar resumo de tenders com contagens"""
        
        # Subquery para contar items
        items_count = (
            select(func.count(TenderItem.id))
            .where(TenderItem.tender_id == Tender.id)
            .scalar_subquery()
        )
        
        stmt = (
            select(
                Tender.id,
                Tender.title,
                Tender.tender_number,
                Tender.status,
                Tender.opening_date,
                Tender.closing_date,
                Tender.estimated_value,
                Tender.risk_score,
                items_count.label('items_count'),
                func.count(Quote.id).label('quotes_count')
            )
            .outerjoin(Quote)
            .where(Tender.company_id == company_id)
            .group_by(Tender.id)
            .order_by(Tender.created_at.desc())
        )
        
        # Aplicar filtros adicionais
        if filters.get('status'):
            stmt = stmt.where(Tender.status == filters['status'])
        
        if filters.get('date_from'):
            stmt = stmt.where(Tender.opening_date >= filters['date_from'])
        
        if filters.get('date_to'):
            stmt = stmt.where(Tender.closing_date <= filters['date_to'])
        
        result = await db.execute(stmt)
        return [dict(row._mapping) for row in result]
    
    async def update_ai_analysis(
        self, 
        db: AsyncSession, 
        tender_id: UUID, 
        analysis_data: Dict[str, Any]
    ) -> Optional[Tender]:
        """Atualizar análise de IA"""
        
        tender = await self.get(db, tender_id)
        if not tender:
            return None
        
        update_data = {
            'ai_analysis': analysis_data,
            'risk_score': analysis_data.get('risk_score'),
            'confidence_score': analysis_data.get('confidence_score'),
            'status': TenderStatus.READY if tender.status == TenderStatus.ANALYZING else tender.status
        }
        
        return await self.update(db, db_obj=tender, obj_in=update_data)
    
    async def get_requiring_analysis(self, db: AsyncSession, limit: int = 10) -> List[Tender]:
        """Buscar tenders que precisam de análise de IA"""
        
        stmt = (
            select(Tender)
            .where(
                and_(
                    Tender.status == TenderStatus.ANALYZING,
                    or_(
                        Tender.ai_analysis == {},
                        Tender.ai_analysis.is_(None)
                    )
                )
            )
            .limit(limit)
            .order_by(Tender.created_at.asc())
        )
        
        result = await db.execute(stmt)
        return result.scalars().all()
```

### 1.4. Service Layer

```python
# app/domains/tenders/services.py
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.shared.common.base_service import CRUDService
from app.domains.tenders.repository import TenderRepository
from app.domains.tenders.models import Tender, TenderStatus
from app.domains.tenders.schemas import TenderCreate, TenderUpdate, TenderAnalysisResult
from app.shared.infrastructure.ai.services import AIService
from app.tasks.ai_tasks import process_tender_document
from app.core.logging import logger
import secrets

class TenderService(CRUDService[Tender, TenderRepository]):
    """Service para gerenciamento de editais"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(TenderRepository())
        self.db = db
        self.ai_service = AIService()
    
    async def create_tender(
        self, 
        tender_data: TenderCreate, 
        company_id: UUID, 
        user_id: UUID
    ) -> Tender:
        """Criar novo edital com validações de negócio"""
        
        # Gerar número único do edital
        tender_number = await self._generate_tender_number(company_id)
        
        # Preparar dados para criação
        create_data = {
            **tender_data.model_dump(exclude={'items'}),
            'tender_number': tender_number,
            'company_id': company_id,
            'created_by_id': user_id,
            'status': TenderStatus.DRAFT
        }
        
        # Criar tender principal
        tender = await self.repository.create(self.db, obj_in=create_data)
        
        # Criar items se fornecidos
        if tender_data.items:
            await self._create_tender_items(tender.id, tender_data.items)
        
        logger.info(
            "Tender created successfully",
            tender_id=str(tender.id),
            tender_number=tender_number,
            company_id=str(company_id),
            user_id=str(user_id)
        )
        
        return await self.repository.get_with_items(self.db, tender.id)
    
    async def update_tender(
        self, 
        tender_id: UUID, 
        tender_data: TenderUpdate, 
        user_id: UUID
    ) -> Optional[Tender]:
        """Atualizar edital com validações"""
        
        tender = await self.repository.get(self.db, tender_id)
        if not tender:
            return None
        
        # Validar permissões de edição
        await self._validate_edit_permissions(tender, user_id)
        
        # Validar regras de negócio para atualização
        await self._validate_update_rules(tender, tender_data)
        
        # Atualizar
        update_data = tender_data.model_dump(exclude_unset=True)
        updated_tender = await self.repository.update(
            self.db, db_obj=tender, obj_in=update_data
        )
        
        logger.info(
            "Tender updated successfully",
            tender_id=str(tender_id),
            user_id=str(user_id),
            updated_fields=list(update_data.keys())
        )
        
        return updated_tender
    
    async def publish_tender(self, tender_id: UUID, user_id: UUID) -> Tender:
        """Publicar edital (transição de status)"""
        
        tender = await self.repository.get_with_items(self.db, tender_id)
        if not tender:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tender not found"
            )
        
        # Validar se pode ser publicado
        await self._validate_publication_requirements(tender)
        
        # Atualizar status
        from datetime import datetime
        update_data = {
            'status': TenderStatus.PUBLISHED,
            'publication_date': datetime.utcnow()
        }
        
        updated_tender = await self.repository.update(
            self.db, db_obj=tender, obj_in=update_data
        )
        
        # Trigger notificações/emails assíncronos
        await self._trigger_publication_notifications(updated_tender)
        
        logger.info(
            "Tender published successfully",
            tender_id=str(tender_id),
            user_id=str(user_id)
        )
        
        return updated_tender
    
    async def analyze_with_ai(self, tender_id: UUID, file_path: str) -> str:
        """Iniciar análise de edital com IA"""
        
        tender = await self.repository.get(self.db, tender_id)
        if not tender:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tender not found"
            )
        
        # Atualizar status para analyzing
        await self.repository.update(
            self.db, 
            db_obj=tender, 
            obj_in={'status': TenderStatus.ANALYZING}
        )
        
        # Disparar task assíncrona
        task = process_tender_document.delay(str(tender_id), file_path)
        
        logger.info(
            "AI analysis started",
            tender_id=str(tender_id),
            task_id=task.id,
            file_path=file_path
        )
        
        return task.id
    
    async def save_analysis_result(
        self, 
        tender_id: UUID, 
        analysis_result: TenderAnalysisResult
    ) -> Tender:
        """Salvar resultado da análise de IA"""
        
        analysis_data = {
            **analysis_result.model_dump(),
            'processed_at': datetime.utcnow().isoformat()
        }
        
        tender = await self.repository.update_ai_analysis(
            self.db, tender_id, analysis_data
        )
        
        if not tender:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tender not found"
            )
        
        logger.info(
            "AI analysis completed",
            tender_id=str(tender_id),
            confidence_score=float(analysis_result.confidence_score),
            estimated_complexity=analysis_result.estimated_complexity
        )
        
        return tender
    
    async def get_company_tenders_summary(
        self, 
        company_id: UUID, 
        **filters
    ) -> List[Dict[str, Any]]:
        """Obter resumo de editais da empresa"""
        
        return await self.repository.get_summary_by_company(
            self.db, company_id, **filters
        )
    
    # Métodos privados para validações e lógica interna
    
    async def _generate_tender_number(self, company_id: UUID) -> str:
        """Gerar número único do edital"""
        from datetime import datetime
        
        year = datetime.utcnow().year
        random_suffix = secrets.token_hex(4).upper()
        
        # Format: YEAR-COMPANY_PREFIX-RANDOM
        company_prefix = str(company_id)[:8].upper()
        return f"{year}-{company_prefix}-{random_suffix}"
    
    async def _create_tender_items(self, tender_id: UUID, items_data: List[Any]):
        """Criar items do edital"""
        # Implementar criação de items
        pass
    
    async def _validate_edit_permissions(self, tender: Tender, user_id: UUID):
        """Validar se usuário pode editar o edital"""
        
        # Verificar se é o criador ou tem permissão de admin
        if tender.created_by_id != user_id:
            # Aqui verificaríamos permissões mais granulares
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to edit this tender"
            )
    
    async def _validate_update_rules(self, tender: Tender, update_data: TenderUpdate):
        """Validar regras de negócio para atualização"""
        
        # Não permitir alteração de datas se já publicado
        if tender.status == TenderStatus.PUBLISHED:
            if update_data.opening_date or update_data.closing_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot change dates of published tender"
                )
    
    async def _validate_publication_requirements(self, tender: Tender):
        """Validar se edital pode ser publicado"""
        
        if tender.status != TenderStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only draft tenders can be published"
            )
        
        if not tender.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tender must have at least one item to be published"
            )
        
        from datetime import datetime
        if tender.opening_date <= datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Opening date must be in the future"
            )
    
    async def _trigger_publication_notifications(self, tender: Tender):
        """Disparar notificações de publicação"""
        # Implementar envio de notificações/emails
        pass
```

### 1.5. Router (FastAPI)

```python
# app/domains/tenders/router.py
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user, get_service_factory
from app.core.factory import ServiceFactory
from app.domains.tenders.schemas import (
    Tender, TenderCreate, TenderUpdate, TenderSummary, TenderAnalysisResult
)
from app.domains.auth.models import User
from app.shared.common.validators import SecurityValidators
from app.core.logging import logger, log_execution

router = APIRouter(prefix="/tenders", tags=["tenders"])

@router.post("/", response_model=Tender, status_code=status.HTTP_201_CREATED)
@log_execution("create_tender")
async def create_tender(
    tender_data: TenderCreate,
    current_user: User = Depends(get_current_user),
    service_factory: ServiceFactory = Depends(get_service_factory)
) -> Tender:
    """Criar novo edital"""
    
    tender_service = service_factory.get_tender_service()
    
    try:
        tender = await tender_service.create_tender(
            tender_data=tender_data,
            company_id=current_user.company_id,
            user_id=current_user.id
        )
        
        return tender
        
    except Exception as e:
        logger.error(
            "Failed to create tender",
            user_id=str(current_user.id),
            company_id=str(current_user.company_id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create tender: {str(e)}"
        )

@router.get("/", response_model=List[TenderSummary])
async def list_tenders(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    current_user: User = Depends(get_current_user),
    service_factory: ServiceFactory = Depends(get_service_factory)
) -> List[TenderSummary]:
    """Listar editais da empresa"""
    
    tender_service = service_factory.get_tender_service()
    
    filters = {}
    if status_filter:
        filters['status'] = status_filter
    
    tenders_data = await tender_service.get_company_tenders_summary(
        company_id=current_user.company_id,
        **filters
    )
    
    return [TenderSummary(**tender) for tender in tenders_data]

@router.get("/{tender_id}", response_model=Tender)
async def get_tender(
    tender_id: UUID,
    current_user: User = Depends(get_current_user),
    service_factory: ServiceFactory = Depends(get_service_factory)
) -> Tender:
    """Buscar edital específico"""
    
    tender_service = service_factory.get_tender_service()
    
    tender = await tender_service.get_by_id(tender_id)
    
    if not tender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tender not found"
        )
    
    # Verificar se pertence à empresa do usuário
    if tender.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return tender

@router.put("/{tender_id}", response_model=Tender)
@log_execution("update_tender")
async def update_tender(
    tender_id: UUID,
    tender_data: TenderUpdate,
    current_user: User = Depends(get_current_user),
    service_factory: ServiceFactory = Depends(get_service_factory)
) -> Tender:
    """Atualizar edital"""
    
    tender_service = service_factory.get_tender_service()
    
    tender = await tender_service.update_tender(
        tender_id=tender_id,
        tender_data=tender_data,
        user_id=current_user.id
    )
    
    if not tender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tender not found"
        )
    
    return tender

@router.post("/{tender_id}/publish", response_model=Tender)
@log_execution("publish_tender")
async def publish_tender(
    tender_id: UUID,
    current_user: User = Depends(get_current_user),
    service_factory: ServiceFactory = Depends(get_service_factory)
) -> Tender:
    """Publicar edital"""
    
    tender_service = service_factory.get_tender_service()
    
    tender = await tender_service.publish_tender(
        tender_id=tender_id,
        user_id=current_user.id
    )
    
    return tender

@router.post("/{tender_id}/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_tender_document(
    tender_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    service_factory: ServiceFactory = Depends(get_service_factory)
) -> Dict[str, str]:
    """Upload e análise de documento de edital"""
    
    # Validar arquivo
    if not SecurityValidators.validate_file_type(
        file.filename, 
        [".pdf", ".doc", ".docx"]
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type"
        )
    
    # Salvar arquivo temporariamente
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_file_path = tmp_file.name
    
    try:
        tender_service = service_factory.get_tender_service()
        
        # Iniciar análise assíncrona
        task_id = await tender_service.analyze_with_ai(
            tender_id=tender_id,
            file_path=tmp_file_path
        )
        
        return {
            "message": "File uploaded successfully, analysis started",
            "task_id": task_id
        }
        
    except Exception as e:
        # Limpar arquivo temporário em caso de erro
        os.unlink(tmp_file_path)
        raise

@router.get("/{tender_id}/analysis", response_model=Dict[str, Any])
async def get_tender_analysis(
    tender_id: UUID,
    current_user: User = Depends(get_current_user),
    service_factory: ServiceFactory = Depends(get_service_factory)
) -> Dict[str, Any]:
    """Obter resultado da análise de IA do edital"""
    
    tender_service = service_factory.get_tender_service()
    
    tender = await tender_service.get_by_id(tender_id)
    
    if not tender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tender not found"
        )
    
    if tender.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    if not tender.ai_analysis:
        return {"status": "not_analyzed", "analysis": None}
    
    return {
        "status": "completed",
        "analysis": tender.ai_analysis,
        "risk_score": tender.risk_score,
        "confidence_score": tender.confidence_score
    }
```

## 2. Exemplo de Task Celery Complexa

```python
# app/tasks/ai_tasks.py
import asyncio
import tempfile
import os
from typing import Dict, Any
from celery import current_app as celery_app
from app.tasks.base_task import OptimizedTask
from app.shared.infrastructure.ai.services import AIService
from app.domains.tenders.services import TenderService
from app.domains.tenders.schemas import TenderAnalysisResult
from app.core.database import get_db
from app.core.logging import logger

@celery_app.task(
    base=OptimizedTask,
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,)
)
def process_tender_document(self, tender_id: str, file_path: str):
    """
    Processar documento de edital com IA
    Task complexa com retry, logging e cleanup
    """
    
    async def _process_async():
        async for db in get_db():
            try:
                # Inicializar services
                ai_service = AIService()
                tender_service = TenderService(db)
                
                logger.info(
                    "Starting tender document processing",
                    tender_id=tender_id,
                    file_path=file_path
                )
                
                # Verificar se arquivo existe
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"File not found: {file_path}")
                
                # Ler conteúdo do arquivo
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                
                # Processar com IA - múltiplos prompts
                analysis_tasks = [
                    ai_service.extract_basic_info(file_content),
                    ai_service.identify_requirements(file_content),
                    ai_service.assess_risks(file_content),
                    ai_service.estimate_complexity(file_content)
                ]
                
                # Executar análises em paralelo
                results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
                
                # Consolidar resultados
                analysis_result = _consolidate_ai_results(results)
                
                # Salvar no banco
                tender_analysis = TenderAnalysisResult(**analysis_result)
                await tender_service.save_analysis_result(tender_id, tender_analysis)
                
                logger.info(
                    "Tender document processing completed",
                    tender_id=tender_id,
                    confidence_score=analysis_result.get('confidence_score', 0)
                )
                
                return {
                    "status": "completed",
                    "tender_id": tender_id,
                    "analysis_summary": analysis_result.get("summary", "")
                }
                
            except Exception as exc:
                logger.error(
                    "Tender document processing failed",
                    tender_id=tender_id,
                    error=str(exc),
                    retry_count=self.request.retries
                )
                
                # Atualizar status para erro se esgotaram as tentativas
                if self.request.retries >= self.max_retries - 1:
                    try:
                        await tender_service.update_status(tender_id, "ERROR")
                    except:
                        pass
                
                raise self.retry(exc=exc)
                
            finally:
                # Cleanup do arquivo temporário
                try:
                    if os.path.exists(file_path):
                        os.unlink(file_path)
                        logger.debug("Temporary file cleaned up", file_path=file_path)
                except:
                    logger.warning("Failed to cleanup temporary file", file_path=file_path)
    
    # Executar função assíncrona
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_process_async())
    finally:
        loop.close()

def _consolidate_ai_results(results: list) -> Dict[str, Any]:
    """Consolidar resultados das múltiplas análises de IA"""
    
    basic_info, requirements, risks, complexity = results
    
    # Tratar exceções
    if isinstance(basic_info, Exception):
        basic_info = {"summary": "Failed to extract basic info"}
    
    if isinstance(requirements, Exception):
        requirements = {"key_requirements": []}
    
    if isinstance(risks, Exception):
        risks = {"potential_risks": [], "risk_score": 0.5}
    
    if isinstance(complexity, Exception):
        complexity = {"estimated_complexity": "MEDIUM", "confidence_score": 0.5}
    
    # Consolidar
    return {
        "summary": basic_info.get("summary", ""),
        "key_requirements": requirements.get("key_requirements", []),
        "potential_risks": risks.get("potential_risks", []),
        "estimated_complexity": complexity.get("estimated_complexity", "MEDIUM"),
        "recommended_actions": _generate_recommendations(risks, complexity),
        "confidence_score": min(
            risks.get("confidence_score", 0.5),
            complexity.get("confidence_score", 0.5)
        ),
        "processing_time_seconds": 0.0  # Será calculado pelo OptimizedTask
    }

def _generate_recommendations(risks: Dict, complexity: Dict) -> list:
    """Gerar recomendações baseadas nos riscos e complexidade"""
    
    recommendations = []
    
    risk_level = risks.get("risk_score", 0.5)
    complexity_level = complexity.get("estimated_complexity", "MEDIUM")
    
    if risk_level > 0.7:
        recommendations.append("Atenção especial aos riscos identificados")
        recommendations.append("Considerar consulta com especialista jurídico")
    
    if complexity_level == "HIGH":
        recommendations.append("Alocar tempo adicional para preparação da proposta")
        recommendations.append("Revisar equipe técnica necessária")
    
    if risk_level > 0.5 and complexity_level in ["MEDIUM", "HIGH"]:
        recommendations.append("Realizar análise detalhada antes de participar")
    
    return recommendations or ["Proceder com análise padrão"]
```

## 3. WebSocket Manager Avançado

```python
# app/websockets/connection_manager.py
import json
import asyncio
from typing import Dict, List, Set, Optional, Any
from uuid import UUID
import weakref
from fastapi import WebSocket
from app.core.logging import logger

class ConnectionManager:
    """Gerenciador avançado de conexões WebSocket"""
    
    def __init__(self):
        # Conexões ativas por usuário
        self._user_connections: Dict[UUID, Set[WebSocket]] = {}
        
        # Conexões ativas por empresa
        self._company_connections: Dict[UUID, Set[WebSocket]] = {}
        
        # Salas/channels de conexões
        self._room_connections: Dict[str, Set[WebSocket]] = {}
        
        # Metadados das conexões
        self._connection_metadata: weakref.WeakKeyDictionary = weakref.WeakKeyDictionary()
        
        # Lock para thread safety
        self._lock = asyncio.Lock()
    
    async def connect(
        self, 
        websocket: WebSocket, 
        user_id: UUID, 
        company_id: UUID,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Conectar usuário ao WebSocket"""
        
        await websocket.accept()
        
        async with self._lock:
            # Adicionar às conexões por usuário
            if user_id not in self._user_connections:
                self._user_connections[user_id] = set()
            self._user_connections[user_id].add(websocket)
            
            # Adicionar às conexões por empresa
            if company_id not in self._company_connections:
                self._company_connections[company_id] = set()
            self._company_connections[company_id].add(websocket)
            
            # Salvar metadados
            self._connection_metadata[websocket] = {
                'user_id': user_id,
                'company_id': company_id,
                'connected_at': datetime.utcnow(),
                **(metadata or {})
            }
        
        logger.info(
            "WebSocket connection established",
            user_id=str(user_id),
            company_id=str(company_id),
            total_connections=len(self._connection_metadata)
        )
    
    async def disconnect(self, websocket: WebSocket):
        """Desconectar WebSocket"""
        
        metadata = self._connection_metadata.get(websocket)
        if not metadata:
            return
        
        user_id = metadata['user_id']
        company_id = metadata['company_id']
        
        async with self._lock:
            # Remover das conexões por usuário
            if user_id in self._user_connections:
                self._user_connections[user_id].discard(websocket)
                if not self._user_connections[user_id]:
                    del self._user_connections[user_id]
            
            # Remover das conexões por empresa
            if company_id in self._company_connections:
                self._company_connections[company_id].discard(websocket)
                if not self._company_connections[company_id]:
                    del self._company_connections[company_id]
            
            # Remover de todas as salas
            for room_connections in self._room_connections.values():
                room_connections.discard(websocket)
        
        logger.info(
            "WebSocket connection closed",
            user_id=str(user_id),
            company_id=str(company_id),
            total_connections=len(self._connection_metadata) - 1
        )
    
    async def join_room(self, websocket: WebSocket, room_name: str):
        """Entrar em uma sala/channel"""
        
        async with self._lock:
            if room_name not in self._room_connections:
                self._room_connections[room_name] = set()
            self._room_connections[room_name].add(websocket)
        
        metadata = self._connection_metadata.get(websocket, {})
        logger.debug(
            "User joined room",
            user_id=str(metadata.get('user_id')),
            room_name=room_name
        )
    
    async def leave_room(self, websocket: WebSocket, room_name: str):
        """Sair de uma sala/channel"""
        
        async with self._lock:
            if room_name in self._room_connections:
                self._room_connections[room_name].discard(websocket)
                if not self._room_connections[room_name]:
                    del self._room_connections[room_name]
    
    async def send_to_user(self, user_id: UUID, message: Dict[str, Any]):
        """Enviar mensagem para todas as conexões de um usuário"""
        
        connections = self._user_connections.get(user_id, set())
        if not connections:
            logger.debug("No active connections for user", user_id=str(user_id))
            return 0
        
        message_str = json.dumps(message, default=str)
        sent_count = 0
        
        # Criar lista de conexões para evitar modificação durante iteração
        connection_list = list(connections)
        
        for websocket in connection_list:
            try:
                await websocket.send_text(message_str)
                sent_count += 1
            except Exception as e:
                logger.warning(
                    "Failed to send message to WebSocket",
                    user_id=str(user_id),
                    error=str(e)
                )
                # Remover conexão inválida
                await self.disconnect(websocket)
        
        return sent_count
    
    async def send_to_company(self, company_id: UUID, message: Dict[str, Any]):
        """Enviar mensagem para todos os usuários de uma empresa"""
        
        connections = self._company_connections.get(company_id, set())
        if not connections:
            return 0
        
        message_str = json.dumps(message, default=str)
        sent_count = 0
        
        connection_list = list(connections)
        
        for websocket in connection_list:
            try:
                await websocket.send_text(message_str)
                sent_count += 1
            except Exception as e:
                logger.warning(
                    "Failed to send company message to WebSocket",
                    company_id=str(company_id),
                    error=str(e)
                )
                await self.disconnect(websocket)
        
        return sent_count
    
    async def send_to_room(self, room_name: str, message: Dict[str, Any]):
        """Enviar mensagem para uma sala/channel"""
        
        connections = self._room_connections.get(room_name, set())
        if not connections:
            return 0
        
        message_str = json.dumps(message, default=str)
        sent_count = 0
        
        connection_list = list(connections)
        
        for websocket in connection_list:
            try:
                await websocket.send_text(message_str)
                sent_count += 1
            except Exception as e:
                logger.warning(
                    "Failed to send room message to WebSocket",
                    room_name=room_name,
                    error=str(e)
                )
                await self.disconnect(websocket)
        
        return sent_count
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast para todas as conexões ativas"""
        
        all_connections = set()
        for connections in self._user_connections.values():
            all_connections.update(connections)
        
        if not all_connections:
            return 0
        
        message_str = json.dumps(message, default=str)
        sent_count = 0
        
        connection_list = list(all_connections)
        
        for websocket in connection_list:
            try:
                await websocket.send_text(message_str)
                sent_count += 1
            except Exception as e:
                logger.warning("Failed to broadcast message", error=str(e))
                await self.disconnect(websocket)
        
        return sent_count
    
    def get_user_connection_count(self, user_id: UUID) -> int:
        """Obter número de conexões ativas de um usuário"""
        return len(self._user_connections.get(user_id, set()))
    
    def get_company_connection_count(self, company_id: UUID) -> int:
        """Obter número de conexões ativas de uma empresa"""
        return len(self._company_connections.get(company_id, set()))
    
    def get_total_connections(self) -> int:
        """Obter número total de conexões ativas"""
        return len(self._connection_metadata)
    
    def get_stats(self) -> Dict[str, Any]:
        """Obter estatísticas das conexões"""
        
        return {
            'total_connections': self.get_total_connections(),
            'total_users_connected': len(self._user_connections),
            'total_companies_connected': len(self._company_connections),
            'total_rooms': len(self._room_connections),
            'room_stats': {
                room: len(connections) 
                for room, connections in self._room_connections.items()
            }
        }

# Instância global
connection_manager = ConnectionManager()
```

Este conjunto de exemplos mostra como implementar na prática os padrões arquiteturais descritos no plano técnico principal. Cada exemplo demonstra:

1. **Separação clara de responsabilidades** entre Model, Schema, Repository, Service e Router
2. **Validações de negócio** centralizadas nos Services
3. **Logging estruturado** com contexto
4. **Error handling** robusto com HTTPExceptions apropriadas
5. **Tasks assíncronas** com retry e cleanup
6. **WebSocket management** escalável
7. **Type hints** completos para melhor IDE support
8. **Documentação** inline para facilitar manutenção

Estes exemplos servem como template para implementar os demais domínios do sistema seguindo os mesmos padrões de qualidade e arquitetura.
