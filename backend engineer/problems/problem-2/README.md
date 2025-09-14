# Problem 2: Microservice Architecture

## Overview
Design and implement a microservice architecture for an e-commerce system using FastAPI, Redis, Message Queue, and Docker Compose.

## Requirements

### Core Services
- **User Service**: Authentication, user profiles, and user management
- **Product Service**: Product catalog, inventory management, and search
- **Order Service**: Order management, payment processing, and order tracking
- **API Gateway**: Request routing, load balancing, and authentication
- **Message Queue**: Inter-service communication and event handling

### Technical Requirements
- FastAPI for each microservice
- Redis for caching and session management
- RabbitMQ for message queuing
- PostgreSQL for data persistence
- Docker Compose for orchestration
- Service discovery and health checks
- Event-driven architecture
- Data consistency strategies

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

## Service Specifications

### User Service
**Port**: 8001
**Database**: users_db
**Endpoints**:
- `POST /auth/register` - User registration
- `POST /auth/login` - User authentication
- `GET /users/{user_id}` - Get user profile
- `PUT /users/{user_id}` - Update user profile
- `GET /users/{user_id}/orders` - Get user orders

### Product Service
**Port**: 8002
**Database**: products_db
**Endpoints**:
- `GET /products` - List products with pagination
- `GET /products/{product_id}` - Get product details
- `POST /products` - Create product (admin only)
- `PUT /products/{product_id}` - Update product (admin only)
- `DELETE /products/{product_id}` - Delete product (admin only)
- `GET /products/search` - Search products
- `GET /products/categories` - Get product categories

### Order Service
**Port**: 8003
**Database**: orders_db
**Endpoints**:
- `POST /orders` - Create new order
- `GET /orders/{order_id}` - Get order details
- `GET /orders/user/{user_id}` - Get user orders
- `PUT /orders/{order_id}/status` - Update order status
- `POST /orders/{order_id}/cancel` - Cancel order

### API Gateway
**Port**: 8000
**Features**:
- Request routing to appropriate services
- Authentication middleware
- Rate limiting
- Request/response logging
- Health check aggregation

## Data Models

### User Service
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    address TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Product Service
```sql
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    category_id INTEGER REFERENCES categories(id),
    stock_quantity INTEGER DEFAULT 0,
    sku VARCHAR(100) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Order Service
```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    shipping_address TEXT NOT NULL,
    billing_address TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL
);
```

## Inter-Service Communication

### Synchronous Communication
- HTTP REST APIs for direct service calls
- API Gateway for request routing
- Service discovery for dynamic routing

### Asynchronous Communication
- RabbitMQ for event publishing/subscribing
- Event types:
  - `user.created`
  - `user.updated`
  - `product.created`
  - `product.updated`
  - `order.created`
  - `order.updated`
  - `order.cancelled`

## Evaluation Criteria

1. **Service Decomposition** (25%)
   - Clear service boundaries
   - Single responsibility principle
   - Proper data ownership

2. **Inter-Service Communication** (20%)
   - RESTful API design
   - Event-driven architecture
   - Error handling and resilience

3. **Data Consistency** (20%)
   - Eventual consistency strategies
   - Transaction management
   - Data synchronization

4. **API Gateway** (15%)
   - Request routing
   - Authentication and authorization
   - Rate limiting and monitoring

5. **Containerization** (10%)
   - Docker configuration
   - Docker Compose orchestration
   - Service health checks

6. **Testing** (10%)
   - Unit tests for each service
   - Integration tests
   - End-to-end testing

## Getting Started

1. Navigate to the problem directory:
   ```bash
   cd problems/problem-2
   ```

2. Start all services:
   ```bash
   docker-compose up -d
   ```

3. Access services:
   - API Gateway: http://localhost:8000
   - User Service: http://localhost:8001
   - Product Service: http://localhost:8002
   - Order Service: http://localhost:8003
   - RabbitMQ Management: http://localhost:15672

4. Run tests:
   ```bash
   pytest tests/ -v
   ```

## Service Communication Examples

### Creating an Order
1. Client sends order request to API Gateway
2. API Gateway validates authentication
3. API Gateway routes to Order Service
4. Order Service validates products with Product Service
5. Order Service creates order and publishes event
6. User Service and Product Service consume events

### Product Search
1. Client sends search request to API Gateway
2. API Gateway routes to Product Service
3. Product Service queries database and cache
4. Product Service returns results through API Gateway

## Monitoring and Observability

- Health check endpoints for each service
- Centralized logging
- Metrics collection
- Distributed tracing
- Error tracking and alerting

## Submission

Submit your solution by:
1. Completing all microservice implementations
2. Configuring Docker Compose for orchestration
3. Implementing inter-service communication
4. Running all tests successfully
5. Creating a pull request with your changes
6. Including architecture diagrams and documentation

