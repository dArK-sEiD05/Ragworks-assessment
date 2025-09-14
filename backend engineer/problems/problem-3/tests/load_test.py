"""
Comprehensive load testing suite using Locust for performance optimization demo.
"""

import random
import json
from locust import HttpUser, task, between, events
from locust.exception import StopUser
import logging

logger = logging.getLogger(__name__)


class PerformanceTestUser(HttpUser):
    """Load test user for performance testing."""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    weight = 1
    
    def on_start(self):
        """Initialize user session."""
        self.user_id = None
        self.auth_token = None
        self.products = []
        self.categories = []
        
        # Login user
        self.login()
        
        # Load initial data
        self.load_initial_data()
    
    def login(self):
        """Login user and get auth token."""
        try:
            # Register a new user
            user_data = {
                "email": f"testuser{random.randint(1000, 9999)}@example.com",
                "username": f"testuser{random.randint(1000, 9999)}",
                "first_name": "Test",
                "last_name": "User"
            }
            
            with self.client.post("/auth/register", json=user_data, catch_response=True) as response:
                if response.status_code == 201:
                    self.user_id = response.json().get("id")
                    logger.info(f"User registered: {self.user_id}")
                elif response.status_code == 400:
                    # User might already exist, try to login
                    pass
                else:
                    response.failure(f"Registration failed: {response.status_code}")
                    return
            
            # Login user
            login_data = {
                "username": user_data["username"],
                "password": "testpassword123"
            }
            
            with self.client.post("/auth/login", json=login_data, catch_response=True) as response:
                if response.status_code == 200:
                    self.auth_token = response.json().get("access_token")
                    logger.info("User logged in successfully")
                else:
                    response.failure(f"Login failed: {response.status_code}")
                    return
                    
        except Exception as e:
            logger.error(f"Login error: {e}")
    
    def load_initial_data(self):
        """Load initial data for testing."""
        try:
            # Load products
            with self.client.get("/products?size=50", catch_response=True) as response:
                if response.status_code == 200:
                    data = response.json()
                    self.products = data.get("items", [])
                    logger.info(f"Loaded {len(self.products)} products")
            
            # Load categories
            with self.client.get("/products/categories", catch_response=True) as response:
                if response.status_code == 200:
                    self.categories = response.json()
                    logger.info(f"Loaded {len(self.categories)} categories")
                    
        except Exception as e:
            logger.error(f"Error loading initial data: {e}")
    
    @task(10)
    def search_products(self):
        """Test product search endpoint."""
        if not self.products:
            return
        
        search_terms = [
            "laptop", "mouse", "shirt", "jeans", "book", "garden", "tennis", 
            "skincare", "game", "car", "wireless", "cotton", "classic"
        ]
        
        query = random.choice(search_terms)
        params = {
            "q": query,
            "page": random.randint(1, 5),
            "size": random.randint(10, 50)
        }
        
        # Add random filters
        if random.random() < 0.3:  # 30% chance
            params["min_price"] = random.randint(10, 100)
        if random.random() < 0.3:  # 30% chance
            params["max_price"] = random.randint(100, 1000)
        if self.categories and random.random() < 0.2:  # 20% chance
            params["category_id"] = random.choice(self.categories)["id"]
        
        with self.client.get("/products/search", params=params, catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("total", 0) == 0:
                    response.failure("No products found for search")
                else:
                    response.success()
            else:
                response.failure(f"Search failed: {response.status_code}")
    
    @task(8)
    def get_product_details(self):
        """Test getting product details."""
        if not self.products:
            return
        
        product = random.choice(self.products)
        product_id = product["id"]
        
        with self.client.get(f"/products/{product_id}", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.failure("Product not found")
            else:
                response.failure(f"Get product failed: {response.status_code}")
    
    @task(6)
    def get_products_list(self):
        """Test getting products list."""
        params = {
            "page": random.randint(1, 10),
            "size": random.randint(10, 50)
        }
        
        # Add random filters
        if random.random() < 0.2:  # 20% chance
            params["category_id"] = random.choice(self.categories)["id"] if self.categories else None
        if random.random() < 0.1:  # 10% chance
            params["min_price"] = random.randint(10, 100)
        if random.random() < 0.1:  # 10% chance
            params["max_price"] = random.randint(100, 1000)
        
        with self.client.get("/products", params=params, catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if not data.get("items"):
                    response.failure("No products returned")
                else:
                    response.success()
            else:
                response.failure(f"Get products failed: {response.status_code}")
    
    @task(4)
    def get_categories(self):
        """Test getting categories."""
        with self.client.get("/products/categories", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if not data:
                    response.failure("No categories returned")
                else:
                    response.success()
            else:
                response.failure(f"Get categories failed: {response.status_code}")
    
    @task(3)
    def get_popular_products(self):
        """Test getting popular products."""
        params = {
            "limit": random.randint(10, 50)
        }
        
        with self.client.get("/products/popular", params=params, catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if not data:
                    response.failure("No popular products returned")
                else:
                    response.success()
            else:
                response.failure(f"Get popular products failed: {response.status_code}")
    
    @task(2)
    def get_user_analytics(self):
        """Test getting user analytics."""
        if not self.auth_token:
            return
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        with self.client.get("/analytics/users", headers=headers, catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if not data.get("total_users"):
                    response.failure("No analytics data returned")
                else:
                    response.success()
            else:
                response.failure(f"Get user analytics failed: {response.status_code}")
    
    @task(2)
    def get_product_analytics(self):
        """Test getting product analytics."""
        if not self.auth_token:
            return
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        with self.client.get("/analytics/products", headers=headers, catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if not data.get("total_products"):
                    response.failure("No analytics data returned")
                else:
                    response.success()
            else:
                response.failure(f"Get product analytics failed: {response.status_code}")
    
    @task(1)
    def get_performance_metrics(self):
        """Test getting performance metrics."""
        with self.client.get("/metrics", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if not data.get("response_times"):
                    response.failure("No metrics data returned")
                else:
                    response.success()
            else:
                response.failure(f"Get metrics failed: {response.status_code}")
    
    @task(1)
    def health_check(self):
        """Test health check endpoint."""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("status") != "healthy":
                    response.failure("Service not healthy")
                else:
                    response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")


class HighLoadUser(PerformanceTestUser):
    """High load user with more aggressive testing."""
    
    weight = 2
    wait_time = between(0.5, 1.5)  # Faster requests
    
    @task(15)
    def rapid_search_products(self):
        """Rapid product search testing."""
        self.search_products()
    
    @task(10)
    def rapid_get_products(self):
        """Rapid product retrieval testing."""
        self.get_products_list()


class AnalyticsUser(PerformanceTestUser):
    """User focused on analytics testing."""
    
    weight = 1
    wait_time = between(2, 5)  # Slower requests for analytics
    
    @task(5)
    def detailed_user_analytics(self):
        """Test detailed user analytics."""
        if not self.auth_token:
            return
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test with date range
        params = {
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-12-31T23:59:59Z"
        }
        
        with self.client.get("/analytics/users", params=params, headers=headers, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Detailed analytics failed: {response.status_code}")
    
    @task(5)
    def detailed_product_analytics(self):
        """Test detailed product analytics."""
        if not self.auth_token:
            return
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test with date range
        params = {
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-12-31T23:59:59Z"
        }
        
        with self.client.get("/analytics/products", params=params, headers=headers, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Detailed analytics failed: {response.status_code}")


class SearchUser(PerformanceTestUser):
    """User focused on search testing."""
    
    weight = 3
    wait_time = between(0.5, 2)
    
    @task(20)
    def complex_search(self):
        """Test complex search queries."""
        if not self.products:
            return
        
        # Complex search with multiple filters
        search_terms = [
            "laptop computer professional", "wireless mouse ergonomic",
            "cotton t-shirt casual", "classic jeans denim",
            "programming book python", "garden tools outdoor",
            "tennis racket sports", "skincare beauty natural"
        ]
        
        query = random.choice(search_terms)
        params = {
            "q": query,
            "page": random.randint(1, 3),
            "size": random.randint(20, 100),
            "min_price": random.randint(10, 50),
            "max_price": random.randint(100, 500),
            "sort_by": random.choice(["relevance", "price", "rating", "sales"]),
            "sort_order": random.choice(["asc", "desc"])
        }
        
        with self.client.get("/products/search", params=params, catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("total", 0) == 0:
                    response.failure("No results for complex search")
                else:
                    response.success()
            else:
                response.failure(f"Complex search failed: {response.status_code}")
    
    @task(10)
    def search_suggestions(self):
        """Test search suggestions (if available)."""
        search_terms = ["lap", "mou", "shi", "jea", "boo", "gar", "ten", "ski"]
        query = random.choice(search_terms)
        
        with self.client.get(f"/products/search/suggestions?q={query}", catch_response=True) as response:
            if response.status_code in [200, 404]:  # 404 is acceptable if not implemented
                response.success()
            else:
                response.failure(f"Search suggestions failed: {response.status_code}")


# Event handlers for custom metrics
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, context, **kwargs):
    """Log slow requests."""
    if response_time > 2.0:  # Log requests slower than 2 seconds
        logger.warning(f"Slow request: {name} took {response_time:.2f}s")


@events.user_error.add_listener
def on_user_error(user_instance, exception, tb, **kwargs):
    """Log user errors."""
    logger.error(f"User error: {exception}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Initialize test."""
    logger.info("Load test started")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Cleanup after test."""
    logger.info("Load test completed")