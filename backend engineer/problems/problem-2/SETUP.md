# E-commerce Microservices Setup Guide

This guide will help you set up and run the complete e-commerce microservices architecture.

## Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Git

## Quick Start

1. **Clone and navigate to the project:**
   ```bash
   cd problems/problem-2
   ```

2. **Start all services:**
   ```bash
   docker-compose up -d
   ```

3. **Initialize the database:**
   ```bash
   python init_db.py
   ```

4. **Verify services are running:**
   ```bash
   # Check API Gateway
   curl http://localhost:8000/health
   
   # Check User Service
   curl http://localhost:8001/health
   
   # Check Product Service
   curl http://localhost:8002/health
   
   # Check Order Service
   curl http://localhost:8003/health
   ```

## Service Endpoints

### API Gateway (Port 8000)
- **Health Check:** `GET /health`
- **User Auth:** `POST /auth/register`, `POST /auth/login`
- **User Management:** `GET /users/{id}`, `PUT /users/{id}`
- **Products:** `GET /products`, `GET /products/{id}`, `GET /products/search`
- **Orders:** `GET /orders`, `POST /orders`, `GET /orders/{id}`

### User Service (Port 8001)
- **Health Check:** `GET /health`
- **Authentication:** `POST /auth/register`, `POST /auth/login`, `GET /auth/me`
- **User Management:** `GET /users/{id}`, `PUT /users/{id}`, `GET /users/{id}/orders`

### Product Service (Port 8002)
- **Health Check:** `GET /health`
- **Products:** `GET /products`, `GET /products/{id}`, `POST /products`, `PUT /products/{id}`, `DELETE /products/{id}`
- **Search:** `GET /products/search`
- **Categories:** `GET /categories`, `POST /categories`

### Order Service (Port 8003)
- **Health Check:** `GET /health`
- **Orders:** `GET /orders/{id}`, `POST /orders`, `GET /orders/user/{user_id}`
- **Order Management:** `PUT /orders/{id}/status`, `POST /orders/{id}/cancel`

## Testing

1. **Install test dependencies:**
   ```bash
   pip install -r tests/requirements.txt
   ```

2. **Run tests:**
   ```bash
   # Run all tests
   pytest tests/ -v
   
   # Run specific test files
   pytest tests/test_api_gateway.py -v
   pytest tests/test_user_service.py -v
   pytest tests/test_product_service.py -v
   pytest tests/test_order_service.py -v
   pytest tests/test_integration.py -v
   ```

## Example API Usage

### 1. Register a User
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "password": "password123",
    "first_name": "Test",
    "last_name": "User"
  }'
```

### 2. Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

### 3. Get Products
```bash
curl http://localhost:8000/products
```

### 4. Search Products
```bash
curl "http://localhost:8000/products/search?q=laptop"
```

### 5. Create Order (requires authentication)
```bash
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "shipping_address": "123 Main St, City, State 12345",
    "billing_address": "123 Main St, City, State 12345",
    "items": [
      {
        "product_id": 1,
        "quantity": 2,
        "unit_price": 29.99,
        "total_price": 59.98
      }
    ]
  }'
```

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Gateway   │    │   Load Balancer │    │   Service Mesh  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
    ┌────────────────────────────┼────────────────────────────┐
    │                            │                            │
┌───▼───┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
│ User  │  │Product  │  │ Order   │  │Payment  │  │Notification│
│Service│  │Service  │  │Service  │  │Service  │  │Service  │
└───┬───┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘
    │           │           │           │           │
    └───────────┼───────────┼───────────┼───────────┘
                │           │           │
        ┌───────▼───┐ ┌─────▼───┐ ┌─────▼───┐
        │   Redis   │ │RabbitMQ │ │PostgreSQL│
        │  (Cache)  │ │(Events) │ │ (Data)  │
        └───────────┘ └─────────┘ └─────────┘
```

## Monitoring

- **RabbitMQ Management:** http://localhost:15672
  - Username: `ecommerce_user`
  - Password: `ecommerce_password`

- **Service Health:** Each service provides a `/health` endpoint
- **API Gateway Health:** Aggregates health status of all services

## Troubleshooting

### Common Issues

1. **Services not starting:**
   - Check if ports 8000-8003, 5432, 6379, 5672, 15672 are available
   - Ensure Docker is running
   - Check logs: `docker-compose logs [service_name]`

2. **Database connection issues:**
   - Wait for PostgreSQL to fully start (30-60 seconds)
   - Check if database initialization completed successfully

3. **Authentication issues:**
   - Ensure you're using the correct token format: `Bearer YOUR_TOKEN`
   - Check if user exists and is active

4. **Message queue issues:**
   - Check RabbitMQ management interface
   - Verify exchange and queue creation

### Logs

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs api-gateway
docker-compose logs user-service
docker-compose logs product-service
docker-compose logs order-service

# Follow logs in real-time
docker-compose logs -f [service_name]
```

## Development

### Adding New Features

1. **New Service:**
   - Create service directory with `main.py`, `Dockerfile`, `requirements.txt`
   - Add to `docker-compose.yml`
   - Update API Gateway routing
   - Add health check endpoint

2. **New Endpoints:**
   - Add to service `main.py`
   - Update API Gateway routing
   - Add tests
   - Update documentation

3. **New Events:**
   - Add event type to `shared/schemas.py`
   - Update message handlers
   - Add event publishing/consuming logic

### Code Structure

```
problems/problem-2/
├── api-gateway/          # API Gateway service
├── user-service/         # User management service
├── product-service/      # Product catalog service
├── order-service/        # Order management service
├── shared/              # Shared components
│   ├── schemas.py       # Common Pydantic schemas
│   └── messaging.py     # Message queue utilities
├── tests/               # Test suite
├── scripts/             # Utility scripts
├── docker-compose.yml   # Service orchestration
├── init_db.py          # Database initialization
└── README.md           # This file
```

## Performance Considerations

- **Caching:** Redis is used for session management and caching
- **Rate Limiting:** API Gateway implements rate limiting (100 requests/minute)
- **Database:** PostgreSQL with proper indexing
- **Message Queue:** RabbitMQ for async communication
- **Load Balancing:** Can be added with additional API Gateway instances

## Security

- **Authentication:** JWT tokens with configurable expiration
- **Password Hashing:** bcrypt with salt
- **CORS:** Configured for cross-origin requests
- **Rate Limiting:** Prevents abuse
- **Input Validation:** Pydantic schemas for all inputs
- **SQL Injection:** SQLAlchemy ORM prevents SQL injection

## Scaling

- **Horizontal Scaling:** Add more instances of each service
- **Database:** Use read replicas for read-heavy operations
- **Caching:** Redis cluster for distributed caching
- **Message Queue:** RabbitMQ cluster for high availability
- **Load Balancing:** Use external load balancer (nginx, HAProxy)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

## License

This project is part of a backend role evaluation and is for demonstration purposes.
