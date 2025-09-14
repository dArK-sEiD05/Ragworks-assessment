"""
Advanced caching service with Redis and multi-level caching.
"""

import json
import pickle
import gzip
import asyncio
import time
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta
import redis.asyncio as redis
from redis.asyncio import ConnectionPool
import logging

from core.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Advanced caching service with Redis and local caching."""
    
    def __init__(self):
        self.redis_pool: Optional[ConnectionPool] = None
        self.redis_client: Optional[redis.Redis] = None
        self.local_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0
        }
        self.compression_enabled = settings.CACHE_COMPRESSION
        self.serializer = settings.CACHE_SERIALIZER
    
    async def initialize(self):
        """Initialize Redis connection pool."""
        try:
            self.redis_pool = ConnectionPool.from_url(
                settings.REDIS_URL,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                socket_keepalive=settings.REDIS_SOCKET_KEEPALIVE,
                socket_keepalive_options=settings.REDIS_SOCKET_KEEPALIVE_OPTIONS,
                retry_on_timeout=True,
                health_check_interval=30
            )
            self.redis_client = redis.Redis(connection_pool=self.redis_pool)
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Redis cache service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis cache: {e}")
            self.redis_client = None
    
    async def close(self):
        """Close Redis connections."""
        if self.redis_client:
            await self.redis_client.close()
        if self.redis_pool:
            await self.redis_pool.disconnect()
        logger.info("Cache service closed")
    
    def _serialize(self, data: Any) -> bytes:
        """Serialize data for caching."""
        if self.serializer == "json":
            serialized = json.dumps(data, default=str).encode('utf-8')
        elif self.serializer == "pickle":
            serialized = pickle.dumps(data)
        else:
            serialized = json.dumps(data, default=str).encode('utf-8')
        
        if self.compression_enabled and len(serialized) > 1024:  # Compress if > 1KB
            serialized = gzip.compress(serialized)
            return b"gzip:" + serialized
        
        return serialized
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize cached data."""
        if data.startswith(b"gzip:"):
            data = gzip.decompress(data[5:])
        
        if self.serializer == "json":
            return json.loads(data.decode('utf-8'))
        elif self.serializer == "pickle":
            return pickle.loads(data)
        else:
            return json.loads(data.decode('utf-8'))
    
    def _get_cache_key(self, key: str) -> str:
        """Generate full cache key with prefix."""
        return f"{settings.CACHE_PREFIX}:{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache (Redis + local fallback)."""
        try:
            # Try local cache first
            if key in self.local_cache:
                cache_entry = self.local_cache[key]
                if cache_entry["expires_at"] > time.time():
                    self.cache_stats["hits"] += 1
                    return cache_entry["data"]
                else:
                    # Remove expired entry
                    del self.local_cache[key]
            
            # Try Redis cache
            if self.redis_client:
                full_key = self._get_cache_key(key)
                cached_data = await self.redis_client.get(full_key)
                
                if cached_data:
                    data = self._deserialize(cached_data)
                    # Store in local cache for faster access
                    self.local_cache[key] = {
                        "data": data,
                        "expires_at": time.time() + settings.CACHE_SHORT_TTL
                    }
                    self.cache_stats["hits"] += 1
                    return data
            
            self.cache_stats["misses"] += 1
            return None
            
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            self.cache_stats["errors"] += 1
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache (Redis + local)."""
        try:
            ttl = ttl or settings.CACHE_DEFAULT_TTL
            serialized_data = self._serialize(value)
            
            # Store in local cache
            self.local_cache[key] = {
                "data": value,
                "expires_at": time.time() + min(ttl, settings.CACHE_SHORT_TTL)
            }
            
            # Store in Redis
            if self.redis_client:
                full_key = self._get_cache_key(key)
                await self.redis_client.setex(full_key, ttl, serialized_data)
            
            self.cache_stats["sets"] += 1
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            self.cache_stats["errors"] += 1
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            # Remove from local cache
            if key in self.local_cache:
                del self.local_cache[key]
            
            # Remove from Redis
            if self.redis_client:
                full_key = self._get_cache_key(key)
                await self.redis_client.delete(full_key)
            
            self.cache_stats["deletes"] += 1
            return True
            
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            self.cache_stats["errors"] += 1
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        try:
            if not self.redis_client:
                return 0
            
            full_pattern = self._get_cache_key(pattern)
            keys = await self.redis_client.keys(full_pattern)
            
            if keys:
                deleted_count = await self.redis_client.delete(*keys)
                self.cache_stats["deletes"] += deleted_count
                return deleted_count
            
            return 0
            
        except Exception as e:
            logger.error(f"Cache delete pattern error for {pattern}: {e}")
            self.cache_stats["errors"] += 1
            return 0
    
    async def clear_all(self) -> bool:
        """Clear all cache data."""
        try:
            # Clear local cache
            self.local_cache.clear()
            
            # Clear Redis cache
            if self.redis_client:
                pattern = f"{settings.CACHE_PREFIX}:*"
                keys = await self.redis_client.keys(pattern)
                if keys:
                    await self.redis_client.delete(*keys)
            
            logger.info("All caches cleared")
            return True
            
        except Exception as e:
            logger.error(f"Cache clear all error: {e}")
            self.cache_stats["errors"] += 1
            return False
    
    async def get_or_set(self, key: str, factory_func, ttl: Optional[int] = None) -> Any:
        """Get from cache or set using factory function."""
        cached_value = await self.get(key)
        if cached_value is not None:
            return cached_value
        
        # Generate value using factory function
        if asyncio.iscoroutinefunction(factory_func):
            value = await factory_func()
        else:
            value = factory_func()
        
        await self.set(key, value, ttl)
        return value
    
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from cache."""
        results = {}
        
        for key in keys:
            value = await self.get(key)
            if value is not None:
                results[key] = value
        
        return results
    
    async def set_many(self, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple values in cache."""
        try:
            ttl = ttl or settings.CACHE_DEFAULT_TTL
            
            # Set in local cache
            for key, value in data.items():
                self.local_cache[key] = {
                    "data": value,
                    "expires_at": time.time() + min(ttl, settings.CACHE_SHORT_TTL)
                }
            
            # Set in Redis
            if self.redis_client:
                pipe = self.redis_client.pipeline()
                for key, value in data.items():
                    full_key = self._get_cache_key(key)
                    serialized_data = self._serialize(value)
                    pipe.setex(full_key, ttl, serialized_data)
                await pipe.execute()
            
            self.cache_stats["sets"] += len(data)
            return True
            
        except Exception as e:
            logger.error(f"Cache set many error: {e}")
            self.cache_stats["errors"] += 1
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "hits": self.cache_stats["hits"],
            "misses": self.cache_stats["misses"],
            "hit_rate": round(hit_rate, 2),
            "sets": self.cache_stats["sets"],
            "deletes": self.cache_stats["deletes"],
            "errors": self.cache_stats["errors"],
            "local_cache_size": len(self.local_cache),
            "redis_connected": self.redis_client is not None
        }
    
    # Specialized cache methods for common use cases
    
    async def get_categories(self) -> Optional[List[Dict[str, Any]]]:
        """Get cached categories."""
        return await self.get("categories:all")
    
    async def set_categories(self, categories: List[Dict[str, Any]]) -> bool:
        """Cache categories."""
        return await self.set("categories:all", categories, settings.CACHE_LONG_TTL)
    
    async def get_popular_products(self, limit: int = 20) -> Optional[List[Dict[str, Any]]]:
        """Get cached popular products."""
        return await self.get(f"products:popular:{limit}")
    
    async def set_popular_products(self, products: List[Dict[str, Any]], limit: int = 20) -> bool:
        """Cache popular products."""
        return await self.set(f"products:popular:{limit}", products, settings.CACHE_SHORT_TTL)
    
    async def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get cached product."""
        return await self.get(f"product:{product_id}")
    
    async def set_product(self, product_id: int, product: Dict[str, Any]) -> bool:
        """Cache product."""
        return await self.set(f"product:{product_id}", product, settings.CACHE_DEFAULT_TTL)
    
    async def invalidate_product(self, product_id: int) -> bool:
        """Invalidate product cache."""
        return await self.delete(f"product:{product_id}")
    
    async def invalidate_category_products(self, category_id: int) -> int:
        """Invalidate all products in a category."""
        return await self.delete_pattern(f"products:category:{category_id}:*")
    
    async def warm_up_cache(self) -> bool:
        """Warm up cache with frequently accessed data."""
        try:
            logger.info("Starting cache warm-up...")
            
            # This would typically load frequently accessed data
            # For now, we'll just log the warm-up process
            logger.info("Cache warm-up completed")
            return True
            
        except Exception as e:
            logger.error(f"Cache warm-up failed: {e}")
            return False
