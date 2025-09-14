#!/bin/bash

# Performance Optimization Demo Startup Script

set -e

echo "🚀 Starting Performance Optimization Demo..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose and try again."
    exit 1
fi

# Create necessary directories
mkdir -p logs
mkdir -p data/postgres
mkdir -p data/redis

# Start services
echo "📦 Starting services with Docker Compose..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
echo "🔍 Checking service health..."

# Check PostgreSQL
if docker-compose exec postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo "✅ PostgreSQL is ready"
else
    echo "❌ PostgreSQL is not ready"
    exit 1
fi

# Check Redis
if docker-compose exec redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is ready"
else
    echo "❌ Redis is not ready"
    exit 1
fi

# Run database migration
echo "🗄️ Running database migration..."
docker-compose exec app python migrations/001_initial_migration.py

# Check application health
echo "🏥 Checking application health..."
sleep 5

if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Application is healthy"
else
    echo "❌ Application is not healthy"
    exit 1
fi

echo ""
echo "🎉 Performance Optimization Demo is ready!"
echo ""
echo "📊 Available endpoints:"
echo "  • API Documentation: http://localhost:8000/docs"
echo "  • Health Check: http://localhost:8000/health"
echo "  • Monitoring Dashboard: http://localhost:8000/dashboard"
echo "  • Performance Metrics: http://localhost:8000/metrics"
echo ""
echo "🧪 Testing:"
echo "  • Load Testing: http://localhost:8089 (Locust)"
echo "  • Run benchmarks: python scripts/benchmark.py"
echo "  • Run tests: python scripts/run_tests.py"
echo ""
echo "📈 Monitoring:"
echo "  • Real-time Dashboard: http://localhost:8000/dashboard"
echo "  • Cache Stats: http://localhost:8000/cache/stats"
echo "  • Search Stats: http://localhost:8000/search/stats"
echo ""
echo "🛑 To stop the demo:"
echo "  docker-compose down"
echo ""
