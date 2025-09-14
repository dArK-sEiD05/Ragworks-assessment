"""
API Gateway for E-commerce Microservices
Routes requests to appropriate services and handles cross-cutting concerns.
"""

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import httpx
import redis
import json
import time
from typing import Optional
import logging

from shared.schemas import ErrorResponse, ServiceHealth
from shared.messaging import MessagePublisher, Event, EventType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service URLs
USER_SERVICE_URL = "http://user-service:8001"
PRODUCT_SERVICE_URL = "http://product-service:8002"
ORDER_SERVICE_URL = "http://order-service:8003"

# Redis client for caching and rate limiting
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

# Message publisher
message_publisher = MessagePublisher("amqp://ecommerce_user:ecommerce_password@rabbitmq:5672/ecommerce_vhost")

app = FastAPI(
    title="E-commerce API Gateway",
    description="API Gateway for E-commerce Microservices",
    version="1.0.0"
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]
)


class RateLimiter:
    """Rate limiter using Redis."""
    
    def __init__(self, redis_client, max_requests: int = 100, window: int = 60):
        self.redis = redis_client
        self.max_requests = max_requests
        self.window = window
    
    def is_allowed(self, client_ip: str) -> bool:
        """Check if request is allowed based on rate limit."""
        key = f"rate_limit:{client_ip}"
        current = self.redis.get(key)
        
        if current is None:
            self.redis.setex(key, self.window, 1)
            return True
        
        if int(current) >= self.max_requests:
            return False
        
        self.redis.incr(key)
        return True


rate_limiter = RateLimiter(redis_client)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware."""
    client_ip = request.client.host
    
    if not rate_limiter.is_allowed(client_ip):
        return JSONResponse(
            status_code=429,
            content={"error": "Rate limit exceeded", "message": "Too many requests"}
        )
    
    response = await call_next(request)
    return response


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Request logging middleware."""
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.4f}s"
    )
    
    return response


async def get_auth_token(request: Request) -> Optional[str]:
    """Extract authentication token from request."""
    authorization = request.headers.get("Authorization")
    if authorization and authorization.startswith("Bearer "):
        return authorization[7:]
    return None


async def authenticate_user(token: str) -> Optional[dict]:
    """Authenticate user with user service."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{USER_SERVICE_URL}/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        logger.error(f"Authentication error: {e}")
    return None


async def forward_request(
    service_url: str,
    path: str,
    method: str,
    request: Request,
    user_data: Optional[dict] = None
) -> JSONResponse:
    """Forward request to appropriate service."""
    try:
        # Prepare headers
        headers = dict(request.headers)
        if user_data:
            headers["X-User-ID"] = str(user_data["id"])
            headers["X-User-Email"] = user_data["email"]
        
        # Prepare query parameters
        query_params = dict(request.query_params)
        
        # Prepare body for POST/PUT requests
        body = None
        if method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
            except:
                pass
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=f"{service_url}{path}",
                headers=headers,
                params=query_params,
                content=body,
                timeout=30.0
            )
            
            return JSONResponse(
                content=response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
    
    except httpx.TimeoutException:
        return JSONResponse(
            status_code=504,
            content={"error": "Gateway Timeout", "message": "Service unavailable"}
        )
    except Exception as e:
        logger.error(f"Service communication error: {e}")
        return JSONResponse(
            status_code=502,
            content={"error": "Bad Gateway", "message": "Service communication failed"}
        )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    services = {}
    
    # Check user service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{USER_SERVICE_URL}/health", timeout=5.0)
            services["user-service"] = "healthy" if response.status_code == 200 else "unhealthy"
    except:
        services["user-service"] = "unhealthy"
    
    # Check product service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{PRODUCT_SERVICE_URL}/health", timeout=5.0)
            services["product-service"] = "healthy" if response.status_code == 200 else "unhealthy"
    except:
        services["product-service"] = "unhealthy"
    
    # Check order service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ORDER_SERVICE_URL}/health", timeout=5.0)
            services["order-service"] = "healthy" if response.status_code == 200 else "unhealthy"
    except:
        services["order-service"] = "unhealthy"
    
    overall_status = "healthy" if all(status == "healthy" for status in services.values()) else "degraded"
    
    return {
        "status": overall_status,
        "services": services,
        "timestamp": time.time()
    }


# User service routes
@app.api_route("/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def user_auth_routes(path: str, request: Request):
    """Route authentication requests to user service."""
    return await forward_request(USER_SERVICE_URL, f"/auth/{path}", request.method, request)


@app.api_route("/users/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def user_routes(path: str, request: Request, token: Optional[str] = Depends(get_auth_token)):
    """Route user requests to user service."""
    user_data = None
    if token:
        user_data = await authenticate_user(token)
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    return await forward_request(USER_SERVICE_URL, f"/users/{path}", request.method, request, user_data)


# Product service routes
@app.api_route("/products/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def product_routes(path: str, request: Request, token: Optional[str] = Depends(get_auth_token)):
    """Route product requests to product service."""
    user_data = None
    if token:
        user_data = await authenticate_user(token)
    
    return await forward_request(PRODUCT_SERVICE_URL, f"/products/{path}", request.method, request, user_data)


@app.api_route("/products", methods=["GET"])
async def product_list_route(request: Request, token: Optional[str] = Depends(get_auth_token)):
    """Route product list requests to product service."""
    user_data = None
    if token:
        user_data = await authenticate_user(token)
    
    return await forward_request(PRODUCT_SERVICE_URL, "/products", request.method, request, user_data)


# Order service routes
@app.api_route("/orders/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def order_routes(path: str, request: Request, token: str = Depends(get_auth_token)):
    """Route order requests to order service."""
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_data = await authenticate_user(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    return await forward_request(ORDER_SERVICE_URL, f"/orders/{path}", request.method, request, user_data)


@app.api_route("/orders", methods=["GET", "POST"])
async def order_list_route(request: Request, token: str = Depends(get_auth_token)):
    """Route order list requests to order service."""
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_data = await authenticate_user(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    return await forward_request(ORDER_SERVICE_URL, "/orders", request.method, request, user_data)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "E-commerce API Gateway",
        "version": "1.0.0",
        "services": {
            "user-service": USER_SERVICE_URL,
            "product-service": PRODUCT_SERVICE_URL,
            "order-service": ORDER_SERVICE_URL
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
