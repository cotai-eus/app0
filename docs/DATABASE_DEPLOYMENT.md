# 🗄️ Documentação de Deploy e Manutenção - Arquitetura Multi-Database

## 📋 Visão Geral

Esta documentação cobre o deploy e manutenção de uma arquitetura moderna multi-database com:

- **🐘 PostgreSQL**: Dados relacionais e transacionais
- **🍃 MongoDB**: Dados flexíveis, logs e analytics
- **🔴 Redis**: Cache, sessões e comunicação real-time

## 📁 Estrutura de Pastas Organizada

O projeto foi estruturado de forma modular para facilitar manutenção e deploy:

```
app/
├── 📋 manage_databases.sh          # Script principal de gerenciamento
├── 🐳 docker-compose.yml           # Orquestração dos serviços
├── 📖 README.md                    # Documentação principal
├── 🗄️ db/                          # Configurações dos bancos de dados
│   ├── data/                       # Volumes persistentes
│   ├── postgres-config/            # Configurações PostgreSQL
│   ├── mongo-config/               # Configurações MongoDB
│   ├── redis-config/               # Configurações Redis
│   ├── grafana-config/             # Configurações Grafana
│   └── prometheus-config/          # Configurações Prometheus
├── 🌐 frontend/                    # Frontend e proxy reverso
│   ├── scripts/                    # Scripts de automação
│   ├── nginx-config/               # Configurações Nginx
│   └── ssl-certs/                  # Certificados SSL
├── 🔧 backend/                     # Backend da aplicação
└── 📚 docs/                        # Documentação
```

### Vantagens da Estrutura

- ✅ **Modularidade**: Cada componente em sua pasta
- ✅ **Manutenção**: Fácil localização de arquivos
- ✅ **Backup**: Separação clara entre dados e configurações  
- ✅ **Deploy**: Scripts organizados por funcionalidade
- ✅ **Escalabilidade**: Fácil adição de novos serviços

## 🚀 Deploy Inicial

### 1. Pré-requisitos

```bash
# Sistemas operacionais suportados
- Ubuntu 20.04+ / Debian 11+
- CentOS 8+ / RHEL 8+
- Docker / Docker Compose

# Recursos mínimos recomendados
- CPU: 4 cores
- RAM: 8GB
- Storage: 100GB SSD
- Network: 1Gbps
```

### 2. Instalação dos Bancos de Dados

#### PostgreSQL 15+
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql-15 postgresql-contrib-15

# CentOS/RHEL
sudo dnf install postgresql15-server postgresql15-contrib

# Configuração inicial
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

#### MongoDB 7.0+
```bash
# Ubuntu/Debian
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt update
sudo apt install mongodb-org

# Inicialização
sudo systemctl enable mongod
sudo systemctl start mongod
```

#### Redis 7.0+
```bash
# Ubuntu/Debian
sudo apt install redis-server

# CentOS/RHEL
sudo dnf install redis

# Configuração e inicialização
sudo systemctl enable redis
sudo systemctl start redis
```

### 3. Configuração de Segurança

#### PostgreSQL
```bash
# Configurar autenticação
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'secure_password';"

# Editar pg_hba.conf
sudo nano /etc/postgresql/15/main/pg_hba.conf
# Alterar method para 'md5' para conexões locais

# Configurar postgresql.conf
sudo nano /etc/postgresql/15/main/postgresql.conf
# listen_addresses = 'localhost'
# max_connections = 200
# shared_buffers = 256MB
```

#### MongoDB
```bash
# Habilitar autenticação
sudo nano /etc/mongod.conf
```

```yaml
security:
  authorization: enabled
  
net:
  port: 27017
  bindIp: 127.0.0.1

storage:
  dbPath: /var/lib/mongodb
  journal:
    enabled: true

systemLog:
  destination: file
  logAppend: true
  path: /var/log/mongodb/mongod.log
```

#### Redis
```bash
# Configurar Redis
sudo nano /etc/redis/redis.conf
```

```conf
# Security
requirepass your_secure_redis_password
bind 127.0.0.1

# Memory
maxmemory 2gb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000

# Logging
loglevel notice
logfile /var/log/redis/redis-server.log
```

### 4. Executar Scripts de Inicialização

