# 🗄️ Database Configuration - `/db` Folder

Esta pasta contém todas as configurações dos bancos de dados da arquitetura multi-database.

## 📁 Estrutura de Pastas

```
db/
├── data/                          # Volumes de dados persistentes
│   ├── postgres/                  # Dados do PostgreSQL
│   ├── mongodb/                   # Dados do MongoDB
│   ├── mongodb-config/           # Configurações do MongoDB
│   ├── redis/                    # Dados do Redis
│   ├── grafana/                  # Dados do Grafana
│   └── prometheus/               # Dados do Prometheus
├── postgres-config/              # Configurações do PostgreSQL
│   └── postgresql.conf           # Arquivo principal de configuração
├── mongo-config/                 # Configurações do MongoDB
│   └── mongod.conf              # Arquivo principal de configuração
├── redis-config/                 # Configurações do Redis
│   └── redis.conf               # Arquivo principal de configuração
├── grafana-config/               # Configurações do Grafana
│   └── provisioning/            # Datasources e dashboards
├── prometheus-config/            # Configurações do Prometheus
│   ├── prometheus.yml           # Configuração principal
│   └── rules/                   # Regras de alerting
└── monitoring/                   # Scripts de monitoramento
```

## ⚙️ Configurações por Serviço

### 🐘 PostgreSQL
- **Arquivo**: `postgres-config/postgresql.conf`
- **Port**: 5432
- **Database**: app_relational
- **User**: app_user
- **Otimizado para**: Desenvolvimento e produção leve

### 🍃 MongoDB
- **Arquivo**: `mongo-config/mongod.conf`
- **Port**: 27017
- **Database**: app_flexible
- **Auth**: Habilitado
- **Compressão**: Snappy para performance

### 🔴 Redis
- **Arquivo**: `redis-config/redis.conf`
- **Port**: 6379
- **Memory**: 512MB com LRU eviction
- **Persistence**: AOF + RDB habilitado

### 📊 Grafana
- **Port**: 3000
- **Admin**: admin/admin123
- **Datasources**: PostgreSQL, MongoDB, Redis, Prometheus

### 📈 Prometheus
- **Port**: 9090
- **Targets**: PostgreSQL, MongoDB, Redis, Node metrics
- **Retention**: 200h

## 🔧 Customização

### Modificar Configurações
```bash
# PostgreSQL
vim db/postgres-config/postgresql.conf

# MongoDB
vim db/mongo-config/mongod.conf

# Redis
vim db/redis-config/redis.conf

# Prometheus
vim db/prometheus-config/prometheus.yml
```

### Aplicar Mudanças
```bash
# Reiniciar serviços específicos
docker-compose restart postgres
docker-compose restart mongodb
docker-compose restart redis

# Ou reiniciar tudo
./manage_databases.sh restart
```

## 📦 Volumes de Dados

Os dados são persistidos nas pastas `data/` usando bind mounts para facilitar backup e portabilidade:

- ✅ **Vantagens**: Backup simples, portabilidade, debugging
- ⚠️ **Atenção**: Não deletar as pastas `data/` em produção

## 🔐 Segurança

- Senhas padrão apenas para desenvolvimento
- Em produção, alterar todas as credenciais
- Usar secrets do Docker Swarm ou Kubernetes
- Habilitar SSL/TLS para conexões externas

## 📋 Manutenção

### Backup Manual
```bash
# Backup completo
./manage_databases.sh backup

# Backup individual
./frontend/scripts/backup_databases.sh postgres
```

### Monitoramento
```bash
# Status dos serviços
./manage_databases.sh health

# Logs em tempo real
./manage_databases.sh logs

# Dashboard de monitoramento
./manage_databases.sh monitor
```

## 🚨 Troubleshooting

### Problemas Comuns

1. **Serviço não inicia**
   ```bash
   docker-compose logs [service_name]
   ```

2. **Falta de espaço em disco**
   ```bash
   df -h ./db/data/
   docker system prune -f
   ```

3. **Performance lenta**
   ```bash
   # Verificar métricas
   curl http://localhost:9090  # Prometheus
   curl http://localhost:3000  # Grafana
   ```

4. **Reset completo**
   ```bash
   ./manage_databases.sh clean
   ./manage_databases.sh start
   ```
