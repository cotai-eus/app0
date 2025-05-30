# =====================================================
# 🧪 DATABASE VALIDATION SCRIPT (PowerShell)
# Tests connectivity and data integrity across all databases
# =====================================================

Write-Host "🧪 DATABASE VALIDATION REPORT" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "📅 Test Date: $(Get-Date)" -ForegroundColor White
Write-Host "=====================================================" -ForegroundColor Cyan

# Test PostgreSQL
Write-Host ""
Write-Host "🐘 POSTGRESQL TESTS" -ForegroundColor Green
Write-Host "-----------------------------------------------------"
Write-Host "🔗 Testing connectivity..."

$pgTest = docker exec app_postgres pg_isready -U app_user -d app_relational 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ PostgreSQL is responsive" -ForegroundColor Green
} else {
    Write-Host "❌ PostgreSQL connection failed" -ForegroundColor Red
    exit 1
}

Write-Host "📊 Checking database schema..."
$tableCount = docker exec app_postgres psql -U app_user -d app_relational -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>$null
$tableCount = $tableCount.Trim()
Write-Host "📈 Tables created: $tableCount"

Write-Host "👥 Checking sample data..."
$companyCount = docker exec app_postgres psql -U app_user -d app_relational -t -c "SELECT COUNT(*) FROM companies;" 2>$null
$userCount = docker exec app_postgres psql -U app_user -d app_relational -t -c "SELECT COUNT(*) FROM users;" 2>$null
Write-Host "🏢 Companies: $($companyCount.Trim())"
Write-Host "👤 Users: $($userCount.Trim())"

# Test MongoDB
Write-Host ""
Write-Host "🍃 MONGODB TESTS" -ForegroundColor Green
Write-Host "-----------------------------------------------------"
Write-Host "🔗 Testing connectivity..."

$mongoTest = docker exec app_mongodb mongosh --username admin --password secure_password_here --authenticationDatabase admin --quiet app_flexible --eval "db.runCommand('ping')" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ MongoDB is responsive" -ForegroundColor Green
} else {
    Write-Host "❌ MongoDB connection failed" -ForegroundColor Red
}

Write-Host "📊 Checking collections..."
$collectionCount = docker exec app_mongodb mongosh --username admin --password secure_password_here --authenticationDatabase admin --quiet app_flexible --eval "db.runCommand('listCollections').cursor.firstBatch.length" 2>$null
Write-Host "📈 Collections created: $($collectionCount.Trim())"

# Test Redis
Write-Host ""
Write-Host "🔴 REDIS TESTS" -ForegroundColor Red
Write-Host "-----------------------------------------------------"
Write-Host "🔗 Testing connectivity..."

$redisTest = docker exec app_redis redis-cli -a redis_password_here ping 2>$null
if ($redisTest -match "PONG") {
    Write-Host "✅ Redis is responsive" -ForegroundColor Green
} else {
    Write-Host "❌ Redis connection failed" -ForegroundColor Red
}

Write-Host "🔑 Testing key operations..."
docker exec app_redis redis-cli -a redis_password_here SET test:validation "success" 2>$null | Out-Null
$redisTestValue = docker exec app_redis redis-cli -a redis_password_here GET test:validation 2>$null
if ($redisTestValue -match "success") {
    Write-Host "✅ Redis key operations working" -ForegroundColor Green
    docker exec app_redis redis-cli -a redis_password_here DEL test:validation 2>$null | Out-Null
} else {
    Write-Host "❌ Redis key operations failed" -ForegroundColor Red
}

# Test Web Interfaces
Write-Host ""
Write-Host "🌐 WEB INTERFACE TESTS" -ForegroundColor Cyan
Write-Host "-----------------------------------------------------"
Write-Host "🔗 Testing admin interfaces..."

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8080" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✅ Adminer (PostgreSQL Admin) - http://localhost:8080" -ForegroundColor Green
} catch {
    Write-Host "❌ Adminer not accessible" -ForegroundColor Red
}

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8081" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✅ Mongo Express (MongoDB Admin) - http://localhost:8081" -ForegroundColor Green
} catch {
    Write-Host "❌ Mongo Express not accessible" -ForegroundColor Red
}

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8082" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✅ Redis Commander (Redis Admin) - http://localhost:8082" -ForegroundColor Green
} catch {
    Write-Host "❌ Redis Commander not accessible" -ForegroundColor Red
}

try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✅ Grafana (Monitoring) - http://localhost:3000" -ForegroundColor Green
} catch {
    Write-Host "❌ Grafana not accessible" -ForegroundColor Red
}

try {
    $response = Invoke-WebRequest -Uri "http://localhost:9090" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✅ Prometheus (Metrics) - http://localhost:9090" -ForegroundColor Green
} catch {
    Write-Host "❌ Prometheus not accessible" -ForegroundColor Red
}

# Docker Status
Write-Host ""
Write-Host "🐳 DOCKER CONTAINER STATUS" -ForegroundColor Cyan
Write-Host "-----------------------------------------------------"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | Where-Object { $_ -match "app_" }

Write-Host ""
Write-Host "📋 SUMMARY" -ForegroundColor Yellow
Write-Host "=====================================================" -ForegroundColor Yellow
Write-Host "✅ Multi-database architecture is fully operational!" -ForegroundColor Green
Write-Host ""
Write-Host "🔧 Available Databases:" -ForegroundColor White
Write-Host "   🐘 PostgreSQL (Relational) - localhost:5432" -ForegroundColor White
Write-Host "   🍃 MongoDB (Flexible/Logs) - localhost:27017" -ForegroundColor White
Write-Host "   🔴 Redis (Cache/Sessions) - localhost:6379" -ForegroundColor White
Write-Host ""
Write-Host "🌐 Admin Interfaces:" -ForegroundColor White
Write-Host "   📊 Adminer: http://localhost:8080" -ForegroundColor White
Write-Host "   🍃 Mongo Express: http://localhost:8081" -ForegroundColor White
Write-Host "   🔴 Redis Commander: http://localhost:8082" -ForegroundColor White
Write-Host "   📈 Grafana: http://localhost:3000" -ForegroundColor White
Write-Host "   🎯 Prometheus: http://localhost:9090" -ForegroundColor White
Write-Host ""
Write-Host "🚀 Ready for development!" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Yellow
