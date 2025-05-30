# 🌐 Frontend Configuration - `/frontend` Folder

Esta pasta contém configurações do frontend, scripts de inicialização e proxy reverso Nginx.

## 📁 Estrutura de Pastas

```
frontend/
├── scripts/                      # Scripts de automação
│   ├── init_databases.sh         # Inicialização dos bancos
│   ├── backup_databases.sh       # Backup automatizado
│   ├── restore_databases.sh      # Restauração de backups
│   ├── validate_databases.sh     # Validação de integridade
│   ├── validate_databases.ps1    # Validação (PowerShell)
│   ├── create_initial_data.py    # Dados iniciais (Python)
│   ├── postgresql_complete_schema.sql  # Schema PostgreSQL
│   ├── postgresql_simple_schema.sql    # Schema simplificado
│   ├── mongodb_schemas.js         # Schemas MongoDB
│   └── redis_configuration.yml   # Configuração Redis
├── nginx-config/                 # Configurações do Nginx
│   ├── nginx.conf                # Configuração principal
│   └── conf.d/                   # Virtual hosts
│       └── default.conf          # Configurações dos admin panels
├── ssl-certs/                    # Certificados SSL/TLS
└── src/                          # Código fonte do frontend (futura implementação)
```

## 🚀 Scripts de Automação

### 📊 Inicialização dos Bancos (`init_databases.sh`)
```bash
# Uso básico
./frontend/scripts/init_databases.sh

# Com configurações específicas
POSTGRES_DB_NAME=my_app ./frontend/scripts/init_databases.sh

# Inicializar apenas um banco
./frontend/scripts/init_databases.sh postgres
./frontend/scripts/init_databases.sh mongodb
./frontend/scripts/init_databases.sh redis
```

**Funcionalidades:**
- ✅ Verificação de conectividade
- ✅ Criação de schemas e collections
- ✅ Inserção de dados de exemplo
- ✅ Configuração de índices e constraints
- ✅ Validação final

### 💾 Backup Automatizado (`backup_databases.sh`)
```bash
# Backup completo
./frontend/scripts/backup_databases.sh

# Backup com retenção customizada
RETENTION_DAYS=30 ./frontend/scripts/backup_databases.sh

# Backup apenas PostgreSQL
./frontend/scripts/backup_databases.sh postgres
```

**Características:**
- 🗜️ Compressão automática (gzip)
- 📅 Retenção configurável
- 📝 Logs detalhados
- 🔄 Backup incremental (Redis)
- ⚡ Formato otimizado por banco

### 🔄 Restauração (`restore_databases.sh`)
```bash
# Restaurar do backup mais recente
./frontend/scripts/restore_databases.sh

# Restaurar de backup específico
./frontend/scripts/restore_databases.sh /path/to/backup/20231201_120000

# Restaurar apenas um banco
./frontend/scripts/restore_databases.sh postgres /path/to/backup
```

### ✅ Validação (`validate_databases.sh` / `.ps1`)
```bash
# Linux/WSL
./frontend/scripts/validate_databases.sh

# PowerShell (Windows)
./frontend/scripts/validate_databases.ps1
```

**Verificações:**
- 🔗 Conectividade dos bancos
- 📊 Integridade dos dados
- 🏗️ Estrutura das tabelas/collections
- 🔍 Índices e constraints
- 📈 Performance básica

## 🌐 Configuração Nginx

### Proxy Reverso
O Nginx atua como proxy reverso para os admin panels:

```nginx
# Acessos unificados
http://localhost/adminer    # PostgreSQL Admin
http://localhost/mongo      # MongoDB Admin  
http://localhost/redis      # Redis Admin
http://localhost/grafana    # Monitoring
http://localhost/prometheus # Metrics
```

### SSL/TLS (Opcional)
```bash
# Gerar certificado auto-assinado para desenvolvimento
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout frontend/ssl-certs/nginx.key \
  -out frontend/ssl-certs/nginx.crt
```

## 🔧 Personalização

### Variáveis de Ambiente
```bash
# PostgreSQL
export POSTGRES_DB_NAME="my_custom_db"
export POSTGRES_USER="my_user"
export POSTGRES_PASSWORD="my_secure_password"

# MongoDB
export MONGODB_DB_NAME="my_flexible_db"
export MONGODB_AUTH_DB="admin"

# Redis
export REDIS_PASSWORD="my_redis_password"
export REDIS_MAX_MEMORY="1gb"
```

### Scripts Customizados
```bash
# Criar script personalizado
cp frontend/scripts/init_databases.sh frontend/scripts/my_custom_init.sh

# Editar para suas necessidades
vim frontend/scripts/my_custom_init.sh

# Executar
chmod +x frontend/scripts/my_custom_init.sh
./frontend/scripts/my_custom_init.sh
```

## 🐍 Python Scripts

### Dados Iniciais (`create_initial_data.py`)
```python
# Executar dentro do container
docker-compose exec postgres python3 /scripts/create_initial_data.py

# Ou via manage script
./manage_databases.sh init
```

**Funcionalidades:**
- 🏢 Empresas de exemplo
- 👥 Usuários de teste
- 📄 Documentos sample
- 🗓️ Eventos de calendário
- 📊 Dados analíticos

## 📊 SQL Schemas

### Schema Completo (`postgresql_complete_schema.sql`)
- 12 tabelas inter-relacionadas
- Constraints e foreign keys
- Índices otimizados
- Triggers de auditoria
- Views materialized

### Schema Simples (`postgresql_simple_schema.sql`)
- 5 tabelas básicas
- Ideal para testes rápidos
- Estrutura mínima funcional

## 🍃 MongoDB Schemas (`mongodb_schemas.js`)
```javascript
// Validação de documentos
db.createCollection("users", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["email", "name"],
      properties: {
        email: { bsonType: "string" },
        name: { bsonType: "string" }
      }
    }
  }
});
```

## 🚨 Troubleshooting

### Script não executa
```bash
# Verificar permissões
chmod +x frontend/scripts/*.sh

# Verificar dependências
which docker docker-compose curl
```

### Falha na inicialização
```bash
# Logs detalhados
./frontend/scripts/init_databases.sh --verbose

# Debug step-by-step
./frontend/scripts/init_databases.sh --debug
```

### Problemas de conectividade
```bash
# Testar conectividade
./frontend/scripts/validate_databases.sh

# Verificar serviços
docker-compose ps
docker-compose logs
```

### Reset completo
```bash
# Parar tudo
./manage_databases.sh stop

# Limpar dados
rm -rf db/data/*

# Reinicializar
./manage_databases.sh start
./manage_databases.sh init
```

## 📚 Próximos Passos

1. **Frontend React/Vue**: Implementar SPA em `src/`
2. **API Gateway**: Configurar roteamento avançado
3. **SSL/TLS**: Certificados válidos para produção
4. **CI/CD**: Automação de deploy
5. **Monitoring**: Dashboards customizados
