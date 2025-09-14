#!/bin/bash

# Start E-commerce Microservices
echo "Starting E-commerce Microservices..."

# Start infrastructure services first
echo "Starting infrastructure services..."
docker-compose up -d postgres redis rabbitmq

# Wait for infrastructure to be ready
echo "Waiting for infrastructure services to be ready..."
sleep 30

# Initialize database
echo "Initializing database..."
python init_db.py

# Start microservices
echo "Starting microservices..."
docker-compose up -d api-gateway user-service product-service order-service

echo "All services started successfully!"
echo "API Gateway: http://localhost:8000"
echo "User Service: http://localhost:8001"
echo "Product Service: http://localhost:8002"
echo "Order Service: http://localhost:8003"
echo "RabbitMQ Management: http://localhost:15672"
