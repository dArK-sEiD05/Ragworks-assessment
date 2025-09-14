"""
Pydantic schemas for request/response validation and serialization.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from decimal import Decimal
from enum import Enum


class OrderStatus(str, Enum):
    """Order status enumeration."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentStatus(str, Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class ShippingStatus(str, Enum):
    """Shipping status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    RETURNED = "returned"


# Category Schemas
class CategoryBase(BaseModel):
    """Base category schema."""
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    is_active: bool = True
    sort_order: int = 0


class CategoryCreate(CategoryBase):
    """Schema for category creation."""
    pass


class CategoryUpdate(BaseModel):
    """Schema for category updates."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    slug: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class CategoryResponse(CategoryBase):
    """Schema for category response."""
    id: int
    created_at: datetime
    updated_at: datetime
    children: List['CategoryResponse'] = []
    product_count: Optional[int] = None
    
    class Config:
        from_attributes = True


# Product Schemas
class ProductBase(BaseModel):
    """Base product schema."""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    short_description: Optional[str] = Field(None, max_length=500)
    price: Decimal = Field(..., gt=0)
    compare_price: Optional[Decimal] = None
    cost_price: Optional[Decimal] = None
    category_id: Optional[int] = None
    brand: Optional[str] = Field(None, max_length=100)
    sku: str = Field(..., min_length=1, max_length=100)
    barcode: Optional[str] = Field(None, max_length=50)
    weight: Optional[Decimal] = None
    dimensions: Optional[Dict[str, Any]] = None
    stock_quantity: int = Field(0, ge=0)
    min_stock_level: int = Field(0, ge=0)
    max_stock_level: Optional[int] = None
    is_active: bool = True
    is_featured: bool = False
    is_digital: bool = False
    requires_shipping: bool = True
    tags: Optional[List[str]] = None
    attributes: Optional[Dict[str, Any]] = None
    seo_title: Optional[str] = Field(None, max_length=255)
    seo_description: Optional[str] = Field(None, max_length=500)


class ProductCreate(ProductBase):
    """Schema for product creation."""
    pass


