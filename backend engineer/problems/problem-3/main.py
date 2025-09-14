"""
Performance Optimization Demo
A FastAPI application demonstrating various performance optimization techniques.
"""

from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, selectinload
from sqlalchemy import select, func, text, Index
from sqlalchemy.pool import QueuePool
import redis.asyncio as redis
import asyncio
import json
import time
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uvicorn
import psutil
import os

from models.database import Product, User, Order, OrderItem, Category, ProductReview, PerformanceLog
from schemas.models import (
    ProductResponse, ProductSearchRequest, ProductSearchResponse,
    UserAnalyticsResponse, PerformanceMetrics, HealthCheckResponse
)
from services.cache_service import CacheService
from services.analytics_service import AnalyticsService
from services.search_service import SearchService
from core.config import settings
from core.monitoring import PerformanceMonitor
from dashboard.monitoring_dashboard import MonitoringDashboard, create_dashboard_html

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database engine with optimized connection pooling
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    poolclass=QueuePool,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=settings.DATABASE_POOL_PRE_PING,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
    connect_args={
        "command_timeout": settings.QUERY_TIMEOUT,
        "server_settings": {
            "application_name": "performance_demo",
            "jit": "off"  # Disable JIT for better performance in some cases
        }
    }
)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

# Create FastAPI app
app = FastAPI(
    title="Performance Optimization Demo",
    description="Demonstrating various performance optimization techniques",
    version="1.0.0"
)

# Add middleware for performance optimization
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Add GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add performance monitoring middleware
@app.middleware("http")
async def performance_middleware(request: Request, call_next):
    """Performance monitoring middleware."""
    start_time = time.time()
    
    # Get user info if available
    user_id = None
    if hasattr(request.state, 'user_id'):
        user_id = request.state.user_id
    
    # Process request
    response = await call_next(request)
    
    # Calculate metrics
    process_time = time.time() - start_time
    memory_usage = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024  # MB
    
    # Record performance metrics
    performance_monitor.record_request(
        endpoint=request.url.path,
        response_time=process_time,
        status_code=response.status_code,
        user_id=user_id,
        ip_address=request.client.host if request.client else None,
        memory_usage=int(memory_usage)
    )
    
    # Add performance headers
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Memory-Usage"] = str(int(memory_usage))
    
    return response

# Initialize services
cache_service = CacheService()
analytics_service = AnalyticsService(cache_service)
search_service = SearchService(cache_service)
performance_monitor = PerformanceMonitor()
dashboard = MonitoringDashboard(performance_monitor, cache_service)

async def get_db():
    """Get database session with connection pooling."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    await cache_service.initialize()
    await analytics_service.initialize()
    await search_service.initialize()
    await performance_monitor.initialize()
    
    # Start monitoring dashboard
    asyncio.create_task(dashboard.start_monitoring_loop())
    
    # Warm up caches
    await warm_up_caches()
    
    logger.info("Performance optimization demo started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    await cache_service.close()
    await analytics_service.close()
    await search_service.close()
    await performance_monitor.close()
    logger.info("Performance optimization demo stopped")


async def warm_up_caches():
    """Warm up caches with frequently accessed data."""
    try:
        # Warm up product categories
        await cache_service.get_categories()
        
        # Warm up popular products
        await cache_service.get_popular_products(limit=50)
        
        logger.info("Caches warmed up successfully")
    except Exception as e:
        logger.error(f"Failed to warm up caches: {e}")


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Comprehensive health check endpoint."""
    try:
        # Check database connection
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
            db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # Check Redis connection
    try:
        await cache_service.get("health_check")
        redis_status = "healthy"
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"
    
    # Get system metrics
    memory = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent()
    
    # Get performance metrics
    performance_data = await performance_monitor.get_metrics()
    
    return HealthCheckResponse(
        status="healthy" if db_status == "healthy" and redis_status == "healthy" else "degraded",
        timestamp=datetime.utcnow(),
        version="1.0.0",
        services={
            "database": db_status,
            "redis": redis_status,
            "application": "healthy"
        },
        performance={
            "memory_usage_percent": memory.percent,
            "cpu_usage_percent": cpu_percent,
            "response_times": performance_data.get("response_times", {}),
            "cache_hit_rates": performance_data.get("cache_hit_rates", {})
        }
    )


