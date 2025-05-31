// =====================================================
// 🍃 MONGODB - COLLECTIONS E SCHEMAS BSON
// Estruturas flexíveis para logs, cache e dados dinâmicos
// =====================================================

// Conectar ao banco MongoDB
use('app_flexible');

// =================== LOGS E AUDIT TRAIL ===================

// System Logs Collection
db.createCollection('system_logs', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['level', 'message', 'timestamp', 'source'],
      properties: {
        _id: { bsonType: 'objectId' },
        level: {
          bsonType: 'string',
          enum: ['debug', 'info', 'warning', 'error', 'critical']
        },
        message: { bsonType: 'string' },
        timestamp: { bsonType: 'date' },
        source: { bsonType: 'string' },
        
        // Context data
        user_id: { bsonType: 'string' },
        company_id: { bsonType: 'string' },
        session_id: { bsonType: 'string' },
        request_id: { bsonType: 'string' },
        
        // Technical details
        module: { bsonType: 'string' },
        function_name: { bsonType: 'string' },
        file_path: { bsonType: 'string' },
        line_number: { bsonType: 'int' },
        
        // Additional data
        metadata: { bsonType: 'object' },
        stack_trace: { bsonType: 'string' },
        error_code: { bsonType: 'string' },
        
        // Performance
        execution_time_ms: { bsonType: 'int' },
        memory_usage_mb: { bsonType: 'double' },
        
        // Environment
        server_name: { bsonType: 'string' },
        environment: { bsonType: 'string' }
      }
    }
  }
});

// User Activity Logs
db.createCollection('user_activity_logs', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['user_id', 'action', 'timestamp', 'ip_address'],
      properties: {
        _id: { bsonType: 'objectId' },
        user_id: { bsonType: 'string' },
        company_id: { bsonType: 'string' },
        session_id: { bsonType: 'string' },
        
        // Action details
        action: { bsonType: 'string' },
        action_category: { bsonType: 'string' },
        resource_type: { bsonType: 'string' },
        resource_id: { bsonType: 'string' },
        
        // Request context
        endpoint: { bsonType: 'string' },
        method: { bsonType: 'string' },
        user_agent: { bsonType: 'string' },
        ip_address: { bsonType: 'string' },
        
        // Data changes
        before_state: { bsonType: 'object' },
        after_state: { bsonType: 'object' },
        changes_summary: { bsonType: 'array' },
        
        // Metadata
        timestamp: { bsonType: 'date' },
        success: { bsonType: 'bool' },
        error_message: { bsonType: 'string' },
        additional_data: { bsonType: 'object' }
      }
    }
  }
});

// API Request Logs
db.createCollection('api_request_logs', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['endpoint', 'method', 'timestamp', 'response_time_ms'],
      properties: {
        _id: { bsonType: 'objectId' },
        request_id: { bsonType: 'string' },
        
        // Request details
        endpoint: { bsonType: 'string' },
        method: { bsonType: 'string' },
        query_params: { bsonType: 'object' },
        request_headers: { bsonType: 'object' },
        request_body: { bsonType: 'object' },
        
        // Response details
        status_code: { bsonType: 'int' },
        response_headers: { bsonType: 'object' },
        response_body: { bsonType: 'object' },
        response_time_ms: { bsonType: 'int' },
        
        // Context
        user_id: { bsonType: 'string' },
        company_id: { bsonType: 'string' },
        ip_address: { bsonType: 'string' },
        user_agent: { bsonType: 'string' },
        
        // Metadata
        timestamp: { bsonType: 'date' },
        server_name: { bsonType: 'string' },
        environment: { bsonType: 'string' }
      }
    }
  }
});

// =================== DOCUMENT STORAGE & PROCESSING ===================

