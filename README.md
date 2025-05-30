# 🗄️ Multi-Database Architecture

Uma arquitetura moderna e escalável utilizando **PostgreSQL**, **MongoDB** e **Redis** para cobrir todas as necessidades de dados da aplicação.

## 📋 Visão Geral

Esta implementação fornece uma solução completa de banco de dados com:

- **🐘 PostgreSQL**: Dados relacionais, transações ACID, integridade referencial
- **🍃 MongoDB**: Dados flexíveis, logs, analytics, documentos dinâmicos  
- **🔴 Redis**: Cache, sessões, rate limiting, comunicação real-time

## 🚀 Início Rápido

### 1. Pré-requisitos

```bash
# Docker e Docker Compose
docker --version
docker-compose --version

# WSL (para Windows)
wsl --version
```

### 2. Inicialização Completa

```bash
# Clone e acesse o diretório
cd \\wsl.localhost\Ubuntu-20.04\home\app

# Torne o script executável
chmod +x manage_databases.sh

# Inicie toda a arquitetura
./manage_databases.sh start

# Inicialize com dados de exemplo
./manage_databases.sh init
```

### 3. Acesso às Interfaces

- **🐘 Adminer (PostgreSQL)**: http://localhost:8080
- **🍃 Mongo Express (MongoDB)**: http://localhost:8081  
- **🔴 Redis Commander (Redis)**: http://localhost:8082
- **📊 Grafana (Monitoring)**: http://localhost:3000
- **📈 Prometheus (Metrics)**: http://localhost:9090

### 4. Credenciais Padrão

```
PostgreSQL:
- Host: localhost:5432
- Database: app_relational
- User: app_user
- Password: secure_password_here

MongoDB:
- Host: localhost:27017
- Database: app_flexible
- User: admin
- Password: secure_password_here

Redis:
- Host: localhost:6379
- Password: redis_password_here

Interfaces Web:
- Adminer: postgres/app_user/secure_password_here
- Mongo Express: admin/admin123
- Redis Commander: admin/admin123
- Grafana: admin/admin123
```

## 🏗️ Estrutura de Dados

### PostgreSQL - Dados Relacionais

```sql
-- Estruturas principais
companies               -- Empresas
users                   -- Usuários
user_profiles          -- Perfis de usuário
company_users          -- Associações empresa-usuário
user_sessions          -- Sessões ativas
documents              -- Documentos
ai_processing_jobs     -- Jobs de IA
forms                  -- Formulários dinâmicos
calendar_events        -- Eventos de calendário
kanban_boards          -- Quadros kanban
audit_logs             -- Logs de auditoria
```

### MongoDB - Dados Flexíveis

```javascript
// Collections principais
system_logs            // Logs do sistema
user_activity_logs     // Atividades dos usuários
api_request_logs       // Logs de API
document_metadata      // Metadados de documentos
ai_processing_results  // Resultados de IA
form_submissions       // Submissões de formulários
dynamic_configurations // Configurações dinâmicas
realtime_events        // Eventos em tempo real
usage_analytics        // Analytics de uso
```

### Redis - Cache e Real-time

```bash
# Padrões de chaves
session:user:{user_id}              # Sessões de usuário
cache:user:{user_id}                # Cache de usuário
rate_limit:user:{user_id}:{endpoint} # Rate limiting
realtime:user:{user_id}:presence    # Presença online
temp:upload:{upload_id}             # Uploads temporários
lock:document:{document_id}         # Locks de documento
counter:api_calls:{endpoint}:{date} # Contadores de API
```

## 🛠️ Comandos de Gerenciamento

### Controle de Serviços

```bash
# Iniciar tudo
./manage_databases.sh start

# Parar tudo
./manage_databases.sh stop

# Reiniciar
./manage_databases.sh restart

# Status dos serviços
./manage_databases.sh status

# Health check completo
./manage_databases.sh health
```

### Backup e Restauração

