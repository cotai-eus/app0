"""
Forms repository for database operations.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import and_, or_, select, update, delete, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domains.forms.models import Form, FormField, FormAnalytics, FormStatus
from app.shared.common.base_repository import BaseRepository


class FormRepository(BaseRepository[Form]):
    """Repository for form operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Form, session)
    
    async def get_by_company(
        self, 
        company_id: UUID, 
        status: Optional[FormStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Form]:
        """Get forms by company with optional status filter."""
        query = select(Form).where(
            and_(
                Form.company_id == company_id,
                Form.deleted_at.is_(None)
            )
        )
        
        if status:
            query = query.where(Form.status == status)
            
        query = query.options(selectinload(Form.fields)).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_with_fields(self, form_id: UUID) -> Optional[Form]:
        """Get form with all fields loaded."""
        result = await self.session.execute(
            select(Form)
            .options(selectinload(Form.fields))
            .where(
                and_(
                    Form.id == form_id,
                    Form.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_active_forms(self, company_id: UUID) -> List[Form]:
        """Get all active forms for a company."""
        result = await self.session.execute(
            select(Form)
            .options(selectinload(Form.fields))
            .where(
                and_(
                    Form.company_id == company_id,
                    Form.status == FormStatus.ACTIVE,
                    Form.deleted_at.is_(None)
                )
            )
        )
        return result.scalars().all()
    
    async def get_public_forms(self) -> List[Form]:
        """Get all public active forms."""
        result = await self.session.execute(
            select(Form)
            .options(selectinload(Form.fields))
            .where(
                and_(
                    Form.is_public == True,
                    Form.status == FormStatus.ACTIVE,
                    Form.deleted_at.is_(None)
                )
            )
        )
        return result.scalars().all()
    
    async def count_by_company(self, company_id: UUID, status: Optional[FormStatus] = None) -> int:
        """Count forms by company with optional status filter."""
        query = select(func.count(Form.id)).where(
            and_(
                Form.company_id == company_id,
                Form.deleted_at.is_(None)
            )
        )
        
        if status:
            query = query.where(Form.status == status)
            
        result = await self.session.execute(query)
        return result.scalar() or 0


class FormFieldRepository(BaseRepository[FormField]):
    """Repository for form field operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(FormField, session)
    
    async def get_by_form(self, form_id: UUID, ordered: bool = True) -> List[FormField]:
        """Get fields by form, optionally ordered."""
        query = select(FormField).where(
            and_(
                FormField.form_id == form_id,
                FormField.deleted_at.is_(None)
            )
        )
        
        if ordered:
            query = query.order_by(FormField.order)
            
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def reorder_fields(self, form_id: UUID, field_orders: List[Dict[str, Any]]) -> None:
        """Reorder fields for a form."""
        for field_order in field_orders:
            await self.session.execute(
                update(FormField)
                .where(
                    and_(
                        FormField.id == field_order["field_id"],
                        FormField.form_id == form_id
                    )
                )
                .values(order=field_order["order"])
            )
    
    async def bulk_delete(self, field_ids: List[UUID]) -> None:
        """Soft delete multiple fields."""
        await self.session.execute(
            update(FormField)
            .where(FormField.id.in_(field_ids))
            .values(deleted_at=datetime.utcnow())        )


# FormSubmissionRepository moved to audit domain for compliance tracking
# All FormSubmission-related operations now handled in app.domains.audit

class FormAnalyticsRepository(BaseRepository[FormAnalytics]):
    """Repository for form analytics operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(FormAnalytics, session)
    
    async def get_by_form_and_date_range(
        self, 
        form_id: UUID,
        date_from: datetime,
        date_to: datetime
    ) -> List[FormAnalytics]:
        """Get analytics for a form within date range."""
        result = await self.session.execute(
            select(FormAnalytics)
            .where(
                and_(
                    FormAnalytics.form_id == form_id,
                    FormAnalytics.date >= date_from,
                    FormAnalytics.date <= date_to,
                    FormAnalytics.deleted_at.is_(None)
                )
            )
            .order_by(FormAnalytics.date)
        )
        return result.scalars().all()
    
    async def get_or_create_for_date(
        self, 
        form_id: UUID, 
        date: datetime
    ) -> FormAnalytics:
        """Get or create analytics record for specific date."""
        # Normalize date to start of day
        date_normalized = date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        result = await self.session.execute(
            select(FormAnalytics)
            .where(
                and_(
                    FormAnalytics.form_id == form_id,
                    FormAnalytics.date == date_normalized,
                    FormAnalytics.deleted_at.is_(None)
                )
            )
        )
        
        analytics = result.scalar_one_or_none()
        
        if not analytics:
            analytics = FormAnalytics(
                form_id=form_id,
                date=date_normalized
            )
            self.session.add(analytics)
            await self.session.flush()
        
        return analytics
    
    async def increment_views(self, form_id: UUID, date: datetime) -> None:
        """Increment view count for a form on specific date."""
        analytics = await self.get_or_create_for_date(form_id, date)
        analytics.views += 1
    
    async def increment_submissions(self, form_id: UUID, date: datetime) -> None:
        """Increment submission count for a form on specific date."""
        analytics = await self.get_or_create_for_date(form_id, date)
        analytics.submissions += 1
    
    async def increment_completions(self, form_id: UUID, date: datetime) -> None:
        """Increment completion count for a form on specific date."""
        analytics = await self.get_or_create_for_date(form_id, date)
        analytics.completions += 1
    
    async def increment_abandons(self, form_id: UUID, date: datetime) -> None:
        """Increment abandon count for a form on specific date."""
        analytics = await self.get_or_create_for_date(form_id, date)
        analytics.abandons += 1
    
    async def update_avg_completion_time(
        self, 
        form_id: UUID, 
        date: datetime, 
        completion_time: int
    ) -> None:
        """Update average completion time for a form."""
        analytics = await self.get_or_create_for_date(form_id, date)
        
        if analytics.avg_completion_time is None:
            analytics.avg_completion_time = completion_time
        else:
            # Calculate running average
            total_completions = analytics.completions or 1
            current_total = analytics.avg_completion_time * (total_completions - 1)
            analytics.avg_completion_time = int((current_total + completion_time) / total_completions)
    
    async def get_form_summary(self, form_id: UUID, days: int = 30) -> Dict[str, Any]:
        """Get summary analytics for a form over specified days."""
        date_from = datetime.utcnow() - timedelta(days=days)
        date_to = datetime.utcnow()
        
        analytics_data = await self.get_by_form_and_date_range(form_id, date_from, date_to)
        
        total_views = sum(a.views for a in analytics_data)
        total_submissions = sum(a.submissions for a in analytics_data)
        total_completions = sum(a.completions for a in analytics_data)
        total_abandons = sum(a.abandons for a in analytics_data)
        
        conversion_rate = (total_submissions / total_views * 100) if total_views > 0 else 0
        completion_rate = (total_completions / total_submissions * 100) if total_submissions > 0 else 0
        abandon_rate = (total_abandons / total_views * 100) if total_views > 0 else 0
        
        avg_completion_times = [a.avg_completion_time for a in analytics_data if a.avg_completion_time is not None]
        avg_completion_time = sum(avg_completion_times) / len(avg_completion_times) if avg_completion_times else None
        
        return {
            'period_days': days,
            'total_views': total_views,
            'total_submissions': total_submissions,
            'total_completions': total_completions,
            'total_abandons': total_abandons,
            'conversion_rate': round(conversion_rate, 2),
            'completion_rate': round(completion_rate, 2),
            'abandon_rate': round(abandon_rate, 2),
            'avg_completion_time': avg_completion_time,
            'daily_data': [
                {
                    'date': a.date.isoformat(),
                    'views': a.views,
                    'submissions': a.submissions,
                    'completions': a.completions,
                    'abandons': a.abandons,
                    'avg_completion_time': a.avg_completion_time
                }
                for a in analytics_data
            ]
        }
