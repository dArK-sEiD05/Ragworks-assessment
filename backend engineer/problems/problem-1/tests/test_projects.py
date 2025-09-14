"""
Test project endpoints.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.project import Project


class TestProjects:
    """Test project management functionality."""
    
    @pytest.mark.asyncio
    async def test_create_project_success(self, client, auth_headers):
        """Test successful project creation."""
        project_data = {
            "name": "Test Project",
            "description": "A test project"
        }
        
        response = await client.post(
            "/api/v1/projects/",
            json=project_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == project_data["name"]
        assert data["description"] == project_data["description"]
        assert "id" in data
        assert "created_at" in data
    
    @pytest.mark.asyncio
    async def test_create_project_unauthorized(self, client):
        """Test project creation without authentication."""
        project_data = {
            "name": "Test Project",
            "description": "A test project"
        }
        response = await client.post("/api/v1/projects/", json=project_data)
        assert response.status_code in (401, 403)
    
    @pytest.mark.asyncio
    async def test_get_projects(self, client, auth_headers, db_session, test_user):
        """Test getting user's projects."""
        # Create test projects
        project1 = Project(name="Project 1", description="First project", owner_id=test_user.id)
        project2 = Project(name="Project 2", description="Second project", owner_id=test_user.id)
        
        db_session.add(project1)
        db_session.add(project2)
        await db_session.commit()
        
        response = await client.get("/api/v1/projects/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] in ["Project 1", "Project 2"]
        assert data[1]["name"] in ["Project 1", "Project 2"]
    
    @pytest.mark.asyncio
    async def test_get_projects_pagination(self, client, auth_headers, db_session, test_user):
        """Test project pagination."""
        # Create multiple projects
        for i in range(25):
            project = Project(
                name=f"Project {i}",
                description=f"Project {i} description",
                owner_id=test_user.id
            )
            db_session.add(project)
        await db_session.commit()
        
        # Test first page
        response = await client.get("/api/v1/projects/?skip=0&limit=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10
        
        # Test second page
        response = await client.get("/api/v1/projects/?skip=10&limit=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10
    
    @pytest.mark.asyncio
    async def test_get_project_by_id(self, client, auth_headers, db_session, test_user):
        """Test getting a specific project by ID."""
        project = Project(
            name="Specific Project",
            description="A specific project",
            owner_id=test_user.id
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)
        
        response = await client.get(f"/api/v1/projects/{project.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Specific Project"
        assert data["id"] == project.id
    
    @pytest.mark.asyncio
    async def test_get_project_not_found(self, client, auth_headers):
        """Test getting a non-existent project."""
        response = await client.get("/api/v1/projects/999", headers=auth_headers)
        
        assert response.status_code == 404
        assert "Project not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_project_unauthorized(self, client, db_session, test_user):
        """Test getting a project without authentication."""
        project = Project(
            name="Unauthorized Project",
            description="A project",
            owner_id=test_user.id
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)
        response = await client.get(f"/api/v1/projects/{project.id}")
        assert response.status_code in (401, 403)
    
    @pytest.mark.asyncio
    async def test_update_project(self, client, auth_headers, db_session, test_user):
        """Test updating a project."""
        project = Project(
            name="Original Name",
            description="Original description",
            owner_id=test_user.id
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)
        
        update_data = {
            "name": "Updated Name",
            "description": "Updated description"
        }
        
        response = await client.put(
            f"/api/v1/projects/{project.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "Updated description"
    
    @pytest.mark.asyncio
    async def test_update_project_not_found(self, client, auth_headers):
        """Test updating a non-existent project."""
        update_data = {"name": "Updated Name"}
        
        response = await client.put(
            "/api/v1/projects/999",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "Project not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_delete_project(self, client, auth_headers, db_session, test_user):
        """Test deleting a project."""
        project = Project(
            name="To Delete",
            description="This project will be deleted",
            owner_id=test_user.id
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)
        
        response = await client.delete(f"/api/v1/projects/{project.id}", headers=auth_headers)
        
        assert response.status_code == 204
        
        # Verify project is deleted
        response = await client.get(f"/api/v1/projects/{project.id}", headers=auth_headers)
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_project_not_found(self, client, auth_headers):
        """Test deleting a non-existent project."""
        response = await client.delete("/api/v1/projects/999", headers=auth_headers)
        
        assert response.status_code == 404
        assert "Project not found" in response.json()["detail"]

