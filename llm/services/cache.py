"""
AI Cache Service

Provides Redis-based caching for AI processing results to improve performance
and reduce redundant LLM calls for similar documents or queries.
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import aioredis
from ..models import CacheEntry, AIProcessingResult
from ..exceptions import CacheError
from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Redis-based cache service for AI processing results."""
    
    def __init__(self):
        self.redis_client: Optional[aioredis.Redis] = None
        self.cache_prefix = "cotai:llm:"
        
    async def initialize(self) -> None:
        """Initialize Redis connection."""
        try:
            self.redis_client = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                retry_on_timeout=True,
                socket_connect_timeout=5
            )
            # Test connection
            await self.redis_client.ping()
            logger.info("AI Cache service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AI Cache service: {e}")
            raise CacheError(f"Cache initialization failed: {e}")
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            
    def _generate_cache_key(self, content: str, operation: str, model: str) -> str:
        """Generate a unique cache key for content and operation."""
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        return f"{self.cache_prefix}{operation}:{model}:{content_hash}"
    
    def _serialize_result(self, result: AIProcessingResult) -> str:
        """Serialize AI processing result to JSON string."""
        try:
            return json.dumps({
                "success": result.success,
                "data": result.data,
                "confidence": result.confidence,
                "processing_time": result.processing_time,
                "model_used": result.model_used,
                "error_message": result.error_message,
                "metadata": result.metadata,
                "timestamp": result.timestamp.isoformat() if result.timestamp else None
            })
        except Exception as e:
            raise CacheError(f"Failed to serialize result: {e}")
    
    def _deserialize_result(self, data: str) -> AIProcessingResult:
        """Deserialize JSON string to AI processing result."""
        try:
            parsed = json.loads(data)
            return AIProcessingResult(
                success=parsed["success"],
                data=parsed["data"],
                confidence=parsed.get("confidence"),
                processing_time=parsed.get("processing_time"),
                model_used=parsed.get("model_used"),
                error_message=parsed.get("error_message"),
                metadata=parsed.get("metadata", {}),
                timestamp=datetime.fromisoformat(parsed["timestamp"]) if parsed.get("timestamp") else None
            )
        except Exception as e:
            raise CacheError(f"Failed to deserialize result: {e}")
      async def get_cached_result(
        self, 
        content: str, 
        operation: str, 
        model: Optional[str] = None
    ) -> Optional[AIProcessingResult]:
        """Retrieve cached AI processing result."""
        if not self.redis_client:
            return None
            
        model = model or settings.OLLAMA_MODEL
        cache_key = self._generate_cache_key(content, operation, model)
        
        try:
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                result = self._deserialize_result(cached_data)
                logger.debug(f"Cache hit for operation: {operation}")
                return result
            else:
                logger.debug(f"Cache miss for operation: {operation}")
                return None
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")
            return None
      async def cache_result(
        self,
        content: str,
        operation: str,
        result: AIProcessingResult,
        model: Optional[str] = None,
        ttl_hours: Optional[int] = None
    ) -> bool:
        """Cache AI processing result."""
        if not self.redis_client:
            return False
            
        model = model or settings.OLLAMA_MODEL
        ttl_hours = ttl_hours or settings.AI_CACHE_TTL_HOURS
        cache_key = self._generate_cache_key(content, operation, model)
        
        try:
            serialized_result = self._serialize_result(result)
            ttl_seconds = ttl_hours * 3600
            
            await self.redis_client.setex(
                cache_key,
                ttl_seconds,
                serialized_result
            )
            
            # Store cache metadata
            metadata_key = f"{cache_key}:meta"
            metadata = {
                "operation": operation,
                "model": model,
                "cached_at": datetime.utcnow().isoformat(),
                "ttl_hours": ttl_hours,
                "content_length": len(content)
            }
            await self.redis_client.setex(
                metadata_key,
                ttl_seconds,
                json.dumps(metadata)
            )
            
            logger.debug(f"Cached result for operation: {operation}")
            return True
            
        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")
            return False
    
    async def invalidate_cache(self, pattern: Optional[str] = None) -> int:
        """Invalidate cached results by pattern."""
        if not self.redis_client:
            return 0
            
        try:
            if pattern:
                search_pattern = f"{self.cache_prefix}{pattern}*"
            else:
                search_pattern = f"{self.cache_prefix}*"
                
            keys = await self.redis_client.keys(search_pattern)
            if keys:
                deleted = await self.redis_client.delete(*keys)
                logger.info(f"Invalidated {deleted} cache entries")
                return deleted
            return 0
            
        except Exception as e:
            logger.error(f"Cache invalidation failed: {e}")
            raise CacheError(f"Failed to invalidate cache: {e}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.redis_client:
            return {}
            
        try:
            # Get all cache keys
            cache_keys = await self.redis_client.keys(f"{self.cache_prefix}*")
            metadata_keys = [k for k in cache_keys if k.endswith(":meta")]
            result_keys = [k for k in cache_keys if not k.endswith(":meta")]
            
            # Calculate cache size and statistics
            total_size = 0
            operations = {}
            models = {}
            
            for key in metadata_keys:
                try:
                    metadata_str = await self.redis_client.get(key)
                    if metadata_str:
                        metadata = json.loads(metadata_str)
                        operation = metadata.get("operation", "unknown")
                        model = metadata.get("model", "unknown")
                        content_length = metadata.get("content_length", 0)
                        
                        operations[operation] = operations.get(operation, 0) + 1
                        models[model] = models.get(model, 0) + 1
                        total_size += content_length
                except Exception:
                    continue
            
            return {
                "total_entries": len(result_keys),
                "total_size_bytes": total_size,
                "operations": operations,
                "models": models,
                "cache_hit_rate": await self._calculate_hit_rate()
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}
    
    async def _calculate_hit_rate(self) -> float:
        """Calculate cache hit rate from Redis info."""
        try:
            info = await self.redis_client.info("stats")
            hits = info.get("keyspace_hits", 0)
            misses = info.get("keyspace_misses", 0)
            total = hits + misses
            return (hits / total * 100) if total > 0 else 0.0
        except Exception:
            return 0.0
    
    async def cleanup_expired_entries(self) -> int:
        """Clean up expired cache entries (Redis handles this automatically, but useful for monitoring)."""
        if not self.redis_client:
            return 0
            
        try:
            # Get all cache keys and check if they exist (expired ones will be gone)
            cache_keys = await self.redis_client.keys(f"{self.cache_prefix}*:meta")
            valid_count = 0
            
            for key in cache_keys:
                if await self.redis_client.exists(key):
                    valid_count += 1
            
            expired_count = len(cache_keys) - valid_count
            if expired_count > 0:
                logger.info(f"Found {expired_count} expired cache entries")
                
            return expired_count
            
        except Exception as e:
            logger.error(f"Cache cleanup failed: {e}")
            return 0


# Global cache service instance
cache_service = CacheService()
