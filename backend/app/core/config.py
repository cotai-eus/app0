"""
Configurações centralizadas da aplicação
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # API Configuration
    api_v1_str: str = Field(default="/api/v1", alias="API_V1_STR")
    project_name: str = Field(default="CotAi Backend", alias="PROJECT_NAME")
    version: str = Field(default="0.1.0", alias="VERSION")
    description: str = Field(
        default="Backend do CotAi - Monólito Modularizado", 
        alias="DESCRIPTION"
    )
    debug: bool = Field(default=False, alias="DEBUG")
    reload: bool = Field(default=False, alias="RELOAD")

    # Server Configuration
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    # Security
    secret_key: str = Field(alias="SECRET_KEY")
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30, 
        alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )    # Database Configuration
    postgres_server: str = Field(alias="POSTGRES_SERVER")
    postgres_user: str = Field(alias="POSTGRES_USER")
    postgres_password: str = Field(alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(alias="POSTGRES_DB")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    database_url_override: Optional[str] = Field(default=None, alias="DATABASE_URL")

    # MongoDB
    mongodb_url: str = Field(alias="MONGODB_URL")
    mongodb_db: str = Field(alias="MONGODB_DB")

    # Redis
    redis_url: str = Field(alias="REDIS_URL")

    # Celery
    celery_broker_url: str = Field(alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(alias="CELERY_RESULT_BACKEND")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")    # CORS
    backend_cors_origins: List[str] = Field(
        default=[], 
        alias="BACKEND_CORS_ORIGINS"
    )

    # Rate Limiting
    rate_limit_per_minute: int = Field(
        default=60, 
        alias="RATE_LIMIT_PER_MINUTE"
    )

    # Health Check
    health_check_interval: int = Field(
        default=30, 
        alias="HEALTH_CHECK_INTERVAL"
    )

    # === LLM/AI Configuration ===
    ollama_api_url: str = Field(default="http://localhost:11434", alias="OLLAMA_API_URL")
    ollama_default_model: str = Field(default="llama3:8b", alias="OLLAMA_DEFAULT_MODEL")
    ollama_timeout: float = Field(default=300.0, alias="OLLAMA_TIMEOUT")
    ollama_max_retries: int = Field(default=3, alias="OLLAMA_MAX_RETRIES")
    ollama_retry_delay: float = Field(default=2.0, alias="OLLAMA_RETRY_DELAY")
    
    # GPU e Performance
    ollama_gpu_layers: int = Field(default=35, alias="OLLAMA_GPU_LAYERS")
    ollama_context_length: int = Field(default=4096, alias="OLLAMA_CONTEXT_LENGTH")
    ollama_threads: int = Field(default=8, alias="OLLAMA_THREADS")
    ollama_temperature: float = Field(default=0.1, alias="OLLAMA_TEMPERATURE")
    
    # Processamento de Documentos
    max_document_size_mb: int = Field(default=50, alias="MAX_DOCUMENT_SIZE_MB")
    text_extraction_timeout: float = Field(default=120.0, alias="TEXT_EXTRACTION_TIMEOUT")
    chunk_size_tokens: int = Field(default=3000, alias="CHUNK_SIZE_TOKENS")
    chunk_overlap_tokens: int = Field(default=200, alias="CHUNK_OVERLAP_TOKENS")
    
    # Prompts e Modelos
    prompt_version: str = Field(default="v1.0", alias="PROMPT_VERSION")
    prompt_templates_path: str = Field(default="app/ai/prompts", alias="PROMPT_TEMPLATES_PATH")
    fallback_model: str = Field(default="llama3:8b", alias="FALLBACK_MODEL")
    
    # Monitoring e Logging
    ai_metrics_enabled: bool = Field(default=True, alias="AI_METRICS_ENABLED")
    ai_response_time_threshold: float = Field(default=60.0, alias="AI_RESPONSE_TIME_THRESHOLD")
    ai_log_prompts: bool = Field(default=True, alias="AI_LOG_PROMPTS")
    ai_log_responses: bool = Field(default=True, alias="AI_LOG_RESPONSES")
    
    # Rate Limiting IA
    ai_rate_limit_per_minute: int = Field(default=30, alias="AI_RATE_LIMIT_PER_MINUTE")
    ai_rate_limit_per_hour: int = Field(default=500, alias="AI_RATE_LIMIT_PER_HOUR")
    ai_concurrent_requests: int = Field(default=3, alias="AI_CONCURRENT_REQUESTS")
    
    # Cache Configuration
    ai_cache_ttl_hours: int = Field(default=24, alias="AI_CACHE_TTL_HOURS")
    ai_cache_enabled: bool = Field(default=True, alias="AI_CACHE_ENABLED")
    
    # Monitoring Configuration  
    ai_metrics_retention_days: int = Field(default=30, alias="AI_METRICS_RETENTION_DAYS")
    ai_processing_timeout: float = Field(default=300.0, alias="AI_PROCESSING_TIMEOUT")
    
    # Property aliases for backward compatibility
    @property
    def REDIS_URL(self) -> str:
        return self.redis_url
        
    @property
    def OLLAMA_MODEL(self) -> str:
        return self.ollama_default_model
        
    @property
    def AI_CACHE_TTL_HOURS(self) -> int:
        return self.ai_cache_ttl_hours
        
    @property
    def AI_METRICS_RETENTION_DAYS(self) -> int:
        return self.ai_metrics_retention_days
        
    @property
    def AI_PROCESSING_TIMEOUT(self) -> float:
        return self.ai_processing_timeout
    
    # Main application properties for compatibility
    @property
    def API_V1_STR(self) -> str:
        return self.api_v1_str
    
    @property
    def PROJECT_NAME(self) -> str:
        return self.project_name
    
    @property
    def VERSION(self) -> str:
        return self.version
    
    @property
    def PROJECT_DESCRIPTION(self) -> str:
        return self.description
    
    @property
    def ENVIRONMENT(self) -> str:
        return "development" if self.debug else "production"
    
    @property
    def ALLOWED_HOSTS(self) -> List[str]:
        return ["*"] if self.debug else ["localhost", "127.0.0.1"]
    
    @property
    def BACKEND_CORS_ORIGINS(self) -> List[str]:
        return self.backend_cors_origins
    
    @property
    def DEBUG(self) -> bool:
        return self.debug

    @validator("backend_cors_origins", pre=True)
    def assemble_cors_origins(cls, v):
        """Processa a lista de origins do CORS"""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    @property
    def database_url(self) -> str:
        """Construct database URL from components if not provided directly"""
        if self.database_url_override:
            return self.database_url_override
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@"
            f"{self.postgres_server}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_sync(self) -> str:
        """URL do banco de dados para operações síncronas"""
        return self.database_url.replace(
            "postgresql+asyncpg://", 
            "postgresql://"
        )


@lru_cache()
def get_settings() -> Settings:
    """Retorna as configurações da aplicação (cached)"""
    return Settings()


# Instância global das configurações
settings = get_settings()
