<!-- filepath: \\wsl.localhost\Ubuntu-20.04\home\app\.docs\Plano_backend.md -->
Okay, Engenheiro. Analisando os documentos `Plano.md` e `Plano_db.md`, podemos elaborar um plano técnico detalhado para o backend do Sistema de Automação de Licitações.

## Plano Técnico Detalhado do Backend

### 1. Arquitetura Geral - Monólito Modularizado Avançado

A arquitetura será um **Monólito Modularizado** com princípios de **Domain-Driven Design (DDD)** e **Clean Architecture**, construído com FastAPI. Esta abordagem facilita o aprendizado e permite futura migração para microsserviços.

**Princípios Arquiteturais:**
- **Separação de Responsabilidades**: Cada módulo tem responsabilidade única
- **Inversão de Dependência**: Abstrações não dependem de implementações
- **Domínios Isolados**: Cada domínio (Auth, Tenders, Quotes) é independente
- **Repository Pattern**: Abstração da camada de dados
- **Service Pattern**: Lógica de negócio centralizada
- **Factory Pattern**: Criação de objetos complexos

**Fluxo de Requisição Otimizado:**
```
Cliente (React) -> 
Nginx (Load Balancer + Rate Limiting) -> 
FastAPI App (Middleware Stack) -> 
Router -> 
Service Layer -> 
Repository Layer -> 
Database -> 
Response (+ Cache)
```

**Componentes Principais:**
1. **API Gateway (FastAPI)**: Ponto de entrada com middleware avançado
2. **Domain Services**: Lógica de negócio por domínio
3. **Repository Layer**: Abstração de dados (PostgreSQL/MongoDB)
4. **Integration Layer**: Serviços externos (Ollama, APIs)
5. **Background Processor (Celery)**: Tarefas assíncronas
6. **Real-time Communication**: WebSockets otimizados
7. **Caching Layer**: Redis multi-nível
8. **Monitoring & Observability**: Métricas e rastreamento

### 1.1. Estrutura de Domínios (DDD)

```
app/
├── domains/                    # Domínios de negócio
│   ├── auth/                  # Autenticação e autorização
│   │   ├── models.py         # Modelos SQLAlchemy
│   │   ├── schemas.py        # Pydantic schemas
│   │   ├── services.py       # Lógica de negócio
│   │   ├── repository.py     # Acesso a dados
│   │   └── router.py         # Endpoints FastAPI
│   ├── companies/            # Gestão de empresas
│   ├── tenders/              # Editais e licitações
│   ├── quotes/               # Cotações
│   ├── suppliers/            # Fornecedores
│   ├── forms/                # Formulários dinâmicos
│   ├── kanban/               # Gestão de projetos
│   ├── calendar/             # Integração calendário
│   ├── reports/              # Relatórios
│   └── notifications/        # Sistema de notificações
├── shared/                    # Código compartilhado
│   ├── infrastructure/       # Infraestrutura
│   ├── common/              # Utilitários comuns
│   └── interfaces/          # Contratos/Abstrações
├── tasks/                      # Celery tasks
│   ├── __init__.py
│   ├── celery_app.py          # Celery configuration
│   ├── base_task.py           # Base task class
│   ├── ai_tasks.py            # AI processing tasks
│   ├── email_tasks.py         # Email tasks
│   ├── report_tasks.py        # Report generation
│   └── maintenance_tasks.py   # System maintenance
├── websockets/                 # WebSocket handlers
│   ├── __init__.py
│   ├── connection_manager.py  # Connection management
│   ├── handlers/              # Message handlers
│   └── events.py              # Event types
├── tests/                      # Tests
│   ├── __init__.py
│   ├── conftest.py           # Pytest configuration
│   ├── factories/            # Test factories
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   └── e2e/                  # End-to-end tests
├── migrations/                 # Alembic migrations
│   ├── env.py
│   └── versions/
├── scripts/                    # Scripts utilitários
│   ├── init_db.py             # Database initialization
│   ├── seed_data.py           # Sample data
│   └── backup.py              # Backup utilities
├── docker/                     # Docker configurations
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   └── entrypoint.sh
├── monitoring/                 # Monitoring configuration
│   ├── prometheus.yml
│   ├── grafana/
│   └── alerts/
├── docs/                      # Documentation
│   ├── api/                    # API documentation
│   ├── architecture/           # Architecture docs
│   └── deployment/             # Deployment guides
├── .env.example                 # Environment variables example
├── pyproject.toml               # Poetry configuration
├── alembic.ini                  # Alembic configuration
├── pytest.ini                  # Pytest configuration
├── mypy.ini                     # MyPy configuration
├── .pre-commit-config.yaml      # Pre-commit hooks
└── README.md
```

### 2. Tecnologias e Versões Otimizadas

**Core Stack:**
- **Python**: 3.11+ (Performance melhorada)
- **FastAPI**: ~0.110.0 (Async nativo, validação Pydantic v2)
- **Uvicorn**: ~0.27.0 (ASGI server otimizado)
- **Gunicorn**: ~21.2.0 (Production workers)

**Database Stack:**
- **PostgreSQL**: 15+ (Performance e JSON melhorado)
- **SQLAlchemy**: ~2.0.x (Async ORM, melhor performance)
- **asyncpg**: ~0.29.0 (Driver async PostgreSQL)
- **MongoDB**: 6.0+ (Com Motor ~3.3.x)
- **Redis**: 7+ (Com aioredis ~2.0.x)

**Background Processing:**
- **Celery**: ~5.3.x (Task queue robusto)
- **Redis**: Broker e resultado backend
- **Flower**: Monitoramento Celery

**Security & Validation:**
- **Pydantic**: v2 (Validação 10x mais rápida)
- **python-jose[cryptography]**: ~3.3.0 (JWT)
- **passlib[bcrypt]**: ~1.7.4 (Hash senhas)
- **slowapi**: Rate limiting

**Integration & Utils:**
- **httpx**: ~0.26.0 (HTTP client async)
- **emails**: Envio de emails
- **PyMuPDF**: Processamento PDF
- **python-docx**: Processamento Word

**Development & Testing:**
- **pytest**: ~7.4.x
- **pytest-asyncio**: Testes async
- **pytest-cov**: Cobertura de código
- **black**: Code formatting
- **isort**: Import sorting
- **mypy**: Type checking
- **ruff**: Linting ultra-rápido

### 2.1. Configuração Avançada com Pydantic Settings

```python
# app/core/config.py
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Optional, List, Dict, Any
import secrets
from functools import lru_cache

class DatabaseSettings(BaseSettings):
    """Configurações de banco de dados"""
    POSTGRES_SERVER: str = Field(..., env="POSTGRES_SERVER")
    POSTGRES_USER: str = Field(..., env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(..., env="POSTGRES_PASSWORD")
    POSTGRES_DB: str = Field(..., env="POSTGRES_DB")
    POSTGRES_PORT: int = Field(default=5432, env="POSTGRES_PORT")
    
    # Pool de conexões otimizado
    DB_POOL_SIZE: int = Field(default=20, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(default=30, env="DB_MAX_OVERFLOW")
    DB_POOL_TIMEOUT: int = Field(default=30, env="DB_POOL_TIMEOUT")
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

class RedisSettings(BaseSettings):
    """Configurações Redis"""
    REDIS_URL: str = Field(default="redis://redis:6379", env="REDIS_URL")
    REDIS_CACHE_TTL: int = Field(default=3600, env="REDIS_CACHE_TTL")
    REDIS_MAX_CONNECTIONS: int = Field(default=100, env="REDIS_MAX_CONNECTIONS")

class SecuritySettings(BaseSettings):
    """Configurações de segurança"""
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    PASSWORD_MIN_LENGTH: int = 8
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 30
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600  # 1 hora

class AISettings(BaseSettings):
    """Configurações de IA"""
    OLLAMA_API_URL: str = Field(default="http://ollama:11434", env="OLLAMA_API_URL")
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    AI_PROVIDER: str = Field(default="ollama", env="AI_PROVIDER")
    AI_DEFAULT_MODEL: str = Field(default="llama3", env="AI_DEFAULT_MODEL")
    AI_REQUEST_TIMEOUT: int = Field(default=300, env="AI_REQUEST_TIMEOUT")
    AI_MAX_RETRIES: int = Field(default=3, env="AI_MAX_RETRIES")

class ObservabilitySettings(BaseSettings):
    """Configurações de observabilidade"""
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    SENTRY_DSN: Optional[str] = Field(default=None, env="SENTRY_DSN")
    JAEGER_AGENT_HOST: Optional[str] = Field(default=None, env="JAEGER_AGENT_HOST")

class Settings(
    DatabaseSettings,
    RedisSettings,
    SecuritySettings,
    AISettings,
    ObservabilitySettings
):
    """Configurações principais da aplicação"""
    
    # Aplicação
    PROJECT_NAME: str = "Sistema de Automação de Licitações"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"],
        env="BACKEND_CORS_ORIGINS"
    )
    
    # Upload de arquivos
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_FILE_TYPES: List[str] = [".pdf", ".doc", ".docx", ".txt"]
    UPLOAD_FOLDER: str = "/app/uploads"
    
    # MongoDB
    MONGO_DATABASE_URI: str = Field(..., env="MONGO_DATABASE_URI")
    
    # Email
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Cache das configurações"""
    return Settings()

settings = get_settings()
```

### 3. Estrutura de Diretórios Otimizada

```
backend/
├── app/
│   ├── main.py                     # Entry point FastAPI
│   ├── core/                       # Configurações core
│   │   ├── __init__.py
│   │   ├── config.py              # Configurações Pydantic
│   │   ├── security.py            # JWT, hashing, crypto
│   │   ├── logging.py             # Logging estruturado
│   │   ├── database.py            # Database connections
│   │   ├── cache.py               # Redis cache manager
│   │   └── exceptions.py          # Exception handlers
│   ├── api/                        # API layer
│   │   ├── __init__.py
│   │   ├── deps.py                # Dependências globais
│   │   ├── middleware.py          # Middleware stack
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py             # Router agregador
│   │       └── endpoints/         # Endpoints por domínio
│   ├── domains/                    # Domain-driven design
│   │   ├── __init__.py
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── models.py          # SQLAlchemy models
│   │   │   ├── schemas.py         # Pydantic schemas
│   │   │   ├── services.py        # Lógica de negócio
│   │   │   ├── repository.py      # Acesso a dados
│   │   │   ├── router.py          # Endpoints FastAPI
│   │   │   └── exceptions.py      # Domain exceptions
│   │   ├── companies/
│   │   ├── tenders/
│   │   ├── quotes/
│   │   ├── suppliers/
│   │   ├── forms/
│   │   ├── kanban/
│   │   ├── calendar/
│   │   ├── reports/
│   │   └── notifications/
│   ├── shared/                     # Código compartilhado
│   │   ├── __init__.py
│   │   ├── infrastructure/
│   │   │   ├── __init__.py
│   │   │   ├── email/            # Email service
│   │   │   ├── storage/          # File storage
│   │   │   ├── ai/               # AI integration
│   │   │   └── external_apis/    # External APIs
│   │   ├── common/
│   │   │   ├── __init__.py
│   │   │   ├── base_models.py    # Base SQLAlchemy models
│   │   │   ├── base_schemas.py   # Base Pydantic schemas
│   │   │   ├── base_repository.py # Base repository
│   │   │   ├── base_service.py   # Base service
│   │   │   ├── utils.py          # Utilities
│   │   │   └── constants.py      # Constants
│   │   └── interfaces/
│   │       ├── __init__.py
│   │       ├── repositories.py   # Repository interfaces
│   │       ├── services.py       # Service interfaces
│   │       └── external.py       # External service interfaces
│   ├── tasks/                      # Celery tasks
│   │   ├── __init__.py
│   │   ├── celery_app.py          # Celery configuration
│   │   ├── base_task.py           # Base task class
│   │   ├── ai_tasks.py            # AI processing tasks
│   │   ├── email_tasks.py         # Email tasks
│   │   ├── report_tasks.py        # Report generation
│   │   └── maintenance_tasks.py   # System maintenance
│   ├── websockets/                 # WebSocket handlers
│   │   ├── __init__.py
│   │   ├── connection_manager.py  # Connection management
│   │   ├── handlers/              # Message handlers
│   │   └── events.py              # Event types
│   ├── tests/                      # Tests
│   │   ├── __init__.py
│   │   ├── conftest.py           # Pytest configuration
│   │   ├── factories/            # Test factories
│   │   ├── unit/                 # Unit tests
│   │   ├── integration/          # Integration tests
│   │   └── e2e/                  # End-to-end tests
│   └── migrations/                 # Alembic migrations
│       ├── env.py
│       └── versions/
├── scripts/                        # Scripts utilitários
│   ├── init_db.py                 # Database initialization
│   ├── seed_data.py               # Sample data
│   └── backup.py                  # Backup utilities
├── docker/                         # Docker configurations
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   └── entrypoint.sh
├── monitoring/                     # Monitoring configuration
│   ├── prometheus.yml
│   ├── grafana/
│   └── alerts/
├── docs/                          # Documentation
│   ├── api/                      # API documentation
│   ├── architecture/             # Architecture docs
│   └── deployment/               # Deployment guides
├── .env.example                   # Environment variables example
├── pyproject.toml                 # Poetry configuration
├── alembic.ini                    # Alembic configuration
├── pytest.ini                    # Pytest configuration
├── mypy.ini                       # MyPy configuration
├── .pre-commit-config.yaml        # Pre-commit hooks
└── README.md
```

### 2. Tecnologias e Versões Otimizadas

**Core Stack:**
- **Python**: 3.11+ (Performance melhorada)
- **FastAPI**: ~0.110.0 (Async nativo, validação Pydantic v2)
- **Uvicorn**: ~0.27.0 (ASGI server otimizado)
- **Gunicorn**: ~21.2.0 (Production workers)

**Database Stack:**
- **PostgreSQL**: 15+ (Performance e JSON melhorado)
- **SQLAlchemy**: ~2.0.x (Async ORM, melhor performance)
- **asyncpg**: ~0.29.0 (Driver async PostgreSQL)
- **MongoDB**: 6.0+ (Com Motor ~3.3.x)
- **Redis**: 7+ (Com aioredis ~2.0.x)

**Background Processing:**
- **Celery**: ~5.3.x (Task queue robusto)
- **Redis**: Broker e resultado backend
- **Flower**: Monitoramento Celery

**Security & Validation:**
- **Pydantic**: v2 (Validação 10x mais rápida)
- **python-jose[cryptography]**: ~3.3.0 (JWT)
- **passlib[bcrypt]**: ~1.7.4 (Hash senhas)
- **slowapi**: Rate limiting

**Integration & Utils:**
- **httpx**: ~0.26.0 (HTTP client async)
- **emails**: Envio de emails
- **PyMuPDF**: Processamento PDF
- **python-docx**: Processamento Word

