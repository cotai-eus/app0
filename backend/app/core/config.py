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
