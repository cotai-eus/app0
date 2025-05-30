"""
Audit and compliance repositories for logging, form management, and data retention.
Based on the database architecture plan.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import desc, asc, func, and_, or_, text
from sqlalchemy.orm import Session, joinedload

from app.shared.common.repository import BaseRepository
from app.core.exceptions import NotFoundError, ValidationError
from .models import (
    AuditLog, FormTemplate, FormSubmission, DataRetentionPolicy,
    AuditEventType, AuditSeverity, SubmissionStatus
)


class AuditLogRepository(BaseRepository[AuditLog]):
    """Repository for comprehensive audit logging and compliance tracking."""
    
    def __init__(self, db: Session):
        super().__init__(db, AuditLog)
    
    def log_event(
        self,
        event_type: AuditEventType,
        description: str,
        user_id: Optional[str] = None,
        company_id: Optional[str] = None,
        severity: AuditSeverity = AuditSeverity.LOW,
        **kwargs
    ) -> AuditLog:
        """Log an audit event."""
        audit_log = AuditLog(
            event_type=event_type,
            description=description,
            user_id=user_id,
            company_id=company_id,
            severity=severity,
            **kwargs
        )
        return self.create(audit_log)
    
    def log_user_action(
        self,
        user_id: str,
        company_id: str,
        event_type: AuditEventType,
        description: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        old_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None,
        request_context: Optional[Dict] = None,
        **kwargs
    ) -> AuditLog:
        """Log a user action with full context."""
        audit_data = {
            'user_id': user_id,
            'company_id': company_id,
            'event_type': event_type,
            'description': description,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'old_values': old_values,
            'new_values': new_values,
            **kwargs
        }
        
        if request_context:
            audit_data.update({
                'ip_address': request_context.get('ip_address'),
                'user_agent': request_context.get('user_agent'),
                'request_id': request_context.get('request_id'),
                'endpoint': request_context.get('endpoint'),
                'method': request_context.get('method'),
                'session_id': request_context.get('session_id')
            })
        
        # Identify changed fields
        if old_values and new_values:
            changed_fields = []
            for key, new_value in new_values.items():
                if key in old_values and old_values[key] != new_value:
                    changed_fields.append(key)
            audit_data['changed_fields'] = changed_fields
        
        return self.log_event(**audit_data)
    
    def log_security_event(
        self,
        description: str,
        severity: AuditSeverity,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict] = None,
        **kwargs
    ) -> AuditLog:
        """Log a security-related event."""
        return self.log_event(
            event_type=AuditEventType.LOGIN,  # Could be more specific
            description=description,
            severity=severity,
            user_id=user_id,
            ip_address=ip_address,
            details=details,
            event_category="Security",
            **kwargs
        )
    
    def get_user_activity(
        self,
        user_id: str,
        company_id: Optional[str] = None,
        hours: int = 24,
        event_types: Optional[List[AuditEventType]] = None
    ) -> List[AuditLog]:
        """Get user activity within specified timeframe."""
        since = datetime.utcnow() - timedelta(hours=hours)
        
        query = self.db.query(AuditLog).filter(
            AuditLog.user_id == user_id,
            AuditLog.created_at >= since
        )
        
        if company_id:
            query = query.filter(AuditLog.company_id == company_id)
        
        if event_types:
            query = query.filter(AuditLog.event_type.in_(event_types))
        
        return query.order_by(desc(AuditLog.created_at)).all()
    
    def get_resource_history(
        self,
        resource_type: str,
        resource_id: str,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit history for a specific resource."""
        return self.db.query(AuditLog).filter(
            AuditLog.resource_type == resource_type,
            AuditLog.resource_id == resource_id
        ).order_by(desc(AuditLog.created_at)).limit(limit).all()
    
    def get_security_events(
        self,
        company_id: Optional[str] = None,
        severity: Optional[AuditSeverity] = None,
        hours: int = 24
    ) -> List[AuditLog]:
        """Get security events within specified timeframe."""
        since = datetime.utcnow() - timedelta(hours=hours)
        
        query = self.db.query(AuditLog).filter(
            AuditLog.created_at >= since,
            AuditLog.event_category == "Security"
        )
        
        if company_id:
            query = query.filter(AuditLog.company_id == company_id)
        
        if severity:
            query = query.filter(AuditLog.severity == severity)
        
        return query.order_by(desc(AuditLog.created_at)).all()
    
    def get_failed_login_attempts(
        self,
        ip_address: Optional[str] = None,
        user_email: Optional[str] = None,
        hours: int = 1
    ) -> List[AuditLog]:
        """Get failed login attempts."""
        since = datetime.utcnow() - timedelta(hours=hours)
        
        query = self.db.query(AuditLog).filter(
            AuditLog.created_at >= since,
            AuditLog.event_type == AuditEventType.LOGIN,
            AuditLog.is_error == True
        )
        
        if ip_address:
            query = query.filter(AuditLog.ip_address == ip_address)
        
        if user_email:
            query = query.filter(AuditLog.user_email == user_email)
        
        return query.order_by(desc(AuditLog.created_at)).all()
    
    def get_compliance_report(
        self,
        company_id: str,
        start_date: datetime,
        end_date: datetime,
        compliance_tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate compliance report."""
        query = self.db.query(AuditLog).filter(
            AuditLog.company_id == company_id,
            AuditLog.created_at >= start_date,
            AuditLog.created_at <= end_date
        )
        
        if compliance_tags:
            query = query.filter(
                AuditLog.compliance_tags.overlap(compliance_tags)
            )
        
        total_events = query.count()
        
        # Event type distribution
        event_types = self.db.query(
            AuditLog.event_type,
            func.count(AuditLog.id).label('count')
        ).filter(
            AuditLog.company_id == company_id,
            AuditLog.created_at >= start_date,
            AuditLog.created_at <= end_date
        ).group_by(AuditLog.event_type).all()
        
        # Severity distribution
        severity_dist = self.db.query(
            AuditLog.severity,
            func.count(AuditLog.id).label('count')
        ).filter(
            AuditLog.company_id == company_id,
            AuditLog.created_at >= start_date,
            AuditLog.created_at <= end_date
        ).group_by(AuditLog.severity).all()
        
        # Top users by activity
        top_users = self.db.query(
            AuditLog.user_id,
            AuditLog.user_email,
            func.count(AuditLog.id).label('activity_count')
        ).filter(
            AuditLog.company_id == company_id,
            AuditLog.created_at >= start_date,
            AuditLog.created_at <= end_date,
            AuditLog.user_id.is_not(None)
        ).group_by(
            AuditLog.user_id, AuditLog.user_email
        ).order_by(desc('activity_count')).limit(10).all()
        
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'total_events': total_events,
            'event_types': {et.event_type: et.count for et in event_types},
            'severity_distribution': {sd.severity: sd.count for sd in severity_dist},
            'top_users': [
                {
                    'user_id': user.user_id,
                    'user_email': user.user_email,
                    'activity_count': user.activity_count
                }
                for user in top_users
            ]
        }
    
    def search_audit_logs(
        self,
        company_id: Optional[str] = None,
        user_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        resource_type: Optional[str] = None,
        ip_address: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        search_text: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[AuditLog], int]:
        """Search audit logs with various filters."""
        query = self.db.query(AuditLog)
        
        if company_id:
            query = query.filter(AuditLog.company_id == company_id)
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        
        if event_type:
            query = query.filter(AuditLog.event_type == event_type)
        
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        
        if ip_address:
            query = query.filter(AuditLog.ip_address == ip_address)
        
        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)
        
        if search_text:
            query = query.filter(
                or_(
                    AuditLog.description.ilike(f'%{search_text}%'),
                    AuditLog.resource_name.ilike(f'%{search_text}%')
                )
            )
        
        total_count = query.count()
        results = query.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit).all()
        
        return results, total_count


class FormTemplateRepository(BaseRepository[FormTemplate]):
    """Repository for dynamic form template management."""
    
    def __init__(self, db: Session):
        super().__init__(db, FormTemplate)
    
    def create_template(
        self,
        name: str,
        slug: str,
        form_schema: Dict,
        created_by: str,
        company_id: str,
        **kwargs
    ) -> FormTemplate:
        """Create a new form template."""
        template = FormTemplate(
            name=name,
            slug=slug,
            form_schema=form_schema,
            created_by=created_by,
            company_id=company_id,
            **kwargs
        )
        return self.create(template)
    
    def get_by_slug(
        self,
        slug: str,
        company_id: Optional[str] = None
    ) -> Optional[FormTemplate]:
        """Get form template by slug."""
        query = self.db.query(FormTemplate).filter(
            FormTemplate.slug == slug
        )
        
        if company_id:
            query = query.filter(
                or_(
                    FormTemplate.company_id == company_id,
                    FormTemplate.is_public == True
                )
            )
        
        return query.first()
    
    def get_published_templates(
        self,
        company_id: Optional[str] = None,
        include_public: bool = True
    ) -> List[FormTemplate]:
        """Get published form templates."""
        from app.domains.forms.models import FormStatus
        
        query = self.db.query(FormTemplate).filter(
            FormTemplate.status == FormStatus.PUBLISHED
        )
        
        if company_id:
            filters = [FormTemplate.company_id == company_id]
            if include_public:
                filters.append(FormTemplate.is_public == True)
            query = query.filter(or_(*filters))
        
        return query.order_by(FormTemplate.name).all()
    
    def get_company_templates(
        self,
        company_id: str,
        status: Optional[str] = None
    ) -> List[FormTemplate]:
        """Get form templates for a company."""
        query = self.db.query(FormTemplate).filter(
            FormTemplate.company_id == company_id
        )
        
        if status:
            query = query.filter(FormTemplate.status == status)
        
        return query.order_by(FormTemplate.name).all()
    
    def increment_submission_count(self, template_id: str) -> bool:
        """Increment submission count for a template."""
        template = self.get_by_id(template_id)
        if not template:
            return False
        
        template.submission_count += 1
        self.db.commit()
        return True
    
    def update_analytics(
        self,
        template_id: str,
        completion_rate: Optional[int] = None,
        avg_completion_time: Optional[int] = None
    ) -> bool:
        """Update template analytics."""
        template = self.get_by_id(template_id)
        if not template:
            return False
        
        if completion_rate is not None:
            template.completion_rate = completion_rate
        
        if avg_completion_time is not None:
            template.avg_completion_time_minutes = avg_completion_time
        
        self.db.commit()
        return True
    
    def check_access_permission(
        self,
        template_id: str,
        user_id: str,
        user_role: str,
        company_id: str
    ) -> bool:
        """Check if user has access to form template."""
        template = self.get_by_id(template_id)
        if not template:
            return False
        
        # Public templates are accessible to all
        if template.is_public:
            return True
        
        # Company templates are accessible to company members
        if template.company_id == company_id:
            # Check role restrictions
            if template.allowed_roles and user_role not in template.allowed_roles:
                return False
            
            # Check specific user restrictions
            if template.allowed_users and user_id not in template.allowed_users:
                return False
            
            return True
        
        return False
    
    def get_template_statistics(self, template_id: str) -> Dict[str, Any]:
        """Get statistics for a form template."""
        template = self.get_by_id(template_id)
        if not template:
            return {}
        
        # Get submission statistics
        submission_stats = self.db.query(
            func.count(FormSubmission.id).label('total_submissions'),
            func.count(
                func.nullif(FormSubmission.status != SubmissionStatus.DRAFT, False)
            ).label('completed_submissions'),
            func.avg(FormSubmission.completion_time_minutes).label('avg_completion_time')
        ).filter(
            FormSubmission.form_template_id == template_id
        ).first()
        
        # Status distribution
        status_distribution = self.db.query(
            FormSubmission.status,
            func.count(FormSubmission.id).label('count')
        ).filter(
            FormSubmission.form_template_id == template_id
        ).group_by(FormSubmission.status).all()
        
        return {
            'template_info': {
                'id': str(template.id),
                'name': template.name,
                'status': template.status,
                'created_at': template.created_at.isoformat()
            },
            'submissions': {
                'total': submission_stats.total_submissions or 0,
                'completed': submission_stats.completed_submissions or 0,
                'completion_rate': template.completion_rate or 0,
                'avg_completion_time_minutes': float(submission_stats.avg_completion_time or 0)
            },
            'status_distribution': {
                status.status: status.count for status in status_distribution
            }
        }


class FormSubmissionRepository(BaseRepository[FormSubmission]):
    """Repository for form submission management and tracking."""
    
    def __init__(self, db: Session):
        super().__init__(db, FormSubmission)
    
    def create_submission(
        self,
        form_template_id: str,
        form_data: Dict,
        created_by: Optional[str] = None,
        company_id: Optional[str] = None,
        **kwargs
    ) -> FormSubmission:
        """Create a new form submission."""
        submission = FormSubmission(
            form_template_id=form_template_id,
            form_data=form_data,
            created_by=created_by,
            company_id=company_id,
            started_at=datetime.utcnow(),
            **kwargs
        )
        return self.create(submission)
    
    def submit_form(
        self,
        submission_id: str,
        completion_time_minutes: Optional[int] = None
    ) -> bool:
        """Mark a form submission as submitted."""
        submission = self.get_by_id(submission_id)
        if not submission:
            return False
        
        submission.status = SubmissionStatus.SUBMITTED
        submission.submitted_at = datetime.utcnow()
        
        if completion_time_minutes:
            submission.completion_time_minutes = completion_time_minutes
        elif submission.started_at:
            time_diff = datetime.utcnow() - submission.started_at
            submission.completion_time_minutes = int(time_diff.total_seconds() / 60)
        
        self.db.commit()
        return True
    
    def get_template_submissions(
        self,
        form_template_id: str,
        status: Optional[SubmissionStatus] = None,
        limit: int = 100
    ) -> List[FormSubmission]:
        """Get submissions for a form template."""
        query = self.db.query(FormSubmission).filter(
            FormSubmission.form_template_id == form_template_id
        )
        
        if status:
            query = query.filter(FormSubmission.status == status)
        
        return query.order_by(desc(FormSubmission.created_at)).limit(limit).all()
    
    def get_user_submissions(
        self,
        user_id: str,
        company_id: Optional[str] = None,
        status: Optional[SubmissionStatus] = None
    ) -> List[FormSubmission]:
        """Get submissions by a user."""
        query = self.db.query(FormSubmission).filter(
            FormSubmission.created_by == user_id
        )
        
        if company_id:
            query = query.filter(FormSubmission.company_id == company_id)
        
        if status:
            query = query.filter(FormSubmission.status == status)
        
        return query.order_by(desc(FormSubmission.created_at)).all()
    
    def update_review_status(
        self,
        submission_id: str,
        status: SubmissionStatus,
        reviewed_by: str,
        review_notes: Optional[str] = None
    ) -> bool:
        """Update submission review status."""
        submission = self.get_by_id(submission_id)
        if not submission:
            return False
        
        submission.status = status
        submission.reviewed_by = reviewed_by
        submission.reviewed_at = datetime.utcnow()
        if review_notes:
            submission.review_notes = review_notes
        
        # Add to approval history
        approval_entry = {
            'reviewer_id': reviewed_by,
            'status': status,
            'timestamp': datetime.utcnow().isoformat(),
            'notes': review_notes
        }
        
        if submission.approval_history:
            submission.approval_history.append(approval_entry)
        else:
            submission.approval_history = [approval_entry]
        
        # Mark as modified for SQLAlchemy to detect JSON change
        submission.approval_history = submission.approval_history[:]
        
        self.db.commit()
        return True
    
    def get_pending_reviews(
        self,
        company_id: Optional[str] = None,
        reviewer_id: Optional[str] = None
    ) -> List[FormSubmission]:
        """Get submissions pending review."""
        query = self.db.query(FormSubmission).filter(
            FormSubmission.status == SubmissionStatus.UNDER_REVIEW
        )
        
        if company_id:
            query = query.filter(FormSubmission.company_id == company_id)
        
        if reviewer_id:
            query = query.filter(FormSubmission.reviewed_by == reviewer_id)
        
        return query.order_by(FormSubmission.submitted_at).all()
    
    def search_submissions(
        self,
        form_template_id: Optional[str] = None,
        company_id: Optional[str] = None,
        status: Optional[SubmissionStatus] = None,
        submitter_email: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[FormSubmission], int]:
        """Search form submissions with filters."""
        query = self.db.query(FormSubmission)
        
        if form_template_id:
            query = query.filter(FormSubmission.form_template_id == form_template_id)
        
        if company_id:
            query = query.filter(FormSubmission.company_id == company_id)
        
        if status:
            query = query.filter(FormSubmission.status == status)
        
        if submitter_email:
            query = query.filter(FormSubmission.submitter_email == submitter_email)
        
        if start_date:
            query = query.filter(FormSubmission.created_at >= start_date)
        
        if end_date:
            query = query.filter(FormSubmission.created_at <= end_date)
        
        total_count = query.count()
        results = query.order_by(desc(FormSubmission.created_at)).offset(offset).limit(limit).all()
        
        return results, total_count


class DataRetentionPolicyRepository(BaseRepository[DataRetentionPolicy]):
    """Repository for data retention policy management."""
    
    def __init__(self, db: Session):
        super().__init__(db, DataRetentionPolicy)
    
    def create_policy(
        self,
        name: str,
        data_type: str,
        retention_period_days: int,
        created_by: str,
        company_id: Optional[str] = None,
        **kwargs
    ) -> DataRetentionPolicy:
        """Create a new data retention policy."""
        policy = DataRetentionPolicy(
            name=name,
            data_type=data_type,
            retention_period_days=retention_period_days,
            created_by=created_by,
            company_id=company_id,
            **kwargs
        )
        return self.create(policy)
    
    def get_active_policies(
        self,
        data_type: Optional[str] = None,
        company_id: Optional[str] = None
    ) -> List[DataRetentionPolicy]:
        """Get active retention policies."""
        query = self.db.query(DataRetentionPolicy).filter(
            DataRetentionPolicy.is_active == True
        )
        
        if data_type:
            query = query.filter(DataRetentionPolicy.data_type == data_type)
        
        if company_id:
            query = query.filter(
                or_(
                    DataRetentionPolicy.company_id == company_id,
                    DataRetentionPolicy.applies_to_all_companies == True
                )
            )
        
        return query.all()
    
    def get_due_policies(self) -> List[DataRetentionPolicy]:
        """Get policies that are due for execution."""
        now = datetime.utcnow()
        
        return self.db.query(DataRetentionPolicy).filter(
            DataRetentionPolicy.is_active == True,
            or_(
                DataRetentionPolicy.next_execution.is_(None),
                DataRetentionPolicy.next_execution <= now
            )
        ).all()
    
    def update_execution_stats(
        self,
        policy_id: str,
        records_processed: int,
        records_archived: int,
        records_deleted: int
    ) -> bool:
        """Update policy execution statistics."""
        policy = self.get_by_id(policy_id)
        if not policy:
            return False
        
        policy.last_executed = datetime.utcnow()
        policy.next_execution = datetime.utcnow() + timedelta(days=policy.execution_frequency_days)
        policy.records_processed += records_processed
        policy.records_archived += records_archived
        policy.records_deleted += records_deleted
        
        self.db.commit()
        return True
    
    def get_retention_summary(
        self,
        company_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get retention policy summary."""
        query = self.db.query(DataRetentionPolicy)
        
        if company_id:
            query = query.filter(
                or_(
                    DataRetentionPolicy.company_id == company_id,
                    DataRetentionPolicy.applies_to_all_companies == True
                )
            )
        
        policies = query.all()
        
        total_policies = len(policies)
        active_policies = sum(1 for p in policies if p.is_active)
        
        # Data type coverage
        data_types = list(set(p.data_type for p in policies))
        
        # Recent execution stats
        total_processed = sum(p.records_processed for p in policies)
        total_archived = sum(p.records_archived for p in policies)
        total_deleted = sum(p.records_deleted for p in policies)
        
        return {
            'total_policies': total_policies,
            'active_policies': active_policies,
            'covered_data_types': data_types,
            'execution_stats': {
                'total_records_processed': total_processed,
                'total_records_archived': total_archived,
                'total_records_deleted': total_deleted
            },
            'policies_needing_execution': len([
                p for p in policies 
                if p.is_active and (
                    not p.next_execution or 
                    p.next_execution <= datetime.utcnow()
                )
            ])
        }
