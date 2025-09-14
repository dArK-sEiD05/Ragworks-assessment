"""
Pytest configuration and fixtures for microservices testing.
"""

import pytest
import asyncio
import httpx
from typing import AsyncGenerator
import json


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def api_gateway_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create API Gateway client for testing."""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        yield client


@pytest.fixture
async def user_service_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create User Service client for testing."""
    async with httpx.AsyncClient(base_url="http://localhost:8001") as client:
        yield client


@pytest.fixture
async def product_service_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create Product Service client for testing."""
    async with httpx.AsyncClient(base_url="http://localhost:8002") as client:
        yield client


@pytest.fixture
async def order_service_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create Order Service client for testing."""
    async with httpx.AsyncClient(base_url="http://localhost:8003") as client:
        yield client


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123",
        "first_name": "Test",
        "last_name": "User",
        "phone": "+1234567890",
        "address": "123 Test Street, Test City, TC 12345"
    }


@pytest.fixture
def sample_product_data():
    """Sample product data for testing."""
    return {
        "name": "Test Product",
        "description": "A test product for testing",
        "price": 29.99,
        "category_id": 1,
        "stock_quantity": 100,
        "sku": "TEST-PRODUCT-001"
    }


@pytest.fixture
def sample_order_data():
    """Sample order data for testing."""
    return {
        "shipping_address": "123 Test Street, Test City, TC 12345",
        "billing_address": "123 Test Street, Test City, TC 12345",
        "items": [
            {
                "product_id": 1,
                "quantity": 2,
                "unit_price": 29.99,
                "total_price": 59.98
            }
        ]
    }
