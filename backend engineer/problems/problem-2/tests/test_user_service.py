"""
Tests for User Service.
"""

import pytest
import httpx
from tests.conftest import user_service_client, sample_user_data


class TestUserService:
    """Test cases for User Service."""
    
    async def test_health_check(self, user_service_client: httpx.AsyncClient):
        """Test User Service health check."""
        response = await user_service_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["service_name"] == "user-service"
        assert data["status"] == "healthy"
    
    async def test_user_registration(self, user_service_client: httpx.AsyncClient, sample_user_data):
        """Test user registration."""
        response = await user_service_client.post("/auth/register", json=sample_user_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["email"] == sample_user_data["email"]
        assert data["username"] == sample_user_data["username"]
        assert "id" in data
        assert "created_at" in data
        assert "hashed_password" not in data  # Password should not be returned
    
    async def test_user_registration_duplicate_email(self, user_service_client: httpx.AsyncClient, sample_user_data):
        """Test user registration with duplicate email."""
        # Register first user
        await user_service_client.post("/auth/register", json=sample_user_data)
        
        # Try to register with same email
        duplicate_data = sample_user_data.copy()
        duplicate_data["username"] = "different_username"
        response = await user_service_client.post("/auth/register", json=duplicate_data)
        assert response.status_code == 400
        
        data = response.json()
        assert "Email already registered" in data["detail"]
    
    async def test_user_login(self, user_service_client: httpx.AsyncClient, sample_user_data):
        """Test user login."""
        # Register user first
        await user_service_client.post("/auth/register", json=sample_user_data)
        
        # Login
        login_data = {
            "username": sample_user_data["username"],
            "password": sample_user_data["password"]
        }
        response = await user_service_client.post("/auth/login", json=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    async def test_user_login_invalid_credentials(self, user_service_client: httpx.AsyncClient):
        """Test user login with invalid credentials."""
        login_data = {
            "username": "nonexistent_user",
            "password": "wrong_password"
        }
        response = await user_service_client.post("/auth/login", json=login_data)
        assert response.status_code == 401
        
        data = response.json()
        assert "Incorrect username or password" in data["detail"]
    
    async def test_get_user_profile(self, user_service_client: httpx.AsyncClient, sample_user_data):
        """Test getting user profile."""
        # Register and login user
        await user_service_client.post("/auth/register", json=sample_user_data)
        
        login_data = {
            "username": sample_user_data["username"],
            "password": sample_user_data["password"]
        }
        login_response = await user_service_client.post("/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        
        # Get user profile
        headers = {"Authorization": f"Bearer {token}"}
        response = await user_service_client.get("/auth/me", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["email"] == sample_user_data["email"]
        assert data["username"] == sample_user_data["username"]
    
    async def test_get_user_by_id(self, user_service_client: httpx.AsyncClient, sample_user_data):
        """Test getting user by ID."""
        # Register user
        register_response = await user_service_client.post("/auth/register", json=sample_user_data)
        user_id = register_response.json()["id"]
        
        # Get user by ID
        response = await user_service_client.get(f"/users/{user_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == user_id
        assert data["email"] == sample_user_data["email"]
    
    async def test_update_user_profile(self, user_service_client: httpx.AsyncClient, sample_user_data):
        """Test updating user profile."""
        # Register and login user
        await user_service_client.post("/auth/register", json=sample_user_data)
        
        login_data = {
            "username": sample_user_data["username"],
            "password": sample_user_data["password"]
        }
        login_response = await user_service_client.post("/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        user_id = login_response.json()["id"]
        
        # Update user profile
        update_data = {
            "first_name": "Updated",
            "last_name": "Name"
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = await user_service_client.put(f"/users/{user_id}", json=update_data, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Name"
