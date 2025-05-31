"""
Exceções específicas para processamento de IA
"""


class AIException(Exception):
    """Exceção base para erros de IA"""
    pass


class AIProcessingException(AIException):
    """Erro durante processamento da IA"""
    pass


class DocumentProcessingException(AIException):
    """Erro durante processamento de documento"""
    pass


class ModelUnavailableException(AIException):
    """Modelo de IA não disponível"""
    pass


class PromptException(AIException):
    """Erro relacionado a prompts"""
    pass


class CacheException(AIException):
    """Erro no sistema de cache da IA"""
    pass


class RateLimitException(AIException):
    """Rate limit excedido"""
    pass


class ValidationException(AIException):
    """Erro de validação de dados da IA"""
    pass


# Aliases for compatibility with services
AIProcessingError = AIProcessingException
TextExtractionError = DocumentProcessingException
PromptError = PromptException
CacheError = CacheException
MonitoringError = AIException
