# Problem 1: RESTful API Development

## Overview
Build a RESTful API for a task management system using FastAPI, PostgreSQL, and Docker.

## Requirements

### Core Features
- **User Management**: Registration, authentication, and authorization
- **Project Management**: CRUD operations for projects
- **Task Management**: CRUD operations for tasks within projects
- **Database Design**: Proper relationships and constraints
- **API Documentation**: OpenAPI/Swagger documentation

### Technical Requirements
- FastAPI framework
- PostgreSQL database
- JWT authentication
- Input validation with Pydantic
- Error handling and HTTP status codes
- Docker containerization
- Unit and integration tests

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Projects Table
```sql
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Tasks Table
```sql
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    priority VARCHAR(20) DEFAULT 'medium',
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    assigned_to INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    due_date TIMESTAMP
);
```

## API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /auth/refresh` - Refresh JWT token

### Users
- `GET /users/me` - Get current user profile
- `PUT /users/me` - Update current user profile

### Projects
- `GET /projects` - List user's projects
- `POST /projects` - Create new project
- `GET /projects/{project_id}` - Get project details
- `PUT /projects/{project_id}` - Update project
- `DELETE /projects/{project_id}` - Delete project

### Tasks
- `GET /projects/{project_id}/tasks` - List project tasks
- `POST /projects/{project_id}/tasks` - Create new task
- `GET /tasks/{task_id}` - Get task details
- `PUT /tasks/{task_id}` - Update task
- `DELETE /tasks/{task_id}` - Delete task

## Evaluation Criteria

1. **API Design** (25%)
   - RESTful conventions
   - Proper HTTP methods and status codes
   - Consistent URL patterns

2. **Database Design** (20%)
   - Proper relationships and constraints
   - Efficient schema design
   - Data integrity

3. **Authentication & Security** (20%)
   - JWT implementation
   - Password hashing
   - Authorization checks

4. **Code Quality** (15%)
   - Clean, readable code
   - Proper error handling
   - Type hints and documentation

5. **Testing** (10%)
   - Unit tests
   - Integration tests
   - Test coverage

6. **Documentation** (10%)
   - API documentation
   - Setup instructions
   - Code comments

## Getting Started

1. Navigate to the problem directory:
   ```bash
   cd problems/problem-1
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start the database:
   ```bash
   docker-compose up -d postgres
   ```

4. Run migrations:
   ```bash
   alembic upgrade head
   ```

5. Start the development server:
   ```bash
   uvicorn main:app --reload
   ```

6. Access the API documentation:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## Testing

Run the test suite:
```bash
pytest tests/ -v --cov=app
```

## Submission

Submit your solution by:
1. Completing the implementation
2. Running all tests successfully
3. Creating a pull request with your changes
4. Including a brief summary of your approach

