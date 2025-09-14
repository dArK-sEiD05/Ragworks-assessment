"""
Tests for API Gateway service.
"""

import pytest
import httpx
from tests.conftest import api_gateway_client


class TestAPIGateway:
    """Test cases for API Gateway."""
    
    async def test_health_check(self, api_gateway_client: httpx.AsyncClient):
        """Test API Gateway health check."""
        response = await api_gateway_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "services" in data
        assert "timestamp" in data
    
    async def test_root_endpoint(self, api_gateway_client: httpx.AsyncClient):
        """Test root endpoint."""
        response = await api_gateway_client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "E-commerce API Gateway"
        assert data["version"] == "1.0.0"
        assert "services" in data
    
    async def test_rate_limiting(self, api_gateway_client: httpx.AsyncClient):
        """Test rate limiting functionality."""
        # Make multiple requests to trigger rate limiting
        responses = []
        for _ in range(105):  # Exceed default rate limit of 100
            response = await api_gateway_client.get("/")
            responses.append(response)
        
        # Check if rate limiting is working
        rate_limited_responses = [r for r in responses if r.status_code == 429]
        assert len(rate_limited_responses) > 0
    
    async def test_cors_headers(self, api_gateway_client: httpx.AsyncClient):
        """Test CORS headers are present."""
        response = await api_gateway_client.options("/")
        assert response.status_code == 200
        
        # Check CORS headers
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers
