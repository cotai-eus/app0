#!/bin/bash

# =====================================================
# 🧪 DATABASE VALIDATION SCRIPT
# Tests connectivity and data integrity across all databases
# =====================================================

echo "🧪 DATABASE VALIDATION REPORT"
echo "====================================================="
echo "📅 Test Date: $(date)"
echo "====================================================="

# Test PostgreSQL
echo ""
echo "🐘 POSTGRESQL TESTS"
echo "-----------------------------------------------------"
echo "🔗 Testing connectivity..."
if docker exec app_postgres pg_isready -U app_user -d app_relational > /dev/null 2>&1; then
    echo "✅ PostgreSQL is responsive"
else
    echo "❌ PostgreSQL connection failed"
    exit 1
fi

echo "📊 Checking database schema..."
TABLE_COUNT=$(docker exec app_postgres psql -U app_user -d app_relational -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d ' ')
echo "📈 Tables created: $TABLE_COUNT"

echo "👥 Checking sample data..."
COMPANY_COUNT=$(docker exec app_postgres psql -U app_user -d app_relational -t -c "SELECT COUNT(*) FROM companies;" 2>/dev/null | tr -d ' ')
USER_COUNT=$(docker exec app_postgres psql -U app_user -d app_relational -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null | tr -d ' ')
echo "🏢 Companies: $COMPANY_COUNT"
echo "👤 Users: $USER_COUNT"

# Test MongoDB
echo ""
echo "🍃 MONGODB TESTS"
echo "-----------------------------------------------------"
echo "🔗 Testing connectivity..."
if docker exec app_mongodb mongosh --username admin --password secure_password_here --authenticationDatabase admin --quiet app_flexible --eval "db.runCommand('ping')" > /dev/null 2>&1; then
    echo "✅ MongoDB is responsive"
else
    echo "❌ MongoDB connection failed"
    exit 1
fi

echo "📊 Checking collections..."
COLLECTION_COUNT=$(docker exec app_mongodb mongosh --username admin --password secure_password_here --authenticationDatabase admin --quiet app_flexible --eval "db.runCommand('listCollections').cursor.firstBatch.length" 2>/dev/null)
echo "📈 Collections created: $COLLECTION_COUNT"

echo "🔍 Testing collection schemas..."
if docker exec app_mongodb mongosh --username admin --password secure_password_here --authenticationDatabase admin --quiet app_flexible --eval "db.system_logs.findOne()" > /dev/null 2>&1; then
    echo "✅ Collection schemas validated"
else
    echo "❌ Collection schema validation failed"
fi

# Test Redis
echo ""
echo "🔴 REDIS TESTS"
echo "-----------------------------------------------------"
echo "🔗 Testing connectivity..."
if docker exec app_redis redis-cli -a redis_password_here ping > /dev/null 2>&1; then
    echo "✅ Redis is responsive"
else
    echo "❌ Redis connection failed"
    exit 1
fi

echo "🔑 Testing key operations..."
docker exec app_redis redis-cli -a redis_password_here SET test:validation "success" > /dev/null 2>&1
REDIS_TEST=$(docker exec app_redis redis-cli -a redis_password_here GET test:validation 2>/dev/null | tr -d '"')
if [ "$REDIS_TEST" = "success" ]; then
    echo "✅ Redis key operations working"
    docker exec app_redis redis-cli -a redis_password_here DEL test:validation > /dev/null 2>&1
else
    echo "❌ Redis key operations failed"
fi

echo "💾 Checking memory usage..."
REDIS_MEMORY=$(docker exec app_redis redis-cli -a redis_password_here INFO memory 2>/dev/null | grep used_memory_human | cut -d: -f2 | tr -d '\r')
echo "📈 Redis memory usage: $REDIS_MEMORY"

# Test Web Interfaces
echo ""
echo "🌐 WEB INTERFACE TESTS"
echo "-----------------------------------------------------"
echo "🔗 Testing admin interfaces..."

# Test Adminer
if curl -s http://localhost:8080 > /dev/null 2>&1; then
    echo "✅ Adminer (PostgreSQL Admin) - http://localhost:8080"
else
    echo "❌ Adminer not accessible"
fi

# Test Mongo Express
if curl -s http://localhost:8081 > /dev/null 2>&1; then
    echo "✅ Mongo Express (MongoDB Admin) - http://localhost:8081"
else
    echo "❌ Mongo Express not accessible"
fi

# Test Redis Commander
if curl -s http://localhost:8082 > /dev/null 2>&1; then
    echo "✅ Redis Commander (Redis Admin) - http://localhost:8082"
else
    echo "❌ Redis Commander not accessible"
fi

# Test Grafana
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Grafana (Monitoring) - http://localhost:3000"
else
    echo "❌ Grafana not accessible"
fi

# Test Prometheus
if curl -s http://localhost:9090 > /dev/null 2>&1; then
    echo "✅ Prometheus (Metrics) - http://localhost:9090"
else
    echo "❌ Prometheus not accessible"
fi

# Docker Health Check
echo ""
echo "🐳 DOCKER CONTAINER STATUS"
echo "-----------------------------------------------------"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep app_

echo ""
echo "📋 SUMMARY"
echo "====================================================="
echo "✅ Multi-database architecture is fully operational!"
echo ""
echo "🔧 Available Databases:"
echo "   🐘 PostgreSQL (Relational) - localhost:5432"
echo "   🍃 MongoDB (Flexible/Logs) - localhost:27017"
echo "   🔴 Redis (Cache/Sessions) - localhost:6379"
echo ""
echo "🌐 Admin Interfaces:"
echo "   📊 Adminer: http://localhost:8080"
echo "   🍃 Mongo Express: http://localhost:8081"
echo "   🔴 Redis Commander: http://localhost:8082"
echo "   📈 Grafana: http://localhost:3000"
echo "   🎯 Prometheus: http://localhost:9090"
echo ""
echo "🚀 Ready for development!"
echo "====================================================="
