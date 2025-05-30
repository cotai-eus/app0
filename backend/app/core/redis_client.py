"""
Configuração do Redis para cache e sessões
"""

import json
from datetime import datetime
from typing import Any, Optional, Union

import redis.asyncio as redis

from app.core.config import settings
from app.core.logging import get_logger_with_context

logger = get_logger_with_context(component="redis")


class RedisClient:
    """Cliente Redis singleton"""
    
    def __init__(self):
        self.client: Optional[redis.Redis] = None
    
    async def connect(self) -> None:
        """Conecta ao Redis"""
        try:
            logger.info("Connecting to Redis", url=settings.redis_url)
            self.client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
            
            # Testa a conexão
            await self.client.ping()
            logger.info("Redis connected successfully")
            
        except Exception as exc:
            logger.error("Failed to connect to Redis", error=str(exc))
            raise
    
    async def close(self) -> None:
        """Fecha a conexão com Redis"""
        try:
            if self.client:
                await self.client.close()
                logger.info("Redis connection closed")
        except Exception as exc:
            logger.error("Error closing Redis connection", error=str(exc))
    
    async def get(self, key: str) -> Optional[str]:
        """Recupera um valor do Redis"""
        try:
            if not self.client:
                await self.connect()
            return await self.client.get(key)
        except Exception as exc:
            logger.error("Redis GET error", key=key, error=str(exc))
            return None
    
    async def set(
        self, 
        key: str, 
        value: Union[str, dict, list], 
        ttl: Optional[int] = None
    ) -> bool:
        """Armazena um valor no Redis"""
        try:
            if not self.client:
                await self.connect()
            
            # Serializa objetos complexos
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            if ttl:
                return await self.client.setex(key, ttl, value)
            else:
                return await self.client.set(key, value)
                
        except Exception as exc:
            logger.error("Redis SET error", key=key, error=str(exc))
            return False
    
    async def delete(self, key: str) -> bool:
        """Remove uma chave do Redis"""
        try:
            if not self.client:
                await self.connect()
            result = await self.client.delete(key)
            return result > 0
        except Exception as exc:
            logger.error("Redis DELETE error", key=key, error=str(exc))
            return False
    
    async def exists(self, key: str) -> bool:
        """Verifica se uma chave existe"""
        try:
            if not self.client:
                await self.connect()
            return await self.client.exists(key) > 0
        except Exception as exc:
            logger.error("Redis EXISTS error", key=key, error=str(exc))
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Incrementa um contador"""
        try:
            if not self.client:
                await self.connect()
            return await self.client.incrby(key, amount)
        except Exception as exc:
            logger.error("Redis INCREMENT error", key=key, error=str(exc))
            return None
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Define TTL para uma chave"""
        try:
            if not self.client:
                await self.connect()
            return await self.client.expire(key, ttl)
        except Exception as exc:
            logger.error("Redis EXPIRE error", key=key, error=str(exc))
            return False


# Instância global do Redis
redis_client = RedisClient()


async def get_redis() -> RedisClient:
    """Dependency para obter o cliente Redis"""
    if not redis_client.client:
        await redis_client.connect()
    return redis_client


# Helpers para operações específicas
class CacheService:
    """Serviço de cache usando Redis"""
    
    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client
    
    async def cache_user_session(
        self, 
        user_id: str, 
        session_data: dict, 
        ttl: int = 3600
    ) -> bool:
        """Cache da sessão do usuário"""
        key = f"session:user:{user_id}"
        return await self.redis.set(key, session_data, ttl)
    
    async def get_user_session(self, user_id: str) -> Optional[dict]:
        """Recupera sessão do usuário"""
        key = f"session:user:{user_id}"
        data = await self.redis.get(key)
        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return None
        return None
    
    async def invalidate_user_session(self, user_id: str) -> bool:
        """Invalida sessão do usuário"""
        key = f"session:user:{user_id}"
        return await self.redis.delete(key)
    
    async def rate_limit_check(
        self, 
        identifier: str, 
        limit: int, 
        window: int = 60
    ) -> tuple[bool, int]:
        """Verifica rate limiting
        
        Returns:
            tuple: (is_allowed, current_count)
        """
        key = f"rate_limit:{identifier}"
        current = await self.redis.increment(key)
        
        if current == 1:
            await self.redis.expire(key, window)
        
        is_allowed = current <= limit
        return is_allowed, current


# Serviços especializados para o plano de arquitetura

