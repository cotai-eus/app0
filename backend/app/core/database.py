"""
Configuração do banco de dados PostgreSQL com SQLAlchemy 2.0
"""

from typing import AsyncGenerator

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings
from app.core.logging import get_logger_with_context

logger = get_logger_with_context(component="database")

# Convenção de nomenclatura para constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)


class Base(DeclarativeBase):
    """Base class para todos os modelos"""
    metadata = metadata


# Engine assíncrono
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=20,
    max_overflow=0,
)

# Session maker assíncrono
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency para obter sessão do banco de dados"""
    async with AsyncSessionLocal() as session:
        try:
            logger.debug("Database session created")
            yield session
        except Exception as exc:
            logger.error("Database session error", error=str(exc))
            await session.rollback()
            raise
        finally:
            await session.close()
            logger.debug("Database session closed")


async def init_db() -> None:
    """Inicializa o banco de dados"""
    try:
        async with engine.begin() as conn:
            logger.info("Initializing database")
            # Criar todas as tabelas
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database initialized successfully")
    except Exception as exc:
        logger.error("Failed to initialize database", error=str(exc))
        raise


async def close_db() -> None:
    """Fecha as conexões do banco de dados"""
    try:
        await engine.dispose()
        logger.info("Database connections closed")
    except Exception as exc:
        logger.error("Error closing database connections", error=str(exc))
        raise
