"""
Companies service for business logic.
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.companies.models import Company, CompanyUser, CompanyInvitation
from app.domains.companies.repository import (
    CompanyRepository,
    CompanyUserRepository, 
    CompanyInvitationRepository,
    CompanyDocumentRepository,
    CompanySettingsRepository
)
from app.domains.companies.schemas import (
    CompanyCreate,
    CompanyUpdate,
    CompanyUserInvite,
    CompanyDocumentCreate,
    CompanySettingsCreate,
    CompanySettingsUpdate
)
from app.core.exceptions import (
    BusinessError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError
)
from app.shared.common.base_service import BaseService


class CompanyService(BaseService):
    """Service for company business logic."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.company_repo = CompanyRepository(session)
        self.company_user_repo = CompanyUserRepository(session)
        self.invitation_repo = CompanyInvitationRepository(session)
        self.document_repo = CompanyDocumentRepository(session)
        self.settings_repo = CompanySettingsRepository(session)
    
    async def create_company(
        self, 
        company_data: CompanyCreate, 
        created_by_id: UUID
    ) -> Company:
        """Create a new company."""
        # Check if tax_id is unique (if provided)
        if company_data.tax_id:
            existing_company = await self.company_repo.get_by_tax_id(company_data.tax_id)
            if existing_company:
                raise ValidationError("Company with this tax ID already exists")
        
        # Create company
        company = Company(
            **company_data.model_dump(exclude_unset=True),
            created_by_id=created_by_id,
            updated_by_id=created_by_id
        )
        
        company = await self.company_repo.create(company)
        
        # Add creator as company owner
        company_user = CompanyUser(
            company_id=company.id,
            user_id=created_by_id,
            role="owner",
            is_active=True,
            joined_at=datetime.utcnow()
        )
        await self.company_user_repo.create(company_user)
        
        # Create default settings
        await self.settings_repo.create_default_settings(company.id, created_by_id)
        
        return company
    
    async def get_company(self, company_id: UUID, user_id: UUID) -> Company:
        """Get company by ID with permission check."""
        company = await self.company_repo.get(company_id)
        if not company:
            raise NotFoundError("Company not found")
        
        # Check if user has access to this company
        company_user = await self.company_user_repo.get_by_company_and_user(
            company_id, user_id
        )
        if not company_user or not company_user.is_active:
            raise PermissionDeniedError("Access denied to this company")
        
        return company
    
    async def update_company(
        self, 
        company_id: UUID, 
        company_data: CompanyUpdate, 
        user_id: UUID
    ) -> Company:
        """Update company information."""
        # Check permissions
        await self._check_company_admin_permission(company_id, user_id)
        
        company = await self.company_repo.get(company_id)
        if not company:
            raise NotFoundError("Company not found")
        
        # Check tax_id uniqueness if being updated
        if company_data.tax_id and company_data.tax_id != company.tax_id:
            existing_company = await self.company_repo.get_by_tax_id(company_data.tax_id)
            if existing_company:
                raise ValidationError("Company with this tax ID already exists")
        
        # Update company
        update_data = company_data.model_dump(exclude_unset=True)
        update_data["updated_by_id"] = user_id
        
        return await self.company_repo.update(company_id, update_data)
    
    async def delete_company(self, company_id: UUID, user_id: UUID) -> bool:
        """Soft delete company (owner only)."""
        await self._check_company_owner_permission(company_id, user_id)
        
        company = await self.company_repo.get(company_id)
        if not company:
            raise NotFoundError("Company not found")
        
        # Soft delete company
        await self.company_repo.soft_delete(company_id, user_id)
        return True
    
    async def get_user_companies(
        self, 
        user_id: UUID, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Company]:
        """Get companies where user is a member."""
        return await self.company_repo.get_user_companies(user_id, skip, limit)
    
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
        """Search public companies."""
        return await self.company_repo.search_companies(
            search_query=search_query,
            industry=industry,
            company_size=company_size,
            country=country,
            is_verified=is_verified,
            skip=skip,
            limit=limit
        )
    
    async def get_company_stats(self, company_id: UUID, user_id: UUID) -> Dict[str, Any]:
        """Get company statistics."""
        await self._check_company_access(company_id, user_id)
        return await self.company_repo.get_company_stats(company_id)
    
    # Company User Management
    async def invite_user(
        self, 
        company_id: UUID, 
        invitation_data: CompanyUserInvite, 
        invited_by_id: UUID
    ) -> CompanyInvitation:
        """Invite user to company."""
        await self._check_company_admin_permission(company_id, invited_by_id)
        
        # Check if user is already invited or member
        existing_invitation = await self.invitation_repo.get_by_email_and_company(
            invitation_data.email, company_id
        )
        if existing_invitation:
            raise ValidationError("User already invited to this company")
        
        # Generate invitation token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=7)  # 7 days to accept
        
        invitation = CompanyInvitation(
            company_id=company_id,
            email=invitation_data.email,
            role=invitation_data.role,
            token=token,
            expires_at=expires_at,
            invited_by_id=invited_by_id
        )
        
        invitation = await self.invitation_repo.create(invitation)
        
        # TODO: Send invitation email
        
        return invitation
    
    async def accept_invitation(self, token: str, user_id: UUID) -> CompanyUser:
        """Accept company invitation."""
        invitation = await self.invitation_repo.accept_invitation(token, user_id)
        if not invitation:
            raise NotFoundError("Invalid or expired invitation")
        
        # Check if user is already a member
        existing_membership = await self.company_user_repo.get_by_company_and_user(
            invitation.company_id, user_id
        )
        if existing_membership:
            if existing_membership.is_active:
                raise ValidationError("User is already a member of this company")
            else:
                # Reactivate existing membership
                return await self.company_user_repo.activate_user(
                    invitation.company_id, user_id
                )
        
        # Create new company membership
        company_user = CompanyUser(
            company_id=invitation.company_id,
            user_id=user_id,
            role=invitation.role,
            is_active=True,
            invited_at=invitation.created_at,
            joined_at=datetime.utcnow(),
            invited_by_id=invitation.invited_by_id
        )
        
        return await self.company_user_repo.create(company_user)
    
    async def get_company_members(
        self,
        company_id: UUID,
        user_id: UUID,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[CompanyUser]:
        """Get company members."""
        await self._check_company_access(company_id, user_id)
        
        return await self.company_user_repo.get_company_members(
            company_id=company_id,
            role=role,
            is_active=is_active,
            skip=skip,
            limit=limit
        )
    
    async def update_member_role(
        self,
        company_id: UUID,
        target_user_id: UUID,
        new_role: str,
        permissions: Optional[Dict[str, Any]],
        updated_by_id: UUID
    ) -> CompanyUser:
        """Update member role in company."""
        await self._check_company_admin_permission(company_id, updated_by_id)
        
        # Don't allow changing owner role
        current_membership = await self.company_user_repo.get_by_company_and_user(
            company_id, target_user_id
        )
        if not current_membership:
            raise NotFoundError("User is not a member of this company")
        
        if current_membership.role == "owner" and new_role != "owner":
            raise PermissionDeniedError("Cannot change owner role")
        
        updated_membership = await self.company_user_repo.update_role(
            company_id, target_user_id, new_role, permissions
        )
        
        if not updated_membership:
            raise NotFoundError("Failed to update member role")
        
        return updated_membership
    
    async def remove_member(
        self, 
        company_id: UUID, 
        target_user_id: UUID, 
        removed_by_id: UUID
    ) -> bool:
        """Remove member from company."""
        await self._check_company_admin_permission(company_id, removed_by_id)
        
        # Don't allow removing owner
        current_membership = await self.company_user_repo.get_by_company_and_user(
            company_id, target_user_id
        )
        if not current_membership:
            raise NotFoundError("User is not a member of this company")
        
        if current_membership.role == "owner":
            raise PermissionDeniedError("Cannot remove company owner")
        
        await self.company_user_repo.soft_delete(current_membership.id, removed_by_id)
        return True
    
    # Company Settings
    async def get_company_settings(self, company_id: UUID, user_id: UUID):
        """Get company settings."""
        await self._check_company_access(company_id, user_id)
        
        settings = await self.settings_repo.get_by_company_id(company_id)
        if not settings:
            # Create default settings
            settings = await self.settings_repo.create_default_settings(company_id, user_id)
        
        return settings
    
    async def update_company_settings(
        self,
        company_id: UUID,
        settings_data: CompanySettingsUpdate,
        user_id: UUID
    ):
        """Update company settings."""
        await self._check_company_admin_permission(company_id, user_id)
        
        update_data = settings_data.model_dump(exclude_unset=True)
        settings = await self.settings_repo.update_settings(
            company_id, update_data, user_id
        )
        
        if not settings:
            raise NotFoundError("Company settings not found")
        
        return settings
    
    # Documents
    async def create_document(
        self,
        company_id: UUID,
        document_data: CompanyDocumentCreate,
        created_by_id: UUID
    ):
        """Create company document."""
        await self._check_company_access(company_id, created_by_id)
        
        from app.domains.companies.models import CompanyDocument
        
        document = CompanyDocument(
            company_id=company_id,
            **document_data.model_dump(exclude_unset=True),
            created_by_id=created_by_id,
            updated_by_id=created_by_id
        )
        
        return await self.document_repo.create(document)
    
    async def get_company_documents(
        self,
        company_id: UUID,
        user_id: UUID,
        document_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ):
        """Get company documents."""
        await self._check_company_access(company_id, user_id)
        
        return await self.document_repo.get_company_documents(
            company_id=company_id,
            document_type=document_type,
            skip=skip,
            limit=limit
        )
    
    # Permission helpers
    async def _check_company_access(self, company_id: UUID, user_id: UUID) -> CompanyUser:
        """Check if user has access to company."""
        company_user = await self.company_user_repo.get_by_company_and_user(
            company_id, user_id
        )
        if not company_user or not company_user.is_active:
            raise PermissionDeniedError("Access denied to this company")
        return company_user
    
    async def _check_company_admin_permission(self, company_id: UUID, user_id: UUID) -> CompanyUser:
        """Check if user has admin permission in company."""
        company_user = await self._check_company_access(company_id, user_id)
        if company_user.role not in ["owner", "admin"]:
            raise PermissionDeniedError("Admin permission required")
        return company_user
    
    async def _check_company_owner_permission(self, company_id: UUID, user_id: UUID) -> CompanyUser:
        """Check if user is company owner."""
        company_user = await self._check_company_access(company_id, user_id)
        if company_user.role != "owner":
            raise PermissionDeniedError("Owner permission required")
        return company_user
