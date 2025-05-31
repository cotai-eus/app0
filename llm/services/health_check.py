"""
Serviço de health check para componentes de IA
"""

import asyncio
import logging
from typing import Dict, Any, Optional
import httpx
from datetime import datetime

from backend.app.core.config import get_settings
from llm.services.ai_processing import AIProcessingService

settings = get_settings()
logger = logging.getLogger(__name__)


class AIHealthService:
    """Serviço de health check para componentes de IA"""
    
    def __init__(self):
        self.ai_service = AIProcessingService()
    
    async def check_ollama_health(self) -> Dict[str, Any]:
        """Verifica saúde do serviço Ollama"""
        
        try:
            async with httpx.AsyncClient(
                base_url=settings.ollama_api_url,
                timeout=10.0
            ) as client:
                # Teste de conectividade
                response = await client.get("/")
                
                if response.status_code == 200:
                    # Teste de modelo
                    model_test = await self._test_model_availability()
                    return {
                        "status": "healthy",
                        "ollama_server": "connected",
                        "model_test": model_test,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "error": f"Ollama returned status {response.status_code}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
        except httpx.ConnectError:
            return {
                "status": "unhealthy",
                "error": "Cannot connect to Ollama server",
                "timestamp": datetime.utcnow().isoformat()
            }
        except httpx.TimeoutException:
            return {
                "status": "unhealthy",
                "error": "Timeout connecting to Ollama",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": f"Unexpected error: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _test_model_availability(self) -> Dict[str, Any]:
        """Testa disponibilidade do modelo"""
        
        try:
            test_prompt = "Teste de conectividade. Responda apenas: OK"
            response = await self.ai_service._call_ollama_api(
                test_prompt,
                format_json=False
            )
            
            if "OK" in response.upper():
                return {
                    "status": "available",
                    "model": settings.ollama_default_model,
                    "response_time": "< 5s"
                }
            else:
                return {
                    "status": "responding_incorrectly",
                    "model": settings.ollama_default_model,
                    "response": response[:100]
                }
                
        except Exception as e:
            return {
                "status": "unavailable",
                "model": settings.ollama_default_model,
                "error": str(e)
            }
    
    async def run_comprehensive_health_check(self) -> Dict[str, Any]:
        """Executa verificação completa de saúde"""
        
        results = {
            "overall_status": "unknown",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {}
        }
        
        # Verificar Ollama
        ollama_health = await self.check_ollama_health()
        results["checks"]["ollama"] = ollama_health
        
        # Verificar GPU (se disponível)
        gpu_status = await self._check_gpu_availability()
        results["checks"]["gpu"] = gpu_status
        
        # Verificar dependências
        deps_status = self._check_dependencies()
        results["checks"]["dependencies"] = deps_status
        
        # Status geral
        all_healthy = all(
            check.get("status") == "healthy" 
            for check in results["checks"].values()
        )
        
        results["overall_status"] = "healthy" if all_healthy else "unhealthy"
        
        return results
    
    async def _check_gpu_availability(self) -> Dict[str, Any]:
        """Verifica disponibilidade da GPU"""
        
        try:
            # Simular verificação de GPU via Ollama
            async with httpx.AsyncClient(
                base_url=settings.ollama_api_url,
                timeout=5.0
            ) as client:
                response = await client.get("/api/ps")
                
                if response.status_code == 200:
                    models = response.json()
                    gpu_info = {
                        "status": "available",
                        "loaded_models": len(models.get("models", [])),
                        "models": [m.get("name") for m in models.get("models", [])]
                    }
                    return gpu_info
                
        except Exception as e:
            return {
                "status": "unknown",
                "error": str(e)
            }
        
        return {"status": "not_available"}
    
    def _check_dependencies(self) -> Dict[str, Any]:
        """Verifica dependências críticas"""
        
        dependencies = {
            "httpx": False,
            "pymupdf": False,
            "python-docx": False,
            "pillow": False,
            "pytesseract": False
        }
        
        try:
            import httpx
            dependencies["httpx"] = True
        except ImportError:
            pass
        
        try:
            import fitz
            dependencies["pymupdf"] = True
        except ImportError:
            pass
        
        try:
            import docx
            dependencies["python-docx"] = True
        except ImportError:
            pass
        
        try:
            import PIL
            dependencies["pillow"] = True
        except ImportError:
            pass
        
        try:
            import pytesseract
            dependencies["pytesseract"] = True
        except ImportError:
            pass
        
        all_available = all(dependencies.values())
        
        return {
            "status": "healthy" if all_available else "missing_dependencies",
            "dependencies": dependencies,
            "missing": [name for name, available in dependencies.items() if not available]
        }
    
    async def check_ai_performance(self) -> Dict[str, Any]:
        """Verifica performance da IA com teste real"""
        
        test_prompt = """Analise este texto e extraia as informações em JSON:
        
        Texto: "Licitação 001/2024 para compra de 10 notebooks Dell, valor estimado R$ 50.000"
        
        Extraia: numero_licitacao, objeto, quantidade, valor_estimado"""
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            response = await self.ai_service._call_ollama_api(test_prompt)
            processing_time = asyncio.get_event_loop().time() - start_time
            
            # Validar se retornou JSON válido
            try:
                parsed = await self.ai_service._safe_json_parse(response)
                
                return {
                    "status": "healthy",
                    "processing_time": processing_time,
                    "response_valid": True,
                    "model": settings.ollama_default_model
                }
            except:
                return {
                    "status": "degraded",
                    "processing_time": processing_time,
                    "response_valid": False,
                    "model": settings.ollama_default_model
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "model": settings.ollama_default_model
            }
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Obtém métricas do sistema"""
        
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "settings": {
                "default_model": settings.ollama_default_model,
                "timeout": settings.ollama_timeout,
                "concurrent_requests": settings.ai_concurrent_requests,
                "temperature": settings.ollama_temperature
            }
        }
        
        # Adicionar métricas de performance se disponíveis
        try:
            models = await self.ai_service.get_available_models()
            metrics["available_models"] = models
        except:
            metrics["available_models"] = []
        
        return metrics