**Development & Testing:**
- **pytest**: ~7.4.x
- **pytest-asyncio**: Testes async
- **pytest-cov**: Cobertura de código
- **black**: Code formatting
- **isort**: Import sorting
- **mypy**: Type checking
- **ruff**: Linting ultra-rápido

### 2.1. Configuração Avançada com Pydantic Settings

```python
# app/core/config.py
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Optional, List, Dict, Any
import secrets
from functools import lru_cache

class DatabaseSettings(BaseSettings):
    """Configurações de banco de dados"""
    POSTGRES_SERVER: str = Field(..., env="POSTGRES_SERVER")
    POSTGRES_USER: str = Field(..., env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(..., env="POSTGRES_PASSWORD")
    POSTGRES_DB: str = Field(..., env="POSTGRES_DB")
    POSTGRES_PORT: int = Field(default=5432, env="POSTGRES_PORT")
    
    # Pool de conexões otimizado
    DB_POOL_SIZE: int = Field(default=20, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(default=30, env="DB_MAX_OVERFLOW")
    DB_POOL_TIMEOUT: int = Field(default=30, env="DB_POOL_TIMEOUT")
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

class RedisSettings(BaseSettings):
    """Configurações Redis"""
    REDIS_URL: str = Field(default="redis://redis:6379", env="REDIS_URL")
    REDIS_CACHE_TTL: int = Field(default=3600, env="REDIS_CACHE_TTL")
    REDIS_MAX_CONNECTIONS: int = Field(default=100, env="REDIS_MAX_CONNECTIONS")

class SecuritySettings(BaseSettings):
    """Configurações de segurança"""
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    PASSWORD_MIN_LENGTH: int = 8
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 30
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600  # 1 hora

class AISettings(BaseSettings):
    """Configurações de IA"""
    OLLAMA_API_URL: str = Field(default="http://ollama:11434", env="OLLAMA_API_URL")
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    AI_PROVIDER: str = Field(default="ollama", env="AI_PROVIDER")
    AI_DEFAULT_MODEL: str = Field(default="llama3", env="AI_DEFAULT_MODEL")
    AI_REQUEST_TIMEOUT: int = Field(default=300, env="AI_REQUEST_TIMEOUT")
    AI_MAX_RETRIES: int = Field(default=3, env="AI_MAX_RETRIES")

class ObservabilitySettings(BaseSettings):
    """Configurações de observabilidade"""
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    SENTRY_DSN: Optional[str] = Field(default=None, env="SENTRY_DSN")
    JAEGER_AGENT_HOST: Optional[str] = Field(default=None, env="JAEGER_AGENT_HOST")

class Settings(
    DatabaseSettings,
    RedisSettings,
    SecuritySettings,
    AISettings,
    ObservabilitySettings
):
    """Configurações principais da aplicação"""
    
    # Aplicação
    PROJECT_NAME: str = "Sistema de Automação de Licitações"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"],
        env="BACKEND_CORS_ORIGINS"
    )
    
    # Upload de arquivos
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_FILE_TYPES: List[str] = [".pdf", ".doc", ".docx", ".txt"]
    UPLOAD_FOLDER: str = "/app/uploads"
    
    # MongoDB
    MONGO_DATABASE_URI: str = Field(..., env="MONGO_DATABASE_URI")
    
    # Email
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Cache das configurações"""
    return Settings()

settings = get_settings()
```

### 3. Estrutura de Diretórios Otimizada

```
backend/
├── app/
│   ├── main.py                     # Entry point FastAPI
│   ├── core/                       # Configurações core
│   │   ├── __init__.py
│   │   ├── config.py              # Configurações Pydantic
│   │   ├── security.py            # JWT, hashing, crypto
│   │   ├── logging.py             # Logging estruturado
│   │   ├── database.py            # Database connections
│   │   ├── cache.py               # Redis cache manager
│   │   └── exceptions.py          # Exception handlers
│   ├── api/                        # API layer
│   │   ├── __init__.py
│   │   ├── deps.py                # Dependências globais
│   │   ├── middleware.py          # Middleware stack
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py             # Router agregador
│   │       └── endpoints/         # Endpoints por domínio
│   ├── domains/                    # Domain-driven design
│   │   ├── __init__.py
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── models.py          # SQLAlchemy models
│   │   │   ├── schemas.py         # Pydantic schemas
│   │   │   ├── services.py        # Lógica de negócio
│   │   │   ├── repository.py      # Acesso a dados
│   │   │   ├── router.py          # Endpoints FastAPI
│   │   │   └── exceptions.py      # Domain exceptions
│   │   ├── companies/
│   │   ├── tenders/
│   │   ├── quotes/
│   │   ├── suppliers/
│   │   ├── forms/
│   │   ├── kanban/
│   │   ├── calendar/
│   │   ├── reports/
│   │   └── notifications/
│   ├── shared/                     # Código compartilhado
│   │   ├── __init__.py
│   │   ├── infrastructure/
│   │   │   ├── __init__.py
│   │   │   ├── email/            # Email service
│   │   │   ├── storage/          # File storage
│   │   │   ├── ai/               # AI integration
│   │   │   └── external_apis/    # External APIs
│   │   ├── common/
│   │   │   ├── __init__.py
│   │   │   ├── base_models.py    # Base SQLAlchemy models
│   │   │   ├── base_schemas.py   # Base Pydantic schemas
│   │   │   ├── base_repository.py # Base repository
│   │   │   ├── base_service.py   # Base service
│   │   │   ├── utils.py          # Utilities
│   │   │   └── constants.py      # Constants
│   │   └── interfaces/
│   │       ├── __init__.py
│   │       ├── repositories.py   # Repository interfaces
│   │       ├── services.py       # Service interfaces
│   │       └── external.py       # External service interfaces
│   ├── tasks/                      # Celery tasks
│   │   ├── __init__.py
│   │   ├── celery_app.py          # Celery configuration
│   │   ├── base_task.py           # Base task class
│   │   ├── ai_tasks.py            # AI processing tasks
│   │   ├── email_tasks.py         # Email tasks
│   │   ├── report_tasks.py        # Report generation
│   │   └── maintenance_tasks.py   # System maintenance
│   ├── websockets/                 # WebSocket handlers
│   │   ├── __init__.py
│   │   ├── connection_manager.py  # Connection management
│   │   ├── handlers/              # Message handlers
│   │   └── events.py              # Event types
│   ├── tests/                      # Tests
│   │   ├── __init__.py
│   │   ├── conftest.py           # Pytest configuration
│   │   ├── factories/            # Test factories
│   │   ├── unit/                 # Unit tests
│   │   ├── integration/          # Integration tests
│   │   └── e2e/                  # End-to-end tests
│   └── migrations/                 # Alembic migrations
│       ├── env.py
│       └── versions/
├── scripts/                        # Scripts utilitários
│   ├── init_db.py                 # Database initialization
│   ├── seed_data.py               # Sample data
│   └── backup.py                  # Backup utilities
├── docker/                         # Docker configurations
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   └── entrypoint.sh
├── monitoring/                     # Monitoring configuration
│   ├── prometheus.yml
│   ├── grafana/
│   └── alerts/
├── docs/                          # Documentation
│   ├── api/                      # API documentation
│   ├── architecture/             # Architecture docs
│   └── deployment/               # Deployment guides
├── .env.example                   # Environment variables example
├── pyproject.toml                 # Poetry configuration
├── alembic.ini                    # Alembic configuration
├── pytest.ini                    # Pytest configuration
├── mypy.ini                       # MyPy configuration
├── .pre-commit-config.yaml        # Pre-commit hooks
└── README.md
```

### 2. Tecnologias e Versões Otimizadas

**Core Stack:**
- **Python**: 3.11+ (Performance melhorada)
- **FastAPI**: ~0.110.0 (Async nativo, validação Pydantic v2)
- **Uvicorn**: ~0.27.0 (ASGI server otimizado)
- **Gunicorn**: ~21.2.0 (Production workers)

**Database Stack:**
- **PostgreSQL**: 15+ (Performance e JSON melhorado)
- **SQLAlchemy**: ~2.0.x (Async ORM, melhor performance)
- **asyncpg**: ~0.29.0 (Driver async PostgreSQL)
- **MongoDB**: 6.0+ (Com Motor ~3.3.x)
- **Redis**: 7+ (Com aioredis ~2.0.x)

**Background Processing:**
- **Celery**: ~5.3.x (Task queue robusto)
- **Redis**: Broker e resultado backend
- **Flower**: Monitoramento Celery

**Security & Validation:**
- **Pydantic**: v2 (Validação 10x mais rápida)
- **python-jose[cryptography]**: ~3.3.0 (JWT)
- **passlib[bcrypt]**: ~1.7.4 (Hash senhas)
- **slowapi**: Rate limiting

**Integration & Utils:**
- **httpx**: ~0.26.0 (HTTP client async)
- **emails**: Envio de emails
- **PyMuPDF**: Processamento PDF
- **python-docx**: Processamento Word

**Development & Testing:**
- **pytest**: ~7.4.x
- **pytest-asyncio**: Testes async
- **pytest-cov**: Cobertura de código
- **black**: Code formatting
- **isort**: Import sorting
- **mypy**: Type checking
- **ruff**: Linting ultra-rápido

### 2.1. Configuração Avançada com Pydantic Settings

```python
# app/core/config.py
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Optional, List, Dict, Any
import secrets
from functools import lru_cache

class DatabaseSettings(BaseSettings):
    """Configurações de banco de dados"""
    POSTGRES_SERVER: str = Field(..., env="POSTGRES_SERVER")
    POSTGRES_USER: str = Field(..., env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(..., env="POSTGRES_PASSWORD")
    POSTGRES_DB: str = Field(..., env="POSTGRES_DB")
    POSTGRES_PORT: int = Field(default=5432, env="POSTGRES_PORT")
    
    # Pool de conexões otimizado
    DB_POOL_SIZE: int = Field(default=20, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(default=30, env="DB_MAX_OVERFLOW")
    DB_POOL_TIMEOUT: int = Field(default=30, env="DB_POOL_TIMEOUT")
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

class RedisSettings(BaseSettings):
    """Configurações Redis"""
    REDIS_URL: str = Field(default="redis://redis:6379", env="REDIS_URL")
    REDIS_CACHE_TTL: int = Field(default=3600, env="REDIS_CACHE_TTL")
    REDIS_MAX_CONNECTIONS: int = Field(default=100, env="REDIS_MAX_CONNECTIONS")

class SecuritySettings(BaseSettings):
    """Configurações de segurança"""
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    PASSWORD_MIN_LENGTH: int = 8
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 30
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600  # 1 hora

class AISettings(BaseSettings):
    """Configurações de IA"""
    OLLAMA_API_URL: str = Field(default="http://ollama:11434", env="OLLAMA_API_URL")
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    AI_PROVIDER: str = Field(default="ollama", env="AI_PROVIDER")
    AI_DEFAULT_MODEL: str = Field(default="llama3", env="AI_DEFAULT_MODEL")
    AI_REQUEST_TIMEOUT: int = Field(default=300, env="AI_REQUEST_TIMEOUT")
    AI_MAX_RETRIES: int = Field(default=3, env="AI_MAX_RETRIES")

class ObservabilitySettings(BaseSettings):
    """Configurações de observabilidade"""
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    SENTRY_DSN: Optional[str] = Field(default=None, env="SENTRY_DSN")
    JAEGER_AGENT_HOST: Optional[str] = Field(default=None, env="JAEGER_AGENT_HOST")

class Settings(
    DatabaseSettings,
    RedisSettings,
    SecuritySettings,
    AISettings,
    ObservabilitySettings
):
    """Configurações principais da aplicação"""
    
    # Aplicação
    PROJECT_NAME: str = "Sistema de Automação de Licitações"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"],
        env="BACKEND_CORS_ORIGINS"
    )
    
    # Upload de arquivos
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_FILE_TYPES: List[str] = [".pdf", ".doc", ".docx", ".txt"]
    UPLOAD_FOLDER: str = "/app/uploads"
    
    # MongoDB
    MONGO_DATABASE_URI: str = Field(..., env="MONGO_DATABASE_URI")
    
    # Email
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Cache das configurações"""
    return Settings()

settings = get_settings()
```

### 3. Estrutura de Diretórios Otimizada

```
backend/
├── app/
│   ├── main.py                     # Entry point FastAPI
│   ├── core/                       # Configurações core
│   │   ├── __init__.py
│   │   ├── config.py              # Configurações Pydantic
│   │   ├── security.py            # JWT, hashing, crypto
│   │   ├── logging.py             # Logging estruturado
│   │   ├── database.py            # Database connections
│   │   ├── cache.py               # Redis cache manager
│   │   └── exceptions.py          # Exception handlers
│   ├── api/                        # API layer
│   │   ├── __init__.py
│   │   ├── deps.py                # Dependências globais
│   │   ├── middleware.py          # Middleware stack
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py             # Router agregador
│   │       └── endpoints/         # Endpoints por domínio
│   ├── domains/                    # Domain-driven design
│   │   ├── __init__.py
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── models.py          # SQLAlchemy models
│   │   │   ├── schemas.py         # Pydantic schemas
│   │   │   ├── services.py        # Lógica de negócio
│   │   │   ├── repository.py      # Acesso a dados
│   │   │   ├── router.py          # Endpoints FastAPI
│   │   │   └── exceptions.py      # Domain exceptions
│   │   ├── companies/
│   │   ├── tenders/
│   │   ├── quotes/
│   │   ├── suppliers/
│   │   ├── forms/
│   │   ├── kanban/
│   │   ├── calendar/
│   │   ├── reports/
│   │   └── notifications/
│   ├── shared/                     # Código compartilhado
│   │   ├── __init__.py
│   │   ├── infrastructure/
│   │   │   ├── __init__.py
│   │   │   ├── email/            # Email service
│   │   │   ├── storage/          # File storage
│   │   │   ├── ai/               # AI integration
│   │   │   └── external_apis/    # External APIs
│   │   ├── common/
│   │   │   ├── __init__.py
│   │   │   ├── base_models.py    # Base SQLAlchemy models
│   │   │   ├── base_schemas.py   # Base Pydantic schemas
│   │   │   ├── base_repository.py # Base repository
│   │   │   ├── base_service.py   # Base service
│   │   │   ├── utils.py          # Utilities
│   │   │   └── constants.py      # Constants
│   │   └── interfaces/
│   │       ├── __init__.py
│   │       ├── repositories.py   # Repository interfaces
│   │       ├── services.py       # Service interfaces
│   │       └── external.py       # External service interfaces
│   ├── tasks/                      # Celery tasks
│   │   ├── __init__.py
│   │   ├── celery_app.py          # Celery configuration
│   │   ├── base_task.py           # Base task class
│   │   ├── ai_tasks.py            # AI processing tasks
│   │   ├── email_tasks.py         # Email tasks
│   │   ├── report_tasks.py        # Report generation
│   │   └── maintenance_tasks.py   # System maintenance
│   ├── websockets/                 # WebSocket handlers
│   │   ├── __init__.py
│   │   ├── connection_manager.py  # Connection management
│   │   ├── handlers/              # Message handlers
│   │   └── events.py              # Event types
│   ├── tests/                      # Tests
│   │   ├── __init__.py
│   │   ├── conftest.py           # Pytest configuration
│   │   ├── factories/            # Test factories
│   │   ├── unit/                 # Unit tests
│   │   ├── integration/          # Integration tests
│   │   └── e2e/                  # End-to-end tests
│   └── migrations/                 # Alembic migrations
│       ├── env.py
│       └── versions/
├── scripts/                        # Scripts utilitários
│   ├── init_db.py                 # Database initialization
│   ├── seed_data.py               # Sample data
│   └── backup.py                  # Backup utilities
├── docker/                         # Docker configurations
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   └── entrypoint.sh
├── monitoring/                     # Monitoring configuration
│   ├── prometheus.yml
│   ├── grafana/
│   └── alerts/
├── docs/                          # Documentation
│   ├── api/                      # API documentation
│   ├── architecture/             # Architecture docs
│   └── deployment/               # Deployment guides
├── .env.example                   # Environment variables example
├── pyproject.toml                 # Poetry configuration
├── alembic.ini                    # Alembic configuration
├── pytest.ini                    # Pytest configuration
├── mypy.ini                       # MyPy configuration
├── .pre-commit-config.yaml        # Pre-commit hooks
└── README.md
```