```bash
# Criar backup completo
./manage_databases.sh backup

# Restaurar do backup mais recente
./manage_databases.sh restore /path/to/backup

# Scripts específicos
./frontend/scripts/backup_databases.sh
./frontend/scripts/restore_databases.sh
```

### Manutenção

```bash
# Logs em tempo real
./manage_databases.sh logs [service_name]

# Shell interativo dos bancos
./manage_databases.sh shell postgres   # PostgreSQL
./manage_databases.sh shell mongodb    # MongoDB
./manage_databases.sh shell redis      # Redis

# Monitoramento em tempo real
./manage_databases.sh monitor

# Limpeza completa (CUIDADO!)
./manage_databases.sh clean
```
./manage_databases.sh health
```

### Logs e Monitoramento

```bash
# Ver todos os logs
./manage_databases.sh logs

# Logs de um serviço específico
./manage_databases.sh logs postgres
./manage_databases.sh logs mongodb
./manage_databases.sh logs redis

# Monitoramento em tempo real
./manage_databases.sh monitor
```

### Backup e Restore

```bash
# Criar backup
./manage_databases.sh backup

# Restaurar backup
./manage_databases.sh restore ./backups/20250530_120000

# Listar backups
ls -la backups/
```

### Shells de Banco

```bash
# PostgreSQL shell
./manage_databases.sh shell postgres

# MongoDB shell
./manage_databases.sh shell mongodb

# Redis shell
./manage_databases.sh shell redis
```

## 📁 Estrutura de Arquivos

```
├── docker-compose.yml              # Configuração Docker
├── manage_databases.sh             # Script de gerenciamento
├── docs/
│   └── DATABASE_DEPLOYMENT.md      # Documentação de deploy
├── scripts/
│   ├── init_databases.sh           # Inicialização dos bancos
│   ├── create_initial_data.py      # Dados iniciais
│   ├── postgresql_complete_schema.sql # Schema PostgreSQL
│   ├── mongodb_schemas.js          # Schemas MongoDB
│   └── redis_configuration.yml     # Configuração Redis
├── data/                           # Dados persistentes
│   ├── postgres/
│   ├── mongodb/
│   ├── redis/
│   ├── grafana/
│   └── prometheus/
├── backups/                        # Backups automáticos
└── logs/                          # Logs da aplicação
```

## 🔧 Configuração Avançada

### Desenvolvimento Local

```bash
# Usar versão de desenvolvimento
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Executar testes
docker-compose exec postgres python -m pytest tests/

# Debug mode
docker-compose up --no-deps postgres mongodb redis
```

### Produção

```bash
# Deploy para produção
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Configurar SSL/TLS
./scripts/setup_ssl.sh

# Configurar backup automático
./scripts/setup_cron_backup.sh
```

### Scaling

```bash
# Escalar serviços
docker-compose up -d --scale redis=3

# Configurar cluster MongoDB
./scripts/setup_mongodb_cluster.sh

# Configurar replicação PostgreSQL
./scripts/setup_postgres_replica.sh
```

## 📊 Monitoramento e Alertas

### Métricas Disponíveis

- **Performance**: Tempo de resposta, throughput, latência
- **Recursos**: CPU, memória, disco, rede
- **Aplicação**: Sessões ativas, uploads, processamento IA
- **Negócio**: Usuários ativos, documentos processados, formulários

### Dashboards Grafana

1. **Database Overview**: Visão geral de todos os bancos
2. **PostgreSQL Metrics**: Métricas específicas do PostgreSQL
3. **MongoDB Analytics**: Analytics do MongoDB
4. **Redis Performance**: Performance do Redis
5. **Application Metrics**: Métricas da aplicação

### Alertas Configurados

- Uso de memória > 80%
- Uso de disco > 85%
- Conexões de banco > 90% do limite
- Tempo de resposta > 2 segundos
- Rate limiting atingido
- Falha em backup automático

## 🔐 Segurança

### Configurações de Segurança

```bash
# Configurar SSL/TLS
./scripts/setup_ssl_certificates.sh

# Configurar autenticação
./scripts/setup_database_auth.sh

# Configurar firewall
./scripts/setup_firewall_rules.sh

