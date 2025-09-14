# Backend Engineer Assessment

Technical assessment for Backend Engineer candidates focusing on API development, database design, system architecture, and backend best practices.

## Overview

This assessment evaluates candidates on:
- **API Design & Development** - RESTful APIs, GraphQL, microservices
- **Database Design** - Data modeling, SQL optimization, NoSQL solutions
- **System Architecture** - Scalability, performance, security
- **Code Quality** - Clean code, testing, documentation
- **DevOps Integration** - CI/CD, containerization, monitoring

## Assessment Structure

### Problem 1: RESTful API Development
**Difficulty**: Intermediate  
**Time**: 2-3 hours  
**Tech Stack**: FastAPI, PostgreSQL, Docker

Build a RESTful API for a task management system with:
- User authentication and authorization
- CRUD operations for tasks and projects
- Database relationships and constraints
- Input validation and error handling
- API documentation with OpenAPI/Swagger

**Evaluation Criteria**:
- API design patterns and REST conventions
- Database schema design and relationships

# Backend Engineer Assessment

Welcome to the Backend Engineer technical assessment! This project evaluates your skills in API development, database design, system architecture, performance optimization, and backend best practices using real-world scenarios.

---

## 🚀 Quick Start

1. **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd "Interview/backend engineer"
    ```
2. **Set up the environment:**
    - To set up everything (infra + all problems):
       ```bash
       bash setup.sh
       ```
    - To start only the main infrastructure:
       ```bash
       bash start.sh
       ```
3. **Access services:**
    - PostgreSQL: `localhost:5432`
    - Redis: `localhost:6379`
    - MongoDB: `localhost:27017`
    - RabbitMQ: `localhost:5672` (Mgmt: `localhost:15672`)
    - Memcached: `localhost:11211`
    - Problem 1 API: `http://localhost:8000`
    - Problem 2 API Gateway: `http://localhost:8000`
    - Problem 2 User: `http://localhost:8001`
    - Problem 2 Product: `http://localhost:8002`
    - Problem 2 Order: `http://localhost:8003`
    - Problem 3 Demo: `http://localhost:8000`
    - Problem 3 Load Testing: `http://localhost:8089`

---

## 📝 Assessment Problems

### 1. RESTful API Development
- **Stack:** FastAPI, PostgreSQL, Docker
- **Goal:** Build a task management API with authentication, CRUD, and relationships.
- **Location:** `problems/problem-1/`

### 2. Microservice Architecture
- **Stack:** FastAPI, Redis, RabbitMQ, Docker Compose
- **Goal:** Design an e-commerce system with user, product, and order microservices, plus an API gateway.
- **Location:** `problems/problem-2/`

### 3. Performance Optimization
- **Stack:** FastAPI, PostgreSQL, Redis
- **Goal:** Optimize a slow API endpoint using DB tuning, caching, async, and benchmarking.
- **Location:** `problems/problem-3/`

---

## 🏗️ Project Structure

```
backend engineer/
├── problems/
│   ├── problem-1/   # RESTful API
│   ├── problem-2/   # Microservices
│   └── problem-3/   # Performance
├── tests/           # Test suites
├── evaluation/      # Evaluation guides
├── examples/        # Example solutions
├── docs/            # Architecture docs
├── setup.sh         # Full environment setup
├── start.sh         # Start main infra only
└── docker-compose.yml
```

---

## 🧪 Testing & Validation

- **Run all tests:**
   ```bash
   pytest tests/
   ```
- **Problem-specific tests:**
   - Problem 1: `cd problems/problem-1 && pytest tests/`
   - Problem 2: `cd problems/problem-2 && pytest tests/`
   - Problem 3: `cd problems/problem-3 && locust -f tests/load_test.py`

---

## 📚 Documentation
- Main: [README.md](../README.md)
- Problem 1: [problems/problem-1/README.md](problems/problem-1/README.md)
- Problem 2: [problems/problem-2/README.md](problems/problem-2/README.md)
- Problem 3: [problems/problem-3/README.md](problems/problem-3/README.md)
- Evaluation: [evaluation/README.md](evaluation/README.md)
- Examples: [examples/README.md](examples/README.md)

---
=