### 2. Tecnologias e Versões Otimizadas

**Core Stack:**
- **Python**: 3.11+ (Performance melhorada)
- **FastAPI**: ~0.110.0 (Async nativo, validação Pydantic v2)
- **Uvicorn**: ~0.27.0 (ASGI server otimizado)
- **Gunicorn**: ~21.2.0 (Production workers)

**Database Stack:**
- **PostgreSQL**: 15+ (Performance e JSON melhorado)
- **SQLAlchemy**: ~2.0.x (Async ORM, melhor performance)
- **asyncpg**: ~0.29.0 (Driver async PostgreSQL)
- **MongoDB**: 6.0+ (Com Motor ~3.3.x)
- **Redis**: 7+ (Com aioredis ~2.0.x)

**Background Processing:**
- **Celery**: ~5.3.x (Task queue robusto)
- **Redis**: Broker e resultado backend
- **Flower**: Monitoramento Celery

**Security & Validation:**
- **Pydantic**: v2 (Validação 10x mais rápida)
- **python-jose[cryptography]**: ~3.3.0 (JWT)
- **passlib[bcrypt]**: ~1.7.4 (Hash senhas)
- **slowapi**: Rate limiting

**Integration & Utils:**
- **httpx**: ~0.26.0 (HTTP client async)
- **emails**: Envio de emails
- **PyMuPDF**: Processamento PDF
- **python-docx**: Processamento Word

**Development & Testing:**
- **pytest**: ~7.4.x
- **pytest-asyncio**: Testes async
- **pytest-cov**: Cobertura de código
- **black**: Code formatting
- **isort**: Import sorting
- **mypy**: Type checking
- **ruff**: Linting ultra-rápido

### 2.1. Configuração Avançada com Pydantic Settings

```python
# app/core/config.py
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Optional, List, Dict, Any
import secrets
from functools import lru_cache

class DatabaseSettings(BaseSettings):
    """Configurações de banco de dados"""
    POSTGRES_SERVER: str = Field(..., env="POSTGRES_SERVER")
    POSTGRES_USER: str = Field(..., env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(..., env="POSTGRES_PASSWORD")
    POSTGRES_DB: str = Field(..., env="POSTGRES_DB")
    POSTGRES_PORT: int = Field(default=5432, env="POSTGRES_PORT")
    
    # Pool de conexões otimizado
    DB_POOL_SIZE: int = Field(default=20, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(default=30, env="DB_MAX_OVERFLOW")
    DB_POOL_TIMEOUT: int = Field(default=30, env="DB_POOL_TIMEOUT")
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

class RedisSettings(BaseSettings):
    """Configurações Redis"""
    REDIS_URL: str = Field(default="redis://redis:6379", env="REDIS_URL")
    REDIS_CACHE_TTL: int = Field(default=3600, env="REDIS_CACHE_TTL")
    REDIS_MAX_CONNECTIONS: int = Field(default=100, env="REDIS_MAX_CONNECTIONS")

class SecuritySettings(BaseSettings):
    """Configurações de segurança"""
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    PASSWORD_MIN_LENGTH: int = 8
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 30
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600  # 1 hora

class AISettings(BaseSettings):
    """Configurações de IA"""
    OLLAMA_API_URL: str = Field(default="http://ollama:11434", env="OLLAMA_API_URL")
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    AI_PROVIDER: str = Field(default="ollama", env="AI_PROVIDER")
    AI_DEFAULT_MODEL: str = Field(default="llama3", env="AI_DEFAULT_MODEL")
    AI_REQUEST_TIMEOUT: int = Field(default=300, env="AI_REQUEST_TIMEOUT")
    AI_MAX_RETRIES: int = Field(default=3, env="AI_MAX_RETRIES")

class ObservabilitySettings(BaseSettings):
    """Configurações de observabilidade"""
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    SENTRY_DSN: Optional[str] = Field(default=None, env="SENTRY_DSN")
    JAEGER_AGENT_HOST: Optional[str] = Field(default=None, env="JAEGER_AGENT_HOST")

class Settings(
    DatabaseSettings,
    RedisSettings,
    SecuritySettings,
    AISettings,
    ObservabilitySettings
):
    """Configurações principais da aplicação"""
    
    # Aplicação
    PROJECT_NAME: str = "Sistema de Automação de Licitações"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"],
        env="BACKEND_CORS_ORIGINS"
    )
    
    # Upload de arquivos
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_FILE_TYPES: List[str] = [".pdf", ".doc", ".docx", ".txt"]
    UPLOAD_FOLDER: str = "/app/uploads"
    
    # MongoDB
    MONGO_DATABASE_URI: str = Field(..., env="MONGO_DATABASE_URI")
    
    # Email
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Cache das configurações"""
    return Settings()

settings = get_settings()
```

### 3. Estrutura de Diretórios Otimizada

```
backend/
├── app/
│   ├── main.py                     # Entry point FastAPI
│   ├── core/                       # Configurações core
│   │   ├── __init__.py
│   │   ├── config.py              # Configurações Pydantic
│   │   ├── security.py            # JWT, hashing, crypto
│   │   ├── logging.py             # Logging estruturado
│   │   ├── database.py            # Database connections
│   │   ├── cache.py               # Redis cache manager
│   │   └── exceptions.py          # Exception handlers
│   ├── api/                        # API layer
│   │   ├── __init__.py
│   │   ├── deps.py                # Dependências globais
│   │   ├── middleware.py          # Middleware stack
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py             # Router agregador
│   │       └── endpoints/         # Endpoints por domínio
│   ├── domains/                    # Domain-driven design
│   │   ├── __init__.py
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── models.py          # SQLAlchemy models
│   │   │   ├── schemas.py         # Pydantic schemas
│   │   │   ├── services.py        # Lógica de negócio
│   │   │   ├── repository.py      # Acesso a dados
│   │   │   ├── router.py          # Endpoints FastAPI
│   │   │   └── exceptions.py      # Domain exceptions
│   │   ├── companies/
│   │   ├── tenders/
│   │   ├── quotes/
│   │   ├── suppliers/
│   │   ├── forms/
│   │   ├── kanban/
│   │   ├── calendar/
│   │   ├── reports/
│   │   └── notifications/
│   ├── shared/                     # Código compartilhado
│   │   ├── __init__.py
│   │   ├── infrastructure/
│   │   │   ├── __init__.py
│   │   │   ├── email/            # Email service
│   │   │   ├── storage/          # File storage
│   │   │   ├── ai/               # AI integration
│   │   │   └── external_apis/    # External APIs
│   │   ├── common/
│   │   │   ├── __init__.py
│   │   │   ├── base_models.py    # Base SQLAlchemy models
│   │   │   ├── base_schemas.py   # Base Pydantic schemas
│   │   │   ├── base_repository.py # Base repository
│   │   │   ├── base_service.py   # Base service
│   │   │   ├── utils.py          # Utilities
│   │   │   └── constants.py      # Constants
│   │   └── interfaces/
│   │       ├── __init__.py
│   │       ├── repositories.py   # Repository interfaces
│   │       ├── services.py       # Service interfaces
│   │       └── external.py       # External service interfaces
│   ├── tasks/                      # Celery tasks
│   │   ├── __init__.py
│   │   ├── celery_app.py          # Celery configuration
│   │   ├── base_task.py           # Base task class
│   │   ├── ai_tasks.py            # AI processing tasks
│   │   ├── email_tasks.py         # Email tasks
│   │   ├── report_tasks.py        # Report generation
│   │   └── maintenance_tasks.py   # System maintenance
│   ├── websockets/                 # WebSocket handlers
│   │   ├── __init__.py
│   │   ├── connection_manager.py  # Connection management
│   │   ├── handlers/              # Message handlers
│   │   └── events.py              # Event types
│   ├── tests/                      # Tests
│   │   ├── __init__.py
│   │   ├── conftest.py           # Pytest configuration
│   │   ├── factories/            # Test factories
│   │   ├── unit/                 # Unit tests
│   │   ├── integration/          # Integration tests
│   │   └── e2e/                  # End-to-end tests
│   └── migrations/                 # Alembic migrations
│       ├── env.py
│       └── versions/
├── scripts/                        # Scripts utilitários
│   ├── init_db.py                 # Database initialization
│   ├── seed_data.py               # Sample data
│   └── backup.py                  # Backup utilities
├── docker/                         # Docker configurations
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   └── entrypoint.sh
├── monitoring/                     # Monitoring configuration
│   ├── prometheus.yml
│   ├── grafana/
│   └── alerts/
├── docs/                          # Documentation
│   ├── api/                      # API documentation
│   ├── architecture/             # Architecture docs
│   └── deployment/               # Deployment guides
├── .env.example                   # Environment variables example
├── pyproject.toml                 # Poetry configuration
├── alembic.ini                    # Alembic configuration
├── pytest.ini                    # Pytest configuration
├── mypy.ini                       # MyPy configuration
├── .pre-commit-config.yaml        # Pre-commit hooks
└── README.md
```

### 2. Tecnologias e Versões Otimizadas

**Core Stack:**
- **Python**: 3.11+ (Performance melhorada)
- **FastAPI**: ~0.110.0 (Async nativo, validação Pydantic v2)
- **Uvicorn**: ~0.27.0 (ASGI server otimizado)
- **Gunicorn**: ~21.2.0 (Production workers)

**Database Stack:**
- **PostgreSQL**: 15+ (Performance e JSON melhorado)
- **SQLAlchemy**: ~2.0.x (Async ORM, melhor performance)
- **asyncpg**: ~0.29.0 (Driver async PostgreSQL)
- **MongoDB**: 6.0+ (Com Motor ~3.3.x)
- **Redis**: 7+ (Com aioredis ~2.0.x)

**Background Processing:**
- **Celery**: ~5.3.x (Task queue robusto)
- **Redis**: Broker e resultado backend
- **Flower**: Monitoramento Celery

**Security & Validation:**
- **Pydantic**: v2 (Validação 10x mais rápida)
- **python-jose[cryptography]**: ~3.3.0 (JWT)
- **passlib[bcrypt]**: ~1.7.4 (Hash senhas)
- **slowapi**: Rate limiting

**Integration & Utils:**
- **httpx**: ~0.26.0 (HTTP client async)
- **emails**: Envio de emails
- **PyMuPDF**: Processamento PDF
- **python-docx**: Processamento Word

**Development & Testing:**
- **pytest**: ~7.4.x
- **pytest-asyncio**: Testes async
- **pytest-cov**: Cobertura de código
- **black**: Code formatting
- **isort**: Import sorting
- **mypy**: Type checking
- **ruff**: Linting ultra-rápido

### 2.1. Configuração Avançada com Pydantic Settings

```python
# app/core/config.py
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Optional, List, Dict, Any
import secrets
from functools import lru_cache

class DatabaseSettings(BaseSettings):
    """Configurações de banco de dados"""
    POSTGRES_SERVER: str = Field(..., env="POSTGRES_SERVER")
    POSTGRES_USER: str = Field(..., env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(..., env="POSTGRES_PASSWORD")
    POSTGRES_DB: str = Field(..., env="POSTGRES_DB")
    POSTGRES_PORT: int = Field(default=5432, env="POSTGRES_PORT")
    
    # Pool de conexões otimizado
    DB_POOL_SIZE: int = Field(default=20, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(default=30, env="DB_MAX_OVERFLOW")
    DB_POOL_TIMEOUT: int = Field(default=30, env="DB_POOL_TIMEOUT")
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

class RedisSettings(BaseSettings):
    """Configurações Redis"""
    REDIS_URL: str = Field(default="redis://redis:6379", env="REDIS_URL")
    REDIS_CACHE_TTL: int = Field(default=3600, env="REDIS_CACHE_TTL")
    REDIS_MAX_CONNECTIONS: int = Field(default=100, env="REDIS_MAX_CONNECTIONS")

class SecuritySettings(BaseSettings):
    """Configurações de segurança"""
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    PASSWORD_MIN_LENGTH: int = 8
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 30
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600  # 1 hora

class AISettings(BaseSettings):
    """Configurações de IA"""
    OLLAMA_API_URL: str = Field(default="http://ollama:11434", env="OLLAMA_API_URL")
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    AI_PROVIDER: str = Field(default="ollama", env="AI_PROVIDER")
    AI_DEFAULT_MODEL: str = Field(default="llama3", env="AI_DEFAULT_MODEL")
    AI_REQUEST_TIMEOUT: int = Field(default=300, env="AI_REQUEST_TIMEOUT")
    AI_MAX_RETRIES: int = Field(default=3, env="AI_MAX_RETRIES")

class ObservabilitySettings(BaseSettings):
    """Configurações de observabilidade"""
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    SENTRY_DSN: Optional[str] = Field(default=None, env="SENTRY_DSN")
    JAEGER_AGENT_HOST: Optional[str] = Field(default=None, env="JAEGER_AGENT_HOST")

class Settings(
    DatabaseSettings,
    RedisSettings,
    SecuritySettings,
    AISettings,
    ObservabilitySettings
):
    """Configurações principais da aplicação"""
    
    # Aplicação
    PROJECT_NAME: str = "Sistema de Automação de Licitações"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"],
        env="BACKEND_CORS_ORIGINS"
    )
    
    # Upload de arquivos
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_FILE_TYPES: List[str] = [".pdf", ".doc", ".docx", ".txt"]
    UPLOAD_FOLDER: str = "/app/uploads"
    
    # MongoDB
    MONGO_DATABASE_URI: str = Field(..., env="MONGO_DATABASE_URI")
    
    # Email
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Cache das configurações"""
    return Settings()

settings = get_settings()
```