```bash
# Tornar os scripts executáveis
chmod +x manage_databases.sh
chmod +x frontend/scripts/*.sh

# Configurar variáveis de ambiente (opcional)
export POSTGRES_DB_NAME="app_relational"
export POSTGRES_USER="app_user"
export POSTGRES_PASSWORD="secure_password_here"
export MONGODB_DB_NAME="app_flexible"
export REDIS_PASSWORD="redis_password_here"

# Método 1: Script principal (RECOMENDADO)
./manage_databases.sh start
./manage_databases.sh init

# Método 2: Script específico de inicialização
./db/scripts/init_databases.sh

# Método 3: Inicialização individual
./db/scripts/init_databases.sh postgres
./db/scripts/init_databases.sh mongodb
./db/scripts/init_databases.sh redis
```

## 🔧 Configuração de Produção

### 1. PostgreSQL - Otimizações

```sql
-- postgresql.conf otimizado para produção
-- Conexões
max_connections = 200
shared_buffers = 2GB
effective_cache_size = 6GB
maintenance_work_mem = 512MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200

-- Logging
log_destination = 'csvlog'
logging_collector = on
log_directory = 'pg_log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_min_duration_statement = 1000
log_checkpoints = on
log_connections = on
log_disconnections = on
```

### 2. MongoDB - Configuração de Produção

```yaml
# /etc/mongod.conf
storage:
  dbPath: /var/lib/mongodb
  journal:
    enabled: true
  engine: wiredTiger
  wiredTiger:
    engineConfig:
      cacheSizeGB: 2
      directoryForIndexes: true
    collectionConfig:
      blockCompressor: snappy
    indexConfig:
      prefixCompression: true

operationProfiling:
  slowOpThresholdMs: 100
  mode: slowOp

replication:
  replSetName: "rs0"

net:
  port: 27017
  bindIp: 127.0.0.1
  maxIncomingConnections: 200
```

### 3. Redis - Configuração de Produção

```conf
# /etc/redis/redis.conf
# Memory
maxmemory 4gb
maxmemory-policy allkeys-lru
maxmemory-samples 5

# Network
tcp-keepalive 300
timeout 300
tcp-nodelay yes

# Performance
io-threads 4
io-threads-do-reads yes

# Persistence (para dados críticos)
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb

# Security
requirepass your_very_secure_redis_password
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command DEBUG ""
```

## 📊 Monitoramento e Métricas

### 1. PostgreSQL Monitoring

```sql
-- Views para monitoramento
CREATE VIEW pg_stat_database_extended AS
SELECT 
    datname,
    numbackends,
    xact_commit,
    xact_rollback,
    blks_read,
    blks_hit,
    tup_returned,
    tup_fetched,
    tup_inserted,
    tup_updated,
    tup_deleted,
    conflicts,
    temp_files,
    temp_bytes,
    deadlocks,
    blk_read_time,
    blk_write_time
FROM pg_stat_database 
WHERE datname = 'app_relational';

-- Queries lentas
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements 
ORDER BY total_time DESC 
LIMIT 10;
```

### 2. MongoDB Monitoring

```javascript
// Comandos de monitoramento
db.runCommand({ serverStatus: 1 })
db.stats()
db.currentOp()

// Profiler para queries lentas
db.setProfilingLevel(1, { slowms: 100 })
db.system.profile.find().limit(5).sort({ ts: -1 })

// Status de replicação (se aplicável)
rs.status()
```

### 3. Redis Monitoring

```bash
# Comandos de monitoramento
redis-cli INFO all
redis-cli INFO memory
redis-cli INFO stats
redis-cli INFO replication

# Monitoramento contínuo
redis-cli MONITOR

# Slow log
redis-cli SLOWLOG GET 10
```

## 🔄 Backup e Recuperação

### 1. PostgreSQL Backup

```bash
#!/bin/bash
# Script de backup PostgreSQL
BACKUP_DIR="/backup/postgresql"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="app_relational"

# Backup completo
pg_dump -h localhost -U app_user -d $DB_NAME -f "$BACKUP_DIR/full_backup_$DATE.sql"

# Backup apenas schema
pg_dump -h localhost -U app_user -d $DB_NAME --schema-only -f "$BACKUP_DIR/schema_backup_$DATE.sql"

# Backup apenas dados
pg_dump -h localhost -U app_user -d $DB_NAME --data-only -f "$BACKUP_DIR/data_backup_$DATE.sql"

# Compressão
gzip "$BACKUP_DIR/full_backup_$DATE.sql"

# Limpeza de backups antigos (manter 30 dias)
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete
```

### 2. MongoDB Backup

