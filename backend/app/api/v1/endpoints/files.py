"""
File Management API endpoints.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import io

from app.api.deps import get_db_session, get_current_user
from app.domains.auth.models import User
from app.domains.files.repository import (
    FileRepository,
    FileAccessLogRepository,
    FileShareRepository,
    FileQuotaRepository,
    FileVersionRepository,
    FileUploadSessionRepository
)
from app.domains.files.schemas import (
    FileResponse,
    FileCreate,
    FileUpdate,
    FileShareResponse,
    FileShareCreate,
    FileVersionResponse,
    FileQuotaResponse,
    FileUploadSessionResponse,
    FileUploadSessionCreate,
    ChunkUploadRequest,
)

router = APIRouter()


@router.post("/upload", response_model=FileResponse)
async def upload_file(
    file: UploadFile = File(...),
    parent_folder_id: Optional[UUID] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    is_public: bool = Form(False),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Upload a file."""
    try:
        file_repo = FileRepository(db)
        quota_repo = FileQuotaRepository(db)
        
        # Check user quota
        file_size = 0
        content = await file.read()
        file_size = len(content)
        
        quota_check = await quota_repo.check_quota(current_user.id, file_size)
        if not quota_check["can_upload"]:
            raise HTTPException(
                status_code=413, 
                detail=f"Upload would exceed quota. Available: {quota_check['available_space']} bytes"
            )
        
        # Create file record
        file_data = FileCreate(
            name=file.filename,
            size=file_size,
            mime_type=file.content_type,
            content=content,
            uploaded_by=current_user.id,
            parent_folder_id=parent_folder_id,
            description=description,
            tags=tags.split(',') if tags else [],
            is_public=is_public
        )
        
        file_record = await file_repo.create(file_data)
        
        # Update quota usage
        await quota_repo.update_usage(current_user.id, file_size)
        
        return FileResponse.model_validate(file_record)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/upload/chunked/start", response_model=FileUploadSessionResponse)
