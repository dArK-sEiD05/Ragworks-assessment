"""
Configuration settings for Product Service.
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    APP_NAME: str = "Product Service"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql://ecommerce_user:ecommerce_password@postgres:5432/ecommerce"
    
    # Redis
    REDIS_URL: str = "redis://redis:6379"
    
    # RabbitMQ
    RABBITMQ_URL: str = "amqp://ecommerce_user:ecommerce_password@rabbitmq:5672/ecommerce_vhost"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()
