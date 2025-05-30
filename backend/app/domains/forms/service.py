"""
Forms service for business logic.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.forms.models import Form, FormField, FormAnalytics, FormStatus, FormFieldType
from app.domains.forms.repository import (
    FormRepository,
    FormFieldRepository,
    FormAnalyticsRepository,
)
from app.domains.forms.schemas import (
    FormCreate,
    FormUpdate,
    FormResponse,
    FormFieldCreate,
    FormFieldUpdate,
    FormFieldResponse,
    FormAnalyticsResponse,
    FormSummary,
    FormWithFields,
    FieldReorder,
)
from app.shared.common.base_service import BaseService


class FormService(BaseService[Form, FormCreate, FormUpdate]):
    """Service for form operations."""
    
    def __init__(self, session: AsyncSession):
        self.form_repo = FormRepository(session)
        self.field_repo = FormFieldRepository(session)
        self.submission_repo = FormSubmissionRepository(session)
        self.analytics_repo = FormAnalyticsRepository(session)
        super().__init__(self.form_repo)
    
    async def create_form(self, form_data: FormCreate, created_by: UUID) -> FormResponse:
        """Create a new form with fields."""
        try:
            # Create form
            form_dict = form_data.model_dump(exclude={'fields'})
            form_dict['created_by'] = created_by
            
            form = Form(**form_dict)
            created_form = await self.form_repo.create(form)
            
            # Create fields if provided
            if form_data.fields:
                for order, field_data in enumerate(form_data.fields):
                    field_dict = field_data.model_dump()
                    field_dict['form_id'] = created_form.id
                    field_dict['order'] = order
                    
                    field = FormField(**field_dict)
                    await self.field_repo.create(field)
            
            await self.form_repo.session.commit()
            
            # Load form with fields
            form_with_fields = await self.form_repo.get_with_fields(created_form.id)
            return FormResponse.model_validate(form_with_fields)
            
        except Exception as e:
            await self.form_repo.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create form: {str(e)}"
            )
    
    async def get_form_with_fields(self, form_id: UUID) -> Optional[FormWithFields]:
        """Get form with all fields."""
        form = await self.form_repo.get_with_fields(form_id)
        if not form:
            return None
        
        return FormWithFields.model_validate(form)
    
    async def get_company_forms(
        self, 
        company_id: UUID,
        status: Optional[FormStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[FormResponse]:
        """Get forms for a company."""
        forms = await self.form_repo.get_by_company(company_id, status, skip, limit)
        return [FormResponse.model_validate(form) for form in forms]
    
    async def get_public_forms(self) -> List[FormResponse]:
        """Get all public forms."""
        forms = await self.form_repo.get_public_forms()
        return [FormResponse.model_validate(form) for form in forms]
    
    async def update_form(self, form_id: UUID, form_data: FormUpdate) -> Optional[FormResponse]:
        """Update form."""
        form = await self.form_repo.get_by_id(form_id)
        if not form:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Form not found"
            )
        
        update_data = form_data.model_dump(exclude_unset=True)
        updated_form = await self.form_repo.update(form, update_data)
        await self.form_repo.session.commit()
        
        return FormResponse.model_validate(updated_form)
    
    async def change_form_status(self, form_id: UUID, new_status: FormStatus) -> Optional[FormResponse]:
        """Change form status."""
        form = await self.form_repo.get_by_id(form_id)
        if not form:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Form not found"
            )
        
        form.status = new_status
        updated_form = await self.form_repo.update(form, {'status': new_status})
        await self.form_repo.session.commit()
        
        return FormResponse.model_validate(updated_form)
    
    async def duplicate_form(self, form_id: UUID, new_title: str, created_by: UUID) -> FormResponse:
        """Duplicate an existing form."""
        original_form = await self.form_repo.get_with_fields(form_id)
        if not original_form:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Form not found"
            )
        
        try:
            # Create new form
            new_form_data = {
                'title': new_title,
                'description': original_form.description,
                'company_id': original_form.company_id,
                'created_by': created_by,
                'is_public': False,  # New form starts as private
                'status': FormStatus.DRAFT,
                'allow_multiple_submissions': original_form.allow_multiple_submissions,
                'submission_limit': original_form.submission_limit,
                'settings': original_form.settings.copy() if original_form.settings else {}
            }
            
            new_form = Form(**new_form_data)
            created_form = await self.form_repo.create(new_form)
            
            # Copy fields
            for field in original_form.fields:
                field_data = {
                    'form_id': created_form.id,
                    'label': field.label,
                    'field_type': field.field_type,
                    'name': field.name,
                    'placeholder': field.placeholder,
                    'help_text': field.help_text,
                    'is_required': field.is_required,
                    'min_length': field.min_length,
                    'max_length': field.max_length,
                    'min_value': field.min_value,
                    'max_value': field.max_value,
                    'pattern': field.pattern,
                    'options': field.options.copy() if field.options else [],
                    'default_value': field.default_value,
                    'order': field.order,
                    'is_visible': field.is_visible,
                    'settings': field.settings.copy() if field.settings else {}
                }
                
                new_field = FormField(**field_data)
                await self.field_repo.create(new_field)
            
            await self.form_repo.session.commit()
            
            # Return form with fields
            form_with_fields = await self.form_repo.get_with_fields(created_form.id)
            return FormResponse.model_validate(form_with_fields)
            
        except Exception as e:
            await self.form_repo.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to duplicate form: {str(e)}"
            )


class FormFieldService:
    """Service for form field operations."""
    
    def __init__(self, session: AsyncSession):
        self.field_repo = FormFieldRepository(session)
        self.form_repo = FormRepository(session)
    
    async def add_field(self, form_id: UUID, field_data: FormFieldCreate) -> FormFieldResponse:
        """Add a field to a form."""
        # Verify form exists
        form = await self.form_repo.get_by_id(form_id)
        if not form:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Form not found"
            )
        
        # Get current fields count for ordering
        existing_fields = await self.field_repo.get_by_form(form_id)
        next_order = len(existing_fields)
        
        field_dict = field_data.model_dump()
        field_dict['form_id'] = form_id
        field_dict['order'] = next_order
        
        field = FormField(**field_dict)
        created_field = await self.field_repo.create(field)
        await self.field_repo.session.commit()
        
        return FormFieldResponse.model_validate(created_field)
    
    async def update_field(self, field_id: UUID, field_data: FormFieldUpdate) -> Optional[FormFieldResponse]:
        """Update a form field."""
        field = await self.field_repo.get_by_id(field_id)
        if not field:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Field not found"
            )
        
        update_data = field_data.model_dump(exclude_unset=True)
        updated_field = await self.field_repo.update(field, update_data)
        await self.field_repo.session.commit()
        
        return FormFieldResponse.model_validate(updated_field)
    
    async def delete_field(self, field_id: UUID) -> bool:
        """Delete a form field."""
        field = await self.field_repo.get_by_id(field_id)
        if not field:
            return False
        
        await self.field_repo.soft_delete(field_id)
        await self.field_repo.session.commit()
        return True
    
    async def reorder_fields(self, form_id: UUID, field_orders: List[FieldReorder]) -> List[FormFieldResponse]:
        """Reorder form fields."""
        # Verify form exists
        form = await self.form_repo.get_by_id(form_id)
        if not form:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Form not found"
            )
        
        # Convert to format expected by repository
        field_order_data = [
            {"field_id": fo.field_id, "order": fo.order}
            for fo in field_orders
        ]
        
        await self.field_repo.reorder_fields(form_id, field_order_data)
        await self.field_repo.session.commit()
          # Return updated fields
        updated_fields = await self.field_repo.get_by_form(form_id, ordered=True)
        return [FormFieldResponse.model_validate(field) for field in updated_fields]


# FormSubmissionService moved to audit domain for compliance tracking
# All form submission operations now handled in app.domains.audit


class FormAnalyticsService:
    """Service for form analytics operations."""
    
    def __init__(self, session: AsyncSession):
        self.analytics_repo = FormAnalyticsRepository(session)
        self.form_repo = FormRepository(session)
    
    async def track_form_view(self, form_id: UUID) -> None:
        """Track a form view."""
        await self.analytics_repo.increment_views(form_id, datetime.utcnow())
        await self.analytics_repo.session.commit()
    
    async def get_form_analytics(
        self, 
        form_id: UUID,
        days: int = 30
    ) -> FormAnalyticsResponse:
        """Get analytics for a form."""
        # Verify form exists
        form = await self.form_repo.get_by_id(form_id)
        if not form:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Form not found"
            )
        
        summary = await self.analytics_repo.get_form_summary(form_id, days)
        return FormAnalyticsResponse(**summary)
    
    async def get_form_summary(self, form_id: UUID) -> FormSummary:
        """Get comprehensive form summary including analytics and data."""
        form = await self.form_repo.get_with_fields(form_id)
        if not form:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Form not found"
            )
          # Get analytics
        analytics = await self.analytics_repo.get_form_summary(form_id, 30)
        
        # Get submission data summary - moved to audit domain
        # submission_service = FormSubmissionService(self.analytics_repo.session)
        # data_summary = await submission_service.get_form_data_summary(form_id)
        data_summary = {}  # TODO: Get from audit domain
        
        return FormSummary(
            form=FormWithFields.model_validate(form),
            analytics=FormAnalyticsResponse(**analytics),
            data_summary=data_summary
        )
