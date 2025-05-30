"""
Configuração do MongoDB com Motor
"""

from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings
from app.core.logging import get_logger_with_context

logger = get_logger_with_context(component="mongodb")


class MongoDB:
    """Cliente MongoDB singleton"""
    
    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None


mongodb = MongoDB()


async def connect_to_mongo() -> None:
    """Conecta ao MongoDB"""
    try:
        logger.info("Connecting to MongoDB", url=settings.mongodb_url)
        mongodb.client = AsyncIOMotorClient(settings.mongodb_url)
        mongodb.database = mongodb.client[settings.mongodb_db]
        
        # Testa a conexão
        await mongodb.client.admin.command("ping")
        logger.info("MongoDB connected successfully")
        
    except Exception as exc:
        logger.error("Failed to connect to MongoDB", error=str(exc))
        raise


async def close_mongo_connection() -> None:
    """Fecha a conexão com MongoDB"""
    try:
        if mongodb.client:
            mongodb.client.close()
            logger.info("MongoDB connection closed")
    except Exception as exc:
        logger.error("Error closing MongoDB connection", error=str(exc))


async def get_mongo_db() -> AsyncIOMotorDatabase:
    """Dependency para obter o banco MongoDB"""
    if not mongodb.database:
        await connect_to_mongo()
    return mongodb.database


# Collections helpers
class MongoCollections:
    """Helper para acessar collections do MongoDB"""
    
    @staticmethod
    async def get_collection(collection_name: str):
        """Retorna uma collection específica"""
        db = await get_mongo_db()
        return db[collection_name]
    
    # Collections do Sistema
    @staticmethod
    async def users_cache():
        """Collection de cache de usuários (sessões ativas, preferências)"""
        return await MongoCollections.get_collection("users_cache")
    
    @staticmethod
    async def application_logs():
        """Collection de logs da aplicação"""
        return await MongoCollections.get_collection("application_logs")
    
    @staticmethod
    async def audit_events():
        """Collection de eventos de auditoria"""
        return await MongoCollections.get_collection("audit_events")
    
    # Collections de IA
    @staticmethod
    async def ai_processing_logs():
        """Collection de logs de processamento de IA"""
        return await MongoCollections.get_collection("ai_processing_logs")
    
    @staticmethod
    async def ai_analytics():
        """Collection de analytics de IA"""
        return await MongoCollections.get_collection("ai_analytics")
    
    @staticmethod
    async def ai_model_performance():
        """Collection de performance dos modelos de IA"""
        return await MongoCollections.get_collection("ai_model_performance")
    
    @staticmethod
    async def ai_conversations():
        """Collection de conversas/interações com IA"""
        return await MongoCollections.get_collection("ai_conversations")
    
    # Collections de Notificações
    @staticmethod
    async def notification_events():
        """Collection de eventos de notificação (logs flexíveis)"""
        return await MongoCollections.get_collection("notification_events")
    
    @staticmethod
    async def notification_analytics():
        """Collection de analytics de notificações"""
        return await MongoCollections.get_collection("notification_analytics")
    
    @staticmethod
    async def push_notification_logs():
        """Collection de logs de push notifications"""
        return await MongoCollections.get_collection("push_notification_logs")
    
    # Collections de Analytics
    @staticmethod
    async def user_behavior():
        """Collection de comportamento do usuário"""
        return await MongoCollections.get_collection("user_behavior")
    
    @staticmethod
    async def system_metrics():
        """Collection de métricas do sistema"""
        return await MongoCollections.get_collection("system_metrics")
    
    @staticmethod
    async def api_usage():
        """Collection de uso da API"""
        return await MongoCollections.get_collection("api_usage")
    
    @staticmethod
    async def business_analytics():
        """Collection de analytics de negócio"""
        return await MongoCollections.get_collection("business_analytics")
    
    # Collections de Arquivos
    @staticmethod
    async def file_metadata():
        """Collection de metadados de arquivos"""
        return await MongoCollections.get_collection("file_metadata")
    
    @staticmethod
    async def file_processing_logs():
        """Collection de logs de processamento de arquivos"""
        return await MongoCollections.get_collection("file_processing_logs")
    
    # Collections de Configurações
    @staticmethod
    async def dynamic_configs():
        """Collection de configurações dinâmicas"""
        return await MongoCollections.get_collection("dynamic_configs")
    
    @staticmethod
    async def feature_flags():
        """Collection de feature flags"""
        return await MongoCollections.get_collection("feature_flags")
    
    @staticmethod
    async def ab_test_data():
        """Collection de dados de testes A/B"""
        return await MongoCollections.get_collection("ab_test_data")
    
    # Collections de Integração
    @staticmethod
    async def webhook_logs():
        """Collection de logs de webhooks"""
        return await MongoCollections.get_collection("webhook_logs")
    
    @staticmethod
    async def external_api_logs():
        """Collection de logs de APIs externas"""
        return await MongoCollections.get_collection("external_api_logs")
    
    @staticmethod
    async def integration_events():
        """Collection de eventos de integração"""
        return await MongoCollections.get_collection("integration_events")


# Indexes para performance
async def create_mongodb_indexes():
    """Cria índices no MongoDB para otimizar queries"""
    try:
        # Índices para logs de aplicação
        logs_collection = await MongoCollections.application_logs()
        await logs_collection.create_index([("timestamp", -1), ("level", 1)])
        await logs_collection.create_index([("company_id", 1), ("timestamp", -1)])
        await logs_collection.create_index([("user_id", 1), ("timestamp", -1)])
        
        # Índices para IA
        ai_logs = await MongoCollections.ai_processing_logs()
        await ai_logs.create_index([("company_id", 1), ("timestamp", -1)])
        await ai_logs.create_index([("model_name", 1), ("timestamp", -1)])
        await ai_logs.create_index([("status", 1), ("timestamp", -1)])
        
        # Índices para notificações
        notif_events = await MongoCollections.notification_events()
        await notif_events.create_index([("user_id", 1), ("timestamp", -1)])
        await notif_events.create_index([("company_id", 1), ("timestamp", -1)])
        await notif_events.create_index([("status", 1), ("timestamp", -1)])
        
        # Índices para comportamento do usuário
        behavior = await MongoCollections.user_behavior()
        await behavior.create_index([("user_id", 1), ("timestamp", -1)])
        await behavior.create_index([("event_type", 1), ("timestamp", -1)])
        await behavior.create_index([("session_id", 1)])
        
        # Índices para métricas do sistema
        metrics = await MongoCollections.system_metrics()
        await metrics.create_index([("metric_name", 1), ("timestamp", -1)])
        await metrics.create_index([("service", 1), ("timestamp", -1)])
        
        # Índices TTL para limpeza automática (30 dias para logs)
        await logs_collection.create_index([("timestamp", 1)], expireAfterSeconds=30*24*60*60)
        await ai_logs.create_index([("timestamp", 1)], expireAfterSeconds=90*24*60*60)  # 90 dias para IA
        await notif_events.create_index([("timestamp", 1)], expireAfterSeconds=60*24*60*60)  # 60 dias
        
        logger.info("MongoDB indexes created successfully")
        
    except Exception as exc:
        logger.error("Failed to create MongoDB indexes", error=str(exc))