// Document Metadata
db.createCollection('document_metadata', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['document_id', 'filename', 'uploaded_at'],
      properties: {
        _id: { bsonType: 'objectId' },
        document_id: { bsonType: 'string' },
        
        // File details
        filename: { bsonType: 'string' },
        original_filename: { bsonType: 'string' },
        file_extension: { bsonType: 'string' },
        mime_type: { bsonType: 'string' },
        file_size_bytes: { bsonType: 'long' },
        file_hash: { bsonType: 'string' },
        
        // Storage info
        storage_path: { bsonType: 'string' },
        storage_provider: { bsonType: 'string' },
        backup_locations: { bsonType: 'array' },
        
        // Processing status
        processing_status: {
          bsonType: 'string',
          enum: ['pending', 'processing', 'completed', 'failed', 'archived']
        },
        ocr_completed: { bsonType: 'bool' },
        ai_analysis_completed: { bsonType: 'bool' },
        
        // Content analysis
        extracted_text: { bsonType: 'string' },
        text_confidence: { bsonType: 'double' },
        language_detected: { bsonType: 'string' },
        page_count: { bsonType: 'int' },
        
        // AI insights
        ai_summary: { bsonType: 'string' },
        ai_tags: { bsonType: 'array' },
        ai_categories: { bsonType: 'array' },
        sentiment_score: { bsonType: 'double' },
        
        // Context
        uploaded_by: { bsonType: 'string' },
        company_id: { bsonType: 'string' },
        folder_path: { bsonType: 'string' },
        
        // Timestamps
        uploaded_at: { bsonType: 'date' },
        processed_at: { bsonType: 'date' },
        last_accessed: { bsonType: 'date' },
        
        // Additional metadata
        custom_metadata: { bsonType: 'object' },
        version_history: { bsonType: 'array' }
      }
    }
  }
});

// AI Processing Results
db.createCollection('ai_processing_results', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['job_id', 'document_id', 'processing_type', 'started_at'],
      properties: {
        _id: { bsonType: 'objectId' },
        job_id: { bsonType: 'string' },
        document_id: { bsonType: 'string' },
        
        // Processing details
        processing_type: {
          bsonType: 'string',
          enum: ['ocr', 'text_extraction', 'summarization', 'classification', 'entity_extraction', 'sentiment_analysis']
        },
        model_used: { bsonType: 'string' },
        model_version: { bsonType: 'string' },
        
        // Results
        status: {
          bsonType: 'string',
          enum: ['pending', 'running', 'completed', 'failed', 'cancelled']
        },
        confidence_score: { bsonType: 'double' },
        results: { bsonType: 'object' },
        
        // Performance metrics
        processing_time_seconds: { bsonType: 'double' },
        tokens_processed: { bsonType: 'int' },
        api_cost: { bsonType: 'double' },
        
        // Error handling
        error_message: { bsonType: 'string' },
        retry_count: { bsonType: 'int' },
        
        // Timestamps
        started_at: { bsonType: 'date' },
        completed_at: { bsonType: 'date' },
        
        // Context
        company_id: { bsonType: 'string' },
        user_id: { bsonType: 'string' }
      }
    }
  }
});

// =================== DYNAMIC FORMS & CONFIGURATIONS ===================

// Form Submissions
db.createCollection('form_submissions', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['form_id', 'submission_data', 'submitted_at'],
      properties: {
        _id: { bsonType: 'objectId' },
        form_id: { bsonType: 'string' },
        submission_id: { bsonType: 'string' },
        
        // Form data
        submission_data: { bsonType: 'object' },
        form_version: { bsonType: 'string' },
        
        // Validation
        validation_errors: { bsonType: 'array' },
        is_valid: { bsonType: 'bool' },
        
        // Context
        submitted_by: { bsonType: 'string' },
        company_id: { bsonType: 'string' },
        ip_address: { bsonType: 'string' },
        user_agent: { bsonType: 'string' },
        
        // Processing
        status: {
          bsonType: 'string',
          enum: ['pending', 'processing', 'approved', 'rejected', 'archived']
        },
        processed_by: { bsonType: 'string' },
        processing_notes: { bsonType: 'string' },
        
        // Timestamps
        submitted_at: { bsonType: 'date' },
        processed_at: { bsonType: 'date' },
        
        // Attachments
        attached_files: { bsonType: 'array' },
        
        // Additional metadata
        source: { bsonType: 'string' },
        tags: { bsonType: 'array' },
        custom_fields: { bsonType: 'object' }
      }
    }
  }
});

