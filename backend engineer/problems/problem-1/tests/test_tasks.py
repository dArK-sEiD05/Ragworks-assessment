"""
Test task endpoints.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.project import Project
from app.models.task import Task, TaskStatus, TaskPriority


class TestTasks:
    """Test task management functionality."""
    
    @pytest.mark.asyncio
    async def test_create_task_success(self, client, auth_headers, db_session, test_user):
        """Test successful task creation."""
        # Create a project first
        project = Project(
            name="Test Project",
            description="A test project",
            owner_id=test_user.id
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)
        
        task_data = {
            "title": "Test Task",
            "description": "A test task",
            "status": "pending",
            "priority": "medium",
            "assigned_to": test_user.id
        }
        
        response = await client.post(
            f"/api/v1/tasks/?project_id={project.id}",
            json=task_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == task_data["title"]
        assert data["description"] == task_data["description"]
        assert data["status"] == task_data["status"]
        assert data["priority"] == task_data["priority"]
        assert data["project_id"] == project.id
        assert data["assigned_to"] == test_user.id
    
    @pytest.mark.asyncio
    async def test_create_task_project_not_found(self, client, auth_headers):
        """Test creating a task for a non-existent project."""
        task_data = {
            "title": "Test Task",
            "description": "A test task"
        }
        
        response = await client.post(
            "/api/v1/tasks/?project_id=999",
            json=task_data,
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "Project not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_create_task_unauthorized(self, client, db_session, test_user):
        """Test creating a task without authentication."""
        project = Project(
            name="Test Project",
            description="A test project",
            owner_id=test_user.id
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)
        
        task_data = {
            "title": "Test Task",
            "description": "A test task"
        }
        
        response = await client.post(
            f"/api/v1/tasks/?project_id={project.id}",
            json=task_data
        )
        assert response.status_code in (401, 403)
    
    @pytest.mark.asyncio
    async def test_get_tasks(self, client, auth_headers, db_session, test_user):
        """Test getting user's tasks."""
        # Create a project and tasks
        project = Project(
            name="Test Project",
            description="A test project",
            owner_id=test_user.id
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)
        
        task1 = Task(
            title="Task 1",
            description="First task",
            project_id=project.id,
            status=TaskStatus.PENDING
        )
        task2 = Task(
            title="Task 2",
            description="Second task",
            project_id=project.id,
            status=TaskStatus.IN_PROGRESS
        )
        
        db_session.add(task1)
        db_session.add(task2)
        await db_session.commit()
        
        response = await client.get("/api/v1/tasks/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["title"] in ["Task 1", "Task 2"]
        assert data[1]["title"] in ["Task 1", "Task 2"]
    
    @pytest.mark.asyncio
    async def test_get_tasks_with_filters(self, client, auth_headers, db_session, test_user):
        """Test getting tasks with status and priority filters."""
        # Create a project and tasks
        project = Project(
            name="Test Project",
            description="A test project",
            owner_id=test_user.id
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)
        
        task1 = Task(
            title="High Priority Task",
            project_id=project.id,
            status=TaskStatus.PENDING,
            priority=TaskPriority.HIGH
        )
        task2 = Task(
            title="Low Priority Task",
            project_id=project.id,
            status=TaskStatus.COMPLETED,
            priority=TaskPriority.LOW
        )
        
        db_session.add(task1)
        db_session.add(task2)
        await db_session.commit()
        
        # Filter by status
        response = await client.get(
            "/api/v1/tasks/?status=pending",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "pending"
        
        # Filter by priority
        response = await client.get(
            "/api/v1/tasks/?priority=high",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["priority"] == "high"
    
    @pytest.mark.asyncio
    async def test_get_task_by_id(self, client, auth_headers, db_session, test_user):
        """Test getting a specific task by ID."""
        # Create a project and task
        project = Project(
            name="Test Project",
            description="A test project",
            owner_id=test_user.id
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)
        
        task = Task(
            title="Specific Task",
            description="A specific task",
            project_id=project.id
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)
        
        response = await client.get(f"/api/v1/tasks/{task.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Specific Task"
        assert data["id"] == task.id
        assert data["project_name"] == "Test Project"
    
    @pytest.mark.asyncio
    async def test_get_task_not_found(self, client, auth_headers):
        """Test getting a non-existent task."""
        response = await client.get("/api/v1/tasks/999", headers=auth_headers)
        
        assert response.status_code == 404
        assert "Task not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_update_task(self, client, auth_headers, db_session, test_user):
        """Test updating a task."""
        # Create a project and task
        project = Project(
            name="Test Project",
            description="A test project",
            owner_id=test_user.id
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)
        
        task = Task(
            title="Original Title",
            description="Original description",
            project_id=project.id,
            status=TaskStatus.PENDING
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)
        
        update_data = {
            "title": "Updated Title",
            "description": "Updated description",
            "status": "in_progress"
        }
        
        response = await client.put(
            f"/api/v1/tasks/{task.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["description"] == "Updated description"
        assert data["status"] == "in_progress"
    
    @pytest.mark.asyncio
    async def test_update_task_not_found(self, client, auth_headers):
        """Test updating a non-existent task."""
        update_data = {"title": "Updated Title"}
        
        response = await client.put(
            "/api/v1/tasks/999",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "Task not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_delete_task(self, client, auth_headers, db_session, test_user):
        """Test deleting a task."""
        # Create a project and task
        project = Project(
            name="Test Project",
            description="A test project",
            owner_id=test_user.id
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)
        
        task = Task(
            title="To Delete",
            description="This task will be deleted",
            project_id=project.id
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)
        
        response = await client.delete(f"/api/v1/tasks/{task.id}", headers=auth_headers)
        
        assert response.status_code == 204
        
        # Verify task is deleted
        response = await client.get(f"/api/v1/tasks/{task.id}", headers=auth_headers)
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_project_tasks(self, client, auth_headers, db_session, test_user):
        """Test getting tasks for a specific project."""
        # Create a project and tasks
        project = Project(
            name="Test Project",
            description="A test project",
            owner_id=test_user.id
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)
        
        task1 = Task(
            title="Project Task 1",
            description="First project task",
            project_id=project.id
        )
        task2 = Task(
            title="Project Task 2",
            description="Second project task",
            project_id=project.id
        )
        
        db_session.add(task1)
        db_session.add(task2)
        await db_session.commit()
        
        response = await client.get(
            f"/api/v1/tasks/project/{project.id}/tasks",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(task["project_name"] == "Test Project" for task in data)
    
    @pytest.mark.asyncio
    async def test_get_project_tasks_project_not_found(self, client, auth_headers):
        """Test getting tasks for a non-existent project."""
        response = await client.get(
            "/api/v1/tasks/project/999/tasks",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "Project not found" in response.json()["detail"]

