#!/usr/bin/env python3
"""
=====================================================
🐍 SCRIPT DE CRIAÇÃO DE DADOS INICIAIS
Cria dados de exemplo para desenvolvimento e testes
=====================================================
"""

import os
import sys
import uuid
import asyncio
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

# Database connections
import asyncpg
import motor.motor_asyncio
import redis.asyncio as redis

# Configuration
POSTGRES_URL = os.getenv('POSTGRES_URL', 
    'postgresql://app_user:secure_password_here@localhost:5432/app_relational')
MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb://localhost:27017')
MONGODB_DB = os.getenv('MONGODB_DB', 'app_flexible')
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')

class DatabaseInitializer:
    """Inicializador de dados para os três bancos de dados"""
    
    def __init__(self):
        self.pg_pool = None
        self.mongo_client = None
        self.mongo_db = None
        self.redis_client = None
    
    async def connect_databases(self):
        """Conecta com todos os bancos de dados"""
        print("🔌 Connecting to databases...")
        
        # PostgreSQL
        try:
            self.pg_pool = await asyncpg.create_pool(POSTGRES_URL)
            print("✅ PostgreSQL connected")
        except Exception as e:
            print(f"❌ PostgreSQL connection failed: {e}")
            sys.exit(1)
        
        # MongoDB
        try:
            self.mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
            self.mongo_db = self.mongo_client[MONGODB_DB]
            # Test connection
            await self.mongo_client.admin.command('ping')
            print("✅ MongoDB connected")
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            sys.exit(1)
        
        # Redis
        try:
            self.redis_client = redis.from_url(REDIS_URL)
            await self.redis_client.ping()
            print("✅ Redis connected")
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
            sys.exit(1)
    
    async def close_connections(self):
        """Fecha todas as conexões"""
        if self.pg_pool:
            await self.pg_pool.close()
        if self.mongo_client:
            self.mongo_client.close()
        if self.redis_client:
            await self.redis_client.close()
    
    async def create_companies(self) -> List[Dict]:
        """Cria empresas de exemplo"""
        print("🏢 Creating sample companies...")
        
        companies = [
            {
                'id': str(uuid.uuid4()),
                'name': 'TechCorp Solutions',
                'slug': 'techcorp-solutions',
                'legal_name': 'TechCorp Solutions Ltda.',
                'cnpj': '12.345.678/0001-90',
                'email': 'contato@techcorp.com',
                'phone': '+55 11 98765-4321',
                'website': 'https://techcorp.com',
                'address_line1': 'Av. Paulista, 1000',
                'city': 'São Paulo',
                'state': 'SP',
                'postal_code': '01310-100',
                'country': 'Brazil',
                'subscription_tier': 'premium',
                'is_active': True,
                'settings': json.dumps({
                    'theme': 'dark',
                    'language': 'pt-BR',
                    'timezone': 'America/Sao_Paulo'
                })
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'InnovaCorp',
                'slug': 'innovacorp',
                'legal_name': 'InnovaCorp Tecnologia S.A.',
                'cnpj': '98.765.432/0001-10',
                'email': 'hello@innovacorp.io',
                'phone': '+55 21 91234-5678',
                'website': 'https://innovacorp.io',
                'address_line1': 'Rua das Flores, 200',
                'city': 'Rio de Janeiro',
                'state': 'RJ',
                'postal_code': '22071-900',
                'country': 'Brazil',
                'subscription_tier': 'standard',
                'is_active': True,
                'settings': json.dumps({
                    'theme': 'light',
                    'language': 'en-US',
                    'timezone': 'America/Sao_Paulo'
                })
            }
        ]
        
        async with self.pg_pool.acquire() as conn:
            for company in companies:
                await conn.execute("""
                    INSERT INTO companies (
                        id, name, slug, legal_name, cnpj, email, phone, website,
                        address_line1, city, state, postal_code, country,
                        subscription_tier, is_active, settings
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16
                    ) ON CONFLICT (slug) DO NOTHING
                """, *company.values())
        
        print(f"✅ Created {len(companies)} companies")
        return companies
    
    async def create_users(self, companies: List[Dict]) -> List[Dict]:
        """Cria usuários de exemplo"""
        print("👥 Creating sample users...")
        
        users = []
        for i, company in enumerate(companies):
            # Admin user for each company
            admin_user = {
                'id': str(uuid.uuid4()),
                'email': f'admin@{company["slug"]}.com',
                'username': f'admin_{company["slug"]}',
                'password_hash': hashlib.sha256('admin123'.encode()).hexdigest(),
                'first_name': 'Admin',
                'last_name': 'User',
                'is_active': True,
                'is_verified': True,
                'is_superuser': False
            }
            users.append(admin_user)
            
            # Regular user for each company
            regular_user = {
                'id': str(uuid.uuid4()),
                'email': f'user@{company["slug"]}.com',
                'username': f'user_{company["slug"]}',
                'password_hash': hashlib.sha256('user123'.encode()).hexdigest(),
                'first_name': 'Regular',
                'last_name': 'User',
                'is_active': True,
                'is_verified': True,
                'is_superuser': False
            }
            users.append(regular_user)
        
        # Super admin
        super_admin = {
            'id': str(uuid.uuid4()),
            'email': 'superadmin@system.com',
            'username': 'superadmin',
            'password_hash': hashlib.sha256('superadmin123'.encode()).hexdigest(),
            'first_name': 'Super',
            'last_name': 'Admin',
            'is_active': True,
            'is_verified': True,
            'is_superuser': True
        }
        users.append(super_admin)
        
        async with self.pg_pool.acquire() as conn:
            for user in users:
                await conn.execute("""
                    INSERT INTO users (
                        id, email, username, password_hash, first_name, last_name,
                        is_active, is_verified, is_superuser
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (email) DO NOTHING
                """, *user.values())
        
        print(f"✅ Created {len(users)} users")
        return users
    
    async def create_user_profiles_and_associations(self, users: List[Dict], companies: List[Dict]):
        """Cria perfis de usuários e associações com empresas"""
        print("📝 Creating user profiles and company associations...")
        
        async with self.pg_pool.acquire() as conn:
            # Create profiles and company associations
            for i, user in enumerate(users[:-1]):  # Exclude super admin
                company = companies[i // 2]  # 2 users per company
                
                # Create user profile
                await conn.execute("""
                    INSERT INTO user_profiles (
                        user_id, phone, avatar_url, bio, timezone, language, preferences
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (user_id) DO NOTHING
                """, 
                    user['id'],
                    f'+55 11 9{i:04d}-{i+1000:04d}',
                    f'https://avatars.example.com/{user["id"]}.jpg',
                    f'Bio for {user["first_name"]} {user["last_name"]}',
                    'America/Sao_Paulo',
                    'pt-BR',
                    json.dumps({
                        'notifications': True,
                        'theme': 'auto',
                        'dashboard_layout': 'default'
                    })
                )
                
                # Create company association
                role = 'admin' if 'admin' in user['email'] else 'member'
                await conn.execute("""
                    INSERT INTO company_users (
                        company_id, user_id, role, permissions, is_active
                    ) VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (company_id, user_id) DO NOTHING
                """,
                    company['id'],
                    user['id'],
                    role,
                    json.dumps(['read', 'write'] if role == 'admin' else ['read']),
                    True
                )
        
        print("✅ Created user profiles and company associations")
    
    async def create_mongodb_sample_data(self, companies: List[Dict], users: List[Dict]):
        """Cria dados de exemplo no MongoDB"""
        print("🍃 Creating MongoDB sample data...")
        
        # System logs
        system_logs = []
        for i in range(50):
            log = {
                'level': ['info', 'warning', 'error', 'debug'][i % 4],
                'message': f'Sample log message {i+1}',
                'timestamp': datetime.utcnow() - timedelta(hours=i),
                'source': f'module_{(i % 5) + 1}',
                'user_id': users[i % len(users)]['id'],
                'company_id': companies[i % len(companies)]['id'],
                'metadata': {
                    'request_id': str(uuid.uuid4()),
                    'execution_time': i * 10,
                    'memory_usage': 100 + (i * 5)
                }
            }
            system_logs.append(log)
        
        await self.mongo_db.system_logs.insert_many(system_logs)
        
        # User activity logs
        activity_logs = []
        actions = ['login', 'logout', 'view_document', 'create_form', 'update_profile']
        for i in range(30):
            log = {
                'user_id': users[i % len(users)]['id'],
                'company_id': companies[i % len(companies)]['id'],
                'action': actions[i % len(actions)],
                'action_category': 'user_interaction',
                'resource_type': 'document' if i % 3 == 0 else 'form',
                'resource_id': str(uuid.uuid4()),
                'endpoint': f'/api/v1/{actions[i % len(actions)]}',
                'method': 'POST' if i % 2 == 0 else 'GET',
                'ip_address': f'192.168.1.{(i % 254) + 1}',
                'timestamp': datetime.utcnow() - timedelta(minutes=i * 30),
                'success': i % 10 != 0,  # 90% success rate
                'additional_data': {
                    'browser': 'Chrome' if i % 2 == 0 else 'Firefox',
                    'os': 'Windows' if i % 3 == 0 else 'MacOS'
                }
            }
            activity_logs.append(log)
        
        await self.mongo_db.user_activity_logs.insert_many(activity_logs)
        
        # Document metadata
        documents = []
        for i in range(20):
            doc = {
                'document_id': str(uuid.uuid4()),
                'filename': f'document_{i+1}.pdf',
                'original_filename': f'Original Document {i+1}.pdf',
                'file_extension': 'pdf',
                'mime_type': 'application/pdf',
                'file_size_bytes': 1024 * (i + 1) * 10,
                'processing_status': ['completed', 'processing', 'pending'][i % 3],
                'extracted_text': f'Sample extracted text for document {i+1}',
                'ai_summary': f'AI generated summary for document {i+1}',
                'ai_tags': ['important', 'contract', 'legal'][:(i % 3) + 1],
                'uploaded_by': users[i % len(users)]['id'],
                'company_id': companies[i % len(companies)]['id'],
                'uploaded_at': datetime.utcnow() - timedelta(days=i),
                'custom_metadata': {
                    'department': 'Legal' if i % 2 == 0 else 'Finance',
                    'priority': ['low', 'medium', 'high'][i % 3]
                }
            }
            documents.append(doc)
        
        await self.mongo_db.document_metadata.insert_many(documents)
        
        # Dynamic configurations
        configs = [
            {
                'config_key': 'max_file_upload_size',
                'config_value': {'size_mb': 100},
                'company_id': companies[0]['id'],
                'scope': 'company',
                'config_type': 'file_management',
                'is_active': True,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            },
            {
                'config_key': 'ai_processing_enabled',
                'config_value': {'enabled': True, 'models': ['gpt-4', 'claude-3']},
                'company_id': companies[1]['id'],
                'scope': 'company',
                'config_type': 'ai_settings',
                'is_active': True,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
        ]
        
        await self.mongo_db.dynamic_configurations.insert_many(configs)
        
        print("✅ Created MongoDB sample data")
    
    async def create_redis_sample_data(self, users: List[Dict], companies: List[Dict]):
        """Cria dados de exemplo no Redis"""
        print("🔴 Creating Redis sample data...")
        
        # User sessions
        for i, user in enumerate(users[:3]):  # Create sessions for first 3 users
            session_id = str(uuid.uuid4())
            session_key = f"session:user:{user['id']}"
            
            await self.redis_client.hset(session_key, mapping={
                'session_id': session_id,
                'user_id': user['id'],
                'email': user['email'],
                'company_id': companies[i % len(companies)]['id'],
                'created_at': str(int(datetime.utcnow().timestamp())),
                'last_activity': str(int(datetime.utcnow().timestamp())),
                'ip_address': f'192.168.1.{i + 10}',
                'user_agent': 'Mozilla/5.0 (Sample Browser)'
            })
            await self.redis_client.expire(session_key, 86400)  # 24 hours
        
        # Cache some user data
        for i, user in enumerate(users[:2]):
            cache_key = f"cache:user:{user['id']}"
            user_cache = {
                'id': user['id'],
                'email': user['email'],
                'name': f"{user['first_name']} {user['last_name']}",
                'company_id': companies[i % len(companies)]['id'],
                'cached_at': str(int(datetime.utcnow().timestamp()))
            }
            await self.redis_client.hset(cache_key, mapping=user_cache)
            await self.redis_client.expire(cache_key, 3600)  # 1 hour
        
        # Rate limiting data
        for i, user in enumerate(users[:2]):
            rate_key = f"rate_limit:user:{user['id']}:/api/documents"
            await self.redis_client.hset(rate_key, mapping={
                'count': str(i + 1),
                'window_start': str(int(datetime.utcnow().timestamp())),
                'last_request': str(int(datetime.utcnow().timestamp()))
            })
            await self.redis_client.expire(rate_key, 3600)
        
        # Online users
        for company in companies:
            online_key = f"realtime:company:{company['id']}:online_users"
            for user in users[:2]:  # First 2 users are online
                await self.redis_client.sadd(online_key, user['id'])
            await self.redis_client.expire(online_key, 300)  # 5 minutes
        
        # Some counters
        today = datetime.utcnow().strftime('%Y-%m-%d')
        await self.redis_client.set(f"counter:api_calls:/api/documents:{today}", 150)
        await self.redis_client.set(f"counter:api_calls:/api/users:{today}", 75)
        
        print("✅ Created Redis sample data")
    
    async def run(self):
        """Executa a inicialização completa"""
        try:
            await self.connect_databases()
            
            print("\n🚀 Starting database initialization...")
            
            # Create PostgreSQL data
            companies = await self.create_companies()
            users = await self.create_users(companies)
            await self.create_user_profiles_and_associations(users, companies)
            
            # Create MongoDB data
            await self.create_mongodb_sample_data(companies, users)
            
            # Create Redis data
            await self.create_redis_sample_data(users, companies)
            
            print("\n🎉 Database initialization completed successfully!")
            print("\nSample credentials:")
            print("📧 admin@techcorp-solutions.com / admin123")
            print("📧 user@techcorp-solutions.com / user123")
            print("📧 admin@innovacorp.com / admin123")
            print("📧 user@innovacorp.com / user123")
            print("📧 superadmin@system.com / superadmin123")
            
        except Exception as e:
            print(f"❌ Error during initialization: {e}")
            raise
        finally:
            await self.close_connections()

async def main():
    """Função principal"""
    initializer = DatabaseInitializer()
    await initializer.run()

if __name__ == "__main__":
    print("""
    ====================================================
    🐍 DATABASE INITIAL DATA CREATOR
    ====================================================
    
    This script will create sample data in all databases:
    🐘 PostgreSQL: Companies, users, profiles
    🍃 MongoDB: Logs, documents, configurations
    🔴 Redis: Sessions, cache, counters
    
    ====================================================
    """)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Initialization cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Initialization failed: {e}")
        sys.exit(1)