// Dynamic Configurations
db.createCollection('dynamic_configurations', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['config_key', 'config_value', 'company_id'],
      properties: {
        _id: { bsonType: 'objectId' },
        config_key: { bsonType: 'string' },
        config_value: { bsonType: 'object' },
        
        // Scope
        company_id: { bsonType: 'string' },
        user_id: { bsonType: 'string' },
        scope: {
          bsonType: 'string',
          enum: ['global', 'company', 'user', 'module']
        },
        
        // Configuration metadata
        config_type: { bsonType: 'string' },
        description: { bsonType: 'string' },
        is_sensitive: { bsonType: 'bool' },
        is_active: { bsonType: 'bool' },
        
        // Versioning
        version: { bsonType: 'int' },
        previous_versions: { bsonType: 'array' },
        
        // Validation
        schema_version: { bsonType: 'string' },
        validation_rules: { bsonType: 'object' },
        
        // Timestamps
        created_at: { bsonType: 'date' },
        updated_at: { bsonType: 'date' },
        expires_at: { bsonType: 'date' },
        
        // Change tracking
        created_by: { bsonType: 'string' },
        updated_by: { bsonType: 'string' },
        change_reason: { bsonType: 'string' }
      }
    }
  }
});

// =================== REAL-TIME DATA & ANALYTICS ===================

// Real-time Events
db.createCollection('realtime_events', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['event_type', 'event_data', 'timestamp'],
      properties: {
        _id: { bsonType: 'objectId' },
        event_id: { bsonType: 'string' },
        event_type: { bsonType: 'string' },
        event_data: { bsonType: 'object' },
        
        // Context
        company_id: { bsonType: 'string' },
        user_id: { bsonType: 'string' },
        session_id: { bsonType: 'string' },
        
        // Event metadata
        source: { bsonType: 'string' },
        category: { bsonType: 'string' },
        priority: {
          bsonType: 'string',
          enum: ['low', 'normal', 'high', 'critical']
        },
        
        // Delivery tracking
        delivered_to: { bsonType: 'array' },
        delivery_attempts: { bsonType: 'int' },
        last_delivery_attempt: { bsonType: 'date' },
        
        // Timestamps
        timestamp: { bsonType: 'date' },
        expires_at: { bsonType: 'date' },
        
        // Additional data
        tags: { bsonType: 'array' },
        correlation_id: { bsonType: 'string' },
        parent_event_id: { bsonType: 'string' }
      }
    }
  }
});

// Usage Analytics
db.createCollection('usage_analytics', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['metric_name', 'metric_value', 'timestamp'],
      properties: {
        _id: { bsonType: 'objectId' },
        metric_name: { bsonType: 'string' },
        metric_value: { bsonType: 'double' },
        
        // Dimensions
        company_id: { bsonType: 'string' },
        user_id: { bsonType: 'string' },
        module: { bsonType: 'string' },
        feature: { bsonType: 'string' },
        
        // Grouping
        time_bucket: { bsonType: 'string' }, // minute, hour, day, week, month
        aggregation_type: {
          bsonType: 'string',
          enum: ['count', 'sum', 'avg', 'min', 'max', 'unique']
        },
        
        // Metadata
        metric_type: { bsonType: 'string' },
        unit: { bsonType: 'string' },
        tags: { bsonType: 'array' },
        
        // Timestamps
        timestamp: { bsonType: 'date' },
        recorded_at: { bsonType: 'date' },
        
        // Additional context
        metadata: { bsonType: 'object' },
        session_context: { bsonType: 'object' }
      }
    }
  }
});

// =================== ÍNDICES PARA PERFORMANCE ===================

// System Logs Indexes
db.system_logs.createIndex({ 'timestamp': -1 });
db.system_logs.createIndex({ 'level': 1, 'timestamp': -1 });
db.system_logs.createIndex({ 'company_id': 1, 'timestamp': -1 });
db.system_logs.createIndex({ 'user_id': 1, 'timestamp': -1 });
db.system_logs.createIndex({ 'source': 1, 'timestamp': -1 });
db.system_logs.createIndex({ 'request_id': 1 });
db.system_logs.createIndex({ 'error_code': 1 }, { sparse: true });

// User Activity Logs Indexes
db.user_activity_logs.createIndex({ 'user_id': 1, 'timestamp': -1 });
db.user_activity_logs.createIndex({ 'company_id': 1, 'timestamp': -1 });
db.user_activity_logs.createIndex({ 'action': 1, 'timestamp': -1 });
db.user_activity_logs.createIndex({ 'resource_type': 1, 'resource_id': 1 });
db.user_activity_logs.createIndex({ 'session_id': 1 });
db.user_activity_logs.createIndex({ 'ip_address': 1, 'timestamp': -1 });

// API Request Logs Indexes
db.api_request_logs.createIndex({ 'timestamp': -1 });
db.api_request_logs.createIndex({ 'endpoint': 1, 'timestamp': -1 });
db.api_request_logs.createIndex({ 'status_code': 1, 'timestamp': -1 });
db.api_request_logs.createIndex({ 'user_id': 1, 'timestamp': -1 });
db.api_request_logs.createIndex({ 'response_time_ms': -1 });
db.api_request_logs.createIndex({ 'request_id': 1 }, { unique: true });