class ProductUpdate(BaseModel):
    """Schema for product updates."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    short_description: Optional[str] = Field(None, max_length=500)
    price: Optional[Decimal] = Field(None, gt=0)
    compare_price: Optional[Decimal] = None
    cost_price: Optional[Decimal] = None
    category_id: Optional[int] = None
    brand: Optional[str] = Field(None, max_length=100)
    sku: Optional[str] = Field(None, min_length=1, max_length=100)
    barcode: Optional[str] = Field(None, max_length=50)
    weight: Optional[Decimal] = None
    dimensions: Optional[Dict[str, Any]] = None
    stock_quantity: Optional[int] = Field(None, ge=0)
    min_stock_level: Optional[int] = Field(None, ge=0)
    max_stock_level: Optional[int] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    is_digital: Optional[bool] = None
    requires_shipping: Optional[bool] = None
    tags: Optional[List[str]] = None
    attributes: Optional[Dict[str, Any]] = None
    seo_title: Optional[str] = Field(None, max_length=255)
    seo_description: Optional[str] = Field(None, max_length=500)


class ProductResponse(ProductBase):
    """Schema for product response."""
    id: int
    view_count: int = 0
    sales_count: int = 0
    rating_average: Decimal = Field(0, ge=0, le=5)
    rating_count: int = 0
    created_at: datetime
    updated_at: datetime
    category: Optional[CategoryResponse] = None
    in_stock: bool = True
    is_low_stock: bool = False
    
    @validator('in_stock', pre=True, always=True)
    def calculate_in_stock(cls, v, values):
        return values.get('stock_quantity', 0) > 0
    
    @validator('is_low_stock', pre=True, always=True)
    def calculate_low_stock(cls, v, values):
        stock = values.get('stock_quantity', 0)
        min_stock = values.get('min_stock_level', 0)
        return stock <= min_stock
    
    class Config:
        from_attributes = True


# User Schemas
class UserBase(BaseModel):
    """Base user schema."""
    email: str = Field(..., min_length=5, max_length=255)
    username: str = Field(..., min_length=3, max_length=100)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = Field(None, max_length=10)
    is_premium: bool = False


class UserCreate(UserBase):
    """Schema for user creation."""
    pass


class UserUpdate(BaseModel):
    """Schema for user updates."""
    email: Optional[str] = Field(None, min_length=5, max_length=255)
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = Field(None, max_length=10)
    is_premium: Optional[bool] = None


class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    is_active: bool = True
    is_verified: bool = False
    last_login: Optional[datetime] = None
    login_count: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Order Schemas
class OrderItemBase(BaseModel):
    """Base order item schema."""
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)
    unit_price: Decimal = Field(..., gt=0)
    total_price: Decimal = Field(..., gt=0)
    discount_amount: Decimal = Field(0, ge=0)
    tax_amount: Decimal = Field(0, ge=0)
    attributes: Optional[Dict[str, Any]] = None


class OrderItemCreate(OrderItemBase):
    """Schema for order item creation."""
    pass


class OrderItemResponse(OrderItemBase):
    """Schema for order item response."""
    id: int
    product_name: str
    product_sku: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    """Base order schema."""
    user_id: int = Field(..., gt=0)
    status: OrderStatus = OrderStatus.PENDING
    payment_status: PaymentStatus = PaymentStatus.PENDING
    shipping_status: ShippingStatus = ShippingStatus.PENDING
    subtotal: Decimal = Field(..., gt=0)
    tax_amount: Decimal = Field(0, ge=0)
    shipping_amount: Decimal = Field(0, ge=0)
    discount_amount: Decimal = Field(0, ge=0)
    total_amount: Decimal = Field(..., gt=0)
    currency: str = Field("USD", max_length=3)
    notes: Optional[str] = None
    shipping_address: Optional[Dict[str, Any]] = None
    billing_address: Optional[Dict[str, Any]] = None
    payment_method: Optional[str] = Field(None, max_length=50)
    items: List[OrderItemCreate] = Field(..., min_items=1)


class OrderCreate(OrderBase):
    """Schema for order creation."""
    pass


class OrderUpdate(BaseModel):
    """Schema for order updates."""
    status: Optional[OrderStatus] = None
    payment_status: Optional[PaymentStatus] = None
    shipping_status: Optional[ShippingStatus] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    payment_method: Optional[str] = Field(None, max_length=50)
    payment_reference: Optional[str] = Field(None, max_length=100)


class OrderResponse(OrderBase):
    """Schema for order response."""
    id: int
    order_number: str
    internal_notes: Optional[str] = None
    payment_reference: Optional[str] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse] = []
    user: Optional[UserResponse] = None
    
    class Config:
        from_attributes = True


# Search and Analytics Schemas
class ProductSearchRequest(BaseModel):
    """Schema for product search request."""
    query: str = Field(..., min_length=1)
    category_id: Optional[int] = None
    brand: Optional[str] = None
    min_price: Optional[Decimal] = Field(None, ge=0)
    max_price: Optional[Decimal] = Field(None, ge=0)
    min_rating: Optional[Decimal] = Field(None, ge=0, le=5)
    in_stock_only: bool = False
    featured_only: bool = False
    tags: Optional[List[str]] = None
    attributes: Optional[Dict[str, Any]] = None
    sort_by: str = Field("relevance", regex="^(relevance|price|rating|sales|newest|oldest)$")
    sort_order: str = Field("desc", regex="^(asc|desc)$")
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)


class ProductSearchResponse(BaseModel):
    """Schema for product search response."""
    products: List[ProductResponse]
    total: int
    page: int
    size: int
    pages: int
    facets: Optional[Dict[str, Any]] = None
    search_time: float
    cache_hit: bool = False


class UserAnalyticsResponse(BaseModel):
    """Schema for user analytics response."""
    total_users: int
    active_users: int
    new_users: int
    premium_users: int
    user_growth_rate: float
    retention_rate: float
    average_session_duration: float
    top_countries: List[Dict[str, Any]]
    user_activity_trend: List[Dict[str, Any]]
    generated_at: datetime


class ProductAnalyticsResponse(BaseModel):
    """Schema for product analytics response."""
    total_products: int
    active_products: int
    low_stock_products: int
    out_of_stock_products: int
    total_revenue: Decimal
    average_order_value: Decimal
    top_selling_products: List[Dict[str, Any]]
    category_performance: List[Dict[str, Any]]
    sales_trend: List[Dict[str, Any]]
    generated_at: datetime


class PerformanceMetrics(BaseModel):
    """Schema for performance metrics."""
    response_times: Dict[str, Dict[str, float]]
    cache_hit_rates: Dict[str, float]
    error_rates: Dict[str, float]
    throughput: Dict[str, float]
    database_performance: Dict[str, Any]
    memory_usage: Dict[str, Any]
    generated_at: datetime


# Pagination Schemas
class PaginationParams(BaseModel):
    """Schema for pagination parameters."""
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)
    sort_by: Optional[str] = None
    sort_order: str = Field("desc", regex="^(asc|desc)$")


class PaginatedResponse(BaseModel):
    """Schema for paginated response."""
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_prev: bool
    
    @validator('has_next', pre=True, always=True)
    def calculate_has_next(cls, v, values):
        page = values.get('page', 1)
        pages = values.get('pages', 1)
        return page < pages
    
    @validator('has_prev', pre=True, always=True)
    def calculate_has_prev(cls, v, values):
        page = values.get('page', 1)
        return page > 1


# Health Check Schemas
class HealthCheckResponse(BaseModel):
    """Schema for health check response."""
    status: str
    timestamp: datetime
    version: str
    services: Dict[str, str]
    performance: Optional[Dict[str, Any]] = None
