"""
Companies repository for database operations.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import and_, or_, select, update, delete, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domains.companies.models import (
    Company, 
    CompanyUser, 
    CompanyInvitation, 
    CompanyDocument, 
    CompanySettings
)
from app.shared.common.base_repository import BaseRepository


class CompanyRepository(BaseRepository[Company]):
    """Repository for company operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Company, session)
    
    async def get_by_tax_id(self, tax_id: str) -> Optional[Company]:
        """Get company by tax ID."""
        result = await self.session.execute(
            select(Company).where(
                and_(
                    Company.tax_id == tax_id,
                    Company.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_user_companies(
        self, 
        user_id: UUID, 
        skip: int = 0, 
        limit: int = 100,
        include_inactive: bool = False
    ) -> List[Company]:
        """Get companies where user is a member."""
        query = (
            select(Company)
            .join(CompanyUser, Company.id == CompanyUser.company_id)
            .where(
                and_(
                    CompanyUser.user_id == user_id,
                    Company.deleted_at.is_(None),
                    CompanyUser.deleted_at.is_(None)
                )
            )
        )
        
        if not include_inactive:
            query = query.where(
                and_(
                    Company.is_active == True,
                    CompanyUser.is_active == True
                )
            )
        
        query = query.offset(skip).limit(limit).order_by(desc(Company.created_at))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def search_companies(
        self,
        search_query: Optional[str] = None,
        industry: Optional[str] = None,
        company_size: Optional[str] = None,
        country: Optional[str] = None,
        is_verified: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Company]:
        """Search companies with filters."""
        query = select(Company).where(
            and_(
                Company.deleted_at.is_(None),
                Company.is_active == True
            )
        )
        
        if search_query:
            search_filter = or_(
                Company.name.ilike(f"%{search_query}%"),
                Company.legal_name.ilike(f"%{search_query}%"),
                Company.description.ilike(f"%{search_query}%")
            )
            query = query.where(search_filter)
        
        if industry:
            query = query.where(Company.industry == industry)
        
        if company_size:
            query = query.where(Company.company_size == company_size)
        
        if country:
            query = query.where(Company.country == country)
        
        if is_verified is not None:
            query = query.where(Company.is_verified == is_verified)
        
        query = query.offset(skip).limit(limit).order_by(desc(Company.created_at))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_company_stats(self, company_id: UUID) -> Dict[str, Any]:
        """Get company statistics."""
        # Count active users
        user_count = await self.session.execute(
            select(func.count(CompanyUser.id)).where(
                and_(
                    CompanyUser.company_id == company_id,
                    CompanyUser.is_active == True,
                    CompanyUser.deleted_at.is_(None)
                )
            )
        )
        
        # Count documents
        document_count = await self.session.execute(
            select(func.count(CompanyDocument.id)).where(
                and_(
                    CompanyDocument.company_id == company_id,
                    CompanyDocument.is_active == True,
                    CompanyDocument.deleted_at.is_(None)
                )
            )
        )
        
        # Count subsidiaries
        subsidiary_count = await self.session.execute(
            select(func.count(Company.id)).where(
                and_(
                    Company.parent_company_id == company_id,
                    Company.is_active == True,
                    Company.deleted_at.is_(None)
                )
            )
        )
        
        return {
            "total_users": user_count.scalar() or 0,
            "total_documents": document_count.scalar() or 0,
            "total_subsidiaries": subsidiary_count.scalar() or 0,
        }


class CompanyUserRepository(BaseRepository[CompanyUser]):
    """Repository for company user operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(CompanyUser, session)
    
    async def get_by_company_and_user(
        self, 
        company_id: UUID, 
        user_id: UUID
    ) -> Optional[CompanyUser]:
        """Get company user relationship."""
        result = await self.session.execute(
            select(CompanyUser).where(
                and_(
                    CompanyUser.company_id == company_id,
                    CompanyUser.user_id == user_id,
                    CompanyUser.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_company_members(
        self, 
        company_id: UUID,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[CompanyUser]:
        """Get company members with optional filters."""
        query = select(CompanyUser).where(
            and_(
                CompanyUser.company_id == company_id,
                CompanyUser.deleted_at.is_(None)
            )
        )
        
        if role:
            query = query.where(CompanyUser.role == role)
        
        if is_active is not None:
            query = query.where(CompanyUser.is_active == is_active)
        
        query = query.offset(skip).limit(limit).order_by(desc(CompanyUser.created_at))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update_role(
        self, 
        company_id: UUID, 
        user_id: UUID, 
        role: str,
        permissions: Optional[Dict[str, Any]] = None
    ) -> Optional[CompanyUser]:
        """Update user role in company."""
        company_user = await self.get_by_company_and_user(company_id, user_id)
        if company_user:
            company_user.role = role
            if permissions is not None:
                company_user.permissions = permissions
            company_user.updated_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(company_user)
        return company_user
    
    async def activate_user(self, company_id: UUID, user_id: UUID) -> Optional[CompanyUser]:
        """Activate user in company."""
        company_user = await self.get_by_company_and_user(company_id, user_id)
        if company_user:
            company_user.is_active = True
            company_user.joined_at = datetime.utcnow()
            company_user.updated_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(company_user)
        return company_user
    
    async def deactivate_user(self, company_id: UUID, user_id: UUID) -> Optional[CompanyUser]:
        """Deactivate user in company."""
        company_user = await self.get_by_company_and_user(company_id, user_id)
        if company_user:
            company_user.is_active = False
            company_user.updated_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(company_user)
        return company_user


class CompanyInvitationRepository(BaseRepository[CompanyInvitation]):
    """Repository for company invitation operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(CompanyInvitation, session)
    
    async def get_by_token(self, token: str) -> Optional[CompanyInvitation]:
        """Get invitation by token."""
        result = await self.session.execute(
            select(CompanyInvitation).where(CompanyInvitation.token == token)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email_and_company(
        self, 
        email: str, 
        company_id: UUID
    ) -> Optional[CompanyInvitation]:
        """Get invitation by email and company."""
        result = await self.session.execute(
            select(CompanyInvitation).where(
                and_(
                    CompanyInvitation.email == email,
                    CompanyInvitation.company_id == company_id,
                    CompanyInvitation.status == "pending"
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_company_invitations(
        self, 
        company_id: UUID,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[CompanyInvitation]:
        """Get company invitations with optional status filter."""
        query = select(CompanyInvitation).where(
            CompanyInvitation.company_id == company_id
        )
        
        if status:
            query = query.where(CompanyInvitation.status == status)
        
        query = query.offset(skip).limit(limit).order_by(desc(CompanyInvitation.created_at))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def accept_invitation(
        self, 
        token: str, 
        user_id: UUID
    ) -> Optional[CompanyInvitation]:
        """Accept a company invitation."""
        invitation = await self.get_by_token(token)
        if invitation and invitation.status == "pending" and invitation.expires_at > datetime.utcnow():
            invitation.status = "accepted"
            invitation.accepted_by_id = user_id
            invitation.accepted_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(invitation)
        return invitation
    
    async def revoke_invitation(self, invitation_id: UUID) -> Optional[CompanyInvitation]:
        """Revoke a company invitation."""
        invitation = await self.get(invitation_id)
        if invitation and invitation.status == "pending":
            invitation.status = "revoked"
            await self.session.commit()
            await self.session.refresh(invitation)
        return invitation
    
    async def cleanup_expired_invitations(self) -> int:
        """Mark expired invitations as expired."""
        result = await self.session.execute(
            update(CompanyInvitation)
            .where(
                and_(
                    CompanyInvitation.status == "pending",
                    CompanyInvitation.expires_at < datetime.utcnow()
                )
            )
            .values(status="expired")
        )
        await self.session.commit()
        return result.rowcount


class CompanyDocumentRepository(BaseRepository[CompanyDocument]):
    """Repository for company document operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(CompanyDocument, session)
    
    async def get_company_documents(
        self,
        company_id: UUID,
        document_type: Optional[str] = None,
        is_active: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[CompanyDocument]:
        """Get company documents with optional filters."""
        query = select(CompanyDocument).where(
            and_(
                CompanyDocument.company_id == company_id,
                CompanyDocument.deleted_at.is_(None)
            )
        )
        
        if document_type:
            query = query.where(CompanyDocument.document_type == document_type)
        
        if is_active is not None:
            query = query.where(CompanyDocument.is_active == is_active)
        
        query = query.offset(skip).limit(limit).order_by(desc(CompanyDocument.created_at))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_expiring_documents(
        self, 
        company_id: UUID, 
        days_ahead: int = 30
    ) -> List[CompanyDocument]:
        """Get documents expiring within specified days."""
        expiry_date = datetime.utcnow() + timedelta(days=days_ahead)
        
        result = await self.session.execute(
            select(CompanyDocument).where(
                and_(
                    CompanyDocument.company_id == company_id,
                    CompanyDocument.expires_at.is_not(None),
                    CompanyDocument.expires_at <= expiry_date,
                    CompanyDocument.is_active == True,
                    CompanyDocument.deleted_at.is_(None)
                )
            ).order_by(CompanyDocument.expires_at)
        )
        return result.scalars().all()


class CompanySettingsRepository(BaseRepository[CompanySettings]):
    """Repository for company settings operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(CompanySettings, session)
    
    async def get_by_company_id(self, company_id: UUID) -> Optional[CompanySettings]:
        """Get company settings by company ID."""
        result = await self.session.execute(
            select(CompanySettings).where(CompanySettings.company_id == company_id)
        )
        return result.scalar_one_or_none()
    
    async def create_default_settings(
        self, 
        company_id: UUID, 
        created_by_id: UUID
    ) -> CompanySettings:
        """Create default settings for a company."""
        settings = CompanySettings(
            company_id=company_id,
            created_by_id=created_by_id,
            updated_by_id=created_by_id
        )
        self.session.add(settings)
        await self.session.commit()
        await self.session.refresh(settings)
        return settings
    
    async def update_settings(
        self,
        company_id: UUID,
        settings_data: Dict[str, Any],
        updated_by_id: UUID
    ) -> Optional[CompanySettings]:
        """Update company settings."""
        settings = await self.get_by_company_id(company_id)
        if settings:
            for key, value in settings_data.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
            settings.updated_by_id = updated_by_id
            settings.updated_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(settings)
        return settings
