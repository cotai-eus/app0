"""
LLM API Endpoints

REST API endpoints for AI/LLM functionality including document processing,
tender data extraction, quotation generation, and system monitoring.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import tempfile
import os
import logging

from llm import llm_manager
from llm.models import AIProcessingResult, ExtractedTenderData
from llm.exceptions import AIProcessingException, ModelUnavailableException

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/llm", tags=["LLM/AI"])


# Request/Response Models
class DocumentProcessRequest(BaseModel):
    """Request model for document processing."""
    use_cache: bool = Field(default=True, description="Whether to use cached results")
    operations: List[str] = Field(default=["extract_tender_data"], description="Operations to perform")


class QuotationRequest(BaseModel):
    """Request model for quotation generation."""
    tender_data: Dict[str, Any] = Field(..., description="Extracted tender data")
    company_info: Dict[str, Any] = Field(..., description="Company information")
    use_cache: bool = Field(default=True, description="Whether to use cached results")


class RiskAnalysisRequest(BaseModel):
    """Request model for risk analysis."""
    tender_data: Dict[str, Any] = Field(..., description="Extracted tender data")
    use_cache: bool = Field(default=True, description="Whether to use cached results")


class BatchProcessRequest(BaseModel):
    """Request model for batch processing."""
    file_paths: List[str] = Field(..., description="List of file paths to process")
    operations: List[str] = Field(default=["extract_tender_data"], description="Operations to perform")


class CacheClearRequest(BaseModel):
    """Request model for cache clearing."""
    operation: Optional[str] = Field(None, description="Specific operation to clear (or all if None)")


# Dependency to ensure LLM manager is initialized
async def get_llm_manager():
    """Dependency to get initialized LLM manager."""
    if not llm_manager._initialized:
        try:
            await llm_manager.initialize()
        except Exception as e:
            logger.error(f"Failed to initialize LLM manager: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"LLM service unavailable: {e}"
            )
    return llm_manager


# Health Check Endpoints
@router.get("/health", summary="Check LLM system health")
async def health_check(
    manager = Depends(get_llm_manager)
) -> JSONResponse:
    """Check the health status of the LLM system."""
    try:
        status = await manager.get_system_status()
        
        # Determine HTTP status code based on health
        if status.get("health", {}).get("healthy", False):
            status_code = 200
        else:
            status_code = 503
            
        return JSONResponse(
            status_code=status_code,
            content={
                "status": "healthy" if status_code == 200 else "unhealthy",
                "details": status
            }
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "error": str(e)
            }
        )


@router.get("/status", summary="Get detailed system status")
async def get_status(
    manager = Depends(get_llm_manager)
) -> Dict[str, Any]:
    """Get detailed status of all LLM services."""
    try:
        return await manager.get_system_status()
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get system status: {e}"
        )


# Document Processing Endpoints
@router.post("/extract/upload", summary="Extract data from uploaded document")
async def extract_from_upload(
    file: UploadFile = File(...),
    request: DocumentProcessRequest = Depends(),
    manager = Depends(get_llm_manager)
) -> AIProcessingResult:
    """Extract tender data from an uploaded document file."""
    
    # Validate file type
    allowed_types = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}"
        )
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_file_path = temp_file.name
    
    try:
        # Process the document
        result = await manager.extract_tender_data(
            file_path=temp_file_path,
            use_cache=request.use_cache
        )
        
        return result
        
    except ModelUnavailableException as e:
        raise HTTPException(status_code=503, detail=f"LLM model unavailable: {e}")
    except AIProcessingException as e:
        raise HTTPException(status_code=422, detail=f"AI processing failed: {e}")
    except Exception as e:
        logger.error(f"Document extraction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Internal processing error: {e}")
    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_file_path)
        except Exception:
            pass


@router.post("/extract/file", summary="Extract data from file path")
async def extract_from_file(
    file_path: str,
    request: DocumentProcessRequest = Depends(),
    manager = Depends(get_llm_manager)
) -> AIProcessingResult:
    """Extract tender data from a file path."""
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        result = await manager.extract_tender_data(
            file_path=file_path,
            use_cache=request.use_cache
        )
        
        return result
        
    except ModelUnavailableException as e:
        raise HTTPException(status_code=503, detail=f"LLM model unavailable: {e}")
    except AIProcessingException as e:
        raise HTTPException(status_code=422, detail=f"AI processing failed: {e}")
    except Exception as e:
        logger.error(f"Document extraction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Internal processing error: {e}")


# Quotation Generation Endpoints
@router.post("/quotation/generate", summary="Generate quotation from tender data")
async def generate_quotation(
    request: QuotationRequest,
    manager = Depends(get_llm_manager)
) -> AIProcessingResult:
    """Generate a quotation based on tender data and company information."""
    
    try:
        # Convert dict to ExtractedTenderData model
        tender_data = ExtractedTenderData(**request.tender_data)
        
        result = await manager.generate_quotation(
            tender_data=tender_data,
            company_info=request.company_info,
            use_cache=request.use_cache
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid tender data: {e}")
    except ModelUnavailableException as e:
        raise HTTPException(status_code=503, detail=f"LLM model unavailable: {e}")
    except AIProcessingException as e:
        raise HTTPException(status_code=422, detail=f"AI processing failed: {e}")
    except Exception as e:
        logger.error(f"Quotation generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Internal processing error: {e}")


# Risk Analysis Endpoints
@router.post("/risk/analyze", summary="Analyze risks in tender")
async def analyze_risks(
    request: RiskAnalysisRequest,
    manager = Depends(get_llm_manager)
) -> AIProcessingResult:
    """Analyze risks in a tender based on extracted data."""
    
    try:
        # Convert dict to ExtractedTenderData model
        tender_data = ExtractedTenderData(**request.tender_data)
        
        result = await manager.analyze_risks(
            tender_data=tender_data,
            use_cache=request.use_cache
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid tender data: {e}")
    except ModelUnavailableException as e:
        raise HTTPException(status_code=503, detail=f"LLM model unavailable: {e}")
    except AIProcessingException as e:
        raise HTTPException(status_code=422, detail=f"AI processing failed: {e}")
    except Exception as e:
        logger.error(f"Risk analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Internal processing error: {e}")


# Batch Processing Endpoints
@router.post("/batch/process", summary="Process multiple documents")
async def batch_process(
    request: BatchProcessRequest,
    background_tasks: BackgroundTasks,
    manager = Depends(get_llm_manager)
) -> Dict[str, Any]:
    """Process multiple documents in batch (asynchronous)."""
    
    # Validate file paths
    missing_files = [fp for fp in request.file_paths if not os.path.exists(fp)]
    if missing_files:
        raise HTTPException(
            status_code=404,
            detail=f"Files not found: {missing_files}"
        )
    
    try:
        # For large batches, use background processing
        if len(request.file_paths) > 10:
            # Add to background tasks
            background_tasks.add_task(
                manager.process_document_batch,
                request.file_paths,
                request.operations
            )
            
            return {
                "status": "accepted",
                "message": "Batch processing started in background",
                "file_count": len(request.file_paths),
                "operations": request.operations
            }
        else:
            # Process immediately for small batches
            results = await manager.process_document_batch(
                request.file_paths,
                request.operations
            )
            
            return {
                "status": "completed",
                "results": results,
                "file_count": len(request.file_paths),
                "success_count": sum(1 for r in results if r.success),
                "error_count": sum(1 for r in results if not r.success)
            }
            
    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch processing error: {e}")


# Cache Management Endpoints
@router.post("/cache/clear", summary="Clear AI cache")
async def clear_cache(
    request: CacheClearRequest,
    manager = Depends(get_llm_manager)
) -> Dict[str, Any]:
    """Clear AI cache for specific operations or all operations."""
    
    try:
        result = await manager.clear_cache(request.operation)
        return result
        
    except Exception as e:
        logger.error(f"Cache clearing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {e}")


@router.get("/cache/stats", summary="Get cache statistics")
async def get_cache_stats(
    manager = Depends(get_llm_manager)
) -> Dict[str, Any]:
    """Get cache usage statistics."""
    
    try:
        from llm.services import cache_service
        stats = await cache_service.get_cache_stats()
        return {
            "status": "success",
            "cache_stats": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {e}")


# Monitoring Endpoints
@router.get("/metrics/operations", summary="Get operation metrics")
async def get_operation_metrics(
    operation: Optional[str] = None,
    hours: int = 24,
    manager = Depends(get_llm_manager)
) -> Dict[str, Any]:
    """Get AI operation metrics and statistics."""
    
    try:
        from llm.services import monitoring_service
        stats = await monitoring_service.get_operation_stats(operation, hours)
        return {
            "status": "success",
            "metrics": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get operation metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {e}")


@router.get("/metrics/performance", summary="Get performance trends")
async def get_performance_trends(
    operation: str,
    hours: int = 24,
    manager = Depends(get_llm_manager)
) -> Dict[str, Any]:
    """Get performance trends for a specific operation."""
    
    try:
        from llm.services import monitoring_service
        trends = await monitoring_service.get_performance_trends(operation, hours)
        return {
            "status": "success",
            "trends": trends
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance trends: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get trends: {e}")


# Utility function to include router in main app
def include_llm_routes(app):
    """Include LLM routes in the main FastAPI app."""
    app.include_router(router)
