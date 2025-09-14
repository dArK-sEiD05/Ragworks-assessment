#!/bin/bash

echo "🚀 Starting Backend Engineer Services..."

# Create network if it doesn't exist
docker network create interview_network 2>/dev/null || true

# Start base services first
docker-compose up -d

echo "✅ Backend services started!"
echo "📊 Available services:"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
echo "  - MongoDB: localhost:27017"
echo "  - RabbitMQ: localhost:5672 (Management: localhost:15672)"
echo "  - Memcached: localhost:11211"
echo "  - Postman: Available in container"

echo ""
echo "🔧 To stop: docker-compose down"
echo "📝 To view logs: docker-compose logs -f [service]"

