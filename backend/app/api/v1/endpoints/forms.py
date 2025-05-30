"""
Forms API endpoints.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, get_current_user, get_current_active_user
from app.domains.forms.service import (
    FormService,
    FormFieldService,
    FormSubmissionService,
    FormAnalyticsService,
)
from app.domains.forms.schemas import (
    FormCreate,
    FormUpdate,
    FormResponse,
    FormFieldCreate,
    FormFieldUpdate,
    FormFieldResponse,
    FormSubmissionCreate,
    FormSubmissionUpdate,
    FormSubmissionResponse,
    FormAnalyticsResponse,
    FormWithFields,
    FormSummary,
    FieldReorder,
)
from app.domains.forms.models import FormStatus, User


router = APIRouter()


# Form endpoints
@router.post("/", response_model=FormResponse, status_code=status.HTTP_201_CREATED)
async def create_form(
    form_data: FormCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new form."""
    service = FormService(session)
    return await service.create_form(form_data, current_user.id)


@router.get("/", response_model=List[FormResponse])
async def get_forms(
    company_id: Optional[UUID] = Query(None),
    status_filter: Optional[FormStatus] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Get forms. If company_id is provided, get forms for that company."""
    service = FormService(session)
    
    if company_id:
        return await service.get_company_forms(company_id, status_filter, skip, limit)
    else:
        # If no company_id provided, get forms for current user's company
        # Assuming user has a company_id field
        if hasattr(current_user, 'company_id') and current_user.company_id:
            return await service.get_company_forms(current_user.company_id, status_filter, skip, limit)
        else:
            return []


@router.get("/public", response_model=List[FormResponse])
async def get_public_forms(
    session: AsyncSession = Depends(get_session)
):
    """Get all public forms."""
    service = FormService(session)
    return await service.get_public_forms()


@router.get("/{form_id}", response_model=FormWithFields)
async def get_form(
    form_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Get a form with its fields."""
    service = FormService(session)
    form = await service.get_form_with_fields(form_id)
    
    if not form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Form not found"
        )
    
    return form


@router.get("/{form_id}/public", response_model=FormWithFields)
async def get_public_form(
    form_id: UUID,
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    """Get a public form (no authentication required)."""
    service = FormService(session)
    analytics_service = FormAnalyticsService(session)
    
    form = await service.get_form_with_fields(form_id)
    
    if not form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Form not found"
        )
    
    if not form.is_public or form.status != FormStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Form is not publicly accessible"
        )
    
    # Track form view
    await analytics_service.track_form_view(form_id)
    
    return form


@router.put("/{form_id}", response_model=FormResponse)
async def update_form(
    form_id: UUID,
    form_data: FormUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Update a form."""
    service = FormService(session)
    return await service.update_form(form_id, form_data)


@router.patch("/{form_id}/status", response_model=FormResponse)
async def change_form_status(
    form_id: UUID,
    new_status: FormStatus,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Change form status."""
    service = FormService(session)
    return await service.change_form_status(form_id, new_status)


@router.post("/{form_id}/duplicate", response_model=FormResponse)
async def duplicate_form(
    form_id: UUID,
    new_title: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Duplicate a form."""
    service = FormService(session)
    return await service.duplicate_form(form_id, new_title, current_user.id)


@router.delete("/{form_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_form(
    form_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a form."""
    service = FormService(session)
    success = await service.delete(form_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Form not found"
        )


# Form Field endpoints
@router.post("/{form_id}/fields", response_model=FormFieldResponse, status_code=status.HTTP_201_CREATED)
async def add_form_field(
    form_id: UUID,
    field_data: FormFieldCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Add a field to a form."""
    service = FormFieldService(session)
    return await service.add_field(form_id, field_data)


@router.put("/fields/{field_id}", response_model=FormFieldResponse)
async def update_form_field(
    field_id: UUID,
    field_data: FormFieldUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Update a form field."""
    service = FormFieldService(session)
    field = await service.update_field(field_id, field_data)
    
    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field not found"
        )
    
    return field


@router.delete("/fields/{field_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_form_field(
    field_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a form field."""
    service = FormFieldService(session)
    success = await service.delete_field(field_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field not found"
        )


@router.post("/{form_id}/fields/reorder", response_model=List[FormFieldResponse])
async def reorder_form_fields(
    form_id: UUID,
    field_orders: List[FieldReorder],
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Reorder form fields."""
    service = FormFieldService(session)
    return await service.reorder_fields(form_id, field_orders)


# Form Submission endpoints
@router.post("/{form_id}/submissions", response_model=FormSubmissionResponse, status_code=status.HTTP_201_CREATED)
async def create_submission(
    form_id: UUID,
    submission_data: FormSubmissionCreate,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user)  # Optional for public forms
):
    """Create a form submission."""
    service = FormSubmissionService(session)
    
    # Get client IP and user agent
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    return await service.create_submission(
        form_id,
        submission_data,
        submitted_by=current_user.id if current_user else None,
        ip_address=client_ip,
        user_agent=user_agent
    )


@router.get("/{form_id}/submissions", response_model=List[FormSubmissionResponse])
async def get_form_submissions(
    form_id: UUID,
    include_drafts: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Get submissions for a form."""
    service = FormSubmissionService(session)
    return await service.get_form_submissions(form_id, include_drafts, skip, limit)


@router.get("/{form_id}/submissions/summary")
async def get_form_data_summary(
    form_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get summary of form submission data."""
    service = FormSubmissionService(session)
    return await service.get_form_data_summary(form_id)


@router.get("/submissions/my", response_model=List[FormSubmissionResponse])
async def get_my_submissions(
    form_id: Optional[UUID] = Query(None),
    include_drafts: bool = Query(True),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's submissions."""
    service = FormSubmissionService(session)
    return await service.get_user_submissions(current_user.id, form_id, include_drafts)


# Analytics endpoints
@router.get("/{form_id}/analytics", response_model=FormAnalyticsResponse)
async def get_form_analytics(
    form_id: UUID,
    days: int = Query(30, ge=1, le=365),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Get form analytics."""
    service = FormAnalyticsService(session)
    return await service.get_form_analytics(form_id, days)


@router.get("/{form_id}/summary", response_model=FormSummary)
async def get_form_summary(
    form_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Get comprehensive form summary including analytics and data."""
    service = FormAnalyticsService(session)
    return await service.get_form_summary(form_id)