async def start_chunked_upload(
    session_data: FileUploadSessionCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Start a chunked file upload session."""
    upload_repo = FileUploadSessionRepository(db)
    quota_repo = FileQuotaRepository(db)
    
    # Check quota
    quota_check = await quota_repo.check_quota(current_user.id, session_data.total_size)
    if not quota_check["can_upload"]:
        raise HTTPException(
            status_code=413, 
            detail=f"Upload would exceed quota. Available: {quota_check['available_space']} bytes"
        )
    
    session = await upload_repo.start_session(session_data, current_user.id)
    return FileUploadSessionResponse.model_validate(session)


@router.post("/upload/chunked/{session_id}/chunk")
async def upload_chunk(
    session_id: UUID,
    chunk_request: ChunkUploadRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Upload a file chunk."""
    upload_repo = FileUploadSessionRepository(db)
    
    result = await upload_repo.upload_chunk(
        session_id, 
        chunk_request.chunk_number, 
        chunk_request.chunk_data
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Upload session not found")
        
    return result


@router.post("/upload/chunked/{session_id}/complete", response_model=FileResponse)
async def complete_chunked_upload(
    session_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Complete a chunked file upload."""
    upload_repo = FileUploadSessionRepository(db)
    file_repo = FileRepository(db)
    quota_repo = FileQuotaRepository(db)
    
    # Complete the upload session
    session = await upload_repo.complete_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Upload session not found")
    
    # Create the final file record
    file_data = FileCreate(
        name=session.file_name,
        size=session.total_size,
        mime_type=session.mime_type,
        content=session.assembled_content,  # Assembled from chunks
        uploaded_by=current_user.id,
        parent_folder_id=session.metadata.get("parent_folder_id"),
        description=session.metadata.get("description"),
        tags=session.metadata.get("tags", []),
        is_public=session.metadata.get("is_public", False)
    )
    
    file_record = await file_repo.create(file_data)
    
    # Update quota usage
    await quota_repo.update_usage(current_user.id, session.total_size)
    
    return FileResponse.model_validate(file_record)


@router.get("/", response_model=List[FileResponse])
async def list_files(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    parent_folder_id: Optional[UUID] = None,
    search: Optional[str] = None,
    tags: Optional[str] = None,
    mime_type: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """List files with filtering and pagination."""
    file_repo = FileRepository(db)
    
    filters = {"uploaded_by": current_user.id}
    if parent_folder_id:
        filters["parent_folder_id"] = parent_folder_id
    if search:
        filters["search"] = search
    if tags:
        filters["tags"] = tags.split(',')
    if mime_type:
        filters["mime_type"] = mime_type
        
    files = await file_repo.get_filtered(
        skip=skip, 
        limit=limit, 
        filters=filters,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return [FileResponse.model_validate(file) for file in files]


@router.get("/{file_id}", response_model=FileResponse)
async def get_file(
    file_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get file metadata."""
    file_repo = FileRepository(db)
    access_repo = FileAccessLogRepository(db)
    
    file_record = await file_repo.get_by_id(file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check access permissions
    if file_record.uploaded_by != current_user.id and not file_record.is_public:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Log access
    await access_repo.log_access(
        file_id=file_id,
        user_id=current_user.id,
        access_type="metadata",
        ip_address="127.0.0.1",  # TODO: Get from request
        user_agent="API"  # TODO: Get from request
    )
    
    return FileResponse.model_validate(file_record)


@router.get("/{file_id}/download")
async def download_file(
    file_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Download file content."""
    file_repo = FileRepository(db)
    access_repo = FileAccessLogRepository(db)
    
    file_record = await file_repo.get_by_id(file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check access permissions
    if file_record.uploaded_by != current_user.id and not file_record.is_public:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Log download
    await access_repo.log_access(
        file_id=file_id,
        user_id=current_user.id,
        access_type="download",
        ip_address="127.0.0.1",  # TODO: Get from request
        user_agent="API"  # TODO: Get from request
    )
    
    # Return file content as stream
    file_stream = io.BytesIO(file_record.content)
    
    return StreamingResponse(
        file_stream,
        media_type=file_record.mime_type,
        headers={
            "Content-Disposition": f"attachment; filename={file_record.name}"
        }
    )


@router.put("/{file_id}", response_model=FileResponse)
async def update_file(
    file_id: UUID,
    file_update: FileUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Update file metadata."""
    file_repo = FileRepository(db)
    
    file_record = await file_repo.get_by_id(file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check permissions
    if file_record.uploaded_by != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    updated_file = await file_repo.update(file_id, file_update)
    return FileResponse.model_validate(updated_file)


@router.delete("/{file_id}")
async def delete_file(
    file_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Delete a file."""
    file_repo = FileRepository(db)
    quota_repo = FileQuotaRepository(db)
    
    file_record = await file_repo.get_by_id(file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check permissions
    if file_record.uploaded_by != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Delete file
    success = await file_repo.delete(file_id)
    if success:
        # Update quota usage
        await quota_repo.update_usage(current_user.id, -file_record.size)
        
    return {"message": "File deleted successfully"}


# File Sharing endpoints
@router.post("/{file_id}/share", response_model=FileShareResponse)
async def create_file_share(
    file_id: UUID,
    share_data: FileShareCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Create a file share link."""
    file_repo = FileRepository(db)
    share_repo = FileShareRepository(db)
    
    file_record = await file_repo.get_by_id(file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check permissions
    if file_record.uploaded_by != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    share = await share_repo.create_share(file_id, share_data, current_user.id)
    return FileShareResponse.model_validate(share)


@router.get("/{file_id}/shares", response_model=List[FileShareResponse])
async def list_file_shares(
    file_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """List file shares."""
    file_repo = FileRepository(db)
    share_repo = FileShareRepository(db)
    
    file_record = await file_repo.get_by_id(file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check permissions
    if file_record.uploaded_by != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    shares = await share_repo.get_file_shares(file_id)
    return [FileShareResponse.model_validate(share) for share in shares]


@router.delete("/shares/{share_id}")
async def revoke_file_share(
    share_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Revoke a file share."""
    share_repo = FileShareRepository(db)
    
    success = await share_repo.revoke_share(share_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Share not found or access denied")
    
    return {"message": "Share revoked successfully"}


@router.get("/shared/{token}")
async def access_shared_file(
    token: str,
    password: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
):
    """Access a file via share token."""
    share_repo = FileShareRepository(db)
    file_repo = FileRepository(db)
    access_repo = FileAccessLogRepository(db)
    
    # Validate share token
    share = await share_repo.validate_token(token, password)
    if not share:
        raise HTTPException(status_code=404, detail="Invalid or expired share link")
    
    # Get file
    file_record = await file_repo.get_by_id(share.file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Log access
    await access_repo.log_access(
        file_id=share.file_id,
        user_id=None,  # Anonymous access
        access_type="shared_access",
        ip_address="127.0.0.1",  # TODO: Get from request
        user_agent="API",  # TODO: Get from request
        share_token=token
    )
    
    # Update share access count
    await share_repo.increment_access_count(share.id)
    
    return {
        "file": FileResponse.model_validate(file_record),
        "share_info": {
            "can_download": share.permissions.get("can_download", True),
            "expires_at": share.expires_at,
            "access_count": share.access_count + 1,
            "max_access_count": share.max_access_count
        }
    }


# File Versions endpoints
@router.get("/{file_id}/versions", response_model=List[FileVersionResponse])
async def list_file_versions(
    file_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """List file versions."""
    file_repo = FileRepository(db)
    version_repo = FileVersionRepository(db)
    
    file_record = await file_repo.get_by_id(file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check permissions
    if file_record.uploaded_by != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    versions = await version_repo.get_file_versions(file_id)
    return [FileVersionResponse.model_validate(version) for version in versions]


@router.post("/{file_id}/versions", response_model=FileVersionResponse)
async def create_file_version(
    file_id: UUID,
    file: UploadFile = File(...),
    version_notes: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Create a new file version."""
    file_repo = FileRepository(db)
    version_repo = FileVersionRepository(db)
    quota_repo = FileQuotaRepository(db)
    
    file_record = await file_repo.get_by_id(file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check permissions
    if file_record.uploaded_by != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Read new file content
    content = await file.read()
    file_size = len(content)
    
    # Check quota
    quota_check = await quota_repo.check_quota(current_user.id, file_size)
    if not quota_check["can_upload"]:
        raise HTTPException(
            status_code=413, 
            detail=f"Upload would exceed quota. Available: {quota_check['available_space']} bytes"
        )
    
    # Create version
    version = await version_repo.create_version(
        file_id=file_id,
        content=content,
        size=file_size,
        mime_type=file.content_type,
        created_by=current_user.id,
        version_notes=version_notes
    )
    
    # Update quota
    await quota_repo.update_usage(current_user.id, file_size)
    
    return FileVersionResponse.model_validate(version)


@router.post("/{file_id}/versions/{version_id}/restore")
async def restore_file_version(
    file_id: UUID,
    version_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Restore a file to a specific version."""
    file_repo = FileRepository(db)
    version_repo = FileVersionRepository(db)
    
    file_record = await file_repo.get_by_id(file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check permissions
    if file_record.uploaded_by != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    success = await version_repo.restore_version(file_id, version_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Version not found")
    
    return {"message": "File restored to version successfully"}


# Quota endpoints
@router.get("/quota", response_model=FileQuotaResponse)
async def get_user_quota(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get user's file quota information."""
    quota_repo = FileQuotaRepository(db)
    quota = await quota_repo.get_user_quota(current_user.id)
    return FileQuotaResponse.model_validate(quota)


@router.get("/quota/usage")
async def get_quota_usage(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get detailed quota usage."""
    quota_repo = FileQuotaRepository(db)
    usage = await quota_repo.get_usage_details(current_user.id)
    return usage


# Analytics endpoints
@router.get("/analytics/access-logs")
async def get_access_analytics(
    file_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get file access analytics."""
    access_repo = FileAccessLogRepository(db)
    
    filters = {"user_id": current_user.id}
    if file_id:
        filters["file_id"] = file_id
    if start_date:
        filters["start_date"] = start_date
    if end_date:
        filters["end_date"] = end_date
    
    analytics = await access_repo.get_access_analytics(
        skip=skip, 
        limit=limit, 
        filters=filters
    )
    return analytics


@router.get("/analytics/popular")
async def get_popular_files(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get most accessed files."""
    access_repo = FileAccessLogRepository(db)
    popular_files = await access_repo.get_popular_files(
        user_id=current_user.id,
        days=days,
        limit=limit
    )
    return popular_files
