"""
Optimized database models with proper indexing for performance.
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, Numeric, 
    ForeignKey, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, ARRAY

Base = declarative_base()


class Category(Base):
    """Product category model with optimized indexing."""
    
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    sort_order = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    parent = relationship("Category", remote_side=[id], back_populates="children")
    children = relationship("Category", back_populates="parent")
    products = relationship("Product", back_populates="category")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_categories_active_sort', 'is_active', 'sort_order'),
        Index('idx_categories_parent_active', 'parent_id', 'is_active'),
    )
    
    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name='{self.name}', slug='{self.slug}')>"


class Product(Base):
    """Product model with comprehensive indexing for search optimization."""
    
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    short_description = Column(String(500), nullable=True)
    price = Column(Numeric(10, 2), nullable=False, index=True)
    compare_price = Column(Numeric(10, 2), nullable=True)
    cost_price = Column(Numeric(10, 2), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    brand = Column(String(100), nullable=True, index=True)
    sku = Column(String(100), unique=True, nullable=False, index=True)
    barcode = Column(String(50), nullable=True, index=True)
    weight = Column(Numeric(8, 3), nullable=True)
    dimensions = Column(JSONB, nullable=True)  # {"length": 10, "width": 5, "height": 2}
    stock_quantity = Column(Integer, default=0, nullable=False, index=True)
    reserved_quantity = Column(Integer, default=0, nullable=False)
    min_stock_level = Column(Integer, default=0, nullable=False)
    max_stock_level = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_featured = Column(Boolean, default=False, nullable=False, index=True)
    is_digital = Column(Boolean, default=False, nullable=False)
    requires_shipping = Column(Boolean, default=True, nullable=False)
    tags = Column(ARRAY(String), nullable=True, index=True)  # ["electronics", "gadgets"]
    attributes = Column(JSONB, nullable=True)  # {"color": "red", "size": "L"}
    seo_title = Column(String(255), nullable=True)
    seo_description = Column(String(500), nullable=True)
    view_count = Column(Integer, default=0, nullable=False, index=True)
    sales_count = Column(Integer, default=0, nullable=False, index=True)
    rating_average = Column(Numeric(3, 2), default=0, nullable=False, index=True)
    rating_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    category = relationship("Category", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")
    reviews = relationship("ProductReview", back_populates="product")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('price >= 0', name='check_price_positive'),
        CheckConstraint('stock_quantity >= 0', name='check_stock_positive'),
        CheckConstraint('rating_average >= 0 AND rating_average <= 5', name='check_rating_range'),
        # Composite indexes for common queries
        Index('idx_products_category_active', 'category_id', 'is_active'),
        Index('idx_products_price_range', 'price', 'is_active'),
        Index('idx_products_stock_active', 'stock_quantity', 'is_active'),
        Index('idx_products_featured_active', 'is_featured', 'is_active'),
        Index('idx_products_sales_rating', 'sales_count', 'rating_average'),
        Index('idx_products_search', 'name', 'description', 'tags'),
        Index('idx_products_brand_active', 'brand', 'is_active'),
        # Partial indexes for performance
        Index('idx_products_in_stock', 'id', postgresql_where='stock_quantity > 0'),
        Index('idx_products_low_stock', 'id', 'stock_quantity', postgresql_where='stock_quantity <= min_stock_level'),
    )
    
    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name='{self.name}', sku='{self.sku}')>"


class User(Base):
    """User model with optimized indexing."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=True, index=True)
    last_name = Column(String(100), nullable=True, index=True)
    phone = Column(String(20), nullable=True, index=True)
    date_of_birth = Column(DateTime, nullable=True, index=True)
    gender = Column(String(10), nullable=True, index=True)
    avatar_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_verified = Column(Boolean, default=False, nullable=False, index=True)
    is_premium = Column(Boolean, default=False, nullable=False, index=True)
    last_login = Column(DateTime, nullable=True, index=True)
    login_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    orders = relationship("Order", back_populates="user")
    reviews = relationship("ProductReview", back_populates="user")
    addresses = relationship("UserAddress", back_populates="user")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_users_active_verified', 'is_active', 'is_verified'),
        Index('idx_users_premium_active', 'is_premium', 'is_active'),
        Index('idx_users_last_login', 'last_login', 'is_active'),
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


class UserAddress(Base):
    """User address model."""
    
    __tablename__ = "user_addresses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String(20), nullable=False, index=True)  # 'billing', 'shipping'
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    company = Column(String(100), nullable=True)
    address_line_1 = Column(String(255), nullable=False)
    address_line_2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=False, index=True)
    state = Column(String(100), nullable=False, index=True)
    postal_code = Column(String(20), nullable=False, index=True)
    country = Column(String(100), nullable=False, index=True)
    phone = Column(String(20), nullable=True)
    is_default = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="addresses")
    
    # Indexes
    __table_args__ = (
        Index('idx_addresses_user_type', 'user_id', 'type'),
        Index('idx_addresses_user_default', 'user_id', 'is_default'),
    )


