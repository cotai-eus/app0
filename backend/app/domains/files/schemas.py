"""
Schemas for the files domain.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.domains.files.models import SharePermission, UploadStatus


# Base schemas
class FileAccessLogBase(BaseModel):
    """Base schema for file access logs."""
    model_config = ConfigDict(from_attributes=True)
    
    action: str = Field(..., description="Ação realizada")
    file_path: str = Field(..., description="Caminho do arquivo")
    user_id: Optional[UUID] = Field(default=None, description="ID do usuário")
    ip_address: Optional[str] = Field(default=None, description="Endereço IP")
    user_agent: Optional[str] = Field(default=None, description="User agent")
    file_size: Optional[int] = Field(default=None, description="Tamanho do arquivo")
    success: bool = Field(default=True, description="Se a ação foi bem-sucedida")
    error_message: Optional[str] = Field(default=None, description="Mensagem de erro")
    access_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadados do acesso")


class FileAccessLogCreate(FileAccessLogBase):
    """Schema for creating file access logs."""
    pass


class FileAccessLogResponse(FileAccessLogBase):
    """Schema for file access log responses."""
    id: UUID
    timestamp: datetime
    created_at: datetime


# File Share schemas
class FileShareBase(BaseModel):
    """Base schema for file shares."""
    model_config = ConfigDict(from_attributes=True)
    
    file_path: str = Field(..., description="Caminho do arquivo")
    shared_with_user_id: Optional[UUID] = Field(default=None, description="ID do usuário compartilhado")
    shared_with_email: Optional[str] = Field(default=None, description="Email para compartilhamento")
    permission: SharePermission = Field(..., description="Permissão de compartilhamento")
    expires_at: Optional[datetime] = Field(default=None, description="Data de expiração")
    password_required: bool = Field(default=False, description="Requer senha")
    password_hash: Optional[str] = Field(default=None, description="Hash da senha")
    download_limit: Optional[int] = Field(default=None, description="Limite de downloads")
    download_count: int = Field(default=0, description="Contador de downloads")
    access_token: Optional[str] = Field(default=None, description="Token de acesso")
    share_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadados do compartilhamento")


class FileShareCreate(FileShareBase):
    """Schema for creating file shares."""
    shared_by_user_id: UUID = Field(..., description="ID do usuário que compartilhou")


class FileShareUpdate(BaseModel):
    """Schema for updating file shares."""
    model_config = ConfigDict(from_attributes=True)
    
    permission: Optional[SharePermission] = None
    expires_at: Optional[datetime] = None
    password_required: Optional[bool] = None
    password_hash: Optional[str] = None
    download_limit: Optional[int] = None
    enabled: Optional[bool] = None
    share_metadata: Optional[Dict[str, Any]] = None


class FileShareResponse(FileShareBase):
    """Schema for file share responses."""
    id: UUID
    shared_by_user_id: UUID
    enabled: bool
    created_at: datetime
    updated_at: datetime


# File Quota schemas
class FileQuotaBase(BaseModel):
    """Base schema for file quotas."""
    model_config = ConfigDict(from_attributes=True)
    
    quota_type: str = Field(..., description="Tipo da quota")
    max_storage_bytes: int = Field(..., description="Máximo de armazenamento em bytes")
    used_storage_bytes: int = Field(default=0, description="Armazenamento usado em bytes")
    max_files_count: int = Field(..., description="Máximo número de arquivos")
    used_files_count: int = Field(default=0, description="Número de arquivos usados")
    max_file_size_bytes: int = Field(..., description="Tamanho máximo por arquivo")
    allowed_file_types: Optional[List[str]] = Field(default=None, description="Tipos de arquivo permitidos")
    quota_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadados da quota")


class FileQuotaCreate(FileQuotaBase):
    """Schema for creating file quotas."""
    user_id: Optional[UUID] = Field(default=None, description="ID do usuário")
    company_id: Optional[UUID] = Field(default=None, description="ID da empresa")


class FileQuotaUpdate(BaseModel):
    """Schema for updating file quotas."""
    model_config = ConfigDict(from_attributes=True)
    
    max_storage_bytes: Optional[int] = None
    used_storage_bytes: Optional[int] = None
    max_files_count: Optional[int] = None
    used_files_count: Optional[int] = None
    max_file_size_bytes: Optional[int] = None
    allowed_file_types: Optional[List[str]] = None
    quota_metadata: Optional[Dict[str, Any]] = None


class FileQuotaResponse(FileQuotaBase):
    """Schema for file quota responses."""
    id: UUID
    user_id: Optional[UUID]
    company_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime


# File Version schemas
class FileVersionBase(BaseModel):
    """Base schema for file versions."""
    model_config = ConfigDict(from_attributes=True)
    
    file_path: str = Field(..., description="Caminho do arquivo")
    version_number: int = Field(..., description="Número da versão")
    file_hash: str = Field(..., description="Hash do arquivo")
    file_size: int = Field(..., description="Tamanho do arquivo")
    change_description: Optional[str] = Field(default=None, description="Descrição da mudança")
    is_current: bool = Field(default=False, description="Se é a versão atual")
    storage_path: str = Field(..., description="Caminho de armazenamento")
    version_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadados da versão")


class FileVersionCreate(FileVersionBase):
    """Schema for creating file versions."""
    created_by_user_id: UUID = Field(..., description="ID do usuário que criou")


class FileVersionResponse(FileVersionBase):
    """Schema for file version responses."""
    id: UUID
    created_by_user_id: UUID
    created_at: datetime


# File Upload Session schemas
class FileUploadSessionBase(BaseModel):
    """Base schema for file upload sessions."""
    model_config = ConfigDict(from_attributes=True)
    
    session_token: str = Field(..., description="Token da sessão")
    filename: str = Field(..., description="Nome do arquivo")
    file_size: int = Field(..., description="Tamanho total do arquivo")
    chunk_size: int = Field(..., description="Tamanho do chunk")
    total_chunks: int = Field(..., description="Total de chunks")
    uploaded_chunks: int = Field(default=0, description="Chunks carregados")
    status: UploadStatus = Field(..., description="Status do upload")
    upload_progress: float = Field(default=0.0, description="Progresso do upload")
    expires_at: datetime = Field(..., description="Data de expiração")
    final_file_path: Optional[str] = Field(default=None, description="Caminho final do arquivo")
    upload_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadados do upload")


class FileUploadSessionCreate(FileUploadSessionBase):
    """Schema for creating file upload sessions."""
    user_id: UUID = Field(..., description="ID do usuário")


class FileUploadSessionUpdate(BaseModel):
    """Schema for updating file upload sessions."""
    model_config = ConfigDict(from_attributes=True)
    
    uploaded_chunks: Optional[int] = None
    status: Optional[UploadStatus] = None
    upload_progress: Optional[float] = None
    final_file_path: Optional[str] = None
    upload_metadata: Optional[Dict[str, Any]] = None


class FileUploadSessionResponse(FileUploadSessionBase):
    """Schema for file upload session responses."""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime


# Advanced schemas for file operations
class FileUploadChunkRequest(BaseModel):
    """Schema for uploading file chunks."""
    model_config = ConfigDict(from_attributes=True)
    
    session_token: str = Field(..., description="Token da sessão")
    chunk_number: int = Field(..., description="Número do chunk")
    chunk_data: bytes = Field(..., description="Dados do chunk")
    chunk_hash: str = Field(..., description="Hash do chunk para verificação")


class FileUploadChunkResponse(BaseModel):
    """Schema for file upload chunk response."""
    model_config = ConfigDict(from_attributes=True)
    
    chunk_number: int = Field(..., description="Número do chunk")
    uploaded_successfully: bool = Field(..., description="Se foi carregado com sucesso")
    total_uploaded: int = Field(..., description="Total de chunks carregados")
    upload_progress: float = Field(..., description="Progresso do upload")
    upload_complete: bool = Field(..., description="Se o upload está completo")


class FileDownloadRequest(BaseModel):
    """Schema for file download request."""
    model_config = ConfigDict(from_attributes=True)
    
    file_path: str = Field(..., description="Caminho do arquivo")
    access_token: Optional[str] = Field(default=None, description="Token de acesso")
    password: Optional[str] = Field(default=None, description="Senha se necessária")
    range_start: Optional[int] = Field(default=None, description="Início do range")
    range_end: Optional[int] = Field(default=None, description="Fim do range")


class FileShareLinkRequest(BaseModel):
    """Schema for creating share links."""
    model_config = ConfigDict(from_attributes=True)
    
    file_path: str = Field(..., description="Caminho do arquivo")
    permission: SharePermission = Field(default=SharePermission.READ, description="Permissão")
    expires_in_hours: Optional[int] = Field(default=24, description="Expira em horas")
    password: Optional[str] = Field(default=None, description="Senha opcional")
    download_limit: Optional[int] = Field(default=None, description="Limite de downloads")
    shared_with_emails: Optional[List[str]] = Field(default=None, description="Emails para compartilhar")


class FileShareLinkResponse(BaseModel):
    """Schema for share link response."""
    model_config = ConfigDict(from_attributes=True)
    
    share_id: UUID = Field(..., description="ID do compartilhamento")
    share_url: HttpUrl = Field(..., description="URL de compartilhamento")
    access_token: str = Field(..., description="Token de acesso")
    expires_at: datetime = Field(..., description="Data de expiração")
    permission: SharePermission = Field(..., description="Permissão")


class FileQuotaUsageResponse(BaseModel):
    """Schema for quota usage response."""
    model_config = ConfigDict(from_attributes=True)
    
    quota: FileQuotaResponse = Field(..., description="Informações da quota")
    storage_percentage: float = Field(..., description="Porcentagem de armazenamento usado")
    files_percentage: float = Field(..., description="Porcentagem de arquivos usados")
    near_limit: bool = Field(..., description="Se está próximo do limite")
    can_upload: bool = Field(..., description="Se pode fazer upload")
    remaining_storage_bytes: int = Field(..., description="Armazenamento restante")
    remaining_files_count: int = Field(..., description="Arquivos restantes")


class FileSearchRequest(BaseModel):
    """Schema for file search."""
    model_config = ConfigDict(from_attributes=True)
    
    query: str = Field(..., description="Texto da busca")
    file_types: Optional[List[str]] = Field(default=None, description="Filtro por tipos")
    date_from: Optional[datetime] = Field(default=None, description="Data inicial")
    date_to: Optional[datetime] = Field(default=None, description="Data final")
    size_min: Optional[int] = Field(default=None, description="Tamanho mínimo")
    size_max: Optional[int] = Field(default=None, description="Tamanho máximo")
    user_id: Optional[UUID] = Field(default=None, description="Filtro por usuário")
    company_id: Optional[UUID] = Field(default=None, description="Filtro por empresa")
    limit: int = Field(default=20, ge=1, le=100, description="Limite de resultados")
    offset: int = Field(default=0, ge=0, description="Offset para paginação")


class FileSearchResponse(BaseModel):
    """Schema for file search response."""
    model_config = ConfigDict(from_attributes=True)
    
    files: List[Dict[str, Any]] = Field(..., description="Arquivos encontrados")
    total_count: int = Field(..., description="Total de arquivos")
    query: str = Field(..., description="Query utilizada")
    execution_time_ms: int = Field(..., description="Tempo de execução em ms")
