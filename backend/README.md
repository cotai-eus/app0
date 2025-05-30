# CotAi Backend

Comprehensive tendering and quotation management platform built with Python 3.11, FastAPI, and modern DevOps practices.

## 🏗️ Architecture

This backend follows a **Monólito Modularizado** (Modular Monolith) architecture with:

- **Domain-Driven Design (DDD)** - Clear separation of business domains
- **Repository Pattern** - Data access abstraction
- **Service Layer** - Business logic encapsulation
- **Async/Await** - High-performance asynchronous operations
- **Multi-database Support** - PostgreSQL, MongoDB, Redis

## 🚀 Features

### Core Domains
- **Authentication** - JWT tokens, session management, API keys
- **Companies** - Multi-tenant company management
- **Tenders** - Procurement request management
- **Quotes** - Supplier response system
- **Notifications** - Multi-channel notification system with templates, preferences, and webhooks
- **Forms** - Dynamic form builder (planned)
- **Kanban** - Project management boards (planned)
- **Calendar** - Event and deadline management (planned)
- **Reports** - Business analytics (planned)

### Technical Features
- **FastAPI** with automatic OpenAPI documentation
- **Pydantic v2** for data validation
- **SQLAlchemy 2.0** with async support
- **Alembic** database migrations
- **Celery** background task processing
- **Redis** caching and message broker
- **Prometheus** metrics collection
- **Structured logging** with correlation IDs
- **Docker** containerization
- **Rate limiting** and security headers

## 📁 Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── core/                   # Core infrastructure
│   │   ├── config.py           # Configuration management
│   │   ├── database.py         # PostgreSQL setup
│   │   ├── mongodb.py          # MongoDB setup
│   │   ├── redis_client.py     # Redis setup
│   │   ├── security.py         # Authentication & authorization
│   │   ├── logging.py          # Structured logging
│   │   └── exceptions.py       # Exception handling
│   ├── api/                    # API layer
│   │   ├── middleware.py       # Custom middleware
│   │   ├── deps.py             # Dependency injection
│   │   └── v1/endpoints/       # API endpoints
│   ├── domains/                # Business domains
│   │   ├── auth/               # Authentication domain
│   │   ├── companies/          # Companies domain
│   │   ├── tenders/            # Tenders domain
│   │   └── notifications/      # Multi-channel notifications
│   ├── shared/                 # Shared components
│   │   └── common/             # Base classes
│   └── tasks/                  # Background tasks
├── alembic/                    # Database migrations
├── docker-compose.yml          # Development environment
├── docker-compose.prod.yml     # Production environment
├── Dockerfile                  # Container image
└── nginx/                      # Reverse proxy configuration
```

## 🛠️ Setup & Development

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Poetry (recommended) or pip

### Quick Start with Docker

1. **Clone and setup environment**:
```bash
git clone <repository>
cd backend
cp .env.example .env
# Edit .env with your configuration
```

2. **Start all services**:
```bash
docker-compose up -d
```

3. **Run database migrations**:
```bash
docker-compose exec backend alembic upgrade head
```

4. **Access the application**:
- API Documentation: http://localhost:8000/api/v1/docs
- Health Check: http://localhost:8000/ping
- Metrics: http://localhost:8000/metrics
- Flower (Celery monitoring): http://localhost:5555

### Local Development

1. **Install dependencies**:
```bash
# With Poetry
poetry install

# With pip
pip install -r requirements.txt
```

2. **Setup databases** (PostgreSQL, MongoDB, Redis):
```bash
docker-compose up -d postgres mongodb redis
```

3. **Run migrations**:
```bash
alembic upgrade head
```

4. **Start the application**:
```bash
# Development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production server
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

5. **Start background workers**:
```bash
celery -A app.tasks.celery_app worker --loglevel=info
```

## 🐘 Database Management

### Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Database Seeds
```bash
# Create initial data (admin user, sample companies, etc.)
python -m app.scripts.seed_data
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run tests with live database
pytest --db-url="postgresql://user:pass@localhost/test_db"
```

## 🚀 Deployment

### Production with Docker

1. **Build production image**:
```bash
docker build -t cotai-backend:latest .
```

2. **Deploy with production compose**:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