// Document Metadata Indexes
db.document_metadata.createIndex({ 'document_id': 1 }, { unique: true });
db.document_metadata.createIndex({ 'company_id': 1, 'uploaded_at': -1 });
db.document_metadata.createIndex({ 'processing_status': 1 });
db.document_metadata.createIndex({ 'file_hash': 1 });
db.document_metadata.createIndex({ 'filename': 'text', 'extracted_text': 'text' });
db.document_metadata.createIndex({ 'ai_tags': 1 });
db.document_metadata.createIndex({ 'uploaded_by': 1, 'uploaded_at': -1 });

// AI Processing Results Indexes
db.ai_processing_results.createIndex({ 'job_id': 1 }, { unique: true });
db.ai_processing_results.createIndex({ 'document_id': 1, 'processing_type': 1 });
db.ai_processing_results.createIndex({ 'status': 1, 'started_at': -1 });
db.ai_processing_results.createIndex({ 'company_id': 1, 'started_at': -1 });
db.ai_processing_results.createIndex({ 'processing_type': 1, 'started_at': -1 });

// Form Submissions Indexes
db.form_submissions.createIndex({ 'form_id': 1, 'submitted_at': -1 });
db.form_submissions.createIndex({ 'submission_id': 1 }, { unique: true });
db.form_submissions.createIndex({ 'company_id': 1, 'submitted_at': -1 });
db.form_submissions.createIndex({ 'submitted_by': 1, 'submitted_at': -1 });
db.form_submissions.createIndex({ 'status': 1, 'submitted_at': -1 });
db.form_submissions.createIndex({ 'is_valid': 1 });

// Dynamic Configurations Indexes
db.dynamic_configurations.createIndex({ 'config_key': 1, 'company_id': 1 }, { unique: true });
db.dynamic_configurations.createIndex({ 'company_id': 1, 'scope': 1 });
db.dynamic_configurations.createIndex({ 'is_active': 1 });
db.dynamic_configurations.createIndex({ 'expires_at': 1 }, { sparse: true });
db.dynamic_configurations.createIndex({ 'config_type': 1 });

// Real-time Events Indexes
db.realtime_events.createIndex({ 'timestamp': -1 });
db.realtime_events.createIndex({ 'event_type': 1, 'timestamp': -1 });
db.realtime_events.createIndex({ 'company_id': 1, 'timestamp': -1 });
db.realtime_events.createIndex({ 'user_id': 1, 'timestamp': -1 });
db.realtime_events.createIndex({ 'expires_at': 1 }, { expireAfterSeconds: 0 });
db.realtime_events.createIndex({ 'correlation_id': 1 });
db.realtime_events.createIndex({ 'priority': 1, 'timestamp': -1 });

// Usage Analytics Indexes
db.usage_analytics.createIndex({ 'timestamp': -1 });
db.usage_analytics.createIndex({ 'metric_name': 1, 'timestamp': -1 });
db.usage_analytics.createIndex({ 'company_id': 1, 'metric_name': 1, 'timestamp': -1 });
db.usage_analytics.createIndex({ 'time_bucket': 1, 'metric_name': 1 });
db.usage_analytics.createIndex({ 'module': 1, 'feature': 1, 'timestamp': -1 });

// =================== TTL PARA LIMPEZA AUTOMÁTICA ===================

// Logs do sistema - manter por 90 dias
db.system_logs.createIndex({ 'timestamp': 1 }, { expireAfterSeconds: 7776000 });

// Logs de atividade do usuário - manter por 1 ano
db.user_activity_logs.createIndex({ 'timestamp': 1 }, { expireAfterSeconds: 31536000 });

// Logs de API - manter por 30 dias
db.api_request_logs.createIndex({ 'timestamp': 1 }, { expireAfterSeconds: 2592000 });

// Eventos em tempo real - manter por 7 dias
db.realtime_events.createIndex({ 'timestamp': 1 }, { expireAfterSeconds: 604800 });

// Analytics - manter por 2 anos
db.usage_analytics.createIndex({ 'timestamp': 1 }, { expireAfterSeconds: 63072000 });

print("✅ MongoDB collections, schemas, and indexes created successfully!");
