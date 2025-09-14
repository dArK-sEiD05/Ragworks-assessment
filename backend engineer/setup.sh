#!/bin/bash

echo "🚀 Setting up Backend Engineer Assessment Environment..."

# Create network if it doesn't exist
docker network create interview_network 2>/dev/null || true
docker network create ecommerce_network 2>/dev/null || true
docker network create performance_network 2>/dev/null || true

echo "✅ Networks created successfully!"

# Function to setup a problem
setup_problem() {
    local problem_name=$1
    local problem_path=$2
    
    echo "📁 Setting up $problem_name..."
    
    if [ -d "$problem_path" ]; then
        echo "  - Installing dependencies..."
        if [ -f "$problem_path/requirements.txt" ]; then
            pip install -r "$problem_path/requirements.txt" > /dev/null 2>&1
        fi
        
        echo "  - Setting up Docker services..."
        if [ -f "$problem_path/docker-compose.yml" ]; then
            cd "$problem_path"
            docker-compose up -d > /dev/null 2>&1
            cd - > /dev/null
        fi
        
        echo "  ✅ $problem_name setup complete!"
    else
        echo "  ❌ $problem_name directory not found!"
    fi
}

# Setup all problems
setup_problem "Problem 1: RESTful API" "problems/problem-1"
setup_problem "Problem 2: Microservices" "problems/problem-2"
setup_problem "Problem 3: Performance Optimization" "problems/problem-3"

# Setup main services
echo "🐳 Starting main infrastructure services..."
docker-compose up -d

echo ""
echo "🎉 Backend Engineer Assessment Environment Ready!"
echo ""
echo "📊 Available Services:"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
echo "  - MongoDB: localhost:27017"
echo "  - RabbitMQ: localhost:5672 (Management: localhost:15672)"
echo "  - Memcached: localhost:11211"
echo ""
echo "🔧 Problem-Specific Services:"
echo "  - Problem 1 API: http://localhost:8000"
echo "  - Problem 2 API Gateway: http://localhost:8000"
echo "  - Problem 2 User Service: http://localhost:8001"
echo "  - Problem 2 Product Service: http://localhost:8002"
echo "  - Problem 2 Order Service: http://localhost:8003"
echo "  - Problem 3 Performance Demo: http://localhost:8000"
echo "  - Problem 3 Load Testing: http://localhost:8089"
echo ""
echo "📚 Documentation:"
echo "  - Main README: ./README.md"
echo "  - Problem 1: ./problems/problem-1/README.md"
echo "  - Problem 2: ./problems/problem-2/README.md"
echo "  - Problem 3: ./problems/problem-3/README.md"
echo "  - Evaluation Guide: ./evaluation/README.md"
echo "  - Examples: ./examples/README.md"
echo ""
echo "🧪 Running Tests:"
echo "  - Problem 1: cd problems/problem-1 && pytest tests/"
echo "  - Problem 2: cd problems/problem-2 && pytest tests/"
echo "  - Problem 3: cd problems/problem-3 && locust -f tests/load_test.py"
echo ""
echo "🛑 To stop all services:"
echo "  docker-compose down"
echo "  docker-compose -f problems/problem-1/docker-compose.yml down"
echo "  docker-compose -f problems/problem-2/docker-compose.yml down"
echo "  docker-compose -f problems/problem-3/docker-compose.yml down"
echo ""
echo "Good luck with your assessment! 🎯"

