"""
Modelos de dados para processamento de IA
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class AIProcessingResult(BaseModel):
    """Resultado base do processamento de IA"""
    success: bool
    processing_time: float
    model_used: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None


class ExtractedTenderData(BaseModel):
    """Dados extraídos de edital de licitação"""
    general_info: Optional[Dict[str, Any]] = None
    delivery_info: Optional[Dict[str, Any]] = None
    participation_conditions: Optional[Dict[str, Any]] = None
    qualification_requirements: Optional[Dict[str, Any]] = None
    risk_analysis: Optional[Dict[str, Any]] = None
    reference_terms: Optional[Dict[str, Any]] = None
    
    class Config:
        extra = "allow"


class TenderItem(BaseModel):
    """Item de licitação para cotação"""
    item_numero: str
    descricao_completa: str
    quantidade: int
    unidade_medida: str
    especificacoes_tecnicas: List[str] = []
    marca_referencia: Optional[str] = None
    observacoes: Optional[str] = None


class QuotationStructure(BaseModel):
    """Estrutura de planilha de cotação"""
    itens: List[TenderItem]
    resumo: Dict[str, Any]
    campos_cotacao: List[str]
    calculos_automaticos: List[str]


class DisputeTracking(BaseModel):
    """Estrutura para acompanhamento de disputa"""
    criterio_julgamento: str
    itens_monitoramento: List[Dict[str, Any]]
    alertas_configurados: List[str]
    estrategia_lance: Dict[str, Any]


class AIMetric(BaseModel):
    """Métrica de operação da IA"""
    timestamp: float
    model: str
    operation: str
    processing_time: float
    success: bool
    error_type: Optional[str] = None
    input_size: int = 0
    output_size: int = 0


class HealthCheck(BaseModel):
    """Status de saúde dos componentes de IA"""
    overall_status: str
    timestamp: str
    checks: Dict[str, Dict[str, Any]]


class CacheEntry(BaseModel):
    """Entrada do cache de IA"""
    key: str
    data: Dict[str, Any]
    created_at: datetime
    expires_at: datetime
    model_version: str
    document_hash: str