class Order(Base):
    """Order model with optimized indexing."""
    
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String(20), default="pending", nullable=False, index=True)
    payment_status = Column(String(20), default="pending", nullable=False, index=True)
    shipping_status = Column(String(20), default="pending", nullable=False, index=True)
    subtotal = Column(Numeric(10, 2), nullable=False, index=True)
    tax_amount = Column(Numeric(10, 2), default=0, nullable=False)
    shipping_amount = Column(Numeric(10, 2), default=0, nullable=False)
    discount_amount = Column(Numeric(10, 2), default=0, nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False, index=True)
    currency = Column(String(3), default="USD", nullable=False, index=True)
    notes = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)
    shipping_address = Column(JSONB, nullable=True)
    billing_address = Column(JSONB, nullable=True)
    payment_method = Column(String(50), nullable=True, index=True)
    payment_reference = Column(String(100), nullable=True, index=True)
    shipped_at = Column(DateTime, nullable=True, index=True)
    delivered_at = Column(DateTime, nullable=True, index=True)
    cancelled_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_orders_user_status', 'user_id', 'status'),
        Index('idx_orders_status_date', 'status', 'created_at'),
        Index('idx_orders_payment_status', 'payment_status', 'created_at'),
        Index('idx_orders_shipping_status', 'shipping_status', 'created_at'),
        Index('idx_orders_total_range', 'total_amount', 'created_at'),
        Index('idx_orders_date_range', 'created_at', 'status'),
    )
    
    def __repr__(self) -> str:
        return f"<Order(id={self.id}, order_number='{self.order_number}', status='{self.status}')>"


class OrderItem(Base):
    """Order item model with optimized indexing."""
    
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    product_name = Column(String(255), nullable=False)  # Snapshot of product name
    product_sku = Column(String(100), nullable=False)  # Snapshot of product SKU
    quantity = Column(Integer, nullable=False, index=True)
    unit_price = Column(Numeric(10, 2), nullable=False, index=True)
    total_price = Column(Numeric(10, 2), nullable=False, index=True)
    discount_amount = Column(Numeric(10, 2), default=0, nullable=False)
    tax_amount = Column(Numeric(10, 2), default=0, nullable=False)
    attributes = Column(JSONB, nullable=True)  # Product variations
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_order_items_product', 'product_id', 'created_at'),
        Index('idx_order_items_order_product', 'order_id', 'product_id'),
        Index('idx_order_items_quantity', 'quantity', 'created_at'),
        Index('idx_order_items_price_range', 'unit_price', 'created_at'),
    )


class ProductReview(Base):
    """Product review model with optimized indexing."""
    
    __tablename__ = "product_reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    rating = Column(Integer, nullable=False, index=True)
    title = Column(String(255), nullable=True)
    comment = Column(Text, nullable=True)
    is_verified_purchase = Column(Boolean, default=False, nullable=False, index=True)
    is_helpful = Column(Integer, default=0, nullable=False, index=True)
    is_approved = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="reviews")
    user = relationship("User", back_populates="reviews")
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
        UniqueConstraint('product_id', 'user_id', name='unique_user_product_review'),
        Index('idx_reviews_product_rating', 'product_id', 'rating'),
        Index('idx_reviews_user_rating', 'user_id', 'rating'),
        Index('idx_reviews_verified_approved', 'is_verified_purchase', 'is_approved'),
        Index('idx_reviews_helpful', 'is_helpful', 'created_at'),
    )


class PerformanceLog(Base):
    """Performance logging model for monitoring."""
    
    __tablename__ = "performance_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    endpoint = Column(String(255), nullable=False, index=True)
    method = Column(String(10), nullable=False, index=True)
    response_time = Column(Numeric(10, 3), nullable=False, index=True)
    status_code = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    ip_address = Column(String(45), nullable=True, index=True)
    user_agent = Column(String(500), nullable=True)
    request_size = Column(Integer, nullable=True)
    response_size = Column(Integer, nullable=True)
    cache_hit = Column(Boolean, default=False, nullable=False, index=True)
    database_queries = Column(Integer, default=0, nullable=False)
    database_time = Column(Numeric(10, 3), default=0, nullable=False)
    memory_usage = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Indexes for performance analysis
    __table_args__ = (
        Index('idx_perf_endpoint_time', 'endpoint', 'created_at'),
        Index('idx_perf_response_time', 'response_time', 'created_at'),
        Index('idx_perf_status_code', 'status_code', 'created_at'),
        Index('idx_perf_cache_hit', 'cache_hit', 'created_at'),
        Index('idx_perf_user_endpoint', 'user_id', 'endpoint', 'created_at'),
    )
