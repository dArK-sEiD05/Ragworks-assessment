"""
Test authentication endpoints.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestAuth:
    """Test authentication functionality."""
    
    @pytest.mark.asyncio
    async def test_register_user_success(self, client):
        """Test successful user registration."""
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "newpassword123"
        }
        
        response = await client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["username"] == user_data["username"]
        assert "id" in data
        assert "created_at" in data
        assert "hashed_password" not in data
    
    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self, client, test_user):
        """Test registration with duplicate email."""
        user_data = {
            "email": "test@example.com",
            "username": "differentuser",
            "password": "password123"
        }
        
        response = await client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_register_user_duplicate_username(self, client, test_user):
        """Test registration with duplicate username."""
        user_data = {
            "email": "different@example.com",
            "username": "testuser",
            "password": "password123"
        }
        
        response = await client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 400
        assert "Username already taken" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_register_user_invalid_data(self, client):
        """Test registration with invalid data."""
        user_data = {
            "email": "invalid-email",
            "username": "ab",  # Too short
            "password": "123"   # Too short
        }
        
        response = await client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_login_success(self, client, test_user):
        """Test successful login."""
        login_data = {
            "username": "testuser",
            "password": "testpassword"
        }
        
        response = await client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client, test_user):
        """Test login with invalid credentials."""
        login_data = {
            "username": "testuser",
            "password": "wrongpassword"
        }
        response = await client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code in (401, 403)
        assert "Incorrect username or password" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user."""
        login_data = {
            "username": "nonexistent",
            "password": "password123"
        }
        response = await client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code in (401, 403)
        assert "Incorrect username or password" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_current_user(self, client, auth_headers):
        """Test getting current user information."""
        response = await client.get("/api/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "hashed_password" not in data
    
    @pytest.mark.asyncio
    async def test_get_current_user_unauthorized(self, client):
        """Test getting current user without authentication."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code in (401, 403)
    
    @pytest.mark.asyncio
    async def test_oauth2_token_endpoint(self, client, test_user):
        """Test OAuth2 compatible token endpoint."""
        form_data = {
            "username": "testuser",
            "password": "testpassword"
        }
        
        response = await client.post("/api/v1/auth/token", data=form_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

