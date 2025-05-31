# 🐳 Docker Environment - CotAi Backend

## Overview

This Docker environment provides a complete, production-ready deployment for the CotAi Backend project, featuring:

- **Multi-stage Dockerfile** with optimized builds for different services
- **Development & Production** docker-compose configurations
- **Microservices Architecture** with proper service isolation
- **Complete Monitoring Stack** (Prometheus + Grafana)
- **Load Balancing** with Nginx reverse proxy
- **High Availability** database setup (PostgreSQL + MongoDB + Redis)
- **LLM Integration** with Ollama and custom LLM service
- **Background Processing** with Celery workers and scheduler

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx Proxy   │────│  Backend API    │────│  LLM Service    │
│   (Port 80/443) │    │   (Port 8000)   │    │   (Port 8001)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         │              │  Celery Workers │              │
         │              │  & Beat Scheduler│              │
         │              └─────────────────┘              │
         │                       │                       │
    ┌─────────────────────────────────────────────────────────┐
    │                  Data Layer                             │
    ├─────────────────┬─────────────────┬─────────────────────┤
    │   PostgreSQL    │    MongoDB      │      Redis          │
    │   (Port 5432)   │   (Port 27017)  │    (Port 6379)      │
    └─────────────────┴─────────────────┴─────────────────────┘
         │                       │                       │
    ┌─────────────────────────────────────────────────────────┐
    │                Monitoring Stack                         │
    ├─────────────────┬─────────────────┬─────────────────────┤
    │    Grafana      │   Prometheus    │      Ollama         │
    │   (Port 3000)   │   (Port 9090)   │   (Port 11434)      │
    └─────────────────┴─────────────────┴─────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker Engine 20.10+
- Docker Compose V2
- 8GB+ RAM (16GB recommended for production)
- NVIDIA GPU (optional, for LLM acceleration)

### Development Environment

```powershell
# Start development environment
.\docker-manager.ps1 -Action dev -Build

# View logs
.\docker-manager.ps1 -Action logs -Follow

# Check status
.\docker-manager.ps1 -Action status
```

### Production Environment

```powershell
# Configure production environment
cp .env.production.example .env.production
# Edit .env.production with your settings

# Start production environment
.\docker-manager.ps1 -Action prod -Build
```

## 📋 Available Services

### Core Services

| Service | Development Port | Production Access | Description |
|---------|------------------|-------------------|-------------|
| Backend API | 8000 | https://localhost/api/ | Main FastAPI application |
| LLM Service | 8001 | https://localhost/llm/ | AI/ML processing service |
| Ollama | 11434 | Internal | LLM model server |
| Celery Worker | - | - | Background task processor |
| Celery Beat | - | - | Task scheduler |
| Flower | 5555 | - | Celery monitoring |

### Databases

| Service | Development Port | Production Access | Credentials |
|---------|------------------|-------------------|-------------|
| PostgreSQL | 5432 | Internal | See .env file |
| MongoDB | 27017 | Internal | See .env file |
| Redis | 6379 | Internal | See .env file |

### Admin Interfaces

| Service | Development Port | Description |
|---------|------------------|-------------|
| Adminer | 8080 | PostgreSQL admin interface |
| Mongo Express | 8081 | MongoDB admin interface |
| Redis Commander | 8082 | Redis admin interface |

### Monitoring

| Service | Development Port | Production Access | Credentials |
|---------|------------------|-------------------|-------------|
| Grafana | 3000 | https://localhost/monitoring/ | admin/admin123 |
| Prometheus | 9090 | https://localhost/metrics/ | Internal only |

## 🔧 Configuration

### Environment Files

- `.env` - Development configuration
- `.env.production` - Production configuration
- `.env.example` - Template with all available options

### Docker Compose Files

- `docker-compose.yml` - Development environment
- `docker-compose.prod.yml` - Production environment with:
  - Nginx reverse proxy with SSL
  - Resource limits and health checks
  - Multiple Celery workers
  - Enhanced security settings
  - Log aggregation

### Dockerfile Stages

The multi-stage Dockerfile provides optimized builds for:

- `base` - Common dependencies and system packages
- `development` - Development tools and hot reload
- `production` - Optimized for production deployment
- `celery-worker` - Background task processing
- `celery-beat` - Task scheduling
- `llm-processor` - AI/ML processing with GPU support

## 🛠️ Management Commands

### Docker Manager Script

```powershell
# Development
.\docker-manager.ps1 -Action dev [-Build]           # Start development
.\docker-manager.ps1 -Action restart [-Service name] # Restart services

# Production
.\docker-manager.ps1 -Action prod [-Build]          # Start production

# Monitoring
.\docker-manager.ps1 -Action status                 # Show service status
.\docker-manager.ps1 -Action logs [-Service name] [-Follow] # View logs

# Maintenance
.\docker-manager.ps1 -Action stop                   # Stop all services
.\docker-manager.ps1 -Action clean [-Force]         # Clean environment
.\docker-manager.ps1 -Action update                 # Update images
.\docker-manager.ps1 -Action backup                 # Backup data
.\docker-manager.ps1 -Action restore -Service path  # Restore from backup
```

### Direct Docker Compose

```powershell
# Development
docker-compose up -d                    # Start all services
docker-compose up -d backend           # Start specific service
docker-compose logs -f backend         # Follow logs
docker-compose restart backend         # Restart service
docker-compose down                     # Stop all services

# Production
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml down
```

## 🔍 Health Monitoring

### Health Check Endpoints

- Backend API: `http://localhost:8000/health`
- LLM Service: `http://localhost:8001/health`
- Ollama: `http://localhost:11434/api/tags`

### Monitoring Stack

- **Grafana**: Dashboards for application and infrastructure metrics
- **Prometheus**: Metrics collection and alerting
- **Container Health Checks**: Automatic service recovery

### Log Aggregation

Logs are centralized and accessible via:
- Development: `docker-compose logs`
- Production: Persistent volumes mounted at `/var/log/`

## 🔒 Security

### Production Security Features

- **SSL/TLS Termination** at Nginx proxy
- **Non-root containers** with dedicated users
- **Network isolation** with custom bridge networks
- **Resource limits** to prevent DoS
- **Rate limiting** on API endpoints
- **Security headers** (HSTS, CSP, XSS protection)
- **Access control** for monitoring interfaces

### Database Security

- **Encrypted connections** between services
- **Strong passwords** required in production
- **Network isolation** from external access
- **Backup encryption** for sensitive data

## 📊 Performance

### Resource Allocation

| Service | Development | Production |
|---------|-------------|------------|
| Backend | 1GB RAM | 2-4GB RAM, 1-2 CPU |
| LLM Service | 2GB RAM | 3-6GB RAM, 2-3 CPU |
| Ollama | 4GB RAM | 6-12GB RAM, 2-4 CPU |
| PostgreSQL | 512MB RAM | 1-2GB RAM, 0.5-1 CPU |
| MongoDB | 512MB RAM | 1-2GB RAM, 0.5-1 CPU |
| Redis | 256MB RAM | 1GB RAM, 0.5-1 CPU |

### Optimization Features

- **Multi-stage builds** for smaller images
- **Layer caching** for faster rebuilds
- **Shared volumes** for development hot reload
- **Connection pooling** between services
- **Gzip compression** at proxy level
- **Static file caching** with proper headers

## 🔄 Backup & Recovery

### Automated Backups

```powershell
# Manual backup
.\docker-manager.ps1 -Action backup

# Scheduled backup (add to Windows Task Scheduler)
.\docker-manager.ps1 -Action backup > "logs\backup_$(Get-Date -Format 'yyyyMMdd').log"
```

### Backup Contents

- **PostgreSQL**: Full database dump
- **MongoDB**: Complete document export
- **Redis**: RDB snapshot
- **Application volumes**: Model cache, logs, data
- **Configuration**: Environment and config files

### Recovery Process

```powershell
# Restore from backup
.\docker-manager.ps1 -Action restore -Service "backups/20250531_120000"
```

## 🚨 Troubleshooting

### Common Issues

1. **Port Conflicts**: Check if ports are already in use
   ```powershell
   netstat -an | findstr "8000\|5432\|27017"
   ```

2. **Memory Issues**: Increase Docker memory limit or system RAM

3. **GPU Not Available**: Ensure NVIDIA Docker runtime is installed

4. **Permission Errors**: Run PowerShell as Administrator

5. **Database Connection Errors**: Check service health and network connectivity

### Debug Commands

```powershell
# Check service health
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Inspect specific service
docker-compose logs backend

# Test network connectivity
docker exec cotai_backend ping postgres

# Monitor resource usage
docker stats --no-stream
```

## 📈 Scaling

### Horizontal Scaling

```yaml
# Scale Celery workers
docker-compose up -d --scale celery-worker=4

# Add more backend instances (requires load balancer)
docker-compose up -d --scale backend=3
```

### Vertical Scaling

Adjust resource limits in docker-compose files:

```yaml
deploy:
  resources:
    limits:
      memory: 8G
      cpus: '4.0'
```

## 🔗 Integration

### External Services

The environment supports integration with:
- External databases (PostgreSQL, MongoDB clusters)
- Message queues (RabbitMQ, AWS SQS)
- Object storage (AWS S3, MinIO)
- Monitoring services (DataDog, New Relic)
- CI/CD pipelines (GitHub Actions, Jenkins)

### API Gateway

Nginx configuration supports:
- SSL termination
- Load balancing
- Rate limiting
- Request routing
- Static file serving
- WebSocket proxying

## 📚 Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Nginx Configuration Guide](https://nginx.org/en/docs/)
- [Prometheus Monitoring](https://prometheus.io/docs/)
- [Grafana Dashboards](https://grafana.com/docs/)
- [Celery Documentation](https://docs.celeryproject.org/)

---

**Note**: This environment has been optimized for both development productivity and production reliability. For specific deployment requirements, consult the configuration files and adjust settings accordingly.