class SessionService:
    """Serviço de gestão de sessões usando Redis"""
    
    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client
    
    async def create_session(
        self, 
        user_id: str, 
        session_id: str,
        session_data: dict, 
        ttl: int = 86400  # 24 horas
    ) -> bool:
        """Cria uma nova sessão"""
        session_key = f"session:{session_id}"
        user_sessions_key = f"user_sessions:{user_id}"
        
        # Armazena dados da sessão
        session_stored = await self.redis.set(session_key, {
            **session_data,
            "user_id": user_id,
            "session_id": session_id,
            "created_at": json.dumps(datetime.utcnow(), default=str)
        }, ttl)
        
        if session_stored and self.redis.client:
            # Adiciona à lista de sessões do usuário
            await self.redis.client.sadd(user_sessions_key, session_id)
            await self.redis.expire(user_sessions_key, ttl)
            
        return session_stored
    
    async def get_session(self, session_id: str) -> Optional[dict]:
        """Recupera dados da sessão"""
        key = f"session:{session_id}"
        data = await self.redis.get(key)
        if data:
            try:
                return json.loads(data) if isinstance(data, str) else data
            except json.JSONDecodeError:
                return None
        return None
    
    async def update_session(
        self, 
        session_id: str, 
        updates: dict,
        extend_ttl: Optional[int] = None
    ) -> bool:
        """Atualiza dados da sessão"""
        current_data = await self.get_session(session_id)
        if not current_data:
            return False
        
        current_data.update(updates)
        key = f"session:{session_id}"
        
        if extend_ttl:
            return await self.redis.set(key, current_data, extend_ttl)
        else:
            return await self.redis.client.set(key, json.dumps(current_data)) if self.redis.client else False
    
    async def invalidate_session(self, session_id: str) -> bool:
        """Invalida uma sessão específica"""
        session_data = await self.get_session(session_id)
        if session_data and "user_id" in session_data:
            user_id = session_data["user_id"]
            user_sessions_key = f"user_sessions:{user_id}"
            
            # Remove da lista de sessões do usuário
            if self.redis.client:
                await self.redis.client.srem(user_sessions_key, session_id)
        
        key = f"session:{session_id}"
        return await self.redis.delete(key)
    
    async def invalidate_all_user_sessions(self, user_id: str) -> bool:
        """Invalida todas as sessões de um usuário"""
        user_sessions_key = f"user_sessions:{user_id}"
        
        if not self.redis.client:
            return False
            
        # Recupera todas as sessões do usuário
        session_ids = await self.redis.client.smembers(user_sessions_key)
        
        # Remove cada sessão
        for session_id in session_ids:
            await self.redis.delete(f"session:{session_id}")
        
        # Remove a lista de sessões
        return await self.redis.delete(user_sessions_key)


class AICache:
    """Cache especializado para IA"""
    
    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client
    
    async def cache_ai_response(
        self, 
        prompt_hash: str, 
        response: dict, 
        model: str,
        ttl: int = 3600  # 1 hora
    ) -> bool:
        """Cache de resposta de IA"""
        key = f"ai_cache:{model}:{prompt_hash}"
        return await self.redis.set(key, {
            **response,
            "cached_at": json.dumps(datetime.utcnow(), default=str),
            "model": model
        }, ttl)
    
    async def get_ai_response(self, prompt_hash: str, model: str) -> Optional[dict]:
        """Recupera resposta de IA do cache"""
        key = f"ai_cache:{model}:{prompt_hash}"
        data = await self.redis.get(key)
        if data:
            try:
                return json.loads(data) if isinstance(data, str) else data
            except json.JSONDecodeError:
                return None
        return None
    
    async def cache_model_metadata(
        self, 
        model_name: str, 
        metadata: dict, 
        ttl: int = 86400  # 24 horas
    ) -> bool:
        """Cache de metadados do modelo"""
        key = f"ai_model_meta:{model_name}"
        return await self.redis.set(key, metadata, ttl)
    
    async def increment_model_usage(self, model_name: str) -> Optional[int]:
        """Incrementa contador de uso do modelo"""
        key = f"ai_model_usage:{model_name}"
        return await self.redis.increment(key)


