@echo off
REM Performance Optimization Demo Startup Script for Windows

echo 🚀 Starting Performance Optimization Demo...

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not running. Please start Docker and try again.
    exit /b 1
)

REM Check if Docker Compose is available
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose is not installed. Please install Docker Compose and try again.
    exit /b 1
)

REM Create necessary directories
if not exist "logs" mkdir logs
if not exist "data\postgres" mkdir data\postgres
if not exist "data\redis" mkdir data\redis

REM Start services
echo 📦 Starting services with Docker Compose...
docker-compose up -d

REM Wait for services to be ready
echo ⏳ Waiting for services to be ready...
timeout /t 10 /nobreak >nul

REM Check if services are running
echo 🔍 Checking service health...

REM Check PostgreSQL
docker-compose exec postgres pg_isready -U postgres >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ PostgreSQL is ready
) else (
    echo ❌ PostgreSQL is not ready
    exit /b 1
)

REM Check Redis
docker-compose exec redis redis-cli ping >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Redis is ready
) else (
    echo ❌ Redis is not ready
    exit /b 1
)

REM Run database migration
echo 🗄️ Running database migration...
docker-compose exec app python migrations/001_initial_migration.py

REM Check application health
echo 🏥 Checking application health...
timeout /t 5 /nobreak >nul

curl -f http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Application is healthy
) else (
    echo ❌ Application is not healthy
    exit /b 1
)

echo.
echo 🎉 Performance Optimization Demo is ready!
echo.
echo 📊 Available endpoints:
echo   • API Documentation: http://localhost:8000/docs
echo   • Health Check: http://localhost:8000/health
echo   • Monitoring Dashboard: http://localhost:8000/dashboard
echo   • Performance Metrics: http://localhost:8000/metrics
echo.
echo 🧪 Testing:
echo   • Load Testing: http://localhost:8089 (Locust)
echo   • Run benchmarks: python scripts/benchmark.py
echo   • Run tests: python scripts/run_tests.py
echo.
echo 📈 Monitoring:
echo   • Real-time Dashboard: http://localhost:8000/dashboard
echo   • Cache Stats: http://localhost:8000/cache/stats
echo   • Search Stats: http://localhost:8000/search/stats
echo.
echo 🛑 To stop the demo:
echo   docker-compose down
echo.
