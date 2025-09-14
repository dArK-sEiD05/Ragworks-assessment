"""
Order Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class OrderItemBase(BaseModel):
    """Base order item schema with common fields."""
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)
    unit_price: Decimal = Field(..., gt=0, decimal_places=2)
    total_price: Decimal = Field(..., gt=0, decimal_places=2)


class OrderItemCreate(OrderItemBase):
    """Schema for order item creation."""
    pass


class OrderItemResponse(OrderItemBase):
    """Schema for order item response."""
    id: int
    
    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    """Base order schema with common fields."""
    shipping_address: str = Field(..., min_length=1)
    billing_address: str = Field(..., min_length=1)
    items: List[OrderItemCreate] = Field(..., min_items=1)


class OrderCreate(OrderBase):
    """Schema for order creation."""
    pass


class OrderUpdate(BaseModel):
    """Schema for order updates."""
    status: Optional[str] = Field(None, pattern="^(pending|confirmed|shipped|delivered|cancelled)$")
    shipping_address: Optional[str] = Field(None, min_length=1)
    billing_address: Optional[str] = Field(None, min_length=1)


class OrderInDB(OrderBase):
    """Schema for order in database."""
    id: int
    user_id: int
    total_amount: Decimal
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class OrderResponse(OrderInDB):
    """Schema for order response."""
    items: List[OrderItemResponse] = []


class OrderListResponse(BaseModel):
    """Schema for order list response."""
    orders: List[OrderResponse]
    total: int
    page: int
    size: int
    pages: int
