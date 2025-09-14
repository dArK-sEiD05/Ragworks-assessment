"""
Tests for Order Service.
"""

import pytest
import httpx
from tests.conftest import order_service_client, sample_order_data


class TestOrderService:
    """Test cases for Order Service."""
    
    async def test_health_check(self, order_service_client: httpx.AsyncClient):
        """Test Order Service health check."""
        response = await order_service_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["service_name"] == "order-service"
        assert data["status"] == "healthy"
    
    async def test_get_user_orders(self, order_service_client: httpx.AsyncClient):
        """Test getting user orders."""
        user_id = 1  # Assuming user exists from test data
        response = await order_service_client.get(f"/orders/user/{user_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert "pages" in data
        assert isinstance(data["items"], list)
    
    async def test_get_user_orders_with_pagination(self, order_service_client: httpx.AsyncClient):
        """Test getting user orders with pagination."""
        user_id = 1
        response = await order_service_client.get(f"/orders/user/{user_id}?page=1&size=5")
        assert response.status_code == 200
        
        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 5
        assert len(data["items"]) <= 5
    
    async def test_get_nonexistent_order(self, order_service_client: httpx.AsyncClient):
        """Test getting nonexistent order."""
        response = await order_service_client.get("/orders/99999")
        assert response.status_code == 404
        
        data = response.json()
        assert "Order not found" in data["detail"]
    
    async def test_cancel_nonexistent_order(self, order_service_client: httpx.AsyncClient):
        """Test cancelling nonexistent order."""
        response = await order_service_client.post("/orders/99999/cancel")
        assert response.status_code == 404
        
        data = response.json()
        assert "Order not found" in data["detail"]
    
    async def test_update_nonexistent_order_status(self, order_service_client: httpx.AsyncClient):
        """Test updating nonexistent order status."""
        update_data = {"status": "confirmed"}
        response = await order_service_client.put("/orders/99999/status", json=update_data)
        assert response.status_code == 404
        
        data = response.json()
        assert "Order not found" in data["detail"]