```bash
#!/bin/bash
# Script de backup MongoDB
BACKUP_DIR="/backup/mongodb"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="app_flexible"

# Backup com mongodump
mongodump --db $DB_NAME --out "$BACKUP_DIR/dump_$DATE"

# Compressão
tar -czf "$BACKUP_DIR/mongodb_backup_$DATE.tar.gz" -C "$BACKUP_DIR" "dump_$DATE"
rm -rf "$BACKUP_DIR/dump_$DATE"

# Limpeza de backups antigos
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

### 3. Redis Backup

```bash
#!/bin/bash
# Script de backup Redis
BACKUP_DIR="/backup/redis"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup RDB
redis-cli BGSAVE
cp /var/lib/redis/dump.rdb "$BACKUP_DIR/redis_backup_$DATE.rdb"

# Backup AOF (se habilitado)
if [ -f /var/lib/redis/appendonly.aof ]; then
    cp /var/lib/redis/appendonly.aof "$BACKUP_DIR/redis_aof_$DATE.aof"
fi

# Compressão
gzip "$BACKUP_DIR/redis_backup_$DATE.rdb"

# Limpeza
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete
```

## 🔧 Manutenção Periódica

### 1. PostgreSQL Maintenance

```sql
-- Vacuum e analyze automático (configurar no cron)
VACUUM ANALYZE;

-- Reindex para otimização
REINDEX DATABASE app_relational;

-- Limpeza de logs antigos
SELECT pg_rotate_logfile();

-- Estatísticas de tabelas
SELECT 
    schemaname,
    tablename,
    n_tup_ins,
    n_tup_upd,
    n_tup_del,
    last_vacuum,
    last_analyze
FROM pg_stat_user_tables
ORDER BY n_tup_ins + n_tup_upd + n_tup_del DESC;
```

### 2. MongoDB Maintenance

```javascript
// Compact collections
db.system_logs.compact()

// Rebuild indexes
db.system_logs.reIndex()

// Verificar fragmentação
db.stats()

// Limpeza de collections com TTL
// (Já configurado nos indexes com expireAfterSeconds)
```

### 3. Redis Maintenance

```bash
# Limpeza de memória
redis-cli MEMORY PURGE

# Informações de memória
redis-cli MEMORY USAGE session:user:*

# Limpeza manual de keys expiradas
redis-cli --scan --pattern "temp:*" | xargs redis-cli DEL
```

## 🚨 Alertas e Monitoramento

### 1. Scripts de Health Check

```bash
#!/bin/bash
# health_check.sh

# PostgreSQL
PG_STATUS=$(pg_isready -h localhost -p 5432 && echo "OK" || echo "FAIL")

# MongoDB
MONGO_STATUS=$(mongosh --quiet --eval "print('OK')" 2>/dev/null || echo "FAIL")

# Redis
REDIS_STATUS=$(redis-cli ping 2>/dev/null || echo "FAIL")

echo "PostgreSQL: $PG_STATUS"
echo "MongoDB: $MONGO_STATUS"
echo "Redis: $REDIS_STATUS"

# Enviar alerta se algum estiver down
if [[ "$PG_STATUS" == "FAIL" || "$MONGO_STATUS" == "FAIL" || "$REDIS_STATUS" == "FAIL" ]]; then
    # Integração com sistema de alertas (Slack, email, etc.)
    echo "ALERT: Database service down!"
fi
```

### 2. Métricas de Performance

```bash
#!/bin/bash
# performance_metrics.sh

# Uso de CPU dos bancos
echo "=== CPU Usage ==="
ps aux | grep -E "(postgres|mongod|redis)" | grep -v grep

# Uso de memória
echo "=== Memory Usage ==="
free -h

# Espaço em disco
echo "=== Disk Usage ==="
df -h | grep -E "(/var/lib/postgresql|/var/lib/mongodb|/var/lib/redis)"

# Conexões ativas PostgreSQL
echo "=== PostgreSQL Connections ==="
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"

# Status MongoDB
echo "=== MongoDB Status ==="
mongosh --quiet --eval "db.serverStatus().connections"

# Informações Redis
echo "=== Redis Info ==="
redis-cli INFO clients | grep connected_clients
```

## 🐳 Deploy com Docker

### 1. Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: app_relational
      POSTGRES_USER: app_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/postgresql_complete_schema.sql:/docker-entrypoint-initdb.d/01-schema.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app_user -d app_relational"]
      interval: 30s
      timeout: 10s
      retries: 3

  mongodb:
    image: mongo:7.0
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: secure_password
      MONGO_INITDB_DATABASE: app_flexible
    volumes:
      - mongodb_data:/data/db
      - ./scripts/mongodb_schemas.js:/docker-entrypoint-initdb.d/mongodb_schemas.js
    ports:
      - "27017:27017"
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7.0-alpine
    command: redis-server --requirepass redis_password
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
  mongodb_data:
  redis_data:
```

### 2. Deploy Commands

```bash
# Build e inicialização
docker-compose up -d

# Executar script de dados iniciais
docker-compose exec postgres python3 /scripts/create_initial_data.py

# Verificar status
docker-compose ps

# Logs
docker-compose logs -f

# Backup dos volumes
docker run --rm -v postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .
```

## 📈 Otimizações de Performance

### 1. Indexação Estratégica

```sql
-- PostgreSQL: Indexes mais utilizados
CREATE INDEX CONCURRENTLY idx_users_email_active ON users(email) WHERE is_active = true;
CREATE INDEX CONCURRENTLY idx_documents_company_created ON documents(company_id, created_at DESC);
CREATE INDEX CONCURRENTLY idx_sessions_user_active ON user_sessions(user_id, is_active);
```

```javascript
// MongoDB: Indexes compostos
db.system_logs.createIndex({ "company_id": 1, "level": 1, "timestamp": -1 })
db.user_activity_logs.createIndex({ "user_id": 1, "action": 1, "timestamp": -1 })
db.document_metadata.createIndex({ "company_id": 1, "processing_status": 1, "uploaded_at": -1 })
```

### 2. Connection Pooling

```python
# asyncpg connection pool
DATABASE_URL = "postgresql://user:pass@localhost/db"
pool = await asyncpg.create_pool(
    DATABASE_URL,
    min_size=10,
    max_size=50,
    command_timeout=60
)

# MongoDB motor
client = motor.motor_asyncio.AsyncIOMotorClient(
    "mongodb://localhost:27017",
    maxPoolSize=50,
    minPoolSize=10,
    maxIdleTimeMS=30000
)

# Redis connection pool
redis_pool = redis.ConnectionPool(
    host='localhost',
    port=6379,
    max_connections=50,
    socket_keepalive=True,
    socket_keepalive_options={}
)
```

## 🔐 Segurança e Compliance

### 1. Configurações de Segurança

```bash
# PostgreSQL - SSL/TLS
ssl = on
ssl_cert_file = 'server.crt'
ssl_key_file = 'server.key'
ssl_ca_file = 'ca.crt'

# MongoDB - TLS
net:
  tls:
    mode: requireTLS
    certificateKeyFile: /etc/ssl/mongodb.pem
    CAFile: /etc/ssl/ca.pem

# Redis - TLS
tls-port 6380
tls-cert-file /etc/redis/tls/redis.crt
tls-key-file /etc/redis/tls/redis.key
tls-ca-cert-file /etc/redis/tls/ca.crt
```

### 2. Backup Security

```bash
# Criptografia de backups
gpg --symmetric --cipher-algo AES256 backup_file.sql
gpg --batch --yes --passphrase "$BACKUP_PASSWORD" --symmetric --cipher-algo AES256 backup_file.sql
```

## 📚 Troubleshooting

### 1. Problemas Comuns

#### PostgreSQL
```bash
# Conexões esgotadas
SELECT count(*) FROM pg_stat_activity;
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle';

# Locks
SELECT * FROM pg_locks WHERE NOT granted;
SELECT pg_cancel_backend(pid) FROM pg_stat_activity WHERE query LIKE '%LOCK%';

# Tabelas com muito bloat
SELECT schemaname, tablename, n_dead_tup, n_live_tup 
FROM pg_stat_user_tables 
WHERE n_dead_tup > n_live_tup;
```

#### MongoDB
```javascript
// Conexões altas
db.serverStatus().connections

// Operações lentas
db.currentOp({"active": true, "secs_running": {"$gt": 5}})

// Matar operação
db.killOp(opid)
```

#### Redis
```bash
# Memória alta
redis-cli INFO memory

# Clientes conectados
redis-cli INFO clients

# Slow queries
redis-cli SLOWLOG GET 10
```

---

## 📞 Suporte e Contato

Para suporte técnico e manutenção:
- 📧 Email: suporte-db@empresa.com
- 📱 Telefone: +55 11 9999-8888
- 🔗 Wiki: https://wiki.empresa.com/databases
- 📋 Issues: https://github.com/empresa/database-setup/issues

---
*Documentação atualizada em: $(date '+%Y-%m-%d %H:%M:%S')*
