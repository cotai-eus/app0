-- =====================================================
-- 🐘 POSTGRESQL - ESQUEMA COMPLETO DE PRODUÇÃO
-- Criado para alta performance, integridade e extensibilidade
-- =====================================================

-- Extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- =================== RATE LIMITING & MONITORING ===================

-- Rate Limit Policies
CREATE TABLE rate_limit_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    
    -- Policy configuration
    policy_name VARCHAR(100) NOT NULL,
    endpoint_pattern VARCHAR(255) NOT NULL,
    method VARCHAR(10) DEFAULT 'ALL',
    
    -- Limits
    requests_per_minute INTEGER NOT NULL DEFAULT 60,
    requests_per_hour INTEGER NOT NULL DEFAULT 1000,
    requests_per_day INTEGER NOT NULL DEFAULT 10000,
    burst_limit INTEGER NOT NULL DEFAULT 10,
    
    -- Scope
    applies_to VARCHAR(20) NOT NULL DEFAULT 'USER', -- USER, COMPANY, IP, GLOBAL
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Configuration
    policy_config JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Indexes
    CONSTRAINT rate_limit_policies_company_name_unique UNIQUE (company_id, policy_name)
);

CREATE INDEX idx_rate_limit_policies_company ON rate_limit_policies(company_id);
CREATE INDEX idx_rate_limit_policies_endpoint ON rate_limit_policies(endpoint_pattern);
CREATE INDEX idx_rate_limit_policies_active ON rate_limit_policies(is_active);

-- Rate Limit Tracking
CREATE TABLE rate_limit_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Request identification
    endpoint VARCHAR(255) NOT NULL,
    user_id UUID REFERENCES users(id),
    ip_address INET,
    company_id UUID REFERENCES companies(id),
    
    -- Tracking data
    request_count INTEGER NOT NULL DEFAULT 1,
    window_start TIMESTAMP WITH TIME ZONE NOT NULL,
    window_end TIMESTAMP WITH TIME ZONE NOT NULL,
    rate_limit_exceeded BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    tracking_metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Indexes for performance
    CONSTRAINT rate_limit_tracking_unique UNIQUE (endpoint, user_id, ip_address, window_start)
);

CREATE INDEX idx_rate_limit_tracking_endpoint ON rate_limit_tracking(endpoint);
CREATE INDEX idx_rate_limit_tracking_user ON rate_limit_tracking(user_id);
CREATE INDEX idx_rate_limit_tracking_ip ON rate_limit_tracking(ip_address);
CREATE INDEX idx_rate_limit_tracking_window ON rate_limit_tracking(window_start, window_end);
CREATE INDEX idx_rate_limit_tracking_exceeded ON rate_limit_tracking(rate_limit_exceeded);

-- API Metrics
CREATE TABLE api_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Request info
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER NOT NULL,
    response_time_ms INTEGER NOT NULL,
    
    -- User context
    user_id UUID REFERENCES users(id),
    company_id UUID REFERENCES companies(id),
    
    -- Technical details
    request_size_bytes INTEGER,
    response_size_bytes INTEGER,
    user_agent TEXT,
    ip_address INET,
    
    -- Error tracking
    error_message TEXT,
    stack_trace TEXT,
    
    -- Business metrics
    feature_used VARCHAR(100),
    api_version VARCHAR(20),
    
    -- Metadata
    request_metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Partitioning by month for performance
CREATE INDEX idx_api_metrics_created_at ON api_metrics(created_at);
CREATE INDEX idx_api_metrics_endpoint ON api_metrics(endpoint);
CREATE INDEX idx_api_metrics_status ON api_metrics(status_code);
CREATE INDEX idx_api_metrics_user ON api_metrics(user_id);
CREATE INDEX idx_api_metrics_company ON api_metrics(company_id);
CREATE INDEX idx_api_metrics_response_time ON api_metrics(response_time_ms);

-- System Health Metrics
CREATE TABLE system_health_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Metric identification
    metric_name VARCHAR(100) NOT NULL,
    metric_type VARCHAR(50) NOT NULL, -- CPU, MEMORY, DISK, NETWORK, DATABASE
    component VARCHAR(100) NOT NULL, -- api, worker, database, redis, etc
    
    -- Values
    value NUMERIC(15,4) NOT NULL,
    threshold_warning NUMERIC(15,4),
    threshold_critical NUMERIC(15,4),
    
    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'OK', -- OK, WARNING, CRITICAL
    
    -- Context
    instance_id VARCHAR(100),
    environment VARCHAR(50) DEFAULT 'production',
    
    -- Metadata
    metric_metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_system_health_metrics_name ON system_health_metrics(metric_name);
CREATE INDEX idx_system_health_metrics_type ON system_health_metrics(metric_type);
CREATE INDEX idx_system_health_metrics_component ON system_health_metrics(component);
CREATE INDEX idx_system_health_metrics_status ON system_health_metrics(status);
CREATE INDEX idx_system_health_metrics_created ON system_health_metrics(created_at);

-- =================== FORMS SYSTEM ===================

-- Forms
CREATE TABLE forms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES users(id),
    
    -- Form details
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'DRAFT', -- DRAFT, PUBLISHED, ARCHIVED, CLOSED
    
    -- Configuration
    is_public BOOLEAN DEFAULT FALSE,
    allow_multiple_submissions BOOLEAN DEFAULT TRUE,
    submission_limit INTEGER,
    close_date TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    settings JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Indexes
    CONSTRAINT forms_company_title_unique UNIQUE (company_id, title)
);

CREATE INDEX idx_forms_company ON forms(company_id);
CREATE INDEX idx_forms_status ON forms(status);
CREATE INDEX idx_forms_public ON forms(is_public);
CREATE INDEX idx_forms_close_date ON forms(close_date);

-- Form Fields
CREATE TABLE form_fields (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    form_id UUID NOT NULL REFERENCES forms(id) ON DELETE CASCADE,
    
    -- Field configuration
    field_type VARCHAR(50) NOT NULL, -- TEXT, EMAIL, NUMBER, SELECT, CHECKBOX, etc
    name VARCHAR(100) NOT NULL,
    label VARCHAR(200) NOT NULL,
    description TEXT,
    
    -- Validation
    is_required BOOLEAN DEFAULT FALSE,
    validation_rules JSONB DEFAULT '{}',
    
    -- Options for select/radio/checkbox
    field_options JSONB DEFAULT '{}',
    
    -- Layout
    position INTEGER NOT NULL DEFAULT 0,
    width VARCHAR(20) DEFAULT 'full', -- full, half, third, quarter
    
    -- Metadata
    field_metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT form_fields_form_name_unique UNIQUE (form_id, name),
    CONSTRAINT form_fields_form_position_unique UNIQUE (form_id, position)
);

CREATE INDEX idx_form_fields_form ON form_fields(form_id);
CREATE INDEX idx_form_fields_type ON form_fields(field_type);
CREATE INDEX idx_form_fields_position ON form_fields(form_id, position);

-- =================== KANBAN SYSTEM ===================

-- Kanban Boards
CREATE TABLE kanban_boards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES users(id),
    
    -- Board details
    title VARCHAR(200) NOT NULL,
    description TEXT,
    board_type VARCHAR(20) DEFAULT 'KANBAN', -- KANBAN, SCRUM, CUSTOM
    
    -- Configuration
    is_active BOOLEAN DEFAULT TRUE,
    is_public BOOLEAN DEFAULT FALSE,
    color VARCHAR(7), -- Hex color
    
    -- Settings
    settings JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Indexes
    CONSTRAINT kanban_boards_company_title_unique UNIQUE (company_id, title)
);

CREATE INDEX idx_kanban_boards_company ON kanban_boards(company_id);
CREATE INDEX idx_kanban_boards_active ON kanban_boards(is_active);
CREATE INDEX idx_kanban_boards_public ON kanban_boards(is_public);

-- Board Columns
CREATE TABLE kanban_board_columns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    board_id UUID NOT NULL REFERENCES kanban_boards(id) ON DELETE CASCADE,
    
    -- Column details
    title VARCHAR(100) NOT NULL,
    description TEXT,
    position INTEGER NOT NULL DEFAULT 0,
    color VARCHAR(7), -- Hex color
    
    -- Configuration
    is_visible BOOLEAN DEFAULT TRUE,
    task_limit INTEGER, -- WIP limit
    default_status VARCHAR(20) DEFAULT 'TODO',
    
    -- Settings
    settings JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT kanban_columns_board_position_unique UNIQUE (board_id, position)
);

CREATE INDEX idx_kanban_columns_board ON kanban_board_columns(board_id);
CREATE INDEX idx_kanban_columns_position ON kanban_board_columns(board_id, position);

-- Kanban Tasks
CREATE TABLE kanban_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    board_id UUID NOT NULL REFERENCES kanban_boards(id) ON DELETE CASCADE,
    column_id UUID REFERENCES kanban_board_columns(id),
    
    -- Task details
    title VARCHAR(200) NOT NULL,
    description TEXT,
    priority VARCHAR(20) DEFAULT 'MEDIUM', -- LOW, MEDIUM, HIGH, URGENT
    status VARCHAR(20) DEFAULT 'TODO',
    
    -- Assignment
    assigned_to UUID REFERENCES users(id),
    created_by UUID NOT NULL REFERENCES users(id),
    
    -- Dates
    due_date TIMESTAMP WITH TIME ZONE,
    start_date TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Position in column
    position INTEGER NOT NULL DEFAULT 0,
    
    -- Metadata
    tags TEXT[] DEFAULT '{}',
    labels JSONB DEFAULT '{}',
    task_metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT kanban_tasks_column_position_unique UNIQUE (column_id, position)
);

CREATE INDEX idx_kanban_tasks_board ON kanban_tasks(board_id);
CREATE INDEX idx_kanban_tasks_column ON kanban_tasks(column_id);
CREATE INDEX idx_kanban_tasks_assigned ON kanban_tasks(assigned_to);
CREATE INDEX idx_kanban_tasks_status ON kanban_tasks(status);
CREATE INDEX idx_kanban_tasks_priority ON kanban_tasks(priority);
CREATE INDEX idx_kanban_tasks_due_date ON kanban_tasks(due_date);
CREATE INDEX idx_kanban_tasks_tags ON kanban_tasks USING GIN(tags);

-- =================== CALENDAR SYSTEM ===================

-- Calendars
CREATE TABLE calendars (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    owner_id UUID NOT NULL REFERENCES users(id),
    
    -- Calendar details
    name VARCHAR(200) NOT NULL,
    description TEXT,
    color VARCHAR(7), -- Hex color
    
    -- Configuration
    is_public BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    timezone VARCHAR(50) DEFAULT 'UTC',
    
    -- Booking settings
    allow_booking BOOLEAN DEFAULT FALSE,
    booking_lead_time_hours INTEGER DEFAULT 24,
    booking_buffer_minutes INTEGER DEFAULT 15,
    
    -- Metadata
    calendar_metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_calendars_company ON calendars(company_id);
CREATE INDEX idx_calendars_owner ON calendars(owner_id);
CREATE INDEX idx_calendars_public ON calendars(is_public);

-- Calendar Events
CREATE TABLE calendar_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    calendar_id UUID NOT NULL REFERENCES calendars(id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES users(id),
    
    -- Event details
    title VARCHAR(200) NOT NULL,
    description TEXT,
    location VARCHAR(255),
    
    -- Timing
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    all_day BOOLEAN DEFAULT FALSE,
    timezone VARCHAR(50) DEFAULT 'UTC',
    
    -- Recurrence
    is_recurring BOOLEAN DEFAULT FALSE,
    recurrence_rule TEXT, -- RFC 5545 RRULE
    recurrence_end TIMESTAMP WITH TIME ZONE,
    parent_event_id UUID REFERENCES calendar_events(id),
    
    -- Status
    status VARCHAR(20) DEFAULT 'CONFIRMED', -- TENTATIVE, CONFIRMED, CANCELLED
    visibility VARCHAR(20) DEFAULT 'PUBLIC', -- PUBLIC, PRIVATE, CONFIDENTIAL
    
    -- Online meeting
    meeting_url VARCHAR(500),
    meeting_id VARCHAR(100),
    meeting_password VARCHAR(100),
    
    -- Metadata
    event_metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_calendar_events_calendar ON calendar_events(calendar_id);
CREATE INDEX idx_calendar_events_time ON calendar_events(start_time, end_time);
CREATE INDEX idx_calendar_events_status ON calendar_events(status);
CREATE INDEX idx_calendar_events_recurring ON calendar_events(is_recurring);

-- Event Participants
CREATE TABLE calendar_event_participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL REFERENCES calendar_events(id) ON DELETE CASCADE,
    
    -- Participant info
    user_id UUID REFERENCES users(id),
    email VARCHAR(255), -- For external participants
    name VARCHAR(200),
    
    -- Response
    status VARCHAR(20) DEFAULT 'PENDING', -- PENDING, ACCEPTED, DECLINED, TENTATIVE
    response_comment TEXT,
    responded_at TIMESTAMP WITH TIME ZONE,
    
    -- Role
    role VARCHAR(20) DEFAULT 'ATTENDEE', -- ORGANIZER, ATTENDEE, OPTIONAL
    
    -- Notifications
    email_reminder_minutes INTEGER DEFAULT 15,
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_event_participants_event ON calendar_event_participants(event_id);
CREATE INDEX idx_event_participants_user ON calendar_event_participants(user_id);
CREATE INDEX idx_event_participants_status ON calendar_event_participants(status);

-- =================== TENDERS & QUOTES SYSTEM ===================

-- Suppliers
CREATE TABLE suppliers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    
    -- Supplier details
    name VARCHAR(255) NOT NULL,
    legal_name VARCHAR(255),
    tax_id VARCHAR(50),
    
    -- Contact
    email VARCHAR(255),
    phone VARCHAR(20),
    website VARCHAR(255),
    
    -- Address
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    postal_code VARCHAR(20),
    
    -- Business info
    industry VARCHAR(100),
    established_year INTEGER,
    employees_count INTEGER,
    annual_revenue DECIMAL(15,2),
    
    -- Status
    status VARCHAR(20) DEFAULT 'ACTIVE', -- ACTIVE, INACTIVE, BLACKLISTED
    is_verified BOOLEAN DEFAULT FALSE,
    
    -- Ratings
    quality_rating DECIMAL(3,2) DEFAULT 0.00, -- 0.00 to 5.00
    delivery_rating DECIMAL(3,2) DEFAULT 0.00,
    service_rating DECIMAL(3,2) DEFAULT 0.00,
    
    -- Metadata
    supplier_metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT suppliers_company_name_unique UNIQUE (company_id, name)
);

CREATE INDEX idx_suppliers_company ON suppliers(company_id);
CREATE INDEX idx_suppliers_status ON suppliers(status);
CREATE INDEX idx_suppliers_verified ON suppliers(is_verified);
CREATE INDEX idx_suppliers_rating ON suppliers(quality_rating);

-- Products/Services Catalog
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    supplier_id UUID REFERENCES suppliers(id),
    
    -- Product details
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    subcategory VARCHAR(100),
    
    -- Identification
    sku VARCHAR(100),
    barcode VARCHAR(100),
    manufacturer VARCHAR(255),
    brand VARCHAR(100),
    model VARCHAR(100),
    
    -- Specifications
    specifications JSONB DEFAULT '{}',
    dimensions JSONB DEFAULT '{}', -- {"length": 10, "width": 5, "height": 3, "unit": "cm"}
    weight DECIMAL(10,3),
    weight_unit VARCHAR(10) DEFAULT 'kg',
    
    -- Pricing
    base_price DECIMAL(12,2),
    currency VARCHAR(10) DEFAULT 'USD',
    price_unit VARCHAR(20), -- per piece, per kg, per meter, etc
    
    -- Inventory
    availability_status VARCHAR(20) DEFAULT 'AVAILABLE',
    lead_time_days INTEGER DEFAULT 0,
    minimum_order_quantity INTEGER DEFAULT 1,
    
    -- Quality
    certifications TEXT[],
    compliance_standards TEXT[],
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    product_metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_products_company ON products(company_id);
CREATE INDEX idx_products_supplier ON products(supplier_id);
CREATE INDEX idx_products_category ON products(category, subcategory);
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_active ON products(is_active);
CREATE INDEX idx_products_availability ON products(availability_status);

-- Tenders
CREATE TABLE tenders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES users(id),
    
    -- Basic info
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    tender_number VARCHAR(100) UNIQUE,
    
    -- Classification
    tender_type VARCHAR(50) NOT NULL, -- RFQ, RFP, ITB, etc
    category VARCHAR(100),
    subcategory VARCHAR(100),
    
    -- Financial
    estimated_budget DECIMAL(15,2),
    currency VARCHAR(10) DEFAULT 'USD',
    
    -- Timeline
    publication_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    submission_deadline TIMESTAMP WITH TIME ZONE NOT NULL,
    opening_date TIMESTAMP WITH TIME ZONE,
    award_date TIMESTAMP WITH TIME ZONE,
    
    -- Requirements
    requirements TEXT,
    technical_specifications TEXT,
    evaluation_criteria TEXT,
    
    -- Documents
    tender_documents JSONB DEFAULT '{}', -- Array of document references
    
    -- Status
    status VARCHAR(20) DEFAULT 'DRAFT', -- DRAFT, PUBLISHED, CLOSED, AWARDED, CANCELLED
    is_public BOOLEAN DEFAULT FALSE,
    
    -- Contact
    contact_person VARCHAR(200),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(20),
    
    -- Metadata
    tender_metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tenders_company ON tenders(company_id);
CREATE INDEX idx_tenders_status ON tenders(status);
CREATE INDEX idx_tenders_type ON tenders(tender_type);
CREATE INDEX idx_tenders_deadline ON tenders(submission_deadline);
CREATE INDEX idx_tenders_public ON tenders(is_public);
CREATE INDEX idx_tenders_number ON tenders(tender_number);

-- Tender Items
CREATE TABLE tender_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tender_id UUID NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
    
    -- Item details
    item_number INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    unit VARCHAR(20) NOT NULL, -- pieces, kg, meters, etc
    
    -- Specifications
    specifications TEXT,
    technical_requirements TEXT,
    
    -- Related product (if identified)
    product_id UUID REFERENCES products(id),
    
    -- Metadata
    item_metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    CONSTRAINT tender_items_unique UNIQUE (tender_id, item_number)
);

