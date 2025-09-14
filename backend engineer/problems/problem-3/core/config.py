"""
Configuration settings for performance optimization demo.
"""

from pydantic_settings import BaseSettings
from typing import List, Dict, Any
import os


class Settings(BaseSettings):
    """Application settings with performance optimizations."""
    
    # Application
    APP_NAME: str = "Performance Optimization Demo"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/performance_demo"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    DATABASE_POOL_RECYCLE: int = 3600
    DATABASE_POOL_PRE_PING: bool = True
    DATABASE_ECHO: bool = False
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_POOL_SIZE: int = 20
    REDIS_MAX_CONNECTIONS: int = 50
    REDIS_SOCKET_KEEPALIVE: bool = True
    REDIS_SOCKET_KEEPALIVE_OPTIONS: Dict[str, Any] = {
        1: 1,  # TCP_KEEPIDLE
        2: 3,  # TCP_KEEPINTVL
        3: 5,  # TCP_KEEPCNT
    }
    
    # Cache Configuration
    CACHE_DEFAULT_TTL: int = 3600  # 1 hour
    CACHE_SHORT_TTL: int = 300     # 5 minutes
    CACHE_LONG_TTL: int = 86400    # 24 hours
    CACHE_PREFIX: str = "perf_demo"
    CACHE_COMPRESSION: bool = True
    CACHE_SERIALIZER: str = "json"  # json, pickle, msgpack
    
    # Performance Monitoring
    ENABLE_METRICS: bool = True
    METRICS_RETENTION_DAYS: int = 30
    SLOW_QUERY_THRESHOLD: float = 1.0  # seconds
    MEMORY_WARNING_THRESHOLD: float = 0.8  # 80%
    
    # Search Configuration
    SEARCH_CACHE_TTL: int = 300
    SEARCH_MAX_RESULTS: int = 1000
    SEARCH_DEFAULT_PAGE_SIZE: int = 20
    ENABLE_SEARCH_ANALYTICS: bool = True
    
    # Analytics Configuration
    ANALYTICS_CACHE_TTL: int = 3600
    ANALYTICS_BATCH_SIZE: int = 1000
    ENABLE_REAL_TIME_ANALYTICS: bool = True
    
    # Background Tasks
    ENABLE_BACKGROUND_TASKS: bool = True
    TASK_QUEUE_SIZE: int = 1000
    TASK_WORKER_COUNT: int = 4
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ENABLE_ACCESS_LOGS: bool = True
    ENABLE_PERFORMANCE_LOGS: bool = True
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # Database Query Optimization
    QUERY_TIMEOUT: int = 30  # seconds
    MAX_QUERY_RESULTS: int = 10000
    ENABLE_QUERY_CACHING: bool = True
    QUERY_CACHE_TTL: int = 300
    
    # Memory Management
    MAX_MEMORY_USAGE: float = 0.9  # 90%
    ENABLE_MEMORY_MONITORING: bool = True
    GARBAGE_COLLECTION_THRESHOLD: int = 1000
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = ["image/jpeg", "image/png", "image/gif"]
    
    # External Services
    ENABLE_EXTERNAL_APIS: bool = False
    EXTERNAL_API_TIMEOUT: int = 10
    EXTERNAL_API_RETRY_COUNT: int = 3
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()