### 3. Estrutura de Diretórios Otimizada

```
backend/
├── app/
│   ├── main.py                     # Entry point FastAPI
│   ├── core/                       # Configurações core
│   │   ├── __init__.py
│   │   ├── config.py              # Configurações Pydantic
│   │   ├── security.py            # JWT, hashing, crypto
│   │   ├── logging.py             # Logging estruturado
│   │   ├── database.py            # Database connections
│   │   ├── cache.py               # Redis cache manager
│   │   └── exceptions.py          # Exception handlers
│   ├── api/                        # API layer
│   │   ├── __init__.py
│   │   ├── deps.py                # Dependências globais
│   │   ├── middleware.py          # Middleware stack
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py             # Router agregador
│   │       └── endpoints/         # Endpoints por domínio
│   ├── domains/                    # Domain-driven design
│   │   ├── __init__.py
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── models.py          # SQLAlchemy models
│   │   │   ├── schemas.py         # Pydantic schemas
│   │   │   ├── services.py        # Lógica de negócio
│   │   │   ├── repository.py      # Acesso a dados
│   │   │   ├── router.py          # Endpoints FastAPI
│   │   │   └── exceptions.py      # Domain exceptions
│   │   ├── companies/
│   │   ├── tenders/
│   │   ├── quotes/
│   │   ├── suppliers/
│   │   ├── forms/
│   │   ├── kanban/
│   │   ├── calendar/
│   │   ├── reports/
│   │   └── notifications/
│   ├── shared/                     # Código compartilhado
│   │   ├── __init__.py
│   │   ├── infrastructure/
│   │   │   ├── __init__.py
│   │   │   ├── email/            # Email service
│   │   │   ├── storage/          # File storage
│   │   │   ├── ai/               # AI integration
│   │   │   └── external_apis/    # External APIs
│   │   ├── common/
│   │   │   ├── __init__.py
│   │   │   ├── base_models.py    # Base SQLAlchemy models
│   │   │   ├── base_schemas.py   # Base Pydantic schemas
│   │   │   ├── base_repository.py # Base repository
│   │   │   ├── base_service.py   # Base service
│   │   │   ├── utils.py          # Utilities
│   │   │   └── constants.py      # Constants
│   │   └── interfaces/
│   │       ├── __init__.py
│   │       ├── repositories.py   # Repository interfaces
│   │       ├── services.py       # Service interfaces
│   │       └── external.py       # External service interfaces
│   ├── tasks/                      # Celery tasks
│   │   ├── __init__.py
│   │   ├── celery_app.py          # Celery configuration
│   │   ├── base_task.py           # Base task class
│   │   ├── ai_tasks.py            # AI processing tasks
│   │   ├── email_tasks.py         # Email tasks
│   │   ├── report_tasks.py        # Report generation
│   │   └── maintenance_tasks.py   # System maintenance
│   ├── websockets/                 # WebSocket handlers
│   │   ├── __init__.py
│   │   ├── connection_manager.py  # Connection management
│   │   ├── handlers/              # Message handlers
│   │   └── events.py              # Event types
│   ├── tests/                      # Tests
│   │   ├── __init__.py
│   │   ├── conftest.py           # Pytest configuration
│   │   ├── factories/            # Test factories
│   │   ├── unit/                 # Unit tests
│   │   ├── integration/          # Integration tests
│   │   └── e2e/                  # End-to-end tests
│   └── migrations/                 # Alembic migrations
│       ├── env.py
│       └── versions/
├── scripts/                        # Scripts utilitários
│   ├── init_db.py                 # Database initialization
│   ├── seed_data.py               # Sample data
│   └── backup.py                  # Backup utilities
├── docker/                         # Docker configurations
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   └── entrypoint.sh
├── monitoring/                     # Monitoring configuration
│   ├── prometheus.yml
│   ├── grafana/
│   └── alerts/
├── docs/                          # Documentation
│   ├── api/                      # API documentation
│   ├── architecture/             # Architecture docs
│   └── deployment/               # Deployment guides
├── .env.example                   # Environment variables example
├── pyproject.toml                 # Poetry configuration
├── alembic.ini                    # Alembic configuration
├── pytest.ini                    # Pytest configuration
├── mypy.ini                       # MyPy configuration
├── .pre-commit-config.yaml        # Pre-commit hooks
└── README.md
```

### 2. Tecnologias e Versões Otimizadas

**Core Stack:**
- **Python**: 3.11+ (Performance melhorada)
- **FastAPI**: ~0.110.0 (Async nativo, validação Pydantic v2)
- **Uvicorn**: ~0.27.0 (ASGI server otimizado)
- **Gunicorn**: ~21.2.0 (Production workers)

**Database Stack:**
- **PostgreSQL**: 15+ (Performance e JSON melhorado)
- **SQLAlchemy**: ~2.0.x (Async ORM, melhor performance)
- **asyncpg**: ~0.29.0 (Driver async PostgreSQL)
- **MongoDB**: 6.0+ (Com Motor ~3.3.x)
- **Redis**:  7+ (Com aioredis ~2.0.x)

**Background Processing:**
- **Celery**: ~5.3.x (Task queue robusto)
- **Redis**: Broker e resultado backend
- **Flower**: Monitoramento Celery

**Security & Validation:**
- **Pydantic**: v2 (Validação 10x mais rápida)
- **python-jose[cryptography]**: ~3.3.0 (JWT)
- **passlib[bcrypt]**: ~1.7.4 (Hash senhas)
- **slowapi**: Rate limiting

**Integration & Utils:**
- **httpx**: ~0.26.0 (HTTP client async)
- **emails**: Envio de emails
- **PyMuPDF**: Processamento PDF
- **python-docx**: Processamento Word

**Development & Testing:**
- **pytest**: ~7.4.x
- **pytest-asyncio**: Testes async
- **pytest-cov**: Cobertura de código
- **black**: Code formatting
- **isort**: Import sorting
- **mypy**: Type checking
- **ruff**: Linting ultra-rápido

### 2.1. Configuração Avançada com Pydantic Settings

```python
# app/core/config.py
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Optional, List, Dict, Any
import secrets
from functools import lru_cache

class DatabaseSettings(BaseSettings):
    """Configurações de banco de dados"""
    POSTGRES_SERVER: str = Field(..., env="POSTGRES_SERVER")
    POSTGRES_USER: str = Field(..., env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(..., env="POSTGRES_PASSWORD")
    POSTGRES_DB: str = Field(..., env="POSTGRES_DB")
    POSTGRES_PORT: int = Field(default=5432, env="POSTGRES_PORT")
    
    # Pool de conexões otimizado
    DB_POOL_SIZE: int = Field(default=20, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(default=30, env="DB_MAX_OVERFLOW")
    DB_POOL_TIMEOUT: int = Field(default=30, env="DB_POOL_TIMEOUT")
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

class RedisSettings(BaseSettings):
    """Configurações Redis"""
    REDIS_URL: str = Field(default="redis://redis:6379", env="REDIS_URL")
    REDIS_CACHE_TTL: int = Field(default=3600, env="REDIS_CACHE_TTL")
    REDIS_MAX_CONNECTIONS: int = Field(default=100, env="REDIS_MAX_CONNECTIONS")

class SecuritySettings(BaseSettings):
    """Configurações de segurança"""
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    PASSWORD_MIN_LENGTH: int = 8
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 30
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600  # 1 hora

class AISettings(BaseSettings):
    """Configurações de IA"""
    OLLAMA_API_URL: str = Field(default="http://ollama:11434", env="OLLAMA_API_URL")
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    AI_PROVIDER: str = Field(default="ollama", env="AI_PROVIDER")
    AI_DEFAULT_MODEL: str = Field(default="llama3", env="AI_DEFAULT_MODEL")
    AI_REQUEST_TIMEOUT: int = Field(default=300, env="AI_REQUEST_TIMEOUT")
    AI_MAX_RETRIES: int = Field(default=3, env="AI_MAX_RETRIES")

class ObservabilitySettings(BaseSettings):
    """Configurações de observabilidade"""
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    SENTRY_DSN: Optional[str] = Field(default=None, env="SENTRY_DSN")
    JAEGER_AGENT_HOST: Optional[str] = Field(default=None, env="JAEGER_AGENT_HOST")

class Settings(
    DatabaseSettings,
    RedisSettings,
    SecuritySettings,
    AISettings,
    ObservabilitySettings
):
    """Configurações principais da aplicação"""
    
    # Aplicação
    PROJECT_NAME: str = "Sistema de Automação de Licitações"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"],
        env="BACKEND_CORS_ORIGINS"
    )
    
    # Upload de arquivos
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_FILE_TYPES: List[str] = [".pdf", ".doc", ".docx", ".txt"]
    UPLOAD_FOLDER: str = "/app/uploads"
    
    # MongoDB
    MONGO_DATABASE_URI: str = Field(..., env="MONGO_DATABASE_URI")
    
    # Email
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Cache das configurações"""
    return Settings()

settings = get_settings()
```

### 3. Estrutura de Diretórios Otimizada

```
backend/
├── app/
│   ├── main.py                     # Entry point FastAPI
│   ├── core/                       # Configurações core
│   │   ├── __init__.py
│   │   ├── config.py              # Configurações Pydantic
│   │   ├── security.py            # JWT, hashing, crypto
│   │   ├── logging.py             # Logging estruturado
│   │   ├── database.py            # Database connections
│   │   ├── cache.py               # Redis cache manager
│   │   └── exceptions.py          # Exception handlers
│   ├── api/                        # API layer
│   │   ├── __init__.py
│   │   ├── deps.py                # Dependências globais
│   │   ├── middleware.py          # Middleware stack
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py             # Router agregador
│   │       └── endpoints/         # Endpoints por domínio
│   ├── domains/                    # Domain-driven design
│   │   ├── __init__.py
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── models.py          # SQLAlchemy models
│   │   │   ├── schemas.py         # Pydantic schemas
│   │   │   ├── services.py        # Lógica de negócio
│   │   │   ├── repository.py      # Acesso a dados
│   │   │   ├── router.py          # Endpoints FastAPI
│   │   │   └── exceptions.py      # Domain exceptions
│   │   ├── companies/
│   │   ├── tenders/
│   │   ├── quotes/
│   │   ├── suppliers/
│   │   ├── forms/
│   │   ├── kanban/
│   │   ├── calendar/
│   │   ├── reports/
│   │   └── notifications/
│   ├── shared/                     # Código compartilhado
│   │   ├── __init__.py
│   │   ├── infrastructure/
│   │   │   ├── __init__.py
│   │   │   ├── email/            # Email service
│   │   │   ├── storage/          # File storage
│   │   │   ├── ai/               # AI integration
│   │   │   └── external_apis/    # External APIs
│   │   ├── common/
│   │   │   ├── __init__.py
│   │   │   ├── base_models.py    # Base SQLAlchemy models
│   │   │   ├── base_schemas.py   # Base Pydantic schemas
│   │   │   ├── base_repository.py # Base repository
│   │   │   ├── base_service.py   # Base service
│   │   │   ├── utils.py          # Utilities
│   │   │   └── constants.py      # Constants
│   │   └── interfaces/
│   │       ├── __init__.py
│   │       ├── repositories.py   # Repository interfaces
│   │       ├── services.py       # Service interfaces
│   │       └── external.py       # External service interfaces
│   ├── tasks/                      # Celery tasks
│   │   ├── __init__.py
│   │   ├── celery_app.py          # Celery configuration
│   │   ├── base_task.py           # Base task class
│   │   ├── ai_tasks.py            # AI processing tasks
│   │   ├── email_tasks.py         # Email tasks
│   │   ├── report_tasks.py        # Report generation
│   │   └── maintenance_tasks.py   # System maintenance
│   ├── websockets/                 # WebSocket handlers
│   │   ├── __init__.py
│   │   ├── connection_manager.py  # Connection management
│   │   ├── handlers/              # Message handlers
│   │   └── events.py              # Event types
│   ├── tests/                      # Tests
│   │   ├── __init__.py
│   │   ├── conftest.py           # Pytest configuration
│   │   ├── factories/            # Test factories
│   │   ├── unit/                 # Unit tests
│   │   ├── integration/          # Integration tests
│   │   └── e2e/                  # End-to-end tests
│   └── migrations/                 # Alembic migrations
│       ├── env.py
│       └── versions/
├── scripts/                        # Scripts utilitários
│   ├── init_db.py                 # Database initialization
│   ├── seed_data.py               # Sample data
│   └── backup.py                  # Backup utilities
├── docker/                         # Docker configurations
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   └── entrypoint.sh
├── monitoring/                     # Monitoring configuration
│   ├── prometheus.yml
│   ├── grafana/
│   └── alerts/
├── docs/                          # Documentation
│   ├── api/                      # API documentation
│   ├── architecture/             # Architecture docs
│   └── deployment/               # Deployment guides
├── .env.example                   # Environment variables example
├── pyproject.toml                 # Poetry configuration
├── alembic.ini                    # Alembic configuration
├── pytest.ini                    # Pytest configuration
├── mypy.ini                       # MyPy configuration
├── .pre-commit-config.yaml        # Pre-commit hooks
└── README.md
```

### 3. Estrutura de Diretórios Otimizada

