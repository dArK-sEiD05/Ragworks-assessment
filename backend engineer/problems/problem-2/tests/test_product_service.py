"""
Tests for Product Service.
"""

import pytest
import httpx
from tests.conftest import product_service_client, sample_product_data


class TestProductService:
    """Test cases for Product Service."""
    
    async def test_health_check(self, product_service_client: httpx.AsyncClient):
        """Test Product Service health check."""
        response = await product_service_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["service_name"] == "product-service"
        assert data["status"] == "healthy"
    
    async def test_get_products(self, product_service_client: httpx.AsyncClient):
        """Test getting products list."""
        response = await product_service_client.get("/products")
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert "pages" in data
        assert isinstance(data["items"], list)
    
    async def test_get_products_with_pagination(self, product_service_client: httpx.AsyncClient):
        """Test getting products with pagination."""
        response = await product_service_client.get("/products?page=1&size=5")
        assert response.status_code == 200
        
        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 5
        assert len(data["items"]) <= 5
    
    async def test_get_products_with_filters(self, product_service_client: httpx.AsyncClient):
        """Test getting products with filters."""
        response = await product_service_client.get("/products?category_id=1&min_price=10&max_price=100")
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        # Verify all returned products are in the specified category and price range
        for product in data["items"]:
            if product.get("category_id"):
                assert product["category_id"] == 1
            assert product["price"] >= 10
            assert product["price"] <= 100
    
    async def test_get_product_by_id(self, product_service_client: httpx.AsyncClient):
        """Test getting product by ID."""
        # First get products to find an existing product ID
        products_response = await product_service_client.get("/products")
        products = products_response.json()["items"]
        
        if products:
            product_id = products[0]["id"]
            response = await product_service_client.get(f"/products/{product_id}")
            assert response.status_code == 200
            
            data = response.json()
            assert data["id"] == product_id
            assert "name" in data
            assert "price" in data
    
    async def test_get_nonexistent_product(self, product_service_client: httpx.AsyncClient):
        """Test getting nonexistent product."""
        response = await product_service_client.get("/products/99999")
        assert response.status_code == 404
        
        data = response.json()
        assert "Product not found" in data["detail"]
    
    async def test_search_products(self, product_service_client: httpx.AsyncClient):
        """Test searching products."""
        response = await product_service_client.get("/products/search?q=laptop")
        assert response.status_code == 200
        
        data = response.json()
        assert "query" in data
        assert "results" in data
        assert "total" in data
        assert data["query"] == "laptop"
        assert isinstance(data["results"], list)
    
    async def test_get_categories(self, product_service_client: httpx.AsyncClient):
        """Test getting product categories."""
        response = await product_service_client.get("/categories")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        if data:  # If categories exist
            category = data[0]
            assert "id" in category
            assert "name" in category
            assert "created_at" in category
    
    async def test_create_category(self, product_service_client: httpx.AsyncClient):
        """Test creating a new category."""
        category_data = {
            "name": "Test Category",
            "description": "A test category for testing"
        }
        response = await product_service_client.post("/categories", json=category_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == category_data["name"]
        assert data["description"] == category_data["description"]
        assert "id" in data
        assert "created_at" in data
    
    async def test_create_duplicate_category(self, product_service_client: httpx.AsyncClient):
        """Test creating duplicate category."""
        category_data = {
            "name": "Duplicate Test Category",
            "description": "A test category for testing"
        }
        
        # Create first category
        await product_service_client.post("/categories", json=category_data)
        
        # Try to create duplicate
        response = await product_service_client.post("/categories", json=category_data)
        assert response.status_code == 400
        
        data = response.json()
        assert "Category name already exists" in data["detail"]