@app.get("/products/search", response_model=ProductSearchResponse)
async def search_products_optimized(
    q: str = Query(..., min_length=1),
    category_id: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Optimized product search endpoint.
    
    Optimizations implemented:
    - Redis caching
    - Database query optimization
    - Connection pooling
    - Async processing
    - Pagination
    """
    start_time = time.time()
    
    # Create cache key
    cache_key = f"search:{q}:{category_id}:{min_price}:{max_price}:{page}:{size}"
    
    # Try to get from cache first
    cached_result = await cache_service.get(cache_key)
    if cached_result:
        performance_monitor.record_cache_hit("product_search")
        return ProductSearchResponse(**cached_result)
    
    # Perform optimized search
    search_request = ProductSearchRequest(
        query=q,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        page=page,
        size=size
    )
    
    result = await search_service.search_products(search_request, db)
    
    # Cache the result for 5 minutes
    await cache_service.set(cache_key, result.model_dump(), ttl=300)
    
    # Record performance metrics
    response_time = time.time() - start_time
    performance_monitor.record_request("product_search", response_time)
    
    return result


@app.get("/products/{product_id}", response_model=ProductResponse)
async def get_product_optimized(
    product_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get product with caching optimization."""
    start_time = time.time()
    
    # Try cache first
    cache_key = f"product:{product_id}"
    cached_product = await cache_service.get(cache_key)
    
    if cached_product:
        performance_monitor.record_cache_hit("get_product")
        return ProductResponse(**cached_product)
    
    # Query database with optimized query
    result = await db.execute(
        select(Product)
        .where(Product.id == product_id)
        .options(selectinload(Product.category))
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product_response = ProductResponse.model_validate(product)
    
    # Cache for 1 hour
    await cache_service.set(cache_key, product_response.model_dump(), ttl=3600)
    
    response_time = time.time() - start_time
    performance_monitor.record_request("get_product", response_time)
    
    return product_response


@app.get("/analytics/users", response_model=UserAnalyticsResponse)
async def get_user_analytics_optimized(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Optimized user analytics endpoint.
    
    Optimizations implemented:
    - Pre-computed analytics with background updates
    - Redis caching
    - Optimized database queries
    - Async processing
    """
    start_time = time.time()
    
    # Set default date range if not provided
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()
    
    # Create cache key
    cache_key = f"analytics:users:{start_date.date()}:{end_date.date()}"
    
    # Try cache first
    cached_result = await cache_service.get(cache_key)
    if cached_result:
        performance_monitor.record_cache_hit("user_analytics")
        return UserAnalyticsResponse(**cached_result)
    
    # Get analytics using optimized service
    analytics = await analytics_service.get_user_analytics(start_date, end_date, db)
    
    # Cache for 1 hour
    await cache_service.set(cache_key, analytics.model_dump(), ttl=3600)
    
    response_time = time.time() - start_time
    performance_monitor.record_request("user_analytics", response_time)
    
    return analytics


@app.get("/analytics/products", response_model=Dict[str, Any])
async def get_product_analytics_optimized(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
):
    """Optimized product analytics endpoint."""
    start_time = time.time()
    
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()
    
    cache_key = f"analytics:products:{start_date.date()}:{end_date.date()}"
    
    cached_result = await cache_service.get(cache_key)
    if cached_result:
        performance_monitor.record_cache_hit("product_analytics")
        return cached_result
    
    # Use optimized analytics service
    analytics = await analytics_service.get_product_analytics(start_date, end_date, db)
    
    await cache_service.set(cache_key, analytics, ttl=3600)
    
    response_time = time.time() - start_time
    performance_monitor.record_request("product_analytics", response_time)
    
    return analytics


@app.get("/products/popular", response_model=List[ProductResponse])
async def get_popular_products_optimized(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get popular products with caching."""
    start_time = time.time()
    
    cache_key = f"popular_products:{limit}"
    
    cached_products = await cache_service.get(cache_key)
    if cached_products:
        performance_monitor.record_cache_hit("popular_products")
        return [ProductResponse(**product) for product in cached_products]
    
    # Get popular products using optimized query
    result = await db.execute(
        select(Product)
        .join(OrderItem, Product.id == OrderItem.product_id)
        .group_by(Product.id)
        .order_by(func.count(OrderItem.id).desc())
        .limit(limit)
    )
    products = result.scalars().all()
    
    product_responses = [ProductResponse.model_validate(product) for product in products]
    
    # Cache for 30 minutes
    await cache_service.set(
        cache_key, 
        [product.model_dump() for product in product_responses], 
        ttl=1800
    )
    
    response_time = time.time() - start_time
    performance_monitor.record_request("popular_products", response_time)
    
    return product_responses


@app.get("/metrics", response_model=PerformanceMetrics)
async def get_performance_metrics():
    """Get performance metrics."""
    return await performance_monitor.get_metrics()


@app.post("/cache/warm")
async def warm_cache(background_tasks: BackgroundTasks):
    """Warm up caches in background."""
    background_tasks.add_task(warm_up_caches)
    return {"message": "Cache warming started in background"}


@app.delete("/cache/clear")
async def clear_cache():
    """Clear all caches."""
    await cache_service.clear_all()
    return {"message": "All caches cleared"}


@app.get("/products/stream")
async def stream_products(
    category_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Stream products for large datasets.
    
    Optimizations implemented:
    - Streaming response
    - Memory-efficient processing
    - Async generators
    """
    async def generate_products():
        # Use streaming query
        query = select(Product)
        if category_id:
            query = query.where(Product.category_id == category_id)
        
        async with db.stream(query) as result:
            async for row in result:
                product = row[0]
                yield f"data: {json.dumps(ProductResponse.model_validate(product).model_dump())}\n\n"
    
    return StreamingResponse(
        generate_products(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache"}
    )


# Dashboard endpoints
@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    """Get monitoring dashboard."""
    return create_dashboard_html()


@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates."""
    await dashboard.add_client(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        await dashboard.remove_client(websocket)


# Additional performance endpoints
@app.get("/performance/slow-queries")
async def get_slow_queries():
    """Get information about slow queries."""
    slow_queries = performance_monitor.get_slow_queries()
    return {
        "slow_queries": slow_queries,
        "count": len(slow_queries),
        "threshold": settings.SLOW_QUERY_THRESHOLD
    }


@app.post("/performance/reset-metrics")
async def reset_performance_metrics():
    """Reset all performance metrics."""
    performance_monitor.reset_metrics()
    return {"message": "Performance metrics reset successfully"}


@app.get("/performance/export")
async def export_performance_metrics():
    """Export performance metrics to file."""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"performance_metrics_{timestamp}.json"
    
    success = performance_monitor.export_metrics(filename)
    if success:
        return {"message": f"Metrics exported to {filename}", "filename": filename}
    else:
        raise HTTPException(status_code=500, detail="Failed to export metrics")


@app.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics."""
    return cache_service.get_stats()


@app.get("/search/stats")
async def get_search_stats():
    """Get search service statistics."""
    return search_service.get_search_stats()


@app.get("/analytics/stats")
async def get_analytics_stats():
    """Get analytics service statistics."""
    return analytics_service.get_analytics_stats()


# Advanced performance features
@app.get("/products/trending")
async def get_trending_products(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get trending products based on recent activity."""
    start_time = time.time()
    
    cache_key = f"trending_products:{limit}"
    cached_products = await cache_service.get(cache_key)
    
    if cached_products:
        performance_monitor.record_cache_hit("trending_products")
        return cached_products
    
    # Get trending products based on view count and sales
    result = await db.execute(
        select(Product)
        .where(Product.is_active == True)
        .order_by(
            (Product.view_count * 0.3 + Product.sales_count * 0.7).desc(),
            Product.rating_average.desc()
        )
        .limit(limit)
    )
    products = result.scalars().all()
    
    product_responses = [ProductResponse.model_validate(product) for product in products]
    
    # Cache for 10 minutes
    await cache_service.set(cache_key, [p.model_dump() for p in product_responses], ttl=600)
    
    response_time = time.time() - start_time
    performance_monitor.record_request("trending_products", response_time)
    
    return product_responses


@app.get("/products/recommendations/{product_id}")
async def get_product_recommendations(
    product_id: int,
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Get product recommendations based on similar products."""
    start_time = time.time()
    
    cache_key = f"recommendations:{product_id}:{limit}"
    cached_recommendations = await cache_service.get(cache_key)
    
    if cached_recommendations:
        performance_monitor.record_cache_hit("product_recommendations")
        return cached_recommendations
    
    # Get the product
    product_result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    product = product_result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get similar products based on category and tags
    recommendations = []
    if product.category_id:
        # Get products from same category
        category_result = await db.execute(
            select(Product)
            .where(
                and_(
                    Product.category_id == product.category_id,
                    Product.id != product_id,
                    Product.is_active == True
                )
            )
            .order_by(Product.rating_average.desc())
            .limit(limit)
        )
        recommendations = category_result.scalars().all()
    
    # If not enough recommendations, get products with similar tags
    if len(recommendations) < limit and product.tags:
        remaining = limit - len(recommendations)
        tag_result = await db.execute(
            select(Product)
            .where(
                and_(
                    Product.tags.overlap(product.tags),
                    Product.id != product_id,
                    Product.is_active == True
                )
            )
            .order_by(Product.rating_average.desc())
            .limit(remaining)
        )
        recommendations.extend(tag_result.scalars().all())
    
    product_responses = [ProductResponse.model_validate(p) for p in recommendations]
    
    # Cache for 30 minutes
    await cache_service.set(cache_key, [p.model_dump() for p in product_responses], ttl=1800)
    
    response_time = time.time() - start_time
    performance_monitor.record_request("product_recommendations", response_time)
    
    return product_responses


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        workers=1,  # Single worker for this demo
        log_level="info"
    )

