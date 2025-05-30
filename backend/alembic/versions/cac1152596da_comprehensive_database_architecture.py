"""comprehensive_database_architecture

Revision ID: cac1152596da
Revises: 
Create Date: 2025-05-30 17:52:03.650966

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'cac1152596da'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
    op.execute("CREATE EXTENSION IF NOT EXISTS \"pg_trgm\"")
    op.execute("CREATE EXTENSION IF NOT EXISTS \"btree_gin\"")
    
    # =================== CORE BUSINESS TABLES ===================
    
    # Companies
    op.create_table(
        'companies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('slug', sa.String(100), nullable=False, unique=True),
        sa.Column('legal_name', sa.String(255), nullable=True),
        sa.Column('tax_id', sa.String(50), nullable=True),
        sa.Column('registration_number', sa.String(100), nullable=True),
        sa.Column('cnpj', sa.String(18), nullable=True, unique=True),
        
        # Contact info
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('website', sa.String(255), nullable=True),
        
        # Address
        sa.Column('address_line1', sa.String(255), nullable=True),
        sa.Column('address_line2', sa.String(255), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('state', sa.String(100), nullable=True),
        sa.Column('postal_code', sa.String(20), nullable=True),
        sa.Column('country', sa.String(100), nullable=True),
        
        # Business info
        sa.Column('industry', sa.String(100), nullable=True),
        sa.Column('company_size', sa.String(50), nullable=True),
        sa.Column('founded_year', sa.Integer, nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('logo_url', sa.String(500), nullable=True),
        
        # Plan configurations
        sa.Column('plan_type', sa.String(50), nullable=False, server_default='BASIC'),
        sa.Column('max_users', sa.Integer, nullable=False, server_default='5'),
        sa.Column('max_storage_gb', sa.Integer, nullable=False, server_default='10'),
        sa.Column('features', postgresql.JSONB, nullable=True, server_default='{}'),
        
        # Business configurations
        sa.Column('business_hours', postgresql.JSONB, nullable=True, server_default='{}'),
        sa.Column('timezone', sa.String(50), nullable=False, server_default='America/Sao_Paulo'),
        
        # Status and hierarchy
        sa.Column('status', sa.String(20), nullable=False, server_default='ACTIVE'),
        sa.Column('parent_company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        
        # Indexes
        sa.Index('idx_companies_name_active', 'name', 'status'),
        sa.Index('idx_companies_cnpj', 'cnpj'),
        sa.Index('idx_companies_slug', 'slug'),
        sa.Index('idx_companies_parent', 'parent_company_id'),
        sa.Index('idx_companies_plan', 'plan_type', 'status'),
    )
    
    # Users
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        
        # Basic user data
        sa.Column('email', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        
        # Role and permissions
        sa.Column('role', sa.String(20), nullable=False, server_default='USER'),
        sa.Column('permissions', postgresql.JSONB, nullable=True, server_default='{}'),
        
        # Status and control
        sa.Column('status', sa.String(20), nullable=False, server_default='ACTIVE'),
        sa.Column('email_verified', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('must_change_password', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean, nullable=False, server_default='false'),
        
        # Security
        sa.Column('failed_login_attempts', sa.Integer, nullable=False, server_default='0'),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('password_changed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        
        # Contact info
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('timezone', sa.String(50), nullable=False, server_default='UTC'),
        sa.Column('language', sa.String(10), nullable=False, server_default='en'),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        
        # Indexes
        sa.Index('idx_users_company', 'company_id'),
        sa.Index('idx_users_email', 'email'),
        sa.Index('idx_users_status', 'status', 'is_active'),
        sa.Index('idx_users_login', 'email', 'status'),
        sa.UniqueConstraint('company_id', 'email', name='uq_users_company_email'),
    )
    
    # User Profiles
    op.create_table(
        'user_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        
        # Personal information
        sa.Column('bio', sa.Text, nullable=True),
        sa.Column('department', sa.String(100), nullable=True),
        sa.Column('position', sa.String(100), nullable=True),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('birth_date', sa.Date, nullable=True),
        
        # System preferences
        sa.Column('theme', sa.String(20), nullable=False, server_default='light'),
        sa.Column('notifications_email', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('notifications_push', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('notifications_desktop', sa.Boolean, nullable=False, server_default='true'),
        
        # Work configurations
        sa.Column('working_hours', postgresql.JSONB, nullable=True, server_default='{}'),
        sa.Column('calendar_integration', postgresql.JSONB, nullable=True, server_default='{}'),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        
        sa.Index('idx_user_profiles_user', 'user_id'),
    )
    
    # Company Users (Association Table)
    op.create_table(
        'company_users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        
        # Role and permissions
        sa.Column('role', sa.String(50), nullable=False, server_default='USER'),
        sa.Column('permissions', postgresql.JSONB, nullable=True, server_default='{}'),
        
        # Status
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('invited_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('invited_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        
        # Constraints and indexes
        sa.UniqueConstraint('company_id', 'user_id', name='uq_company_users_unique'),
        sa.Index('idx_company_users_role', 'company_id', 'role'),
        sa.Index('idx_company_users_active', 'company_id', 'is_active'),
    )
    
    # =================== SESSION MANAGEMENT ===================
    
    # User Sessions (Advanced API Temporal)
    op.create_table(
        'user_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        
        # Token and identification
        sa.Column('token_hash', sa.String(255), nullable=False, index=True),
        sa.Column('refresh_token_hash', sa.String(255), nullable=True),
        sa.Column('device_fingerprint', sa.String(255), nullable=True),
        
        # Session information
        sa.Column('ip_address', postgresql.INET, nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('device_type', sa.String(20), nullable=True),
        sa.Column('os_info', sa.String(100), nullable=True),
        sa.Column('browser_info', sa.String(100), nullable=True),
        sa.Column('location_data', postgresql.JSONB, nullable=True, server_default='{}'),
        
        # Advanced temporal control
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_activity', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('max_idle_minutes', sa.Integer, nullable=False, server_default='30'),
        sa.Column('auto_renew', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('renewal_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('max_renewals', sa.Integer, nullable=False, server_default='100'),
        
        # Activity control
        sa.Column('activity_score', sa.Integer, nullable=False, server_default='100'),
        sa.Column('suspicious_activity', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('failed_requests', sa.Integer, nullable=False, server_default='0'),
        
        # Status
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('force_logout', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('logout_reason', sa.String(100), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('last_renewed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        
        # Indexes for performance
        sa.Index('idx_user_sessions_user_id', 'user_id'),
        sa.Index('idx_user_sessions_token', 'token_hash'),
        sa.Index('idx_user_sessions_active', 'is_active', 'expires_at'),
        sa.Index('idx_user_sessions_activity', 'last_activity'),
        sa.Index('idx_user_sessions_device', 'device_fingerprint'),
    )
    
    # Session Activities
    op.create_table(
        'session_activities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user_sessions.id', ondelete='CASCADE'), nullable=False),
        
        # Activity details
        sa.Column('activity_type', sa.String(50), nullable=False),
        sa.Column('endpoint', sa.String(255), nullable=True),
        sa.Column('method', sa.String(10), nullable=True),
        
        # Metrics
        sa.Column('response_time_ms', sa.Integer, nullable=True),
        sa.Column('status_code', sa.Integer, nullable=True),
        sa.Column('bytes_transferred', sa.BigInteger, nullable=False, server_default='0'),
        
        # Context
        sa.Column('referrer', sa.String(500), nullable=True),
        sa.Column('user_agent_changes', sa.Boolean, nullable=False, server_default='false'),
        
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        
        # Indexes
        sa.Index('idx_session_activities_session', 'session_id'),
        sa.Index('idx_session_activities_created', 'created_at'),
        sa.Index('idx_session_activities_type', 'activity_type'),
    )
    
    # =================== DOCUMENT & AI SYSTEM ===================
    
    # Documents
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        
        # File information
        sa.Column('filename', sa.String(500), nullable=False),
        sa.Column('file_path', sa.String(1000), nullable=False),
        sa.Column('file_size', sa.BigInteger, nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('file_hash', sa.String(128), nullable=False, unique=True),
        
        # Document metadata
        sa.Column('document_type', sa.String(50), nullable=True),
        sa.Column('language', sa.String(10), nullable=False, server_default='pt-BR'),
        sa.Column('page_count', sa.Integer, nullable=True),
        sa.Column('doc_metadata', postgresql.JSONB, nullable=True, server_default='{}'),
        
        # Processing status
        sa.Column('processing_status', sa.String(20), nullable=False, server_default='PENDING'),
        sa.Column('ai_confidence_score', sa.Numeric(5, 4), nullable=True),
        
        # Quality analysis
        sa.Column('quality_score', sa.Integer, nullable=False, server_default='0'),
        sa.Column('has_text', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('needs_ocr', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_searchable', sa.Boolean, nullable=False, server_default='false'),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('processing_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        
        # Indexes
        sa.Index('idx_documents_company', 'company_id'),
        sa.Index('idx_documents_user', 'uploaded_by'),
        sa.Index('idx_documents_status', 'processing_status'),
        sa.Index('idx_documents_hash', 'file_hash'),
        sa.Index('idx_documents_type', 'document_type'),
        sa.Index('idx_documents_searchable', 'is_searchable'),
    )
    
    # AI Processing Jobs
    op.create_table(
        'ai_processing_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        
        # Job configuration
        sa.Column('job_type', sa.String(50), nullable=False),
        sa.Column('ai_model', sa.String(100), nullable=False),
        sa.Column('prompt_template', sa.String(100), nullable=True),
        
        # Processing parameters
        sa.Column('job_parameters', postgresql.JSONB, nullable=True, server_default='{}'),
        sa.Column('priority', sa.Integer, nullable=False, server_default='5'),
        
        # Celery integration
        sa.Column('celery_task_id', sa.String(255), nullable=True, unique=True),
        sa.Column('celery_status', sa.String(20), nullable=True),
        
        # Status and results
        sa.Column('status', sa.String(20), nullable=False, server_default='PENDING'),
        sa.Column('progress_percentage', sa.Integer, nullable=False, server_default='0'),
        sa.Column('result_data', postgresql.JSONB, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('retry_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('max_retries', sa.Integer, nullable=False, server_default='3'),
        
        # Performance metrics
        sa.Column('processing_time_seconds', sa.Integer, nullable=True),
        sa.Column('tokens_used', sa.Integer, nullable=True),
        sa.Column('cost_estimate', sa.Numeric(10, 4), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        
        # Indexes
        sa.Index('idx_ai_jobs_document', 'document_id'),
        sa.Index('idx_ai_jobs_status', 'status'),
        sa.Index('idx_ai_jobs_celery', 'celery_task_id'),
        sa.Index('idx_ai_jobs_type', 'job_type'),
        sa.Index('idx_ai_jobs_priority', 'priority', 'created_at'),
    )
    
    # AI Prompt Templates
    op.create_table(
        'ai_prompt_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        
        # Template info
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('template_type', sa.String(50), nullable=False),
        sa.Column('ai_model', sa.String(100), nullable=False),
        
        # Prompt content
        sa.Column('system_prompt', sa.Text, nullable=True),
        sa.Column('user_prompt_template', sa.Text, nullable=False),
        sa.Column('example_inputs', postgresql.JSONB, nullable=True, server_default='{}'),
        sa.Column('example_outputs', postgresql.JSONB, nullable=True, server_default='{}'),
        
        # Configuration
        sa.Column('parameters', postgresql.JSONB, nullable=True, server_default='{}'),
        sa.Column('validation_rules', postgresql.JSONB, nullable=True, server_default='{}'),
        
        # Usage tracking
        sa.Column('usage_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('success_rate', sa.Numeric(5, 4), nullable=True),
        sa.Column('avg_processing_time', sa.Integer, nullable=True),
        
        # Status
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('is_public', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        
        # Indexes
        sa.Index('idx_ai_templates_company', 'company_id'),
        sa.Index('idx_ai_templates_type', 'template_type'),
        sa.Index('idx_ai_templates_active', 'is_active', 'is_public'),
        sa.Index('idx_ai_templates_usage', 'usage_count'),
    )
    
    # Text Extractions
    op.create_table(
        'text_extractions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('ai_job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('ai_processing_jobs.id', ondelete='CASCADE'), nullable=False),
        
        # Extracted content
        sa.Column('extracted_text', sa.Text, nullable=False),
        sa.Column('extraction_method', sa.String(50), nullable=False),
        sa.Column('confidence_score', sa.Numeric(5, 4), nullable=True),
        
        # Structure analysis
        sa.Column('text_structure', postgresql.JSONB, nullable=True, server_default='{}'),
        sa.Column('detected_language', sa.String(10), nullable=True),
        sa.Column('word_count', sa.Integer, nullable=True),
        sa.Column('character_count', sa.Integer, nullable=True),
        
        # Quality metrics
        sa.Column('quality_indicators', postgresql.JSONB, nullable=True, server_default='{}'),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        
        sa.Index('idx_text_extractions_job', 'ai_job_id'),
        sa.Index('idx_text_extractions_method', 'extraction_method'),
        sa.Index('idx_text_extractions_language', 'detected_language'),
    )
    
    # Continue with the rest of the tables...
    # This is getting quite long, so I'll create this in parts


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('text_extractions')
    op.drop_table('ai_prompt_templates')
    op.drop_table('ai_processing_jobs')
    op.drop_table('documents')
    op.drop_table('session_activities')
    op.drop_table('user_sessions')
    op.drop_table('company_users')
    op.drop_table('user_profiles')
    op.drop_table('users')
    op.drop_table('companies')