class SmartRateLimit:
    """Rate limiting inteligente"""
    
    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client
    
    async def check_rate_limit(
        self,
        identifier: str,
        limit: int,
        window: int = 60,
        burst_limit: Optional[int] = None
    ) -> dict:
        """Verifica rate limit com suporte a burst"""
        key = f"rate_limit:{identifier}"
        burst_key = f"rate_limit_burst:{identifier}"
        
        # Rate limit normal
        current = await self.redis.increment(key)
        if current == 1:
            await self.redis.expire(key, window)
        
        # Burst limit se especificado
        burst_current = 0
        if burst_limit:
            burst_current = await self.redis.increment(burst_key)
            if burst_current == 1:
                await self.redis.expire(burst_key, 10)  # Janela menor para burst
        
        is_allowed = current <= limit
        if burst_limit:
            is_allowed = is_allowed and burst_current <= burst_limit
        
        return {
            "allowed": is_allowed,
            "current": current,
            "limit": limit,
            "burst_current": burst_current,
            "burst_limit": burst_limit,
            "window": window,
            "reset_time": window - (current % window) if current > 0 else window
        }
    
    async def adaptive_rate_limit(
        self,
        user_id: str,
        base_limit: int,
        window: int = 60
    ) -> dict:
        """Rate limiting adaptativo baseado no comportamento do usuário"""
        # Verifica histórico do usuário
        user_score_key = f"user_score:{user_id}"
        user_score_data = await self.redis.get(user_score_key)
        
        if user_score_data:
            try:
                score_data = json.loads(user_score_data) if isinstance(user_score_data, str) else user_score_data
                user_score = score_data.get("score", 1.0)
            except:
                user_score = 1.0
        else:
            user_score = 1.0
        
        # Ajusta limite baseado no score (usuários confiáveis têm limites maiores)
        adjusted_limit = int(base_limit * user_score)
        
        return await self.check_rate_limit(f"user:{user_id}", adjusted_limit, window)


class RealtimeQueue:
    """Filas em tempo real usando Redis Pub/Sub"""
    
    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client
    
    async def publish_event(self, channel: str, event_data: dict) -> bool:
        """Publica evento em tempo real"""
        try:
            if not self.redis.client:
                await self.redis.connect()
            
            message = json.dumps({
                **event_data,
                "timestamp": datetime.utcnow().isoformat(),
                "channel": channel
            })
            
            result = await self.redis.client.publish(channel, message)
            return result > 0
            
        except Exception as exc:
            logger.error("Failed to publish event", channel=channel, error=str(exc))
            return False
    
    async def add_to_queue(
        self, 
        queue_name: str, 
        item: dict, 
        priority: int = 0
    ) -> bool:
        """Adiciona item à fila (com prioridade opcional)"""
        try:
            if not self.redis.client:
                await self.redis.connect()
            
            if priority > 0:
                # Usa sorted set para prioridade
                result = await self.redis.client.zadd(
                    f"queue:{queue_name}:priority", 
                    {json.dumps(item): priority}
                )
            else:
                # Usa lista para FIFO simples
                result = await self.redis.client.lpush(
                    f"queue:{queue_name}", 
                    json.dumps(item)
                )
            
            return result > 0
            
        except Exception as exc:
            logger.error("Failed to add to queue", queue=queue_name, error=str(exc))
            return False
    
    async def get_from_queue(
        self, 
        queue_name: str, 
        use_priority: bool = False
    ) -> Optional[dict]:
        """Recupera item da fila"""
        try:
            if not self.redis.client:
                await self.redis.connect()
            
            if use_priority:
                # Pega item com maior prioridade
                result = await self.redis.client.zpopmax(f"queue:{queue_name}:priority")
                if result:
                    item_json, priority = result[0]
                    return json.loads(item_json)
            else:
                # FIFO simples
                result = await self.redis.client.rpop(f"queue:{queue_name}")
                if result:
                    return json.loads(result)
            
            return None
            
        except Exception as exc:
            logger.error("Failed to get from queue", queue=queue_name, error=str(exc))
            return None


# Funções utilitárias para importar
async def get_session_service() -> SessionService:
    """Dependency para SessionService"""
    redis = await get_redis()
    return SessionService(redis)

async def get_ai_cache() -> AICache:
    """Dependency para AICache"""
    redis = await get_redis()
    return AICache(redis)

async def get_smart_rate_limit() -> SmartRateLimit:
    """Dependency para SmartRateLimit"""
    redis = await get_redis()
    return SmartRateLimit(redis)

async def get_realtime_queue() -> RealtimeQueue:
    """Dependency para RealtimeQueue"""
    redis = await get_redis()
    return RealtimeQueue(redis)


# Cache service backward compatibility
async def get_cache_service() -> CacheService:
    """Dependency para CacheService (compatibilidade)"""
    redis = await get_redis()
    return CacheService(redis)