CREATE INDEX idx_tender_items_tender ON tender_items(tender_id);
CREATE INDEX idx_tender_items_product ON tender_items(product_id);

-- Quotes
CREATE TABLE quotes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tender_id UUID NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    supplier_id UUID REFERENCES suppliers(id),
    
    -- Quote details
    quote_number VARCHAR(100) NOT NULL,
    
    -- Pricing
    total_amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    
    -- Delivery
    delivery_time VARCHAR(100),
    delivery_location VARCHAR(255),
    
    -- Terms
    payment_terms TEXT,
    warranty_terms TEXT,
    additional_terms TEXT,
    
    -- Validity
    valid_until TIMESTAMP WITH TIME ZONE,
    
    -- Status
    status VARCHAR(20) DEFAULT 'DRAFT', -- DRAFT, SUBMITTED, WITHDRAWN, AWARDED, REJECTED
    submitted_at TIMESTAMP WITH TIME ZONE,
    
    -- Contact
    contact_person VARCHAR(200),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(20),
    
    -- Documents
    quote_documents JSONB DEFAULT '{}',
    
    -- Notes
    notes TEXT,
    internal_notes TEXT, -- Only visible to tender creator
    
    -- Tracking
    created_by_id UUID REFERENCES users(id),
    updated_by_id UUID REFERENCES users(id),
    
    -- Metadata
    quote_metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    CONSTRAINT quotes_tender_company_unique UNIQUE (tender_id, company_id)
);

CREATE INDEX idx_quotes_tender ON quotes(tender_id);
CREATE INDEX idx_quotes_company ON quotes(company_id);
CREATE INDEX idx_quotes_supplier ON quotes(supplier_id);
CREATE INDEX idx_quotes_status ON quotes(status);
CREATE INDEX idx_quotes_submitted ON quotes(submitted_at);

-- Quote Items
CREATE TABLE quote_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quote_id UUID NOT NULL REFERENCES quotes(id) ON DELETE CASCADE,
    tender_item_id UUID REFERENCES tender_items(id),
    
    -- Item details
    item_number VARCHAR(50),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Specifications
    specifications JSONB DEFAULT '{}',
    brand VARCHAR(100),
    model VARCHAR(100),
    
    -- Quantity and pricing
    quantity DECIMAL(10,2) NOT NULL,
    unit VARCHAR(50),
    unit_price DECIMAL(15,2) NOT NULL,
    total_price DECIMAL(15,2) NOT NULL,
    
    -- Delivery
    delivery_date TIMESTAMP WITH TIME ZONE,
    delivery_terms TEXT,
    
    -- Notes
    notes TEXT,
    
    -- Metadata
    item_metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_quote_items_quote ON quote_items(quote_id);
CREATE INDEX idx_quote_items_tender_item ON quote_items(tender_item_id);

-- =================== AUDIT & COMPLIANCE ===================

-- Audit Logs
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    
    -- Action details
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id UUID,
    
    -- Actor
    user_id UUID REFERENCES users(id),
    user_email VARCHAR(255),
    
    -- Context
    ip_address INET,
    user_agent TEXT,
    
    -- Changes
    old_values JSONB,
    new_values JSONB,
    
    -- Classification
    severity VARCHAR(20) DEFAULT 'INFO', -- DEBUG, INFO, WARNING, ERROR, CRITICAL
    category VARCHAR(50), -- AUTHENTICATION, AUTHORIZATION, DATA_CHANGE, etc
    
    -- Metadata
    audit_metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Partitioning by month for performance
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_company ON audit_logs(company_id);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_severity ON audit_logs(severity);

-- Data Retention Policies
CREATE TABLE data_retention_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    
    -- Policy details
    policy_name VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    retention_period_days INTEGER NOT NULL,
    
    -- Actions
    action_after_retention VARCHAR(50) DEFAULT 'DELETE', -- DELETE, ARCHIVE, ANONYMIZE
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    policy_config JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    CONSTRAINT data_retention_policies_company_name_unique UNIQUE (company_id, policy_name)
);

CREATE INDEX idx_data_retention_policies_company ON data_retention_policies(company_id);
CREATE INDEX idx_data_retention_policies_resource ON data_retention_policies(resource_type);

-- =================== FILES & STORAGE ===================

-- File Storage
CREATE TABLE files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    uploaded_by UUID NOT NULL REFERENCES users(id),
    
    -- File details
    filename VARCHAR(500) NOT NULL,
    original_filename VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000) NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    file_hash VARCHAR(128) UNIQUE NOT NULL,
    
    -- Storage details
    storage_provider VARCHAR(50) DEFAULT 'local', -- local, s3, gcs, azure
    storage_path VARCHAR(1000),
    storage_metadata JSONB DEFAULT '{}',
    
    -- Access control
    visibility VARCHAR(20) DEFAULT 'PRIVATE', -- PUBLIC, PRIVATE, COMPANY
    access_level VARCHAR(20) DEFAULT 'RESTRICTED', -- PUBLIC, COMPANY, RESTRICTED
    
    -- Organization
    folder_path VARCHAR(500),
    tags TEXT[] DEFAULT '{}',
    
    -- Version control
    version INTEGER DEFAULT 1,
    parent_file_id UUID REFERENCES files(id),
    is_latest_version BOOLEAN DEFAULT TRUE,
    
    -- Virus scanning
    virus_scan_status VARCHAR(20) DEFAULT 'PENDING', -- PENDING, CLEAN, INFECTED, ERROR
    virus_scan_result JSONB,
    scanned_at TIMESTAMP WITH TIME ZONE,
    
    -- Status
    status VARCHAR(20) DEFAULT 'ACTIVE', -- ACTIVE, DELETED, QUARANTINED
    
    -- Metadata
    file_metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    last_accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_files_company ON files(company_id);
CREATE INDEX idx_files_user ON files(uploaded_by);
CREATE INDEX idx_files_hash ON files(file_hash);
CREATE INDEX idx_files_path ON files(folder_path);
CREATE INDEX idx_files_tags ON files USING GIN(tags);
CREATE INDEX idx_files_mime ON files(mime_type);
CREATE INDEX idx_files_size ON files(file_size);
CREATE INDEX idx_files_virus_scan ON files(virus_scan_status);

