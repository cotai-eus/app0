"""
Serviço principal para processamento de IA com Llama 3
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.app.core.config import get_settings
from llm.models import AIProcessingResult, ExtractedTenderData
from llm.services.text_extraction import TextExtractionService
from llm.services.prompt_manager import PromptManagerService
from llm.exceptions import AIProcessingException, DocumentProcessingException

settings = get_settings()
logger = logging.getLogger(__name__)


class AIProcessingService:
    """Serviço principal para processamento de IA com Llama 3"""
    
    def __init__(self):
        self.text_extractor = TextExtractionService()
        self.prompt_manager = PromptManagerService()
        self.client_config = {
            "base_url": settings.ollama_api_url,
            "timeout": settings.ollama_timeout
        }
        self._request_semaphore = asyncio.Semaphore(settings.ai_concurrent_requests)
        
    @retry(
        stop=stop_after_attempt(settings.ollama_max_retries),
        wait=wait_exponential(multiplier=settings.ollama_retry_delay)
    )
    async def _call_ollama_api(
        self, 
        prompt: str, 
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        format_json: bool = True
    ) -> str:
        """Chamada robusta para API Ollama com retry automático"""
        
        async with self._request_semaphore:
            model = model_name or settings.ollama_default_model
            temp = temperature if temperature is not None else settings.ollama_temperature
            
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temp,
                    "num_ctx": settings.ollama_context_length,
                    "num_thread": settings.ollama_threads,
                }
            }
            
            if format_json:
                payload["format"] = "json"
            
            if max_tokens:
                payload["options"]["num_predict"] = max_tokens
                
            start_time = time.time()
            
            try:
                async with httpx.AsyncClient(**self.client_config) as client:
                    response = await client.post("/api/generate", json=payload)
                    response.raise_for_status()
                    
                    result = response.json()
                    ai_response = result.get("response", "")
                    
                    # Logging e métricas
                    processing_time = time.time() - start_time
                    if settings.ai_metrics_enabled:
                        await self._log_ai_metrics(
                            model, prompt, ai_response, processing_time
                        )
                    
                    return ai_response
                    
            except httpx.HTTPStatusError as e:
                error_msg = f"Ollama API Error: {e.response.status_code}"
                if e.response.text:
                    error_msg += f" - {e.response.text}"
                logger.error(error_msg)
                raise AIProcessingException(error_msg)
                
            except httpx.TimeoutException:
                error_msg = f"Ollama API timeout after {settings.ollama_timeout}s"
                logger.error(error_msg)
                raise AIProcessingException(error_msg)
                
            except Exception as e:
                logger.error(f"Unexpected error calling Ollama: {str(e)}")
                raise AIProcessingException(f"AI service error: {str(e)}")
    
    async def _safe_json_parse(self, ai_response: str) -> Dict[str, Any]:
        """Parser robusto para JSON retornado pela IA"""
        
        if not ai_response.strip():
            raise AIProcessingException("IA retornou resposta vazia")
        
        # Limpeza de markdown e artifacts
        cleaned_response = ai_response.strip()
        
        # Remove blocos de código markdown
        if "```json" in cleaned_response:
            cleaned_response = cleaned_response.split("```json\n", 1)[-1]
            cleaned_response = cleaned_response.split("\n```", 1)[0]
        elif "```" in cleaned_response:
            cleaned_response = cleaned_response.split("```\n", 1)[-1]
            cleaned_response = cleaned_response.split("\n```", 1)[0]
        
        # Remove texto antes/depois do JSON
        start_idx = cleaned_response.find('{')
        end_idx = cleaned_response.rfind('}') + 1
        
        if start_idx == -1 or end_idx == 0:
            logger.error(f"No JSON found in AI response: {ai_response[:200]}...")
            raise AIProcessingException("IA não retornou JSON válido")
        
        json_str = cleaned_response[start_idx:end_idx]
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}. Content: {json_str[:200]}...")
            raise AIProcessingException(f"IA retornou JSON malformado: {str(e)}")
    
    async def extract_tender_data(
        self, 
        file_content: bytes, 
        filename: str,
        extraction_types: List[str] = None
    ) -> ExtractedTenderData:
        """Extração completa de dados do edital"""
        
        logger.info(f"Iniciando extração de dados do arquivo: {filename}")
        
        # 1. Extração de texto
        try:
            document_text = await self.text_extractor.extract_text(
                file_content, filename
            )
        except Exception as e:
            raise DocumentProcessingException(f"Erro na extração de texto: {str(e)}")
        
        if not document_text.strip():
            raise DocumentProcessingException("Documento não contém texto extraível")
        
        # 2. Chunking para documentos grandes
        text_chunks = await self._chunk_document(document_text)
        
        # 3. Extração estruturada por tipo
        extraction_types = extraction_types or [
            "general_info", "delivery_info", "participation_conditions",
            "qualification_requirements", "risk_analysis", "reference_terms"
        ]
        
        extracted_data = {}
        
        for extraction_type in extraction_types:
            try:
                result = await self._extract_by_type(
                    text_chunks, extraction_type
                )
                extracted_data[extraction_type] = result
                
            except Exception as e:
                logger.error(f"Erro na extração {extraction_type}: {str(e)}")
                extracted_data[extraction_type] = {"error": str(e)}
        
        return ExtractedTenderData(**extracted_data)
    
    async def _chunk_document(self, text: str) -> List[str]:
        """Quebra documento em chunks menores para processamento"""
        
        # Implementação simples por caracteres/palavras
        max_chars = settings.chunk_size_tokens * 4  # ~4 chars por token
        overlap_chars = settings.chunk_overlap_tokens * 4
        
        if len(text) <= max_chars:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + max_chars
            
            # Tentar quebrar em boundary de palavra/parágrafo
            if end < len(text):
                # Procurar por quebra de parágrafo primeiro
                para_break = text.rfind('\n\n', start, end)
                if para_break > start:
                    end = para_break
                else:
                    # Procurar por quebra de frase
                    sent_break = text.rfind('. ', start, end)
                    if sent_break > start:
                        end = sent_break + 1
            
            chunks.append(text[start:end].strip())
            start = end - overlap_chars if end < len(text) else end
        
        logger.info(f"Documento dividido em {len(chunks)} chunks")
        return chunks
    
    async def _extract_by_type(
        self, 
        text_chunks: List[str], 
        extraction_type: str
    ) -> Dict[str, Any]:
        """Extração específica por tipo de informação"""
        
        prompt_template = self.prompt_manager.get_prompt(extraction_type)
        
        # Para documentos com múltiplos chunks, processa cada um e consolida
        if len(text_chunks) == 1:
            document_text = text_chunks[0]
        else:
            # Para múltiplos chunks, pode processar todos e consolidar
            document_text = "\n\n".join(text_chunks[:3])  # Primeiros 3 chunks
        
        prompt = prompt_template.format(document_text=document_text)
        
        ai_response = await self._call_ollama_api(prompt)
        return await self._safe_json_parse(ai_response)
    
    async def generate_quotation_structure(
        self, 
        reference_terms_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Gera estrutura de planilha de cotação baseada no TR"""
        
        prompt = self.prompt_manager.get_prompt("quotation_structure")
        formatted_prompt = prompt.format(
            reference_terms=json.dumps(reference_terms_data, indent=2)
        )
        
        ai_response = await self._call_ollama_api(formatted_prompt)
        return await self._safe_json_parse(ai_response)
    
    async def generate_dispute_tracking(
        self, 
        quotation_items: List[Dict[str, Any]], 
        bidding_criteria: str
    ) -> Dict[str, Any]:
        """Gera estrutura para acompanhamento de disputa"""
        
        prompt = self.prompt_manager.get_prompt("dispute_tracking")
        formatted_prompt = prompt.format(
            quotation_items=json.dumps(quotation_items, indent=2),
            bidding_criteria=bidding_criteria
        )
        
        ai_response = await self._call_ollama_api(formatted_prompt)
        return await self._safe_json_parse(ai_response)
    
    async def _log_ai_metrics(
        self, 
        model: str, 
        prompt: str, 
        response: str, 
        processing_time: float
    ):
        """Log de métricas para monitoramento"""
        
        metrics = {
            "timestamp": time.time(),
            "model": model,
            "prompt_length": len(prompt),
            "response_length": len(response),
            "processing_time": processing_time,
            "prompt_hash": hash(prompt) % 10000  # Para agrupar prompts similares
        }
        
        # Log estruturado
        logger.info("AI_METRICS", extra=metrics)
        
        # Alerta para tempos longos
        if processing_time > settings.ai_response_time_threshold:
            logger.warning(
                f"AI processing time exceeded threshold: {processing_time:.2f}s"
            )
        
        # TODO: Enviar métricas para sistema de monitoramento
        # await self._send_to_monitoring(metrics)
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço de IA"""
        
        try:
            # Teste básico de conectividade
            start_time = time.time()
            test_response = await self._call_ollama_api(
                "Responda apenas: OK", 
                format_json=False
            )
            response_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "model": settings.ollama_default_model,
                "response_time": response_time,
                "test_response": test_response.strip(),
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
    
    async def get_available_models(self) -> List[str]:
        """Lista modelos disponíveis no Ollama"""
        
        try:
            async with httpx.AsyncClient(**self.client_config) as client:
                response = await client.get("/api/tags")
                response.raise_for_status()
                
                data = response.json()
                models = [model["name"] for model in data.get("models", [])]
                return models
                
        except Exception as e:
            logger.error(f"Erro ao listar modelos: {str(e)}")
            return []
    
    async def validate_model_availability(self, model_name: str) -> bool:
        """Valida se um modelo específico está disponível"""
        
        available_models = await self.get_available_models()
        return model_name in available_models