# Rotação de senhas
./scripts/rotate_passwords.sh
```

### Auditoria e Compliance

- Todos os acessos são logados
- Mudanças de dados são auditadas
- Backups são criptografados
- Acesso baseado em roles (RBAC)
- Conformidade com LGPD/GDPR

## 🧪 Testes

### Testes de Integração

```bash
# Testes dos bancos de dados
docker-compose exec postgres python -m pytest tests/test_databases.py

# Testes de performance
./scripts/run_performance_tests.sh

# Testes de backup/restore
./scripts/test_backup_restore.sh
```

### Carga de Dados de Teste

```python
# Gerar dados de teste
python scripts/generate_test_data.py --records 10000

# Simular carga
python scripts/simulate_load.py --users 100 --duration 600
```

## 🚨 Troubleshooting

### Problemas Comuns

#### PostgreSQL não inicia
```bash
# Verificar logs
./manage_databases.sh logs postgres

# Verificar permissões
sudo chown -R 999:999 data/postgres

# Verificar configuração
docker-compose exec postgres cat /var/lib/postgresql/data/postgresql.conf
```

#### MongoDB sem espaço
```bash
# Verificar uso de disco
df -h data/mongodb

# Compact collections
docker-compose exec mongodb mongosh --eval "db.runCommand({compact: 'collection_name'})"

# Repair database
docker-compose exec mongodb mongosh --eval "db.repairDatabase()"
```

#### Redis memória cheia
```bash
# Verificar uso de memória
docker-compose exec redis redis-cli INFO memory

# Limpeza manual
docker-compose exec redis redis-cli FLUSHDB

# Ajustar política de memória
docker-compose exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### Logs de Debug

```bash
# Ativar debug mode
export DEBUG=true
./manage_databases.sh start

# Verificar conectividade
./scripts/test_connectivity.sh

# Verificar performance
./scripts/benchmark_databases.sh
```

## 📚 Documentação Adicional

- [📖 Database Deployment Guide](docs/DATABASE_DEPLOYMENT.md)
- [🔧 Configuration Reference](docs/CONFIGURATION.md)
- [🚀 Performance Tuning](docs/PERFORMANCE.md)
- [🔐 Security Guide](docs/SECURITY.md)
- [📊 Monitoring Setup](docs/MONITORING.md)
- [🔄 Backup Strategy](docs/BACKUP.md)

## 🤝 Contribuição

### Como Contribuir

1. Fork o repositório
2. Crie uma branch para sua feature (`git checkout -b feature/amazing-feature`)
3. Commit suas mudanças (`git commit -m 'Add some amazing feature'`)
4. Push para a branch (`git push origin feature/amazing-feature`)
5. Abra um Pull Request

### Padrões de Código

- Seguir PEP 8 para Python
- Usar TypeScript para frontend
- Documentar todas as funções
- Testes obrigatórios para novas features
- Seguir padrões de commit convencional

## 📞 Suporte

### Canais de Suporte

- 📧 **Email**: suporte-db@empresa.com
- 💬 **Slack**: #database-support
- 📱 **Telefone**: +55 11 9999-8888 (emergências)
- 🐛 **Issues**: [GitHub Issues](https://github.com/empresa/multi-database/issues)

### SLA

- **Crítico**: 1 hora de resposta
- **Alto**: 4 horas de resposta
- **Médio**: 24 horas de resposta
- **Baixo**: 72 horas de resposta

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🏆 Reconhecimentos

- [PostgreSQL](https://postgresql.org/) - Sistema de banco de dados relacional
- [MongoDB](https://mongodb.com/) - Banco de dados de documentos
- [Redis](https://redis.io/) - Estrutura de dados em memória
- [Docker](https://docker.com/) - Plataforma de contêinerização
- [Grafana](https://grafana.com/) - Plataforma de observabilidade

---

**Versão**: 1.0.0  
**Última atualização**: 30 de Maio de 2025  
**Mantido por**: Equipe de Desenvolvimento
#   a p p 0  
 