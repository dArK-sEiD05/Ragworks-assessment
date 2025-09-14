"""
Shared Pydantic schemas for microservices communication.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    """Event types for inter-service communication."""
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    PRODUCT_CREATED = "product.created"
    PRODUCT_UPDATED = "product.updated"
    PRODUCT_DELETED = "product.deleted"
    ORDER_CREATED = "order.created"
    ORDER_UPDATED = "order.updated"
    ORDER_CANCELLED = "order.cancelled"


class Event(BaseModel):
    """Base event schema."""
    event_type: EventType
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source_service: str
    correlation_id: Optional[str] = None


class UserEventData(BaseModel):
    """User event data."""
    user_id: int
    email: str
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class ProductEventData(BaseModel):
    """Product event data."""
    product_id: int
    name: str
    price: float
    category_id: int
    stock_quantity: int
    sku: str


class OrderEventData(BaseModel):
    """Order event data."""
    order_id: int
    user_id: int
    total_amount: float
    status: str
    items: List[Dict[str, Any]]


class ServiceHealth(BaseModel):
    """Service health check response."""
    service_name: str
    status: str
    timestamp: datetime
    version: str
    dependencies: Dict[str, str] = {}


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)
    sort_by: Optional[str] = None
    sort_order: str = Field("asc", pattern="^(asc|desc)$")


class PaginatedResponse(BaseModel):
    """Paginated response schema."""
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int

