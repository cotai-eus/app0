"""
Audit and Compliance API endpoints.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session, get_current_user
from app.domains.auth.models import User
from app.domains.audit.repository import (
    AuditLogRepository,
    FormTemplateRepository, 
    FormSubmissionRepository,
    DataRetentionPolicyRepository
)
from app.domains.audit.schemas import (
    AuditLogResponse,
    AuditLogCreate,
    FormTemplateResponse,
    FormTemplateCreate,
    FormTemplateUpdate,
    FormSubmissionResponse,
    FormSubmissionCreate,
    FormSubmissionUpdate,
    DataRetentionPolicyResponse,
    DataRetentionPolicyCreate,
    ComplianceReportResponse,
    AuditTrailResponse,
)

router = APIRouter()


# Audit Logs endpoints
@router.post("/logs", response_model=AuditLogResponse)
async def create_audit_log(
    log_data: AuditLogCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Create an audit log entry."""
    audit_repo = AuditLogRepository(db)
    log_entry = await audit_repo.create_log(log_data, current_user.id)
    return AuditLogResponse.model_validate(log_entry)


@router.get("/logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    severity: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get audit logs with filtering."""
    audit_repo = AuditLogRepository(db)
    
    filters = {}
    if start_date:
        filters["start_date"] = start_date
    if end_date:
        filters["end_date"] = end_date
    if action:
        filters["action"] = action
    if entity_type:
        filters["entity_type"] = entity_type
    if entity_id:
        filters["entity_id"] = entity_id
    if user_id:
        filters["user_id"] = user_id
    if severity:
        filters["severity"] = severity
        
    logs = await audit_repo.get_filtered_logs(
        skip=skip, 
        limit=limit, 
        filters=filters
    )
    return [AuditLogResponse.model_validate(log) for log in logs]


@router.get("/logs/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get a specific audit log entry."""
    audit_repo = AuditLogRepository(db)
    log_entry = await audit_repo.get_by_id(log_id)
    
    if not log_entry:
        raise HTTPException(status_code=404, detail="Audit log not found")
        
    return AuditLogResponse.model_validate(log_entry)


@router.get("/logs/entity/{entity_type}/{entity_id}", response_model=List[AuditLogResponse])
async def get_entity_audit_trail(
    entity_type: str,
    entity_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get audit trail for a specific entity."""
    audit_repo = AuditLogRepository(db)
    trail = await audit_repo.get_entity_trail(
        entity_type=entity_type,
        entity_id=entity_id,
        skip=skip,
        limit=limit
    )
    return [AuditLogResponse.model_validate(log) for log in trail]


@router.get("/trail/{entity_type}/{entity_id}", response_model=AuditTrailResponse)
async def get_audit_trail_analysis(
    entity_type: str,
    entity_id: UUID,
    include_related: bool = True,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get comprehensive audit trail analysis for an entity."""
    audit_repo = AuditLogRepository(db)
    trail_analysis = await audit_repo.get_trail_analysis(
        entity_type=entity_type,
        entity_id=entity_id,
        include_related=include_related
    )
    return trail_analysis


# Form Templates endpoints
@router.post("/forms/templates", response_model=FormTemplateResponse)
async def create_form_template(
    template_data: FormTemplateCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Create a form template."""
    form_repo = FormTemplateRepository(db)
    template = await form_repo.create_template(template_data, current_user.id)
    return FormTemplateResponse.model_validate(template)


@router.get("/forms/templates", response_model=List[FormTemplateResponse])
async def list_form_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """List form templates."""
    form_repo = FormTemplateRepository(db)
    
    filters = {}
    if category:
        filters["category"] = category
    if is_active is not None:
        filters["is_active"] = is_active
    if search:
        filters["search"] = search
        
    templates = await form_repo.get_filtered_templates(
        skip=skip, 
        limit=limit, 
        filters=filters
    )
    return [FormTemplateResponse.model_validate(template) for template in templates]


@router.get("/forms/templates/{template_id}", response_model=FormTemplateResponse)
async def get_form_template(
    template_id: UUID,
    version: Optional[int] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get a form template by ID and optionally by version."""
    form_repo = FormTemplateRepository(db)
    
    if version:
        template = await form_repo.get_template_version(template_id, version)
    else:
        template = await form_repo.get_by_id(template_id)
    
    if not template:
        raise HTTPException(status_code=404, detail="Form template not found")
        
    return FormTemplateResponse.model_validate(template)


@router.put("/forms/templates/{template_id}", response_model=FormTemplateResponse)
async def update_form_template(
    template_id: UUID,
    template_update: FormTemplateUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Update a form template."""
    form_repo = FormTemplateRepository(db)
    template = await form_repo.update_template(template_id, template_update, current_user.id)
    
    if not template:
        raise HTTPException(status_code=404, detail="Form template not found")
        
    return FormTemplateResponse.model_validate(template)


@router.delete("/forms/templates/{template_id}")
async def delete_form_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Delete a form template."""
    form_repo = FormTemplateRepository(db)
    success = await form_repo.delete_template(template_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Form template not found")
        
    return {"message": "Form template deleted successfully"}


@router.get("/forms/templates/{template_id}/versions")
async def get_template_versions(
    template_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get all versions of a form template."""
    form_repo = FormTemplateRepository(db)
    versions = await form_repo.get_template_versions(template_id)
    return versions


@router.post("/forms/templates/{template_id}/validate")
async def validate_form_data(
    template_id: UUID,
    form_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Validate form data against a template."""
    form_repo = FormTemplateRepository(db)
    validation_result = await form_repo.validate_submission(template_id, form_data)
    return validation_result


# Form Submissions endpoints
@router.post("/forms/submissions", response_model=FormSubmissionResponse)
async def create_form_submission(
    submission_data: FormSubmissionCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Create a form submission."""
    submission_repo = FormSubmissionRepository(db)
    form_repo = FormTemplateRepository(db)
    
    # Validate against template
    validation_result = await form_repo.validate_submission(
        submission_data.template_id, 
        submission_data.form_data
    )
    
    if not validation_result["is_valid"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Form validation failed: {validation_result['errors']}"
        )
    
    submission = await submission_repo.create_submission(submission_data, current_user.id)
    return FormSubmissionResponse.model_validate(submission)


@router.get("/forms/submissions", response_model=List[FormSubmissionResponse])
async def list_form_submissions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    template_id: Optional[UUID] = None,
    status: Optional[str] = None,
    submitted_by: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """List form submissions."""
    submission_repo = FormSubmissionRepository(db)
    
    filters = {}
    if template_id:
        filters["template_id"] = template_id
    if status:
        filters["status"] = status
    if submitted_by:
        filters["submitted_by"] = submitted_by
    if start_date:
        filters["start_date"] = start_date
    if end_date:
        filters["end_date"] = end_date
        
    submissions = await submission_repo.get_filtered_submissions(
        skip=skip, 
        limit=limit, 
        filters=filters
    )
    return [FormSubmissionResponse.model_validate(submission) for submission in submissions]


@router.get("/forms/submissions/{submission_id}", response_model=FormSubmissionResponse)
async def get_form_submission(
    submission_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get a form submission."""
    submission_repo = FormSubmissionRepository(db)
    submission = await submission_repo.get_by_id(submission_id)
    
    if not submission:
        raise HTTPException(status_code=404, detail="Form submission not found")
        
    return FormSubmissionResponse.model_validate(submission)


@router.put("/forms/submissions/{submission_id}", response_model=FormSubmissionResponse)
async def update_form_submission(
    submission_id: UUID,
    submission_update: FormSubmissionUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Update a form submission."""
    submission_repo = FormSubmissionRepository(db)
    submission = await submission_repo.update_submission(
        submission_id, 
        submission_update, 
        current_user.id
    )
    
    if not submission:
        raise HTTPException(status_code=404, detail="Form submission not found")
        
    return FormSubmissionResponse.model_validate(submission)


@router.post("/forms/submissions/{submission_id}/approve")
async def approve_submission(
    submission_id: UUID,
    approval_notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Approve a form submission."""
    submission_repo = FormSubmissionRepository(db)
    success = await submission_repo.approve_submission(
        submission_id, 
        current_user.id, 
        approval_notes
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Form submission not found")
        
    return {"message": "Submission approved successfully"}


@router.post("/forms/submissions/{submission_id}/reject")
async def reject_submission(
    submission_id: UUID,
    rejection_reason: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Reject a form submission."""
    submission_repo = FormSubmissionRepository(db)
    success = await submission_repo.reject_submission(
        submission_id, 
        current_user.id, 
        rejection_reason
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Form submission not found")
        
    return {"message": "Submission rejected"}


@router.get("/forms/submissions/{submission_id}/workflow")
async def get_submission_workflow(
    submission_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get submission workflow history."""
    submission_repo = FormSubmissionRepository(db)
    workflow = await submission_repo.get_workflow_history(submission_id)
    return workflow


# Data Retention Policies endpoints
@router.post("/retention/policies", response_model=DataRetentionPolicyResponse)
async def create_retention_policy(
    policy_data: DataRetentionPolicyCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Create a data retention policy."""
    retention_repo = DataRetentionPolicyRepository(db)
    policy = await retention_repo.create_policy(policy_data, current_user.id)
    return DataRetentionPolicyResponse.model_validate(policy)


@router.get("/retention/policies", response_model=List[DataRetentionPolicyResponse])
async def list_retention_policies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    data_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """List data retention policies."""
    retention_repo = DataRetentionPolicyRepository(db)
    
    filters = {}
    if data_type:
        filters["data_type"] = data_type
    if is_active is not None:
        filters["is_active"] = is_active
        
    policies = await retention_repo.get_filtered_policies(
        skip=skip, 
        limit=limit, 
        filters=filters
    )
    return [DataRetentionPolicyResponse.model_validate(policy) for policy in policies]


@router.get("/retention/policies/{policy_id}", response_model=DataRetentionPolicyResponse)
async def get_retention_policy(
    policy_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get a data retention policy."""
    retention_repo = DataRetentionPolicyRepository(db)
    policy = await retention_repo.get_by_id(policy_id)
    
    if not policy:
        raise HTTPException(status_code=404, detail="Retention policy not found")
        
    return DataRetentionPolicyResponse.model_validate(policy)


@router.put("/retention/policies/{policy_id}", response_model=DataRetentionPolicyResponse)
async def update_retention_policy(
    policy_id: UUID,
    policy_update: DataRetentionPolicyCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Update a data retention policy."""
    retention_repo = DataRetentionPolicyRepository(db)
    policy = await retention_repo.update_policy(policy_id, policy_update, current_user.id)
    
    if not policy:
        raise HTTPException(status_code=404, detail="Retention policy not found")
        
    return DataRetentionPolicyResponse.model_validate(policy)


@router.delete("/retention/policies/{policy_id}")
async def delete_retention_policy(
    policy_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Delete a data retention policy."""
    retention_repo = DataRetentionPolicyRepository(db)
    success = await retention_repo.delete_policy(policy_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Retention policy not found")
        
    return {"message": "Retention policy deleted successfully"}


@router.post("/retention/policies/{policy_id}/execute")
async def execute_retention_policy(
    policy_id: UUID,
    dry_run: bool = Query(False),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Execute a data retention policy."""
    retention_repo = DataRetentionPolicyRepository(db)
    result = await retention_repo.execute_policy(policy_id, dry_run)
    
    if not result:
        raise HTTPException(status_code=404, detail="Retention policy not found")
        
    return result


@router.post("/retention/execute-all")
async def execute_all_retention_policies(
    dry_run: bool = Query(False),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Execute all active retention policies."""
    retention_repo = DataRetentionPolicyRepository(db)
    results = await retention_repo.execute_all_policies(dry_run)
    return results


@router.get("/retention/preview/{policy_id}")
async def preview_retention_cleanup(
    policy_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Preview what data would be affected by retention policy."""
    retention_repo = DataRetentionPolicyRepository(db)
    preview = await retention_repo.preview_cleanup(policy_id)
    
    if not preview:
        raise HTTPException(status_code=404, detail="Retention policy not found")
        
    return preview


# Compliance Reports endpoints
@router.get("/compliance/report", response_model=ComplianceReportResponse)
async def generate_compliance_report(
    start_date: datetime,
    end_date: datetime,
    report_type: str = "comprehensive",
    include_details: bool = False,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Generate a compliance report."""
    audit_repo = AuditLogRepository(db)
    form_repo = FormSubmissionRepository(db)
    retention_repo = DataRetentionPolicyRepository(db)
    
    report = await audit_repo.generate_compliance_report(
        start_date=start_date,
        end_date=end_date,
        report_type=report_type,
        include_details=include_details
    )
    
    return report


@router.get("/compliance/metrics")
async def get_compliance_metrics(
    period: str = "30d",
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get compliance metrics summary."""
    audit_repo = AuditLogRepository(db)
    metrics = await audit_repo.get_compliance_metrics(period)
    return metrics


@router.get("/compliance/violations")
async def get_compliance_violations(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    severity: Optional[str] = None,
    resolved: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get compliance violations."""
    audit_repo = AuditLogRepository(db)
    
    filters = {}
    if start_date:
        filters["start_date"] = start_date
    if end_date:
        filters["end_date"] = end_date
    if severity:
        filters["severity"] = severity
    if resolved is not None:
        filters["resolved"] = resolved
        
    violations = await audit_repo.get_compliance_violations(
        skip=skip, 
        limit=limit, 
        filters=filters
    )
    return violations


@router.get("/statistics")
async def get_audit_statistics(
    period: str = "30d",
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get audit and compliance statistics."""
    audit_repo = AuditLogRepository(db)
    form_repo = FormSubmissionRepository(db)
    retention_repo = DataRetentionPolicyRepository(db)
    
    stats = {
        "audit_logs": await audit_repo.get_statistics(period),
        "form_submissions": await form_repo.get_statistics(period),
        "retention_policies": await retention_repo.get_statistics()
    }
    
    return stats