```
backend/
├── app/
│   ├── main.py                     # Entry point FastAPI
│   ├── core/                       # Configurações core
│   │   ├── __init__.py
│   │   ├── config.py              # Configurações Pydantic
│   │   ├── security.py            # JWT, hashing, crypto
│   │   ├── logging.py             # Logging estruturado
│   │   ├── database.py            # Database connections
│   │   ├── cache.py               # Redis cache manager
│   │   └── exceptions.py          # Exception handlers
│   ├── api/                        # API layer
│   │   ├── __init__.py
│   │   ├── deps.py                # Dependências globais
│   │   ├── middleware.py          # Middleware stack
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py             # Router agregador
│   │       └── endpoints/         # Endpoints por domínio
│   ├── domains/                    # Domain-driven design
│   │   ├── __init__.py
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── models.py          # SQLAlchemy models
│   │   │   ├── schemas.py         # Pydantic schemas
│   │   │   ├── services.py        # Lógica de negócio
│   │   │   ├── repository.py      # Acesso a dados
│   │   │   ├── router.py          # Endpoints FastAPI
│   │   │   └── exceptions.py      # Domain exceptions
│   │   ├── companies/
│   │   ├── tenders/
│   │   ├── quotes/
│   │   ├── suppliers/
│   │   ├── forms/
│   │   ├── kanban/
│   │   ├── calendar/
│   │   ├── reports/
│   │   └── notifications/
│   ├── shared/                     # Código compartilhado
│   │   ├── __init__.py
│   │   ├── infrastructure/
│   │   │   ├── __init__.py
│   │   │   ├── email/            # Email service
│   │   │   ├── storage/          # File storage
│   │   │   ├── ai/               # AI integration
│   │   │   └── external_apis/    # External APIs
│   │   ├── common/
│   │   │   ├── __init__.py
│   │   │   ├── base_models.py    # Base SQLAlchemy models
│   │   │   ├── base_schemas.py   # Base Pydantic schemas
│   │   │   ├── base_repository.py # Base repository
│   │   │   ├── base_service.py   # Base service
│   │   │   ├── utils.py          # Utilities
│   │   │   └── constants.py      # Constants
│   │   └── interfaces/
│   │       ├── __init__.py
│   │       ├── repositories.py   # Repository interfaces
│   │       ├── services.py       # Service interfaces
│   │       └── external.py       # External service interfaces
│   ├── tasks/                      # Celery tasks
│   │   ├── __init__.py
│   │   ├── celery_app.py          # Celery configuration
│   │   ├── base_task.py           # Base task class
│   │   ├── ai_tasks.py            # AI processing tasks
│   │   ├── email_tasks.py         # Email tasks
│   │   ├── report_tasks.py        # Report generation
│   │   └── maintenance_tasks.py   # System maintenance
│   ├── websockets/                 # WebSocket handlers
│   │   ├── __init__.py
│   │   ├── connection_manager.py  # Connection management
│   │   ├── handlers/              # Message handlers
│   │   └── events.py              # Event types
│   ├── tests/                      # Tests
│   │   ├── __init__.py
│   │   ├── conftest.py           # Pytest configuration
│   │   ├── factories/            # Test factories
│   │   ├── unit/                 # Unit tests
│   │   ├── integration/          # Integration tests
│   │   └── e2e/                  # End-to-end tests
│   └── migrations/                 # Alembic migrations
│       ├── env.py
│       └── versions/
├── scripts/                        # Scripts utilitários
│   ├── init_db.py                 # Database initialization
│   ├── seed_data.py               # Sample data
│   └── backup.py                  # Backup utilities
├── docker/                         # Docker configurations
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   └── entrypoint.sh
├── monitoring/                     # Monitoring configuration
│   ├── prometheus.yml
│   ├── grafana/
│   └── alerts/
├── docs/                          # Documentation
│   ├── api/                      # API documentation
│   ├── architecture/             # Architecture docs
│   └── deployment/               # Deployment guides
├── .env.example                   # Environment variables example
├── pyproject.toml                 # Poetry configuration
├── alembic.ini                    # Alembic configuration
├── pytest.ini                    # Pytest configuration
├── mypy.ini                       # MyPy configuration
├── .pre-commit-config.yaml        # Pre-commit hooks
└── README.md
```

### 4. Padrões de Arquitetura Implementados

### 4.1. Repository Pattern

```python
# app/shared/interfaces/repositories.py
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    """Interface base para repositories"""
    
    @abstractmethod
    async def create(self, db: AsyncSession, *, obj_in: Dict[str, Any]) -> T:
        pass
    
    @abstractmethod
    async def get(self, db: AsyncSession, id: UUID) -> Optional[T]:
        pass
    
    @abstractmethod
    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[T]:
        pass
    
    @abstractmethod
    async def update(
        self, db: AsyncSession, *, db_obj: T, obj_in: Dict[str, Any]
    ) -> T:
        pass
    
    @abstractmethod
    async def delete(self, db: AsyncSession, *, id: UUID) -> T:
        pass

# app/shared/common/base_repository.py
from typing import Type, TypeVar, Generic, List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from app.shared.interfaces.repositories import BaseRepository

ModelType = TypeVar("ModelType")

class SQLAlchemyRepository(BaseRepository[ModelType], Generic[ModelType]):
    """Implementação base do repository para SQLAlchemy"""
    
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    async def create(self, db: AsyncSession, *, obj_in: Dict[str, Any]) -> ModelType:
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def get(self, db: AsyncSession, id: UUID) -> Optional[ModelType]:
        stmt = select(self.model).where(self.model.id == id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_multi(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        stmt = select(self.model).offset(skip).limit(limit)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    stmt = stmt.where(getattr(self.model, key) == value)
        
        result = await db.execute(stmt)
        return result.scalars().all()
    
    async def update(
        self, db: AsyncSession, *, db_obj: ModelType, obj_in: Dict[str, Any]
    ) -> ModelType:
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def delete(self, db: AsyncSession, *, id: UUID) -> Optional[ModelType]:
        db_obj = await self.get(db, id)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
        return db_obj
```

### 4.2. Service Pattern

```python
# app/shared/interfaces/services.py
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar('T')

class BaseService(ABC, Generic[T]):
    """Interface base para services"""
    
    @abstractmethod
    async def create(self, db: AsyncSession, *, obj_in: Dict[str, Any]) -> T:
        pass
    
    @abstractmethod
    async def get_by_id(self, db: AsyncSession, *, id: UUID) -> Optional[T]:
        pass
    
    @abstractmethod
    async def get_all(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[T]:
        pass

# app/shared/common/base_service.py
from typing import Type, TypeVar, Generic, List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.interfaces.services import BaseService
from app.shared.interfaces.repositories import BaseRepository

ModelType = TypeVar("ModelType")
RepositoryType = TypeVar("RepositoryType", bound=BaseRepository)

class CRUDService(BaseService[ModelType], Generic[ModelType, RepositoryType]):
    """Service base com operações CRUD"""
    
    def __init__(self, repository: RepositoryType):
        self.repository = repository
    
    async def create(self, db: AsyncSession, *, obj_in: Dict[str, Any]) -> ModelType:
        """Criar novo registro"""
        # Validações de negócio aqui
        return await self.repository.create(db, obj_in=obj_in)
    
    async def get_by_id(self, db: AsyncSession, *, id: UUID) -> Optional[ModelType]:
        """Buscar por ID"""
        return await self.repository.get(db, id=id)
    
    async def get_all(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """Listar registros com filtros"""
        return await self.repository.get_multi(
            db, skip=skip, limit=limit, filters=filters
        )
    
    async def update(
        self, 
        db: AsyncSession, 
        *, 
        id: UUID, 
        obj_in: Dict[str, Any]
    ) -> Optional[ModelType]:
        """Atualizar registro"""
        db_obj = await self.repository.get(db, id=id)
        if not db_obj:
            return None
        
        # Validações de negócio aqui
        return await self.repository.update(db, db_obj=db_obj, obj_in=obj_in)
    
    async def delete(self, db: AsyncSession, *, id: UUID) -> Optional[ModelType]:
        """Deletar registro"""
        # Validações de negócio aqui
        return await self.repository.delete(db, id=id)
```

### 4.3. Factory Pattern para Serviços

```python
# app/core/factory.py
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.auth.services import AuthService
from app.domains.tenders.services import TenderService
from app.domains.quotes.services import QuoteService
from app.shared.infrastructure.ai.services import AIService
from app.shared.infrastructure.email.services import EmailService

class ServiceFactory:
    """Factory para criação de services"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._services: Dict[str, Any] = {}
    
    def get_auth_service(self) -> AuthService:
        if "auth" not in self._services:
            self._services["auth"] = AuthService(self.db)
        return self._services["auth"]
    
    def get_tender_service(self) -> TenderService:
        if "tender" not in self._services:
            self._services["tender"] = TenderService(self.db)
        return self._services["tender"]
    
    def get_quote_service(self) -> QuoteService:
        if "quote" not in self._services:
            self._services["quote"] = QuoteService(self.db)
        return self._services["quote"]
    
    def get_ai_service(self) -> AIService:
        if "ai" not in self._services:
            self._services["ai"] = AIService()
        return self._services["ai"]
    
    def get_email_service(self) -> EmailService:
        if "email" not in self._services:
            self._services["email"] = EmailService()
        return self._services["email"]

# app/api/deps.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.factory import ServiceFactory

async def get_service_factory(
    db: AsyncSession = Depends(get_db)
) -> ServiceFactory:
    """Dependência para obter service factory"""
    return ServiceFactory(db)
```

### 5. Sistema de Cache Multi-Nível

```python
# app/core/cache.py
import json
import asyncio
from typing import Any, Optional, Dict, List
from functools import wraps
import aioredis
from app.core.config import settings

class CacheManager:
    """Gerenciador de cache Redis com múltiplos níveis"""
    
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self._connection_pool = None
    
    async def init_redis(self):
        """Inicializar conexão Redis"""
        self._connection_pool = aioredis.ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            retry_on_timeout=True
        )
        self.redis = aioredis.Redis(connection_pool=self._connection_pool)
    
    async def get(self, key: str) -> Optional[Any]:
        """Obter valor do cache"""
        if not self.redis:
            return None
        
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
        except Exception:
            return None
        return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: int = settings.REDIS_CACHE_TTL
    ) -> bool:
        """Definir valor no cache"""
        if not self.redis:
            return False
        
        try:
            serialized = json.dumps(value, default=str)
            await self.redis.setex(key, ttl, serialized)
            return True
        except Exception:
            return False
    
    async def delete(self, key: str) -> bool:
        """Deletar chave do cache"""
        if not self.redis:
            return False
        
        try:
            await self.redis.delete(key)
            return True
        except Exception:
            return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidar chaves por padrão"""
        if not self.redis:
            return 0
        
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                return await self.redis.delete(*keys)
            return 0
        except Exception:
            return 0

# Instância global do cache
cache_manager = CacheManager()

def cache_key(*args, **kwargs) -> str:
    """Gerar chave de cache consistente"""
    key_parts = [str(arg) for arg in args]
    key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
    return ":".join(key_parts)

def cached(ttl: int = settings.REDIS_CACHE_TTL, key_prefix: str = "api"):
    """Decorator para cache automático de funções"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Gerar chave de cache
            cache_key_str = f"{key_prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"
            
            # Tentar obter do cache
            cached_result = await cache_manager.get(cache_key_str)
            if cached_result is not None:
                return cached_result
            
            # Executar função e cachear resultado
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key_str, result, ttl)
            
            return result
        return wrapper
    return decorator
```

### 6. Sistema de Performance e Otimização

### 6.1. Connection Pooling Otimizado

```python
# app/core/database.py
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession, 
    async_sessionmaker, 
    create_async_engine
)
from sqlalchemy.pool import NullPool, QueuePool
from app.core.config import settings

class DatabaseManager:
    """Gerenciador de conexões de banco otimizado"""
    
    def __init__(self):
        self.engine = None
        self.async_session = None
    
    async def init_db(self):
        """Inicializar conexões de banco"""
        # Engine PostgreSQL otimizado
        self.engine = create_async_engine(
            settings.SQLALCHEMY_DATABASE_URI,
            poolclass=QueuePool,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            pool_pre_ping=True,
            pool_recycle=3600,  # Reciclar conexões a cada hora
            echo=settings.DEBUG,
            future=True
        )
        
        self.async_session = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False
        )
    
    async def close_db(self):
        """Fechar conexões"""
        if self.engine:
            await self.engine.dispose()

# Instância global
db_manager = DatabaseManager()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency para obter sessão de banco"""
    async with db_manager.async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

### 6.2. Query Optimization

```python
# app/shared/common/query_optimizer.py
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession

