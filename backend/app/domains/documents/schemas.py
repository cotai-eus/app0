"""
Schemas for the documents domain.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domains.documents.models import DocumentType, ProcessingStatus, ExtractionType


# Base schemas
class DocumentBase(BaseModel):
    """Base schema for documents."""
    model_config = ConfigDict(from_attributes=True)
    
    filename: str = Field(..., description="Nome do arquivo")
    file_path: str = Field(..., description="Caminho do arquivo")
    document_type: DocumentType = Field(..., description="Tipo do documento")
    file_size: int = Field(..., description="Tamanho do arquivo em bytes")
    mime_type: str = Field(..., description="Tipo MIME")
    doc_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadados do documento")


class DocumentCreate(DocumentBase):
    """Schema for creating documents."""
    company_id: UUID = Field(..., description="ID da empresa")


class DocumentUpdate(BaseModel):
    """Schema for updating documents."""
    model_config = ConfigDict(from_attributes=True)
    
    filename: Optional[str] = None
    document_type: Optional[DocumentType] = None
    doc_metadata: Optional[Dict[str, Any]] = None


class DocumentResponse(DocumentBase):
    """Schema for document responses."""
    id: UUID
    company_id: UUID
    created_at: datetime
    updated_at: datetime


# Text Extraction schemas
class TextExtractionBase(BaseModel):
    """Base schema for text extractions."""
    model_config = ConfigDict(from_attributes=True)
    
    extraction_type: ExtractionType = Field(..., description="Tipo de extração")
    status: ProcessingStatus = Field(..., description="Status do processamento")
    extracted_text: Optional[str] = Field(default=None, description="Texto extraído")
    confidence_score: Optional[float] = Field(default=None, description="Score de confiança")
    extraction_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadados da extração")


class TextExtractionCreate(TextExtractionBase):
    """Schema for creating text extractions."""
    document_id: UUID = Field(..., description="ID do documento")


class TextExtractionResponse(TextExtractionBase):
    """Schema for text extraction responses."""
    id: UUID
    document_id: UUID
    processing_started_at: Optional[datetime]
    processing_completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


# AI Processing Job schemas
class AIProcessingJobBase(BaseModel):
    """Base schema for AI processing jobs."""
    model_config = ConfigDict(from_attributes=True)
    
    job_type: str = Field(..., description="Tipo do job")
    status: ProcessingStatus = Field(..., description="Status do processamento")
    prompt_used: Optional[str] = Field(default=None, description="Prompt utilizado")
    ai_response: Optional[str] = Field(default=None, description="Resposta da IA")
    confidence_score: Optional[float] = Field(default=None, description="Score de confiança")
    processing_time_ms: Optional[int] = Field(default=None, description="Tempo de processamento em ms")
    ai_model: Optional[str] = Field(default=None, description="Modelo de IA utilizado")
    cost_estimation: Optional[float] = Field(default=None, description="Estimativa de custo")
    job_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadados do job")


class AIProcessingJobCreate(AIProcessingJobBase):
    """Schema for creating AI processing jobs."""
    document_id: UUID = Field(..., description="ID do documento")


class AIProcessingJobResponse(AIProcessingJobBase):
    """Schema for AI processing job responses."""
    id: UUID
    document_id: UUID
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


# Tender AI Analysis schemas
class TenderAIAnalysisBase(BaseModel):
    """Base schema for tender AI analysis."""
    model_config = ConfigDict(from_attributes=True)
    
    summary: Optional[str] = Field(default=None, description="Resumo da licitação")
    key_requirements: Optional[List[str]] = Field(default=None, description="Requisitos principais")
    deadline: Optional[datetime] = Field(default=None, description="Prazo limite")
    estimated_value: Optional[float] = Field(default=None, description="Valor estimado")
    risk_factors: Optional[List[str]] = Field(default=None, description="Fatores de risco")
    recommendation: Optional[str] = Field(default=None, description="Recomendação")
    confidence_level: Optional[float] = Field(default=None, description="Nível de confiança")
    analysis_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadados da análise")


class TenderAIAnalysisCreate(TenderAIAnalysisBase):
    """Schema for creating tender AI analysis."""
    tender_id: UUID = Field(..., description="ID da licitação")
    ai_processing_job_id: UUID = Field(..., description="ID do job de processamento IA")


class TenderAIAnalysisResponse(TenderAIAnalysisBase):
    """Schema for tender AI analysis responses."""
    id: UUID
    tender_id: UUID
    ai_processing_job_id: UUID
    created_at: datetime
    updated_at: datetime


# AI Prompt Template schemas
class AIPromptTemplateBase(BaseModel):
    """Base schema for AI prompt templates."""
    model_config = ConfigDict(from_attributes=True)
    
    name: str = Field(..., description="Nome do template")
    template_type: str = Field(..., description="Tipo do template")
    prompt_template: str = Field(..., description="Template do prompt")
    variables: Optional[List[str]] = Field(default=None, description="Variáveis do template")
    description: Optional[str] = Field(default=None, description="Descrição do template")
    usage_count: int = Field(default=0, description="Contador de uso")
    template_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadados do template")


class AIPromptTemplateCreate(AIPromptTemplateBase):
    """Schema for creating AI prompt templates."""
    company_id: UUID = Field(..., description="ID da empresa")


class AIPromptTemplateUpdate(BaseModel):
    """Schema for updating AI prompt templates."""
    model_config = ConfigDict(from_attributes=True)
    
    name: Optional[str] = None
    template_type: Optional[str] = None
    prompt_template: Optional[str] = None
    variables: Optional[List[str]] = None
    description: Optional[str] = None
    template_metadata: Optional[Dict[str, Any]] = None


class AIPromptTemplateResponse(AIPromptTemplateBase):
    """Schema for AI prompt template responses."""
    id: UUID
    company_id: UUID
    created_at: datetime
    updated_at: datetime


# AI Response Cache schemas
class AIResponseCacheBase(BaseModel):
    """Base schema for AI response cache."""
    model_config = ConfigDict(from_attributes=True)
    
    prompt_hash: str = Field(..., description="Hash do prompt")
    prompt_text: str = Field(..., description="Texto do prompt")
    ai_response: str = Field(..., description="Resposta da IA")
    ai_model: str = Field(..., description="Modelo de IA")
    response_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadados da resposta")
    hit_count: int = Field(default=1, description="Contador de hits")
    expires_at: Optional[datetime] = Field(default=None, description="Data de expiração")


class AIResponseCacheCreate(AIResponseCacheBase):
    """Schema for creating AI response cache."""
    company_id: UUID = Field(..., description="ID da empresa")


class AIResponseCacheResponse(AIResponseCacheBase):
    """Schema for AI response cache responses."""
    id: UUID
    company_id: UUID
    last_accessed_at: datetime
    created_at: datetime
    updated_at: datetime


# Bulk operations schemas
class DocumentBulkUploadRequest(BaseModel):
    """Schema for bulk document upload."""
    model_config = ConfigDict(from_attributes=True)
    
    files: List[DocumentCreate] = Field(..., description="Lista de documentos para upload")
    process_with_ai: bool = Field(default=True, description="Processar com IA")
    extraction_types: List[ExtractionType] = Field(default=[ExtractionType.OCR], description="Tipos de extração")


class DocumentBulkUploadResponse(BaseModel):
    """Schema for bulk document upload response."""
    model_config = ConfigDict(from_attributes=True)
    
    uploaded_documents: List[DocumentResponse] = Field(..., description="Documentos carregados")
    processing_jobs: List[AIProcessingJobResponse] = Field(..., description="Jobs de processamento criados")
    total_uploaded: int = Field(..., description="Total de documentos carregados")
    total_failed: int = Field(..., description="Total de falhas")
    errors: List[str] = Field(default=[], description="Lista de erros")


# Search and filter schemas
class DocumentSearchRequest(BaseModel):
    """Schema for document search."""
    model_config = ConfigDict(from_attributes=True)
    
    query: str = Field(..., description="Texto da busca")
    document_types: Optional[List[DocumentType]] = Field(default=None, description="Filtro por tipos")
    date_from: Optional[datetime] = Field(default=None, description="Data inicial")
    date_to: Optional[datetime] = Field(default=None, description="Data final")
    company_id: Optional[UUID] = Field(default=None, description="Filtro por empresa")
    limit: int = Field(default=20, ge=1, le=100, description="Limite de resultados")
    offset: int = Field(default=0, ge=0, description="Offset para paginação")


class DocumentSearchResponse(BaseModel):
    """Schema for document search response."""
    model_config = ConfigDict(from_attributes=True)
    
    documents: List[DocumentResponse] = Field(..., description="Documentos encontrados")
    total_count: int = Field(..., description="Total de documentos")
    query: str = Field(..., description="Query utilizada")
    execution_time_ms: int = Field(..., description="Tempo de execução em ms")