3. **Scale workers**:
```bash
docker-compose -f docker-compose.prod.yml up -d --scale worker=4
```

### Environment Variables

Key environment variables for production:

```bash
# Security
SECRET_KEY=your-super-secret-key
DEBUG=false
ENVIRONMENT=production

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
MONGODB_URL=mongodb://user:pass@host:27017
REDIS_URL=redis://host:6379/0

# CORS
BACKEND_CORS_ORIGINS=["https://your-frontend.com"]
ALLOWED_HOSTS=["your-api.com"]
```

## 📊 Monitoring & Observability

### Metrics
- **Prometheus metrics** available at `/metrics`
- **Application metrics**: request duration, error rates, database connections
- **Business metrics**: user registrations, tender submissions, quote responses, notification delivery rates

### Logging
- **Structured JSON logging** with correlation IDs
- **Request/response logging** with performance metrics
- **Error tracking** with stack traces
- **Audit logging** for sensitive operations

### Health Checks
- **Health endpoint**: `/api/v1/health`
- **Deep health checks**: Database, Redis, MongoDB connectivity
- **Dependency status**: External service availability

## 🔐 Security

### Authentication
- **JWT tokens** with configurable expiration
- **Refresh tokens** for extended sessions
- **API keys** for service-to-service communication
- **Session management** with device tracking

### Authorization
- **Role-based permissions** with scopes
- **Company-level access control**
- **Resource-level permissions**
- **API key scope restrictions**

### Security Features
- **Rate limiting** per IP and user
- **CORS configuration** for frontend integration
- **Security headers** (HSTS, CSP, etc.)
- **Input validation** with Pydantic
- **SQL injection prevention** with SQLAlchemy
- **Password hashing** with bcrypt

## 📢 Notifications System

### Multi-Channel Notifications
The notifications domain provides a comprehensive system for managing and delivering notifications across multiple channels:

#### Core Components
- **Notifications** - Central notification management with status tracking
- **Templates** - Reusable notification templates with variable substitution
- **Preferences** - User-specific notification preferences and settings
- **Multi-Channel Delivery** - Support for in-app, email, SMS, push, and webhook notifications
- **Webhooks** - External webhook endpoints for system integrations
- **Device Tokens** - Push notification device management
- **Digest System** - Grouped notification summaries

#### Features
- **Template Engine** - Dynamic content with variable substitution
- **Scheduling** - Schedule notifications for future delivery
- **Retry Logic** - Automatic retry for failed deliveries
- **Delivery Tracking** - Complete audit trail of notification attempts
- **User Preferences** - Granular control over notification types and channels
- **Digest Aggregation** - Group notifications by frequency (daily, weekly)
- **Webhook Integration** - External system notifications via HTTP webhooks
- **Push Notifications** - Mobile and web push notification support

#### Repository Layer
The notifications domain includes comprehensive repository classes:

- `NotificationRepository` - Core notification CRUD with advanced filtering
- `NotificationTemplateRepository` - Template management and retrieval
- `NotificationPreferenceRepository` - User preference management
- `NotificationDeliveryRepository` - Multi-channel delivery tracking
- `WebhookEndpointRepository` - Webhook endpoint configuration
- `WebhookDeliveryRepository` - Webhook delivery attempt tracking
- `DeviceTokenRepository` - Push notification device token management
- `NotificationDigestRepository` - Digest creation and management

## 📚 API Documentation

### Interactive Documentation
- **Swagger UI**: `/api/v1/docs`
- **ReDoc**: `/api/v1/redoc`
- **OpenAPI Spec**: `/api/v1/openapi.json`

### Authentication
```bash
# Get access token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# Use token in requests
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/auth/me"
```

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** following the coding standards
4. **Add tests** for new functionality
5. **Run the test suite**: `pytest`
6. **Commit your changes**: `git commit -m 'Add amazing feature'`
7. **Push to the branch**: `git push origin feature/amazing-feature`
8. **Open a Pull Request**

### Coding Standards
- **Black** for code formatting
- **isort** for import sorting
- **mypy** for type checking
- **pytest** for testing
- **Conventional commits** for commit messages

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- **Documentation**: [API Docs](http://localhost:8000/api/v1/docs)
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions

---

Built with ❤️ using FastAPI, SQLAlchemy, and modern Python practices.