class QueryOptimizer:
    """Otimizador de queries SQLAlchemy"""
    
    @staticmethod
    def optimize_select(
        query, 
        *, 
        eager_load: Optional[List[str]] = None,
        join_load: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ):
        """Otimizar query SELECT"""
        
        # Eager loading para evitar N+1
        if eager_load:
            for relation in eager_load:
                query = query.options(selectinload(relation))
        
        # Join loading para relacionamentos 1:1 ou poucos registros
        if join_load:
            for relation in join_load:
                query = query.options(joinedload(relation))
        
        # Paginação
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        return query
    
    @staticmethod
    async def count_optimized(
        session: AsyncSession, 
        model, 
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """Contagem otimizada de registros"""
        query = select(func.count(model.id))
        
        if filters:
            for key, value in filters.items():
                if hasattr(model, key):
                    query = query.where(getattr(model, key) == value)
        
        result = await session.execute(query)
        return result.scalar()
```

### 6.3. Background Tasks Otimizados

```python
# app/tasks/base_task.py
from celery import Task
from celery.signals import task_prerun, task_postrun
from celery.utils.log import get_task_logger
import time
from typing import Any, Dict

logger = get_task_logger(__name__)

class OptimizedTask(Task):
    """Task base otimizada com monitoramento"""
    
    def __call__(self, *args, **kwargs):
        """Wrapper para execução com timing"""
        start_time = time.time()
        
        try:
            result = super().__call__(*args, **kwargs)
            execution_time = time.time() - start_time
            
            logger.info(
                f"Task {self.name} completed in {execution_time:.2f}s",
                extra={
                    "task_name": self.name,
                    "execution_time": execution_time,
                    "status": "success"
                }
            )
            
            return result
            
        except Exception as exc:
            execution_time = time.time() - start_time
            
            logger.error(
                f"Task {self.name} failed after {execution_time:.2f}s: {exc}",
                extra={
                    "task_name": self.name,
                    "execution_time": execution_time,
                    "status": "error",
                    "error": str(exc)
                }
            )
            
            raise
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Hook para retry de tasks"""
        logger.warning(
            f"Task {self.name} retry {self.request.retries + 1}/{self.max_retries}",
            extra={
                "task_name": self.name,
                "task_id": task_id,
                "retry_count": self.request.retries + 1,
                "error": str(exc)
            }
        )

# app/tasks/ai_tasks.py
from celery import current_app as celery_app
from app.tasks.base_task import OptimizedTask
from app.shared.infrastructure.ai.services import AIService
from app.domains.tenders.services import TenderService
from app.core.database import get_db

@celery_app.task(
    base=OptimizedTask,
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,)
)
async def process_tender_document(self, tender_id: str, file_path: str):
    """Processar documento de edital com IA"""
    
    async for db in get_db():
        try:
            # Services
            ai_service = AIService()
            tender_service = TenderService(db)
            
            # Atualizar status
            await tender_service.update_status(tender_id, "PROCESSING")
            
            # Processar com IA
            analysis_result = await ai_service.analyze_tender_document(file_path)
            
            # Salvar resultados
            await tender_service.save_analysis_result(tender_id, analysis_result)
            
            # Atualizar status final
            await tender_service.update_status(tender_id, "READY")
            
            return {
                "tender_id": tender_id,
                "status": "completed",
                "analysis_summary": analysis_result.get("summary", "")
            }
            
        except Exception as exc:
            await tender_service.update_status(tender_id, "ERROR")
            raise self.retry(exc=exc)
```

### 7. Sistema de Testes Abrangente

### 7.1. Test Configuration

```python
# tests/conftest.py
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db
from app.core.factory import ServiceFactory
from app.db.base import Base

# Database de teste em memória
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Event loop para testes async"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_engine():
    """Engine de teste"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=True
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    await engine.dispose()

@pytest.fixture
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Sessão de banco para testes"""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture
def client(test_db: AsyncSession) -> TestClient:
    """Cliente de teste FastAPI"""
    
    def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()

@pytest.fixture
async def service_factory(test_db: AsyncSession) -> ServiceFactory:
    """Factory de serviços para testes"""
    factory = ServiceFactory(test_db)
    
    # Criar dados de teste necessários
    user = await factory.get_auth_service().create_user({
        "email": "test@example.com",
        "password": "testpassword123",
        "first_name": "Test",
        "last_name": "User"
    })
    
    yield factory
    
    # Limpar dados de teste
    await factory.get_auth_service().delete_user(user.id)
```

### 7.2. Test Factories

```python
# tests/factories/user_factory.py
import factory
from factory import fuzzy
from app.domains.auth.models import User
from app.domains.auth.schemas import UserRole, UserStatus

class UserFactory(factory.Factory):
    """Factory para User model"""
    
    class Meta:
        model = User
    
    email = factory.Faker("email")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    role = fuzzy.FuzzyChoice([role.value for role in UserRole])
    status = UserStatus.ACTIVE
    email_verified = True
    password_hash = factory.LazyFunction(
        lambda: "$2b$12$dummy.hash.for.testing"
    )

# tests/factories/tender_factory.py
import factory
from factory import fuzzy
from datetime import datetime, timedelta
from app.domains.tenders.models import Tender
from app.domains.tenders.schemas import TenderStatus

class TenderFactory(factory.Factory):
    """Factory para Tender model"""
    
    class Meta:
        model = Tender
    
    title = factory.Faker("sentence", nb_words=4)
    description = factory.Faker("text", max_nb_chars=500)
    status = TenderStatus.PUBLISHED
    opening_date = factory.LazyFunction(
        lambda: datetime.utcnow() + timedelta(days=30)
    )
    closing_date = factory.LazyFunction(
        lambda: datetime.utcnow() + timedelta(days=60)
    )
    estimated_value = fuzzy.FuzzyDecimal(10000, 1000000, 2)
```

### 7.3. Integration Tests

```python
# tests/integration/test_tender_workflow.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories.user_factory import UserFactory
from tests.factories.tender_factory import TenderFactory
from app.domains.auth.services import AuthService

class TestTenderWorkflow:
    """Testes de integração para workflow de editais"""
    
    @pytest.mark.asyncio
    async def test_complete_tender_workflow(
        self, 
        client: TestClient, 
        test_db: AsyncSession
    ):
        """Teste completo do workflow de editais"""
        
        # 1. Criar usuário e fazer login
        user = UserFactory.build()
        auth_service = AuthService(test_db)
        
        created_user = await auth_service.create_user({
            "email": user.email,
            "password": "testpassword123",
            "first_name": user.first_name,
            "last_name": user.last_name
        })
        
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": user.email,
                "password": "testpassword123"
            }
        )
        assert login_response.status_code == 200
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Criar edital
        tender_data = {
            "title": "Teste de Edital",
            "description": "Descrição do edital de teste",
            "estimated_value": 50000.00,
            "opening_date": "2024-12-01T10:00:00",
            "closing_date": "2024-12-31T17:00:00"
        }
        
        create_response = client.post(
            "/api/v1/tenders/",
            json=tender_data,
            headers=headers
        )
        assert create_response.status_code == 201
        
        tender = create_response.json()
        tender_id = tender["id"]
        
        # 3. Listar editais
        list_response = client.get(
            "/api/v1/tenders/",
            headers=headers
        )
        assert list_response.status_code == 200
        assert len(list_response.json()) >= 1
        
        # 4. Buscar edital específico
        get_response = client.get(
            f"/api/v1/tenders/{tender_id}",
            headers=headers
        )
        assert get_response.status_code == 200
        assert get_response.json()["id"] == tender_id
        
        # 5. Atualizar edital
        update_data = {"title": "Edital Atualizado"}
        update_response = client.put(
            f"/api/v1/tenders/{tender_id}",
            json=update_data,
            headers=headers
        )
        assert update_response.status_code == 200
        assert update_response.json()["title"] == "Edital Atualizado"
    
    @pytest.mark.asyncio
    async def test_tender_file_upload(
        self, 
        client: TestClient, 
        test_db: AsyncSession
    ):
        """Teste de upload de arquivo de edital"""
        
        # Preparar autenticação (similar ao teste anterior)
        # ...
        
        # Upload de arquivo simulado
        files = {"file": ("test.pdf", b"fake pdf content", "application/pdf")}
        
        upload_response = client.post(
            f"/api/v1/tenders/{tender_id}/upload",
            files=files,
            headers=headers
        )
        
        assert upload_response.status_code == 202  # Aceito para processamento
        task_id = upload_response.json()["task_id"]
        
        # Verificar status da task
        status_response = client.get(
            f"/api/v1/tasks/{task_id}/status",
            headers=headers
        )
        assert status_response.status_code == 200
```

### 8. Observabilidade e Monitoramento

### 8.1. Logging Estruturado

```python
# app/core/logging.py
import logging
import sys
from typing import Dict, Any
from pythonjsonlogger import jsonlogger
from app.core.config import settings

class StructuredLogger:
    """Logger estruturado com contexto"""
    
    def __init__(self):
        self.logger = logging.getLogger("app")
        self._setup_logger()
    
    def _setup_logger(self):
        """Configurar logger estruturado"""
        handler = logging.StreamHandler(sys.stdout)
        
        formatter = jsonlogger.JsonFormatter(
            fmt='%(asctime)s %(name)s %(levelname)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    def info(self, message: str, **kwargs):
        """Log info com contexto"""
        self.logger.info(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error com contexto"""
        self.logger.error(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning com contexto"""
        self.logger.warning(message, extra=kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug com contexto"""
        self.logger.debug(message, extra=kwargs)

# Instância global
logger = StructuredLogger()

# Decorator para logging automático
def log_execution(operation: str):
    """Decorator para log automático de execução"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            logger.info(
                f"Starting {operation}",
                operation=operation,
                function=func.__name__
            )
            
            try:
                result = await func(*args, **kwargs)
                logger.info(
                    f"Completed {operation}",
                    operation=operation,
                    function=func.__name__,
                    status="success"
                )
                return result
                
            except Exception as exc:
                logger.error(
                    f"Failed {operation}",
                    operation=operation,
                    function=func.__name__,
                    status="error",
                    error=str(exc)
                )
                raise
                
        return wrapper
    return decorator
```

### 8.2. Metrics e Health Checks

```python
# app/api/v1/endpoints/monitoring.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
import asyncio
import time
from app.core.database import get_db
from app.core.cache import cache_manager
from app.shared.infrastructure.ai.services import AIService

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check básico"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0"
    }

@router.get("/health/detailed")
async def detailed_health_check(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Health check detalhado"""
    
    checks = {}
    overall_status = "healthy"
    
    # Database check
    try:
        await db.execute("SELECT 1")
        checks["database"] = {"status": "healthy", "response_time": 0.001}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}
        overall_status = "unhealthy"
    
    # Redis check
    try:
        start_time = time.time()
        await cache_manager.redis.ping()
        response_time = time.time() - start_time
        checks["redis"] = {"status": "healthy", "response_time": response_time}
    except Exception as e:
        checks["redis"] = {"status": "unhealthy", "error": str(e)}
        overall_status = "unhealthy"
    
    # AI service check
    try:
        ai_service = AIService()
        start_time = time.time()
        await ai_service.health_check()
        response_time = time.time() - start_time
        checks["ai_service"] = {"status": "healthy", "response_time": response_time}
    except Exception as e:
        checks["ai_service"] = {"status": "unhealthy", "error": str(e)}
        overall_status = "degraded"  # AI não é crítico
    
    return {
        "status": overall_status,
        "timestamp": time.time(),
        "checks": checks
    }

@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """Métricas da aplicação"""
    # Implementar coleta de métricas
    return {
        "requests_total": 1000,
        "requests_per_second": 10.5,
        "database_connections_active": 15,
        "cache_hit_ratio": 0.85,
        "memory_usage_mb": 256
    }
```

### 8.3. Error Tracking

```python
# app/core/error_tracking.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from app.core.config import settings

def init_sentry():
    """Inicializar Sentry para tracking de erros"""
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[
                FastApiIntegration(auto_enabling_integrations=False),
                SqlalchemyIntegration(),
                CeleryIntegration()
            ],
            traces_sample_rate=0.1,
            environment=settings.ENVIRONMENT
        )

# Custom exception handler
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import traceback

async def global_exception_handler(request: Request, exc: Exception):
    """Handler global para exceções"""
    
    # Log estruturado
    logger.error(
        "Unhandled exception",
        url=str(request.url),
        method=request.method,
        error=str(exc),
        traceback=traceback.format_exc()
    )
    
    # Enviar para Sentry
    sentry_sdk.capture_exception(exc)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred"
        }
    )
```

### 9. Deployment e DevOps

### 9.1. Dockerfile Otimizado

```dockerfile
# docker/Dockerfile
# Multi-stage build para reduzir tamanho da imagem
FROM python:3.11-slim as builder

# Instalar dependências de sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar Poetry
RUN pip install poetry==1.7.1

# Configurar Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/opt/poetry/cache \
    POETRY_HOME="/opt/poetry"

WORKDIR /app

# Copiar arquivos de dependências
COPY pyproject.toml poetry.lock ./

# Instalar dependências
RUN poetry install --only=main --no-root

# Stage final
FROM python:3.11-slim as runtime

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

# Instalar dependências runtime
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Criar usuário não-root
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copiar virtual environment
COPY --from=builder /app/.venv /app/.venv

# Copiar aplicação
COPY --chown=appuser:appuser ./app ./app
COPY --chown=appuser:appuser ./alembic ./alembic
COPY --chown=appuser:appuser ./alembic.ini ./
COPY --chown=appuser:appuser ./docker/entrypoint.sh ./entrypoint.sh

# Tornar entrypoint executável
RUN chmod +x ./entrypoint.sh

# Criar diretórios necessários
RUN mkdir -p /app/uploads && chown appuser:appuser /app/uploads

# Usar usuário não-root
USER appuser

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
```

### 9.2. Docker Compose para Produção

```yaml
# docker/docker-compose.prod.yml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: docker/Dockerfile
    command: gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app -b 0.0.0.0:8000
    volumes:
      - uploads_data:/app/uploads
    env_file:
      - .env.prod
    depends_on:
      db_postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/monitoring/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.backend.rule=Host(`api.example.com`)"
      - "traefik.http.services.backend.loadbalancer.server.port=8000"

  celery_worker:
    build:
      context: .
      dockerfile: docker/Dockerfile
    command: celery -A app.tasks.celery_app worker -l info --concurrency=4
    volumes:
      - uploads_data:/app/uploads
    env_file:
      - .env.prod
    depends_on:
      - redis
      - db_postgres
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G

  celery_beat:
    build:
      context: .
      dockerfile: docker/Dockerfile
    command: celery -A app.tasks.celery_app beat -l info
    volumes:
      - uploads_data:/app/uploads
    env_file:
      - .env.prod
    depends_on:
      - redis
      - db_postgres
    deploy:
      replicas: 1

  db_postgres:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - backend
    deploy:
      resources:
        limits:
          memory: 256M
        reservations:
          memory: 128M

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}

volumes:
  postgres_data:
  uploads_data:
  prometheus_data:
  grafana_data:
```

### 10. Estratégias de Segurança Avançadas

### 10.1. Rate Limiting Inteligente

```python
# app/api/middleware.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import aioredis
from app.core.config import settings

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

class IntelligentRateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting inteligente baseado em usuário e endpoint"""
    
    def __init__(self, app, redis_client: aioredis.Redis):
        super().__init__(app)
        self.redis = redis_client
        self.default_rate = "100/hour"
        self.endpoint_rates = {
            "/api/v1/auth/login": "5/minute",
            "/api/v1/tenders/upload": "10/hour",
            "/api/v1/ai/analyze": "20/hour"
        }
    
    async def dispatch(self, request: Request, call_next):
        """Aplicar rate limiting baseado no endpoint"""
        
        client_id = self._get_client_id(request)
        endpoint = request.url.path
        
        # Obter rate específico do endpoint
        rate = self.endpoint_rates.get(endpoint, self.default_rate)
        
        # Verificar rate limit
        if await self._is_rate_limited(client_id, endpoint, rate):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded"
            )
        
        response = await call_next(request)
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Obter ID do cliente (IP ou user_id se autenticado)"""
        # Priorizar user_id se disponível
        if hasattr(request.state, "user_id"):
            return f"user:{request.state.user_id}"
        
        # Fallback para IP
        return f"ip:{get_remote_address(request)}"
    
    async def _is_rate_limited(
        self, 
        client_id: str, 
        endpoint: str, 
        rate: str
    ) -> bool:
        """Verificar se cliente excedeu rate limit"""
        
        # Parse rate (ex: "100/hour" -> 100, 3600)
        count, period = self._parse_rate(rate)
        
        # Chave Redis
        key = f"rate_limit:{client_id}:{endpoint}"
        
        # Implementar sliding window
        current_time = int(time.time())
        window_start = current_time - period
        
        # Contar requests na janela
        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, {str(current_time): current_time})
        pipe.expire(key, period)
        
        results = await pipe.execute()
        request_count = results[1]
        
        return request_count >= count
    
    def _parse_rate(self, rate: str) -> tuple[int, int]:
        """Parse rate string para count e period em segundos"""
        count_str, period_str = rate.split("/")
        count = int(count_str)
        
        period_map = {
            "second": 1,
            "minute": 60,
            "hour": 3600,
            "day": 86400
        }
        
        period = period_map.get(period_str, 3600)
        return count, period
```

### 10.2. Input Validation e Sanitization

```python
# app/shared/common/validators.py
from typing import Any, Dict, List
from pydantic import validator, Field
import re
import bleach
from email_validator import validate_email, EmailNotValidError

