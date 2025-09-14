"""
Integration tests for the complete microservices system.
"""

import pytest
import httpx
from tests.conftest import (
    api_gateway_client, user_service_client, product_service_client, 
    order_service_client, sample_user_data, sample_product_data, sample_order_data
)


class TestIntegration:
    """Integration test cases for the complete system."""
    
    async def test_complete_user_journey(self, api_gateway_client: httpx.AsyncClient, sample_user_data):
        """Test complete user journey through API Gateway."""
        # Register user through API Gateway
        response = await api_gateway_client.post("/auth/register", json=sample_user_data)
        assert response.status_code == 201
        
        user_data = response.json()
        user_id = user_data["id"]
        
        # Login through API Gateway
        login_data = {
            "username": sample_user_data["username"],
            "password": sample_user_data["password"]
        }
        login_response = await api_gateway_client.post("/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get user profile through API Gateway
        profile_response = await api_gateway_client.get("/auth/me", headers=headers)
        assert profile_response.status_code == 200
        
        # Update user profile through API Gateway
        update_data = {"first_name": "Updated", "last_name": "Name"}
        update_response = await api_gateway_client.put(f"/users/{user_id}", json=update_data, headers=headers)
        assert update_response.status_code == 200
        
        updated_user = update_response.json()
        assert updated_user["first_name"] == "Updated"
        assert updated_user["last_name"] == "Name"
    
    async def test_product_catalog_access(self, api_gateway_client: httpx.AsyncClient):
        """Test accessing product catalog through API Gateway."""
        # Get products through API Gateway
        response = await api_gateway_client.get("/products")
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
        
        # Get categories through API Gateway
        categories_response = await api_gateway_client.get("/products/categories")
        assert categories_response.status_code == 200
        
        categories = categories_response.json()
        assert isinstance(categories, list)
    
    async def test_search_products_through_gateway(self, api_gateway_client: httpx.AsyncClient):
        """Test searching products through API Gateway."""
        response = await api_gateway_client.get("/products/search?q=test")
        assert response.status_code == 200
        
        data = response.json()
        assert "query" in data
        assert "results" in data
        assert "total" in data
        assert data["query"] == "test"
    
    async def test_service_health_aggregation(self, api_gateway_client: httpx.AsyncClient):
        """Test API Gateway health check aggregation."""
        response = await api_gateway_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "services" in data
        assert "timestamp" in data
        
        # Check that all services are reported
        services = data["services"]
        assert "user-service" in services
        assert "product-service" in services
        assert "order-service" in services
    
    async def test_authentication_required_endpoints(self, api_gateway_client: httpx.AsyncClient):
        """Test that authentication is required for protected endpoints."""
        # Try to access user profile without authentication
        response = await api_gateway_client.get("/users/1")
        assert response.status_code == 401
        
        # Try to access orders without authentication
        response = await api_gateway_client.get("/orders")
        assert response.status_code == 401
        
        # Try to create order without authentication
        response = await api_gateway_client.post("/orders", json=sample_order_data)
        assert response.status_code == 401
    
    async def test_rate_limiting_through_gateway(self, api_gateway_client: httpx.AsyncClient):
        """Test rate limiting through API Gateway."""
        # Make multiple requests to trigger rate limiting
        responses = []
        for _ in range(105):  # Exceed default rate limit of 100
            response = await api_gateway_client.get("/")
            responses.append(response)
        
        # Check if rate limiting is working
        rate_limited_responses = [r for r in responses if r.status_code == 429]
        assert len(rate_limited_responses) > 0
    
    async def test_cors_through_gateway(self, api_gateway_client: httpx.AsyncClient):
        """Test CORS headers through API Gateway."""
        response = await api_gateway_client.options("/")
        assert response.status_code == 200
        
        # Check CORS headers
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers
