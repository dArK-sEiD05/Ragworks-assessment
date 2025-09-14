#!/bin/bash

# Stop E-commerce Microservices
echo "Stopping E-commerce Microservices..."

# Stop all services
docker-compose down

echo "All services stopped successfully!"