class SecurityValidators:
    """Validadores de segurança"""
    
    @staticmethod
    def validate_email_address(email: str) -> str:
        """Validar formato de email"""
        try:
            valid_email = validate_email(email)
            return valid_email.email
        except EmailNotValidError:
            raise ValueError("Invalid email format")
    
    @staticmethod
    def sanitize_html(html_content: str) -> str:
        """Sanitizar conteúdo HTML"""
        allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li']
        allowed_attributes = {}
        
        return bleach.clean(
            html_content,
            tags=allowed_tags,
            attributes=allowed_attributes,
            strip=True
        )
    
    @staticmethod
    def validate_password_strength(password: str) -> str:
        """Validar força da senha"""
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        
        if not re.search(r"[A-Z]", password):
            raise ValueError("Password must contain uppercase letter")
        
        if not re.search(r"[a-z]", password):
            raise ValueError("Password must contain lowercase letter")
        
        if not re.search(r"\d", password):
            raise ValueError("Password must contain number")
        
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            raise ValueError("Password must contain special character")
        
        return password
    
    @staticmethod
    def validate_file_type(filename: str, allowed_types: List[str]) -> bool:
        """Validar tipo de arquivo"""
        file_extension = filename.lower().split('.')[-1]
        return f".{file_extension}" in allowed_types
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitizar nome de arquivo"""
        # Remover caracteres perigosos
        safe_chars = re.sub(r'[^\w\s.-]', '', filename)
        
        # Limitar tamanho
        if len(safe_chars) > 255:
            safe_chars = safe_chars[:255]
        
        return safe_chars.strip()
```

### 11. Pontos Críticos e Recomendações Finais

### 11.1. Performance Crítica

**Database:**
- Usar connection pooling otimizado
- Implementar índices apropriados
- Monitorar queries lentas
- Considerar read replicas para relatórios

**Cache:**
- Cache multi-nível (aplicação, Redis, CDN)
- Invalidação inteligente de cache
- Cache warming para dados críticos

**AI Processing:**
- Processamento assíncrono obrigatório
- Queue prioritária para tasks urgentes
- Timeout configurável por tipo de documento
- Fallback para providers alternativos

### 11.2. Segurança Crítica

**Autenticação:**
- JWT com expiração curta
- Refresh tokens rotativos
- Multi-factor authentication opcional
- Session management rigoroso

**Autorização:**
- RBAC granular
- Isolamento por empresa
- Audit trail completo
- Principle of least privilege

**Data Protection:**
- Encryption at rest e in transit
- PII masking em logs
- Backup criptografado
- GDPR compliance

### 11.3. Escalabilidade

**Horizontal Scaling:**
- Stateless application design
- Load balancer com health checks
- Database sharding consideração futura
- Microservices extraction path

**Vertical Scaling:**
- Resource monitoring
- Auto-scaling triggers
- Performance profiling
- Capacity planning

### 11.4. Manutenibilidade

**Code Quality:**
- Type hints obrigatórios
- Testes com 80%+ cobertura
- Code review process
- Automated quality gates

**Documentation:**
- API documentation automática
- Architecture decision records
- Deployment runbooks
- Troubleshooting guides

**Monitoring:**
- Application metrics
- Business metrics
- Error tracking
- Performance monitoring

### 12. Patterns Avançados e Implementações Completas

### 12.1. CQRS (Command Query Responsibility Segregation)

```python
# app/shared/common/cqrs.py
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Any
from pydantic import BaseModel

TCommand = TypeVar('TCommand', bound=BaseModel)
TQuery = TypeVar('TQuery', bound=BaseModel)
TResult = TypeVar('TResult')

class Command(BaseModel):
    """Base para comandos CQRS"""
    pass

class Query(BaseModel):
    """Base para queries CQRS"""
    pass

class CommandHandler(ABC, Generic[TCommand, TResult]):
    """Handler base para comandos"""
    
    @abstractmethod
    async def handle(self, command: TCommand) -> TResult:
        pass

class QueryHandler(ABC, Generic[TQuery, TResult]):
    """Handler base para queries"""
    
    @abstractmethod
    async def handle(self, query: TQuery) -> TResult:
        pass

class Mediator:
    """Mediator para CQRS pattern"""
    
    def __init__(self):
        self._command_handlers = {}
        self._query_handlers = {}
    
    def register_command_handler(self, command_type: type, handler: CommandHandler):
        self._command_handlers[command_type] = handler
    
    def register_query_handler(self, query_type: type, handler: QueryHandler):
        self._query_handlers[query_type] = handler
    
    async def send_command(self, command: Command) -> Any:
        handler = self._command_handlers.get(type(command))
        if not handler:
            raise ValueError(f"No handler registered for {type(command)}")
        return await handler.handle(command)
    
    async def send_query(self, query: Query) -> Any:
        handler = self._query_handlers.get(type(query))
        if not handler:
            raise ValueError(f"No handler registered for {type(query)}")
        return await handler.handle(query)

# Exemplo de uso - Tenders
class CreateTenderCommand(Command):
    title: str
    description: str
    estimated_value: float
    company_id: str

class GetTendersByCompanyQuery(Query):
    company_id: str
    skip: int = 0
    limit: int = 100

class CreateTenderCommandHandler(CommandHandler[CreateTenderCommand, dict]):
    def __init__(self, tender_service):
        self.tender_service = tender_service
    
    async def handle(self, command: CreateTenderCommand) -> dict:
        return await self.tender_service.create_tender(command.dict())
```

### 12.2. Event Sourcing para Auditoria

```python
# app/shared/common/events.py
from datetime import datetime
from typing import Dict, Any, List
from uuid import UUID, uuid4
from pydantic import BaseModel
from sqlalchemy import Column, String, DateTime, JSON, Integer
from app.shared.common.base_models import BaseDBModel

class DomainEvent(BaseModel):
    """Evento de domínio base"""
    event_id: UUID = uuid4()
    aggregate_id: UUID
    event_type: str
    event_data: Dict[str, Any]
    timestamp: datetime = datetime.utcnow()
    version: int = 1
    user_id: Optional[UUID] = None

class EventStore(BaseDBModel):
    """Store de eventos para auditoria"""
    __tablename__ = "event_store"
    
    event_id = Column(String, primary_key=True)
    aggregate_id = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False)
    event_data = Column(JSON, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    version = Column(Integer, nullable=False)
    user_id = Column(String, nullable=True)

class EventSourcingRepository:
    """Repository para Event Sourcing"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    async def save_event(self, event: DomainEvent):
        """Salvar evento no store"""
        event_record = EventStore(
            event_id=str(event.event_id),
            aggregate_id=str(event.aggregate_id),
            event_type=event.event_type,
            event_data=event.event_data,
            timestamp=event.timestamp,
            version=event.version,
            user_id=str(event.user_id) if event.user_id else None
        )
        
        self.db.add(event_record)
        await self.db.commit()
    
    async def get_events_for_aggregate(
        self, 
        aggregate_id: UUID, 
        from_version: int = 0
    ) -> List[DomainEvent]:
        """Obter eventos para um aggregate"""
        stmt = select(EventStore).where(
            EventStore.aggregate_id == str(aggregate_id),
            EventStore.version > from_version
        ).order_by(EventStore.version)
        
        result = await self.db.execute(stmt)
        events = result.scalars().all()
        
        return [
            DomainEvent(
                event_id=UUID(e.event_id),
                aggregate_id=UUID(e.aggregate_id),
                event_type=e.event_type,
                event_data=e.event_data,
                timestamp=e.timestamp,
                version=e.version,
                user_id=UUID(e.user_id) if e.user_id else None
            )
            for e in events
        ]
```

### 12.3. Advanced Caching Strategies

```python
# app/core/cache_strategies.py
from typing import Optional, Dict, Any, List, Callable
from functools import wraps
import json
import hashlib
from datetime import timedelta
from app.core.cache import cache_manager
from app.core.logging import logger

class CacheStrategy:
    """Estratégias avançadas de cache"""
    
    @staticmethod
    def cache_aside(
        key_prefix: str, 
        ttl: int = 3600,
        serialize_args: bool = True
    ):
        """Cache-aside pattern"""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Gerar chave de cache
                if serialize_args:
                    key_data = f"{args}_{kwargs}"
                    key_hash = hashlib.md5(key_data.encode()).hexdigest()
                    cache_key = f"{key_prefix}:{func.__name__}:{key_hash}"
                else:
                    cache_key = f"{key_prefix}:{func.__name__}"
                
                # Tentar obter do cache
                cached_result = await cache_manager.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for {cache_key}")
                    return cached_result
                
                # Executar função e cachear
                result = await func(*args, **kwargs)
                await cache_manager.set(cache_key, result, ttl)
                logger.debug(f"Cache miss for {cache_key}, result cached")
                
                return result
            return wrapper
        return decorator
    
    @staticmethod
    def write_through(key_prefix: str, ttl: int = 3600):
        """Write-through pattern"""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Executar função (write)
                result = await func(*args, **kwargs)
                
                # Cachear resultado imediatamente
                if hasattr(result, 'id'):
                    cache_key = f"{key_prefix}:{result.id}"
                    await cache_manager.set(cache_key, result, ttl)
                
                return result
            return wrapper
        return decorator
    
    @staticmethod
    def write_behind(key_prefix: str, batch_size: int = 100):
        """Write-behind pattern com batching"""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Adicionar à queue de write-behind
                await cache_manager.redis.lpush(
                    f"write_behind:{key_prefix}",
                    json.dumps({"func": func.__name__, "args": args, "kwargs": kwargs})
                )
                
                # Processar batch se necessário
                queue_size = await cache_manager.redis.llen(f"write_behind:{key_prefix}")
                if queue_size >= batch_size:
                    await _process_write_behind_batch(key_prefix, batch_size)
                
                return {"status": "queued", "queue_size": queue_size}
            return wrapper
        return decorator

async def _process_write_behind_batch(key_prefix: str, batch_size: int):
    """Processar batch de operações write-behind"""
    batch = await cache_manager.redis.lrange(
        f"write_behind:{key_prefix}", 0, batch_size - 1
    )
    
    for item in batch:
        try:
            operation = json.loads(item)
            # Executar operação de write
            logger.info(f"Processing write-behind operation: {operation}")
        except Exception as e:
            logger.error(f"Error processing write-behind operation: {e}")
    
    # Remover items processados
    await cache_manager.redis.ltrim(f"write_behind:{key_prefix}", batch_size, -1)
```

### 12.4. WebSocket Manager Avançado

```python
# app/websockets/connection_manager.py
from typing import Dict, List, Set, Optional, Any
import json
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
from uuid import UUID, uuid4
from app.core.logging import logger
from app.core.cache import cache_manager

