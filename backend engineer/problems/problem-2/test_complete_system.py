"""
Complete system test script to verify the microservices implementation.
"""

import asyncio
import httpx
import json
import time
from typing import Dict, Any


class EcommerceSystemTester:
    """Test the complete e-commerce microservices system."""
    
    def __init__(self):
        self.base_urls = {
            "api_gateway": "http://localhost:8000",
            "user_service": "http://localhost:8001",
            "product_service": "http://localhost:8002",
            "order_service": "http://localhost:8003"
        }
        self.test_user = None
        self.auth_token = None
    
    async def test_service_health(self) -> bool:
        """Test all services are healthy."""
        print("🔍 Testing service health...")
        
        for service_name, base_url in self.base_urls.items():
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{base_url}/health", timeout=5.0)
                    if response.status_code == 200:
                        print(f"✅ {service_name}: Healthy")
                    else:
                        print(f"❌ {service_name}: Unhealthy (Status: {response.status_code})")
                        return False
            except Exception as e:
                print(f"❌ {service_name}: Connection failed - {e}")
                return False
        
        return True
    
    async def test_user_registration_and_login(self) -> bool:
        """Test user registration and login flow."""
        print("\n👤 Testing user registration and login...")
        
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpassword123",
            "first_name": "Test",
            "last_name": "User",
            "phone": "+1234567890",
            "address": "123 Test Street, Test City, TC 12345"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                # Test registration
                response = await client.post(
                    f"{self.base_urls['api_gateway']}/auth/register",
                    json=user_data
                )
                
                if response.status_code == 201:
                    self.test_user = response.json()
                    print("✅ User registration successful")
                else:
                    print(f"❌ User registration failed: {response.status_code} - {response.text}")
                    return False
                
                # Test login
                login_data = {
                    "username": user_data["username"],
                    "password": user_data["password"]
                }
                
                response = await client.post(
                    f"{self.base_urls['api_gateway']}/auth/login",
                    json=login_data
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    self.auth_token = token_data["access_token"]
                    print("✅ User login successful")
                    return True
                else:
                    print(f"❌ User login failed: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ User flow test failed: {e}")
            return False
    
    async def test_product_catalog(self) -> bool:
        """Test product catalog functionality."""
        print("\n🛍️ Testing product catalog...")
        
        try:
            async with httpx.AsyncClient() as client:
                # Test getting products
                response = await client.get(f"{self.base_urls['api_gateway']}/products")
                
                if response.status_code == 200:
                    products = response.json()
                    print(f"✅ Products retrieved: {len(products.get('items', []))} items")
                else:
                    print(f"❌ Failed to get products: {response.status_code}")
                    return False
                
                # Test product search
                response = await client.get(f"{self.base_urls['api_gateway']}/products/search?q=laptop")
                
                if response.status_code == 200:
                    search_results = response.json()
                    print(f"✅ Product search successful: {len(search_results.get('results', []))} results")
                else:
                    print(f"❌ Product search failed: {response.status_code}")
                    return False
                
                # Test getting categories
                response = await client.get(f"{self.base_urls['api_gateway']}/products/categories")
                
                if response.status_code == 200:
                    categories = response.json()
                    print(f"✅ Categories retrieved: {len(categories)} categories")
                else:
                    print(f"❌ Failed to get categories: {response.status_code}")
                    return False
                
                return True
                
        except Exception as e:
            print(f"❌ Product catalog test failed: {e}")
            return False
    
    async def test_order_creation(self) -> bool:
        """Test order creation functionality."""
        print("\n📦 Testing order creation...")
        
        if not self.auth_token:
            print("❌ No authentication token available")
            return False
        
        order_data = {
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
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                
                response = await client.post(
                    f"{self.base_urls['api_gateway']}/orders",
                    json=order_data,
                    headers=headers
                )
                
                if response.status_code == 201:
                    order = response.json()
                    print(f"✅ Order created successfully: Order ID {order['id']}")
                    return True
                else:
                    print(f"❌ Order creation failed: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Order creation test failed: {e}")
            return False
    
    async def test_api_gateway_features(self) -> bool:
        """Test API Gateway specific features."""
        print("\n🚪 Testing API Gateway features...")
        
        try:
            async with httpx.AsyncClient() as client:
                # Test health aggregation
                response = await client.get(f"{self.base_urls['api_gateway']}/health")
                
                if response.status_code == 200:
                    health_data = response.json()
                    services = health_data.get("services", {})
                    print(f"✅ Health aggregation: {len(services)} services monitored")
                    
                    for service_name, status in services.items():
                        print(f"   - {service_name}: {status}")
                else:
                    print(f"❌ Health aggregation failed: {response.status_code}")
                    return False
                
                # Test rate limiting (make multiple requests)
                print("   Testing rate limiting...")
                rate_limited = False
                for i in range(105):  # Exceed rate limit
                    response = await client.get(f"{self.base_urls['api_gateway']}/")
                    if response.status_code == 429:
                        rate_limited = True
                        break
                
                if rate_limited:
                    print("✅ Rate limiting is working")
                else:
                    print("⚠️ Rate limiting may not be working properly")
                
                return True
                
        except Exception as e:
            print(f"❌ API Gateway test failed: {e}")
            return False
    
    async def test_authentication_required_endpoints(self) -> bool:
        """Test that protected endpoints require authentication."""
        print("\n🔒 Testing authentication requirements...")
        
        try:
            async with httpx.AsyncClient() as client:
                # Test accessing protected endpoints without auth
                protected_endpoints = [
                    "/users/1",
                    "/orders",
                    "/orders/1"
                ]
                
                for endpoint in protected_endpoints:
                    response = await client.get(f"{self.base_urls['api_gateway']}{endpoint}")
                    if response.status_code == 401:
                        print(f"✅ {endpoint}: Properly requires authentication")
                    else:
                        print(f"❌ {endpoint}: Should require authentication (Status: {response.status_code})")
                        return False
                
                return True
                
        except Exception as e:
            print(f"❌ Authentication test failed: {e}")
            return False
    
    async def run_complete_test(self) -> bool:
        """Run the complete system test."""
        print("🚀 Starting E-commerce Microservices System Test")
        print("=" * 60)
        
        tests = [
            ("Service Health", self.test_service_health),
            ("User Registration & Login", self.test_user_registration_and_login),
            ("Product Catalog", self.test_product_catalog),
            ("Order Creation", self.test_order_creation),
            ("API Gateway Features", self.test_api_gateway_features),
            ("Authentication Requirements", self.test_authentication_required_endpoints)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                result = await test_func()
                if result:
                    passed += 1
                else:
                    print(f"❌ {test_name} test failed")
            except Exception as e:
                print(f"❌ {test_name} test failed with exception: {e}")
        
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! The microservices system is working correctly.")
            return True
        else:
            print("⚠️ Some tests failed. Please check the service logs and configuration.")
            return False


async def main():
    """Main test function."""
    tester = EcommerceSystemTester()
    
    print("Waiting for services to start...")
    await asyncio.sleep(10)  # Give services time to start
    
    success = await tester.run_complete_test()
    
    if success:
        print("\n✅ System test completed successfully!")
        exit(0)
    else:
        print("\n❌ System test failed!")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