-- File Shares
CREATE TABLE file_shares (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    shared_by_user_id UUID NOT NULL REFERENCES users(id),
    
    -- Share configuration
    share_token VARCHAR(255) UNIQUE,
    permission VARCHAR(20) DEFAULT 'VIEW', -- VIEW, DOWNLOAD, EDIT
    
    -- Access control
    password_required BOOLEAN DEFAULT FALSE,
    password_hash VARCHAR(255),
    expires_at TIMESTAMP WITH TIME ZONE,
    download_limit INTEGER,
    download_count INTEGER DEFAULT 0,
    
    -- Recipients
    shared_with_users UUID[], -- Array of user IDs
    shared_with_emails TEXT[], -- Array of emails for external sharing
    
    -- Status
    enabled BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    share_metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_file_shares_file ON file_shares(file_id);
CREATE INDEX idx_file_shares_token ON file_shares(share_token);
CREATE INDEX idx_file_shares_expires ON file_shares(expires_at);

-- File Quotas
CREATE TABLE file_quotas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Scope (either user or company level)
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    
    -- Quota configuration
    quota_type VARCHAR(50) NOT NULL, -- USER, COMPANY, DEPARTMENT
    max_storage_bytes BIGINT NOT NULL,
    used_storage_bytes BIGINT DEFAULT 0,
    max_files_count INTEGER NOT NULL,
    used_files_count INTEGER DEFAULT 0,
    max_file_size_bytes BIGINT NOT NULL,
    
    -- Restrictions
    allowed_file_types TEXT[],
    blocked_file_types TEXT[],
    
    -- Metadata
    quota_metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Constraints: either user_id or company_id must be set, but not both
    CONSTRAINT file_quotas_scope_check CHECK (
        (user_id IS NOT NULL AND company_id IS NULL) OR 
        (user_id IS NULL AND company_id IS NOT NULL)
    )
);

CREATE INDEX idx_file_quotas_user ON file_quotas(user_id);
CREATE INDEX idx_file_quotas_company ON file_quotas(company_id);

-- =================== REPORTS & ANALYTICS ===================

-- Reports
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES users(id),
    
    -- Report details
    name VARCHAR(200) NOT NULL,
    description TEXT,
    report_type VARCHAR(50) DEFAULT 'TABLE', -- TABLE, CHART, DASHBOARD
    
    -- Data configuration
    data_source VARCHAR(100) NOT NULL, -- forms, tasks, tenders, etc
    query_config JSONB NOT NULL, -- Configuration for data query
    filters JSONB DEFAULT '{}',
    aggregations JSONB DEFAULT '{}',
    
    -- Display configuration
    chart_config JSONB DEFAULT '{}',
    layout_config JSONB DEFAULT '{}',
    
    -- Status
    status VARCHAR(20) DEFAULT 'DRAFT', -- DRAFT, PUBLISHED, ARCHIVED
    is_public BOOLEAN DEFAULT FALSE,
    is_embedded BOOLEAN DEFAULT FALSE,
    
    -- Caching
    cache_duration_minutes INTEGER DEFAULT 60,
    last_cached_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_reports_company ON reports(company_id);
CREATE INDEX idx_reports_created_by ON reports(created_by);
CREATE INDEX idx_reports_type ON reports(report_type);
CREATE INDEX idx_reports_status ON reports(status);
CREATE INDEX idx_reports_data_source ON reports(data_source);

-- =================== CELERY TASKS ===================

-- Celery Task Tracking
CREATE TABLE celery_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),
    
    -- Task identification
    task_id VARCHAR(255) UNIQUE NOT NULL, -- Celery task ID
    task_name VARCHAR(200) NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    
    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING', -- PENDING, STARTED, SUCCESS, FAILURE, RETRY, REVOKED
    
    -- Task data
    task_args JSONB DEFAULT '{}',
    task_kwargs JSONB DEFAULT '{}',
    result JSONB,
    
    -- Error handling
    error_message TEXT,
    traceback TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    -- Timing
    eta TIMESTAMP WITH TIME ZONE, -- Estimated time of arrival
    expires TIMESTAMP WITH TIME ZONE,
    
    -- Priority
    priority INTEGER DEFAULT 5, -- 1-10, higher number = higher priority
    
    -- Progress tracking
    progress_current INTEGER DEFAULT 0,
    progress_total INTEGER DEFAULT 100,
    progress_description TEXT,
    
    -- Metadata
    task_metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE()
);

CREATE INDEX idx_celery_tasks_task_id ON celery_tasks(task_id);
CREATE INDEX idx_celery_tasks_company ON celery_tasks(company_id);
CREATE INDEX idx_celery_tasks_user ON celery_tasks(user_id);
CREATE INDEX idx_celery_tasks_status ON celery_tasks(status);
CREATE INDEX idx_celery_tasks_type ON celery_tasks(task_type);
CREATE INDEX idx_celery_tasks_priority ON celery_tasks(priority, created_at);

-- =================== PERFORMANCE OPTIMIZATIONS ===================

-- Create optimized indexes for common queries
CREATE INDEX CONCURRENTLY idx_companies_search ON companies USING GIN(to_tsvector('portuguese', name || ' ' || COALESCE(description, '')));
CREATE INDEX CONCURRENTLY idx_users_full_name ON users(first_name, last_name);
CREATE INDEX CONCURRENTLY idx_documents_text_search ON documents USING GIN(to_tsvector('portuguese', filename));
CREATE INDEX CONCURRENTLY idx_tenders_search ON tenders USING GIN(to_tsvector('portuguese', title || ' ' || description));
CREATE INDEX CONCURRENTLY idx_suppliers_search ON suppliers USING GIN(to_tsvector('portuguese', name || ' ' || COALESCE(legal_name, '')));

-- Partial indexes for active records only
CREATE INDEX CONCURRENTLY idx_companies_active_search ON companies(name) WHERE status = 'ACTIVE' AND deleted_at IS NULL;
CREATE INDEX CONCURRENTLY idx_users_active_email ON users(email) WHERE status = 'ACTIVE' AND deleted_at IS NULL;
CREATE INDEX CONCURRENTLY idx_files_active_company ON files(company_id) WHERE status = 'ACTIVE' AND deleted_at IS NULL;

-- Composite indexes for common filters
CREATE INDEX CONCURRENTLY idx_api_metrics_company_endpoint_time ON api_metrics(company_id, endpoint, created_at);
CREATE INDEX CONCURRENTLY idx_audit_logs_company_time_action ON audit_logs(company_id, created_at, action);
CREATE INDEX CONCURRENTLY idx_user_sessions_user_active_expires ON user_sessions(user_id, is_active, expires_at);

-- =================== DATA INTEGRITY CONSTRAINTS ===================

-- Add additional check constraints
ALTER TABLE companies ADD CONSTRAINT companies_max_users_positive CHECK (max_users > 0);
ALTER TABLE companies ADD CONSTRAINT companies_max_storage_positive CHECK (max_storage_gb > 0);

ALTER TABLE users ADD CONSTRAINT users_failed_attempts_non_negative CHECK (failed_login_attempts >= 0);

ALTER TABLE documents ADD CONSTRAINT documents_file_size_positive CHECK (file_size > 0);
ALTER TABLE documents ADD CONSTRAINT documents_quality_score_range CHECK (quality_score >= 0 AND quality_score <= 100);

ALTER TABLE files ADD CONSTRAINT files_file_size_positive CHECK (file_size > 0);
ALTER TABLE files ADD CONSTRAINT files_version_positive CHECK (version > 0);

ALTER TABLE api_metrics ADD CONSTRAINT api_metrics_response_time_non_negative CHECK (response_time_ms >= 0);
ALTER TABLE api_metrics ADD CONSTRAINT api_metrics_status_code_range CHECK (status_code >= 100 AND status_code <= 599);

-- =================== VIEWS FOR COMMON QUERIES ===================

-- Active companies with user counts
CREATE VIEW v_companies_with_stats AS
SELECT 
    c.*,
    COUNT(DISTINCT cu.user_id) as active_users_count,
    COUNT(DISTINCT d.id) as documents_count,
    COALESCE(SUM(f.file_size), 0) as total_storage_used
FROM companies c
LEFT JOIN company_users cu ON c.id = cu.company_id AND cu.is_active = TRUE
LEFT JOIN documents d ON c.id = d.company_id
LEFT JOIN files f ON c.id = f.company_id AND f.status = 'ACTIVE'
WHERE c.deleted_at IS NULL
GROUP BY c.id;

-- User session summary
CREATE VIEW v_user_session_summary AS
SELECT 
    u.id as user_id,
    u.email,
    u.first_name,
    u.last_name,
    COUNT(s.id) as total_sessions,
    COUNT(CASE WHEN s.is_active = TRUE THEN 1 END) as active_sessions,
    MAX(s.last_activity) as last_activity,
    MAX(s.created_at) as last_login
FROM users u
LEFT JOIN user_sessions s ON u.id = s.user_id
GROUP BY u.id, u.email, u.first_name, u.last_name;

-- Document processing status overview
CREATE VIEW v_document_processing_overview AS
SELECT 
    d.company_id,
    COUNT(*) as total_documents,
    COUNT(CASE WHEN d.processing_status = 'PENDING' THEN 1 END) as pending_count,
    COUNT(CASE WHEN d.processing_status = 'PROCESSING' THEN 1 END) as processing_count,
    COUNT(CASE WHEN d.processing_status = 'COMPLETED' THEN 1 END) as completed_count,
    COUNT(CASE WHEN d.processing_status = 'FAILED' THEN 1 END) as failed_count,
    AVG(d.ai_confidence_score) as avg_confidence_score,
    AVG(d.quality_score) as avg_quality_score
FROM documents d
GROUP BY d.company_id;

-- =================== FUNCTIONS FOR COMMON OPERATIONS ===================

-- Function to update user last activity
CREATE OR REPLACE FUNCTION update_user_last_activity(user_uuid UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE users 
    SET last_login_at = NOW() 
    WHERE id = user_uuid;
END;
$$ LANGUAGE plpgsql;

-- Function to clean expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM user_sessions 
    WHERE expires_at < NOW() OR 
          (last_activity < NOW() - INTERVAL '1 hour' * max_idle_minutes);
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate file quota usage
CREATE OR REPLACE FUNCTION update_file_quota_usage(target_company_id UUID DEFAULT NULL, target_user_id UUID DEFAULT NULL)
RETURNS VOID AS $$
BEGIN
    IF target_company_id IS NOT NULL THEN
        UPDATE file_quotas 
        SET 
            used_storage_bytes = (
                SELECT COALESCE(SUM(file_size), 0) 
                FROM files 
                WHERE company_id = target_company_id AND status = 'ACTIVE'
            ),
            used_files_count = (
                SELECT COUNT(*) 
                FROM files 
                WHERE company_id = target_company_id AND status = 'ACTIVE'
            ),
            updated_at = NOW()
        WHERE company_id = target_company_id;
    END IF;
    
    IF target_user_id IS NOT NULL THEN
        UPDATE file_quotas 
        SET 
            used_storage_bytes = (
                SELECT COALESCE(SUM(file_size), 0) 
                FROM files 
                WHERE uploaded_by = target_user_id AND status = 'ACTIVE'
            ),
            used_files_count = (
                SELECT COUNT(*) 
                FROM files 
                WHERE uploaded_by = target_user_id AND status = 'ACTIVE'
            ),
            updated_at = NOW()
        WHERE user_id = target_user_id;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- =================== TRIGGERS ===================

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to all tables with updated_at column
CREATE TRIGGER tr_companies_updated_at BEFORE UPDATE ON companies FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER tr_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER tr_user_profiles_updated_at BEFORE UPDATE ON user_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER tr_company_users_updated_at BEFORE UPDATE ON company_users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER tr_documents_updated_at BEFORE UPDATE ON documents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER tr_ai_processing_jobs_updated_at BEFORE UPDATE ON ai_processing_jobs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER tr_files_updated_at BEFORE UPDATE ON files FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER tr_suppliers_updated_at BEFORE UPDATE ON suppliers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER tr_tenders_updated_at BEFORE UPDATE ON tenders FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER tr_quotes_updated_at BEFORE UPDATE ON quotes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger to automatically update file quota usage
CREATE OR REPLACE FUNCTION trigger_update_file_quota()
RETURNS TRIGGER AS $$
BEGIN
    -- Update company quota
    PERFORM update_file_quota_usage(NEW.company_id, NULL);
    
    -- Update user quota
    PERFORM update_file_quota_usage(NULL, NEW.uploaded_by);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_files_quota_update 
    AFTER INSERT OR UPDATE OR DELETE ON files 
    FOR EACH ROW EXECUTE FUNCTION trigger_update_file_quota();

-- =================== INITIAL DATA ===================

-- Insert default rate limit policies
INSERT INTO rate_limit_policies (company_id, policy_name, endpoint_pattern, requests_per_minute, requests_per_hour, requests_per_day) VALUES
(NULL, 'default_api', '/api/*', 100, 3000, 50000),
(NULL, 'auth_endpoints', '/api/auth/*', 10, 100, 1000),
(NULL, 'file_upload', '/api/files/upload', 5, 50, 500),
(NULL, 'ai_processing', '/api/ai/*', 20, 200, 2000);

-- =================== COMMENTS ===================

COMMENT ON TABLE companies IS 'Empresas e organizações do sistema';
COMMENT ON TABLE users IS 'Usuários do sistema com autenticação e autorização';
COMMENT ON TABLE user_sessions IS 'Sessões de usuário com controle temporal avançado';
COMMENT ON TABLE documents IS 'Documentos para processamento de IA';
COMMENT ON TABLE ai_processing_jobs IS 'Jobs de processamento de IA com integração Celery';
COMMENT ON TABLE files IS 'Sistema de arquivos com controle de versão e segurança';
COMMENT ON TABLE tenders IS 'Licitações e processos de cotação';
COMMENT ON TABLE quotes IS 'Cotações de fornecedores';
COMMENT ON TABLE audit_logs IS 'Logs de auditoria para compliance';
COMMENT ON TABLE api_metrics IS 'Métricas de performance da API';
COMMENT ON TABLE rate_limit_policies IS 'Políticas de rate limiting por empresa';

-- =================== PERFORMANCE MONITORING ===================

-- Enable query monitoring
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET track_activity_query_size = 2048;
ALTER SYSTEM SET pg_stat_statements.track = 'all';

-- =================== SECURITY ===================

-- Create row level security policies (examples)
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
CREATE POLICY documents_company_isolation ON documents FOR ALL TO application_role USING (company_id = current_setting('app.current_company_id')::UUID);

ALTER TABLE files ENABLE ROW LEVEL SECURITY;
CREATE POLICY files_company_isolation ON files FOR ALL TO application_role USING (company_id = current_setting('app.current_company_id')::UUID);

-- Create application role
CREATE ROLE application_role;
GRANT CONNECT ON DATABASE postgres TO application_role;
GRANT USAGE ON SCHEMA public TO application_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO application_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO application_role;