class ConnectionManager:
    """Gerenciador avançado de conexões WebSocket"""
    
    def __init__(self):
        # Conexões ativas por usuário
        self.user_connections: Dict[str, Set[WebSocket]] = {}
        # Salas de chat/colaboração
        self.rooms: Dict[str, Set[str]] = {}
        # Metadados de conexão
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
        # Lock para operações thread-safe
        self._lock = asyncio.Lock()
    
    async def connect(
        self, 
        websocket: WebSocket, 
        user_id: str, 
        room_id: Optional[str] = None
    ):
        """Conectar usuário"""
        await websocket.accept()
        
        async with self._lock:
            # Adicionar à lista de conexões do usuário
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(websocket)
            
            # Adicionar à sala se especificada
            if room_id:
                if room_id not in self.rooms:
                    self.rooms[room_id] = set()
                self.rooms[room_id].add(user_id)
            
            # Metadados da conexão
            self.connection_metadata[websocket] = {
                "user_id": user_id,
                "room_id": room_id,
                "connected_at": datetime.utcnow(),
                "last_activity": datetime.utcnow()
            }
        
        # Notificar outros usuários na sala
        if room_id:
            await self.broadcast_to_room(
                room_id,
                {
                    "type": "user_joined",
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                },
                exclude_user=user_id
            )
        
        logger.info(f"User {user_id} connected to room {room_id}")
    
    async def disconnect(self, websocket: WebSocket):
        """Desconectar usuário"""
        async with self._lock:
            metadata = self.connection_metadata.get(websocket)
            if not metadata:
                return
            
            user_id = metadata["user_id"]
            room_id = metadata["room_id"]
            
            # Remover da lista de conexões
            if user_id in self.user_connections:
                self.user_connections[user_id].discard(websocket)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            
            # Remover da sala
            if room_id and room_id in self.rooms:
                self.rooms[room_id].discard(user_id)
                if not self.rooms[room_id]:
                    del self.rooms[room_id]
            
            # Remover metadados
            del self.connection_metadata[websocket]
        
        # Notificar outros usuários
        if room_id:
            await self.broadcast_to_room(
                room_id,
                {
                    "type": "user_left",
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        logger.info(f"User {user_id} disconnected from room {room_id}")
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Enviar mensagem para usuário específico"""
        if user_id not in self.user_connections:
            return False
        
        message_json = json.dumps(message, default=str)
        disconnected_sockets = set()
        
        for websocket in self.user_connections[user_id]:
            try:
                await websocket.send_text(message_json)
                # Atualizar última atividade
                if websocket in self.connection_metadata:
                    self.connection_metadata[websocket]["last_activity"] = datetime.utcnow()
            except WebSocketDisconnect:
                disconnected_sockets.add(websocket)
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                disconnected_sockets.add(websocket)
        
        # Limpar conexões mortas
        for socket in disconnected_sockets:
            await self.disconnect(socket)
        
        return len(self.user_connections.get(user_id, [])) > 0
    
    async def broadcast_to_room(
        self, 
        room_id: str, 
        message: Dict[str, Any],
        exclude_user: Optional[str] = None
    ):
        """Broadcast para todos os usuários da sala"""
        if room_id not in self.rooms:
            return
        
        tasks = []
        for user_id in self.rooms[room_id]:
            if exclude_user and user_id == exclude_user:
                continue
            tasks.append(self.send_to_user(user_id, message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def get_room_users(self, room_id: str) -> List[str]:
        """Obter usuários conectados em uma sala"""
        return list(self.rooms.get(room_id, []))
    
    async def get_user_rooms(self, user_id: str) -> List[str]:
        """Obter salas do usuário"""
        rooms = []
        for room_id, users in self.rooms.items():
            if user_id in users:
                rooms.append(room_id)
        return rooms
    
    async def heartbeat_check(self):
        """Verificar conexões inativas"""
        now = datetime.utcnow()
        inactive_sockets = []
        
        for websocket, metadata in self.connection_metadata.items():
            last_activity = metadata["last_activity"]
            if (now - last_activity).total_seconds() > 300:  # 5 minutos
                inactive_sockets.append(websocket)
        
        for socket in inactive_sockets:
            await self.disconnect(socket)
        
        logger.info(f"Cleaned up {len(inactive_sockets)} inactive connections")

# Instância global
connection_manager = ConnectionManager()

# Task periódica para limpeza
async def periodic_cleanup():
    """Task periódica para limpeza de conexões"""
    while True:
        await asyncio.sleep(60)  # A cada minuto
        await connection_manager.heartbeat_check()
```

### 12.5. Task System Robusto

```python
# app/tasks/robust_tasks.py
from celery import Task
from celery.exceptions import Retry, WorkerLostError
from typing import Dict, Any, Optional, Callable
import asyncio
import time
import tempfile
import os
from contextlib import asynccontextmanager
from app.core.logging import logger
from app.core.database import get_db
from app.shared.infrastructure.ai.services import AIService

class RobustTask(Task):
    """Task robusta com recovery e cleanup automático"""
    
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3, 'countdown': 60}
    retry_backoff = True
    retry_backoff_max = 700
    retry_jitter = False
    
    def __init__(self):
        self.ai_service = AIService()
        self._temp_files: List[str] = []
    
    def on_success(self, retval, task_id, args, kwargs):
        """Callback de sucesso"""
        self._cleanup_temp_files()
        logger.info(
            f"Task {self.name} completed successfully",
            extra={
                "task_id": task_id,
                "result": retval,
                "execution_time": getattr(self, '_execution_time', 0)
            }
        )
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Callback de falha"""
        self._cleanup_temp_files()
        logger.error(
            f"Task {self.name} failed",
            extra={
                "task_id": task_id,
                "error": str(exc),
                "traceback": str(einfo),
                "args": args,
                "kwargs": kwargs
            }
        )
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Callback de retry"""
        logger.warning(
            f"Task {self.name} retrying",
            extra={
                "task_id": task_id,
                "retry_count": self.request.retries,
                "error": str(exc)
            }
        )
    
    def _cleanup_temp_files(self):
        """Limpar arquivos temporários"""
        for file_path in self._temp_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f"Cleaned up temp file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file {file_path}: {e}")
        self._temp_files.clear()
    
    @asynccontextmanager
    async def temp_file(self, suffix: str = ".tmp"):
        """Context manager para arquivos temporários"""
        fd, path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        self._temp_files.append(path)
        
        try:
            yield path
        finally:
            # Cleanup será feito no callback
            pass

@celery_app.task(base=RobustTask, bind=True)
async def process_document_with_ai(
    self, 
    document_id: str, 
    file_path: str, 
    analysis_type: str = "comprehensive"
):
    """Processar documento com IA de forma robusta"""
    
    start_time = time.time()
    
    try:
        async for db in get_db():
            # 1. Verificar se arquivo existe
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Document file not found: {file_path}")
            
            # 2. Atualizar status do documento
            from app.domains.tenders.services import TenderService
            tender_service = TenderService(db)
            
            await tender_service.update_document_status(
                document_id, 
                "PROCESSING",
                {"started_at": time.time(), "analysis_type": analysis_type}
            )
            
            # 3. Processar com IA
            async with self.temp_file(".processed") as temp_output:
                analysis_result = await self.ai_service.analyze_document(
                    file_path=file_path,
                    analysis_type=analysis_type,
                    output_path=temp_output
                )
                
                # 4. Validar resultado
                if not analysis_result or "error" in analysis_result:
                    raise ValueError(f"AI analysis failed: {analysis_result}")
                
                # 5. Salvar resultado no banco
                await tender_service.save_analysis_result(
                    document_id, 
                    analysis_result
                )
                
                # 6. Atualizar status final
                await tender_service.update_document_status(
                    document_id,
                    "COMPLETED",
                    {
                        "completed_at": time.time(),
                        "analysis_summary": analysis_result.get("summary", ""),
                        "confidence_score": analysis_result.get("confidence", 0.0)
                    }
                )
            
            execution_time = time.time() - start_time
            self._execution_time = execution_time
            
            return {
                "document_id": document_id,
                "status": "completed",
                "execution_time": execution_time,
                "analysis_summary": analysis_result.get("summary", ""),
                "confidence_score": analysis_result.get("confidence", 0.0)
            }
    
    except FileNotFoundError as e:
        # Erro irrecuperável - não fazer retry
        await tender_service.update_document_status(
            document_id, 
            "ERROR", 
            {"error": str(e), "error_type": "FILE_NOT_FOUND"}
        )
        raise e
    
    except Exception as e:
        # Atualizar status de erro
        await tender_service.update_document_status(
            document_id,
            "ERROR",
            {"error": str(e), "retry_count": self.request.retries}
        )
        
        # Re-raise para trigger retry
        raise self.retry(exc=e)

@celery_app.task(base=RobustTask, bind=True)
async def batch_process_tenders(self, tender_ids: List[str]):
    """Processar múltiplos editais em batch"""
    
    results = []
    failed_tenders = []
    
    for tender_id in tender_ids:
        try:
            # Processar cada edital
            result = await process_single_tender.delay(tender_id)
            results.append({"tender_id": tender_id, "status": "success", "result": result})
            
        except Exception as e:
            failed_tenders.append({"tender_id": tender_id, "error": str(e)})
            logger.error(f"Failed to process tender {tender_id}: {e}")
    
    # Retry automático para editais que falharam
    if failed_tenders and self.request.retries < self.max_retries:
        retry_ids = [item["tender_id"] for item in failed_tenders]
        raise self.retry(countdown=60, args=[retry_ids])
    
    return {
        "processed": len(results),
        "failed": len(failed_tenders),
        "results": results,
        "errors": failed_tenders
    }
```

### 12.6. API Versioning Strategy

```python
# app/api/versioning.py
from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any, Callable
import importlib
from packaging import version

class APIVersionManager:
    """Gerenciador de versionamento de API"""
    
    def __init__(self):
        self.versions: Dict[str, APIRouter] = {}
        self.version_mapping: Dict[str, str] = {
            "v1": "1.0.0",
            "v2": "2.0.0"
        }
    
    def register_version(self, version_name: str, router: APIRouter):
        """Registrar versão da API"""
        self.versions[version_name] = router
    
    def get_router_for_version(self, version_name: str) -> APIRouter:
        """Obter router para versão específica"""
        if version_name not in self.versions:
            raise HTTPException(
                status_code=400,
                detail=f"API version {version_name} not supported"
            )
        return self.versions[version_name]
    
    def get_latest_version(self) -> str:
        """Obter versão mais recente"""
        if not self.versions:
            return "v1"
        
        latest = max(
            self.version_mapping.keys(),
            key=lambda v: version.parse(self.version_mapping[v])
        )
        return latest

# Decorator para deprecação
def deprecated(since_version: str, remove_in_version: str):
    """Marcar endpoint como deprecated"""
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            # Adicionar header de deprecação
            response = await func(*args, **kwargs)
            if hasattr(response, "headers"):
                response.headers["X-API-Deprecated"] = "true"
                response.headers["X-API-Deprecated-Since"] = since_version
                response.headers["X-API-Remove-In"] = remove_in_version
            return response
        
        wrapper.__deprecated__ = True
        wrapper.__deprecated_since__ = since_version
        wrapper.__remove_in__ = remove_in_version
        
        return wrapper
    return decorator

# app/api/v1/endpoints/tenders.py
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.versioning import deprecated

router = APIRouter()

@router.get("/tenders/", deprecated=True)
@deprecated(since_version="1.1.0", remove_in_version="2.0.0")
async def list_tenders_v1():
    """Listar editais (DEPRECATED - use /tenders/list)"""
    # Implementação...
    pass

@router.get("/tenders/list")
async def list_tenders_v1_new():
    """Listar editais (nova versão)"""
    # Implementação melhorada...
    pass

# app/api/v2/endpoints/tenders.py
router_v2 = APIRouter()

@router_v2.get("/tenders/")
async def list_tenders_v2():
    """Listar editais com paginação melhorada"""
    # Nova implementação...
    pass
```

### 12.7. Advanced Error Handling

```python
# app/core/errors.py
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, Type
import traceback
from enum import Enum
from pydantic import BaseModel

class ErrorCode(str, Enum):
    """Códigos de erro padronizados"""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"
    BUSINESS_RULE_VIOLATION = "BUSINESS_RULE_VIOLATION"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    SYSTEM_ERROR = "SYSTEM_ERROR"

class ErrorDetail(BaseModel):
    """Detalhes do erro"""
    code: ErrorCode
    message: str
    field: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class APIError(BaseModel):
    """Estrutura padronizada de erro da API"""
    error: ErrorCode
    message: str
    details: Optional[List[ErrorDetail]] = None
    request_id: Optional[str] = None
    timestamp: str
    path: Optional[str] = None

class BusinessRuleException(Exception):
    """Exceção para violações de regras de negócio"""
    
    def __init__(
        self, 
        message: str, 
        code: ErrorCode = ErrorCode.BUSINESS_RULE_VIOLATION,
        details: Optional[List[ErrorDetail]] = None
    ):
        self.message = message
        self.code = code
        self.details = details or []
        super().__init__(message)

class ExternalServiceException(Exception):
    """Exceção para erros de serviços externos"""
    
    def __init__(
        self, 
        service_name: str, 
        message: str, 
        status_code: Optional[int] = None
    ):
        self.service_name = service_name
        self.message = message
        self.status_code = status_code
        super().__init__(f"{service_name}: {message}")

async def business_rule_exception_handler(
    request: Request, 
    exc: BusinessRuleException
) -> JSONResponse:
    """Handler para exceções de regras de negócio"""
    
    error_response = APIError(
        error=exc.code,
        message=exc.message,
        details=exc.details,
        request_id=getattr(request.state, "request_id", None),
        timestamp=datetime.utcnow().isoformat(),
        path=str(request.url.path)
    )
    
    return JSONResponse(
        status_code=422,
        content=error_response.dict()
    )

async def external_service_exception_handler(
    request: Request, 
    exc: ExternalServiceException
) -> JSONResponse:
    """Handler para exceções de serviços externos"""
    
    error_response = APIError(
        error=ErrorCode.EXTERNAL_SERVICE_ERROR,
        message=f"External service error: {exc.message}",
        details=[
            ErrorDetail(
                code=ErrorCode.EXTERNAL_SERVICE_ERROR,
                message=exc.message,
                context={
                    "service": exc.service_name,
                    "status_code": exc.status_code
                }
            )
        ],
        request_id=getattr(request.state, "request_id", None),
        timestamp=datetime.utcnow().isoformat(),
        path=str(request.url.path)
    )
    
    return JSONResponse(
        status_code=503,
        content=error_response.dict()
    )
```

### 12.8. Backup e Recovery Strategy

```python
# scripts/backup_system.py
import asyncio
import asyncpg
import aiofiles
import boto3
import gzip
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
from app.core.config import settings
from app.core.logging import logger

class BackupManager:
    """Gerenciador de backup e recovery"""
    
    def __init__(self):
        self.s3_client = boto3.client('s3') if settings.AWS_ACCESS_KEY_ID else None
        self.backup_retention_days = 30
    
    async def create_database_backup(self) -> str:
        """Criar backup do banco PostgreSQL"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"db_backup_{timestamp}.sql.gz"
        backup_path = f"/tmp/{backup_filename}"
        
        try:
            # Conectar ao banco
            conn = await asyncpg.connect(settings.SQLALCHEMY_DATABASE_URI.replace("+asyncpg", ""))
            
            # Dump do schema e dados
            dump_command = f"""
            pg_dump {settings.SQLALCHEMY_DATABASE_URI.replace("+asyncpg", "")} \
            --no-password --verbose --clean --no-acl --no-owner \
            | gzip > {backup_path}
            """
            
            process = await asyncio.create_subprocess_shell(
                dump_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"Database backup failed: {stderr.decode()}")
            
            # Upload para S3 se configurado
            if self.s3_client:
                await self._upload_to_s3(backup_path, backup_filename)
            
            logger.info(f"Database backup created: {backup_filename}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            raise
        finally:
            await conn.close()
    
    async def create_files_backup(self) -> str:
        """Criar backup dos arquivos uploaded"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"files_backup_{timestamp}.tar.gz"
        backup_path = f"/tmp/{backup_filename}"
        
        try:
            # Criar arquivo tar comprimido
            tar_command = f"""
            tar -czf {backup_path} -C {settings.UPLOAD_FOLDER} .
            """
            
            process = await asyncio.create_subprocess_shell(
                tar_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            
            if process.returncode != 0:
                raise Exception("Files backup failed")
            
            # Upload para S3 se configurado
            if self.s3_client:
                await self._upload_to_s3(backup_path, backup_filename)
            
            logger.info(f"Files backup created: {backup_filename}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Files backup failed: {e}")
            raise
    
    async def _upload_to_s3(self, file_path: str, s3_key: str):
        """Upload de backup para S3"""
        try:
            self.s3_client.upload_file(
                file_path, 
                settings.S3_BACKUP_BUCKET, 
                f"backups/{s3_key}"
            )
            logger.info(f"Backup uploaded to S3: {s3_key}")
        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
            raise
    
    async def cleanup_old_backups(self):
        """Limpar backups antigos"""
        cutoff_date = datetime.utcnow() - timedelta(days=self.backup_retention_days)
        
        if self.s3_client:
            # Listar objetos no S3
            response = self.s3_client.list_objects_v2(
                Bucket=settings.S3_BACKUP_BUCKET,
                Prefix="backups/"
            )
            
            for obj in response.get('Contents', []):
                if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                    self.s3_client.delete_object(
                        Bucket=settings.S3_BACKUP_BUCKET,
                        Key=obj['Key']
                    )
                    logger.info(f"Deleted old backup: {obj['Key']}")
    
    async def restore_database(self, backup_file: str):
        """Restaurar banco de dados"""
        try:
            restore_command = f"""
            gunzip -c {backup_file} | psql {settings.SQLALCHEMY_DATABASE_URI.replace("+asyncpg", "")}
            """
            
            process = await asyncio.create_subprocess_shell(
                restore_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"Database restore failed: {stderr.decode()}")
            
            logger.info("Database restored successfully")
            
        except Exception as e:
            logger.error(f"Database restore failed: {e}")
            raise

# Celery task para backup automático
@celery_app.task(bind=True)
async def automated_backup(self):
    """Task automática de backup"""
    backup_manager = BackupManager()
    
    try:
        # Backup do banco
        db_backup_path = await backup_manager.create_database_backup()
        
        # Backup dos arquivos
        files_backup_path = await backup_manager.create_files_backup()
        
        # Limpeza de backups antigos
        await backup_manager.cleanup_old_backups()
        
        return {
            "status": "success",
            "db_backup": db_backup_path,
            "files_backup": files_backup_path,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Automated backup failed: {e}")
        raise
```

Este plano técnico fornece uma base sólida para construir um sistema escalável, seguro e performático. A implementação deve ser iterativa, priorizando funcionalidades core primeiro e expandindo gradualmente com base no feedback e métricas de uso.

### 13. Roadmap de Implementação

**Fase 1 (MVP - 4 semanas):**
- Setup inicial da arquitetura base
- Sistema de autenticação completo
- CRUD básico de editais e empresas
- Upload e armazenamento de documentos

**Fase 2 (Core Features - 6 semanas):**
- Integração com IA (Ollama/OpenAI)
- Sistema de cotações
- WebSockets para atualizações real-time
- Sistema de notificações

**Fase 3 (Advanced Features - 8 semanas):**
- Kanban e gerenciamento de projetos
- Relatórios avançados
- Integração com calendário
- Sistema de formulários dinâmicos

**Fase 4 (Enterprise Ready - 4 semanas):**
- Monitoramento completo
- Backup automático
- Performance optimization
- Security hardening
- Documentação completa

O sistema está projetado para ser facilmente migrado para microsserviços no futuro, mantendo a arquitetura limpa e bem separada por domínios.
