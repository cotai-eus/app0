"""
File management repositories for uploads, sharing, access control, and quotas.
Based on the database architecture plan.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import desc, asc, func, and_, or_, text
from sqlalchemy.orm import Session, joinedload

from app.shared.common.repository import BaseRepository
from app.core.exceptions import NotFoundError, ValidationError
from .models import (
    FileAccessLog, FileShare, FileQuota, FileVersion, 
    FileUploadSession, AccessType, AccessResult
)


class FileAccessLogRepository(BaseRepository[FileAccessLog]):
    """Repository for file access logging and audit trails."""
    
    def __init__(self, db: Session):
        super().__init__(db, FileAccessLog)
    
    def log_access(
        self,
        document_id: str,
        file_path: str,
        filename: str,
        access_type: AccessType,
        access_result: AccessResult,
        user_id: Optional[str] = None,
        company_id: str = None,
        **kwargs
    ) -> FileAccessLog:
        """Log a file access attempt."""
        access_log = FileAccessLog(
            document_id=document_id,
            file_path=file_path,
            filename=filename,
            access_type=access_type,
            access_result=access_result,
            user_id=user_id,
            company_id=company_id,
            **kwargs
        )
        return self.create(access_log)
    
    def get_user_access_history(
        self,
        user_id: str,
        company_id: str,
        limit: int = 100,
        access_type: Optional[AccessType] = None
    ) -> List[FileAccessLog]:
        """Get user's file access history."""
        query = self.db.query(FileAccessLog).filter(
            FileAccessLog.user_id == user_id,
            FileAccessLog.company_id == company_id
        )
        
        if access_type:
            query = query.filter(FileAccessLog.access_type == access_type)
        
        return query.order_by(desc(FileAccessLog.created_at)).limit(limit).all()
    
    def get_document_access_logs(
        self,
        document_id: str,
        limit: int = 100
    ) -> List[FileAccessLog]:
        """Get access logs for a specific document."""
        return self.db.query(FileAccessLog).filter(
            FileAccessLog.document_id == document_id
        ).order_by(desc(FileAccessLog.created_at)).limit(limit).all()
    
    def get_access_stats(
        self,
        company_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get file access statistics."""
        query = self.db.query(FileAccessLog).filter(
            FileAccessLog.company_id == company_id
        )
        
        if start_date:
            query = query.filter(FileAccessLog.created_at >= start_date)
        if end_date:
            query = query.filter(FileAccessLog.created_at <= end_date)
        
        # Access type statistics
        access_type_stats = self.db.query(
            FileAccessLog.access_type,
            func.count(FileAccessLog.id).label('count')
        ).filter(
            FileAccessLog.company_id == company_id
        ).group_by(FileAccessLog.access_type).all()
        
        # Access result statistics
        result_stats = self.db.query(
            FileAccessLog.access_result,
            func.count(FileAccessLog.id).label('count')
        ).filter(
            FileAccessLog.company_id == company_id
        ).group_by(FileAccessLog.access_result).all()
        
        # Top accessed files
        top_files = self.db.query(
            FileAccessLog.document_id,
            FileAccessLog.filename,
            func.count(FileAccessLog.id).label('access_count')
        ).filter(
            FileAccessLog.company_id == company_id
        ).group_by(
            FileAccessLog.document_id, FileAccessLog.filename
        ).order_by(desc('access_count')).limit(10).all()
        
        return {
            'total_accesses': query.count(),
            'access_types': {stat.access_type: stat.count for stat in access_type_stats},
            'access_results': {stat.access_result: stat.count for stat in result_stats},
            'top_files': [
                {
                    'document_id': file.document_id,
                    'filename': file.filename,
                    'access_count': file.access_count
                }
                for file in top_files
            ]
        }
    
    def get_security_incidents(
        self,
        company_id: str,
        hours: int = 24
    ) -> List[FileAccessLog]:
        """Get recent security incidents (denied access, virus detected, etc.)."""
        since = datetime.utcnow() - timedelta(hours=hours)
        
        return self.db.query(FileAccessLog).filter(
            FileAccessLog.company_id == company_id,
            FileAccessLog.created_at >= since,
            FileAccessLog.access_result.in_([
                AccessResult.DENIED,
                AccessResult.VIRUS_DETECTED,
                AccessResult.ERROR
            ])
        ).order_by(desc(FileAccessLog.created_at)).all()


class FileShareRepository(BaseRepository[FileShare]):
    """Repository for file sharing and link management."""
    
    def __init__(self, db: Session):
        super().__init__(db, FileShare)
    
    def create_share(
        self,
        document_id: str,
        share_token: str,
        created_by: str,
        **share_config
    ) -> FileShare:
        """Create a new file share."""
        share = FileShare(
            document_id=document_id,
            share_token=share_token,
            created_by=created_by,
            **share_config
        )
        return self.create(share)
    
    def get_by_token(self, share_token: str) -> Optional[FileShare]:
        """Get share by token."""
        return self.db.query(FileShare).filter(
            FileShare.share_token == share_token,
            FileShare.is_active == True
        ).first()
    
    def get_active_shares(
        self,
        document_id: str
    ) -> List[FileShare]:
        """Get all active shares for a document."""
        now = datetime.utcnow()
        
        return self.db.query(FileShare).filter(
            FileShare.document_id == document_id,
            FileShare.is_active == True,
            or_(
                FileShare.expires_at.is_(None),
                FileShare.expires_at > now
            )
        ).all()
    
    def get_user_shares(
        self,
        created_by: str,
        include_expired: bool = False
    ) -> List[FileShare]:
        """Get all shares created by a user."""
        query = self.db.query(FileShare).filter(
            FileShare.created_by == created_by
        )
        
        if not include_expired:
            now = datetime.utcnow()
            query = query.filter(
                FileShare.is_active == True,
                or_(
                    FileShare.expires_at.is_(None),
                    FileShare.expires_at > now
                )
            )
        
        return query.order_by(desc(FileShare.created_at)).all()
    
    def increment_access_count(self, share_id: str) -> bool:
        """Increment access count for a share."""
        share = self.get_by_id(share_id)
        if not share:
            return False
        
        share.current_access_count += 1
        
        # Check if max access count reached
        if (share.max_access_count and 
            share.current_access_count >= share.max_access_count):
            share.is_active = False
        
        self.db.commit()
        return True
    
    def validate_share_access(
        self,
        share_token: str,
        user_email: Optional[str] = None,
        password: Optional[str] = None
    ) -> Tuple[bool, str, Optional[FileShare]]:
        """Validate access to a shared file."""
        share = self.get_by_token(share_token)
        
        if not share:
            return False, "Share not found", None
        
        if not share.is_active:
            return False, "Share is inactive", share
        
        # Check expiration
        now = datetime.utcnow()
        if share.expires_at and share.expires_at < now:
            return False, "Share has expired", share
        
        # Check availability window
        if share.available_from and share.available_from > now:
            return False, "Share is not yet available", share
        
        if share.available_until and share.available_until < now:
            return False, "Share is no longer available", share
        
        # Check access count limit
        if (share.max_access_count and 
            share.current_access_count >= share.max_access_count):
            return False, "Maximum access count reached", share
        
        # Check email restrictions
        if share.allowed_emails and user_email:
            if user_email not in share.allowed_emails:
                return False, "Email not authorized", share
        
        # Check domain restrictions
        if share.allowed_domains and user_email:
            user_domain = user_email.split('@')[1] if '@' in user_email else ''
            if not any(domain in user_domain for domain in share.allowed_domains):
                return False, "Domain not authorized", share
        
        # Check password protection
        if share.requires_password:
            if not password:
                return False, "Password required", share
            # Note: In production, use proper password hashing
            if share.password_hash != password:  # Simplified for demo
                return False, "Invalid password", share
        
        return True, "Access granted", share
    
    def get_expiring_shares(
        self,
        hours: int = 24
    ) -> List[FileShare]:
        """Get shares that will expire soon."""
        expires_before = datetime.utcnow() + timedelta(hours=hours)
        
        return self.db.query(FileShare).filter(
            FileShare.is_active == True,
            FileShare.expires_at.is_not(None),
            FileShare.expires_at <= expires_before
        ).all()


class FileQuotaRepository(BaseRepository[FileQuota]):
    """Repository for file quota management and tracking."""
    
    def __init__(self, db: Session):
        super().__init__(db, FileQuota)
    
    def get_company_quota(self, company_id: str) -> Optional[FileQuota]:
        """Get company-wide quota."""
        return self.db.query(FileQuota).filter(
            FileQuota.company_id == company_id,
            FileQuota.user_id.is_(None)
        ).first()
    
    def get_user_quota(
        self,
        company_id: str,
        user_id: str
    ) -> Optional[FileQuota]:
        """Get user-specific quota."""
        return self.db.query(FileQuota).filter(
            FileQuota.company_id == company_id,
            FileQuota.user_id == user_id
        ).first()
    
    def get_effective_quota(
        self,
        company_id: str,
        user_id: Optional[str] = None
    ) -> Optional[FileQuota]:
        """Get effective quota (user-specific or company-wide)."""
        if user_id:
            user_quota = self.get_user_quota(company_id, user_id)
            if user_quota:
                return user_quota
        
        return self.get_company_quota(company_id)
    
    def update_usage(
        self,
        company_id: str,
        user_id: Optional[str],
        bytes_change: int,
        file_count_change: int = 0
    ) -> bool:
        """Update quota usage."""
        quota = self.get_effective_quota(company_id, user_id)
        if not quota:
            return False
        
        quota.used_bytes += bytes_change
        quota.current_file_count += file_count_change
        
        # Check if over quota
        quota.is_over_quota = quota.used_bytes > quota.total_quota_bytes
        
        # Check if warning threshold reached
        usage_percent = (quota.used_bytes / quota.total_quota_bytes) * 100
        if usage_percent >= quota.warn_at_percent and not quota.warning_sent:
            quota.warning_sent = True
        
        quota.last_calculated = datetime.utcnow()
        self.db.commit()
        return True
    
    def check_quota_availability(
        self,
        company_id: str,
        user_id: Optional[str],
        required_bytes: int,
        required_files: int = 1
    ) -> Tuple[bool, str]:
        """Check if quota allows for new files."""
        quota = self.get_effective_quota(company_id, user_id)
        if not quota:
            return False, "No quota policy found"
        
        # Check bytes limit
        if quota.used_bytes + required_bytes > quota.total_quota_bytes:
            available_bytes = quota.total_quota_bytes - quota.used_bytes
            return False, f"Insufficient storage space. Available: {available_bytes} bytes"
        
        # Check file count limit
        if quota.max_files:
            if quota.current_file_count + required_files > quota.max_files:
                available_files = quota.max_files - quota.current_file_count
                return False, f"File count limit exceeded. Available slots: {available_files}"
        
        return True, "Quota available"
    
    def get_over_quota_accounts(self) -> List[FileQuota]:
        """Get accounts that are over quota."""
        return self.db.query(FileQuota).filter(
            FileQuota.is_over_quota == True
        ).all()
    
    def calculate_usage_stats(
        self,
        company_id: str
    ) -> Dict[str, Any]:
        """Calculate quota usage statistics for a company."""
        quotas = self.db.query(FileQuota).filter(
            FileQuota.company_id == company_id
        ).all()
        
        total_allocated = sum(q.total_quota_bytes for q in quotas)
        total_used = sum(q.used_bytes for q in quotas)
        over_quota_count = sum(1 for q in quotas if q.is_over_quota)
        
        return {
            'total_accounts': len(quotas),
            'total_allocated_bytes': total_allocated,
            'total_used_bytes': total_used,
            'usage_percentage': (total_used / total_allocated * 100) if total_allocated > 0 else 0,
            'over_quota_count': over_quota_count,
            'accounts_needing_warning': sum(
                1 for q in quotas 
                if (q.used_bytes / q.total_quota_bytes * 100) >= q.warn_at_percent
                and not q.warning_sent
            )
        }


class FileVersionRepository(BaseRepository[FileVersion]):
    """Repository for file version management."""
    
    def __init__(self, db: Session):
        super().__init__(db, FileVersion)
    
    def create_version(
        self,
        document_id: str,
        filename: str,
        file_path: str,
        file_size: int,
        file_hash: str,
        mime_type: str,
        created_by: str,
        **kwargs
    ) -> FileVersion:
        """Create a new file version."""
        # Get next version number
        latest_version = self.db.query(func.max(FileVersion.version_number)).filter(
            FileVersion.document_id == document_id
        ).scalar() or 0
        
        # Mark current version as not current
        self.db.query(FileVersion).filter(
            FileVersion.document_id == document_id,
            FileVersion.is_current == True
        ).update({'is_current': False})
        
        version = FileVersion(
            document_id=document_id,
            version_number=latest_version + 1,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            file_hash=file_hash,
            mime_type=mime_type,
            is_current=True,
            created_by=created_by,
            **kwargs
        )
        
        return self.create(version)
    
    def get_document_versions(
        self,
        document_id: str,
        include_archived: bool = False
    ) -> List[FileVersion]:
        """Get all versions of a document."""
        query = self.db.query(FileVersion).filter(
            FileVersion.document_id == document_id
        )
        
        if not include_archived:
            query = query.filter(FileVersion.is_archived == False)
        
        return query.order_by(desc(FileVersion.version_number)).all()
    
    def get_current_version(self, document_id: str) -> Optional[FileVersion]:
        """Get current version of a document."""
        return self.db.query(FileVersion).filter(
            FileVersion.document_id == document_id,
            FileVersion.is_current == True
        ).first()
    
    def get_version(
        self,
        document_id: str,
        version_number: int
    ) -> Optional[FileVersion]:
        """Get specific version of a document."""
        return self.db.query(FileVersion).filter(
            FileVersion.document_id == document_id,
            FileVersion.version_number == version_number
        ).first()
    
    def set_current_version(
        self,
        document_id: str,
        version_number: int
    ) -> bool:
        """Set a specific version as current."""
        # Mark all versions as not current
        self.db.query(FileVersion).filter(
            FileVersion.document_id == document_id
        ).update({'is_current': False})
        
        # Mark specified version as current
        result = self.db.query(FileVersion).filter(
            FileVersion.document_id == document_id,
            FileVersion.version_number == version_number
        ).update({'is_current': True})
        
        self.db.commit()
        return result > 0
    
    def archive_old_versions(
        self,
        document_id: str,
        keep_versions: int = 5
    ) -> int:
        """Archive old versions, keeping only the most recent ones."""
        versions = self.db.query(FileVersion).filter(
            FileVersion.document_id == document_id,
            FileVersion.is_archived == False
        ).order_by(desc(FileVersion.version_number)).all()
        
        if len(versions) <= keep_versions:
            return 0
        
        # Archive versions beyond the keep limit
        versions_to_archive = versions[keep_versions:]
        archived_count = 0
        
        for version in versions_to_archive:
            if not version.is_current:  # Never archive current version
                version.is_archived = True
                archived_count += 1
        
        self.db.commit()
        return archived_count


class FileUploadSessionRepository(BaseRepository[FileUploadSession]):
    """Repository for managing chunked/resumable file uploads."""
    
    def __init__(self, db: Session):
        super().__init__(db, FileUploadSession)
    
    def create_session(
        self,
        session_token: str,
        filename: str,
        total_size: int,
        user_id: str,
        company_id: str,
        expires_in_hours: int = 24,
        **kwargs
    ) -> FileUploadSession:
        """Create a new upload session."""
        expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        
        session = FileUploadSession(
            session_token=session_token,
            filename=filename,
            total_size=total_size,
            user_id=user_id,
            company_id=company_id,
            expires_at=expires_at,
            uploaded_chunks=[],
            **kwargs
        )
        
        return self.create(session)
    
    def get_by_token(self, session_token: str) -> Optional[FileUploadSession]:
        """Get upload session by token."""
        return self.db.query(FileUploadSession).filter(
            FileUploadSession.session_token == session_token,
            FileUploadSession.expires_at > datetime.utcnow(),
            FileUploadSession.is_completed == False,
            FileUploadSession.is_failed == False
        ).first()
    
    def update_chunk_progress(
        self,
        session_token: str,
        chunk_number: int,
        chunk_size: int
    ) -> bool:
        """Update progress after a chunk is uploaded."""
        session = self.get_by_token(session_token)
        if not session:
            return False
        
        # Add chunk to uploaded chunks list
        if chunk_number not in session.uploaded_chunks:
            session.uploaded_chunks.append(chunk_number)
            session.uploaded_bytes += chunk_size
        
        # Check if upload is complete
        expected_chunks = (session.total_size + session.chunk_size - 1) // session.chunk_size
        if len(session.uploaded_chunks) >= expected_chunks:
            session.is_completed = True
        
        # Mark as modified for SQLAlchemy to detect JSON change
        session.uploaded_chunks = session.uploaded_chunks[:]
        
        self.db.commit()
        return True
    
    def mark_completed(self, session_token: str) -> bool:
        """Mark upload session as completed."""
        session = self.get_by_token(session_token)
        if not session:
            return False
        
        session.is_completed = True
        self.db.commit()
        return True
    
    def mark_failed(
        self,
        session_token: str,
        failure_reason: str
    ) -> bool:
        """Mark upload session as failed."""
        session = self.get_by_token(session_token)
        if not session:
            return False
        
        session.is_failed = True
        session.failure_reason = failure_reason
        self.db.commit()
        return True
    
    def get_user_sessions(
        self,
        user_id: str,
        active_only: bool = True
    ) -> List[FileUploadSession]:
        """Get upload sessions for a user."""
        query = self.db.query(FileUploadSession).filter(
            FileUploadSession.user_id == user_id
        )
        
        if active_only:
            query = query.filter(
                FileUploadSession.expires_at > datetime.utcnow(),
                FileUploadSession.is_completed == False,
                FileUploadSession.is_failed == False
            )
        
        return query.order_by(desc(FileUploadSession.created_at)).all()
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired upload sessions."""
        expired_sessions = self.db.query(FileUploadSession).filter(
            FileUploadSession.expires_at <= datetime.utcnow()
        ).all()
        
        count = len(expired_sessions)
        
        for session in expired_sessions:
            # Clean up temporary files if they exist
            # This would be implemented based on storage backend
            self.db.delete(session)
        
        self.db.commit()
        return count
    
    def get_incomplete_sessions(
        self,
        older_than_hours: int = 1
    ) -> List[FileUploadSession]:
        """Get sessions that are incomplete and stale."""
        cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
        
        return self.db.query(FileUploadSession).filter(
            FileUploadSession.created_at < cutoff_time,
            FileUploadSession.is_completed == False,
            FileUploadSession.is_failed == False,
            FileUploadSession.expires_at > datetime.utcnow()
        ).all()
