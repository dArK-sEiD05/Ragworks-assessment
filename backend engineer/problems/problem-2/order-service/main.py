"""
Order Service for E-commerce Microservices
Handles order management, payment processing, and order tracking.
"""

from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import select, func
from datetime import datetime
from typing import Optional, List
import logging
import httpx

from shared.schemas import Event, EventType, ServiceHealth, PaginationParams, PaginatedResponse
from shared.messaging import MessagePublisher, MessageConsumer
from models.order import Order, OrderItem
from schemas.order import (
    OrderCreate, OrderUpdate, OrderResponse, OrderListResponse,
    OrderItemCreate, OrderItemResponse
)
from core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database engine
engine = create_async_engine(settings.DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

# Create FastAPI app
app = FastAPI(
    title="Order Service",
    description="Order management and tracking service",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Message publisher and consumer
message_publisher = MessagePublisher(settings.RABBITMQ_URL)
message_consumer = MessageConsumer(settings.RABBITMQ_URL, "order-service")

async def get_db():
    """Get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    await message_publisher.connect()
    await message_consumer.connect()
    
    # Register event handlers
    message_consumer.register_handler(EventType.USER_CREATED, handle_user_created)
    message_consumer.register_handler(EventType.USER_UPDATED, handle_user_updated)
    message_consumer.register_handler(EventType.PRODUCT_CREATED, handle_product_created)
    message_consumer.register_handler(EventType.PRODUCT_UPDATED, handle_product_updated)
    message_consumer.register_handler(EventType.PRODUCT_DELETED, handle_product_deleted)
    
    logger.info("Order service started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    await message_publisher.close()
    await message_consumer.close()
    logger.info("Order service stopped")


async def handle_user_created(event: Event):
    """Handle user created event."""
    logger.info(f"User created: {event.data}")
    # Could create user-specific order preferences, etc.


async def handle_user_updated(event: Event):
    """Handle user updated event."""
    logger.info(f"User updated: {event.data}")
    # Could update user-specific data


async def handle_product_created(event: Event):
    """Handle product created event."""
    logger.info(f"Product created: {event.data}")
    # Could update product availability cache


async def handle_product_updated(event: Event):
    """Handle product updated event."""
    logger.info(f"Product updated: {event.data}")
    # Could update product information in orders


async def handle_product_deleted(event: Event):
    """Handle product deleted event."""
    logger.info(f"Product deleted: {event.data}")
    # Could mark orders with this product as problematic


async def validate_user(user_id: int) -> bool:
    """Validate user exists."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.USER_SERVICE_URL}/users/{user_id}")
            return response.status_code == 200
    except Exception as e:
        logger.error(f"Failed to validate user {user_id}: {e}")
        return False


async def validate_products(items: List[OrderItemCreate]) -> tuple[bool, List[dict]]:
    """Validate products and get current prices."""
    try:
        product_ids = [item.product_id for item in items]
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.PRODUCT_SERVICE_URL}/products/validate",
                json={"product_ids": product_ids}
            )
            if response.status_code == 200:
                return True, response.json()
            return False, []
    except Exception as e:
        logger.error(f"Failed to validate products: {e}")
        return False, []


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return ServiceHealth(
        service_name="order-service",
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0"
    )


@app.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    user_id: int = None,  # This would come from authentication
    db: AsyncSession = Depends(get_db)
):
    """Create a new order."""
    # Validate user
    if not await validate_user(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user"
        )
    
    # Validate products and get current prices
    is_valid, product_data = await validate_products(order_data.items)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid products"
        )
    
    # Create product lookup
    product_lookup = {p["id"]: p for p in product_data}
    
    # Calculate total amount
    total_amount = sum(item.total_price for item in order_data.items)
    
    # Create order
    db_order = Order(
        user_id=user_id,
        total_amount=total_amount,
        shipping_address=order_data.shipping_address,
        billing_address=order_data.billing_address
    )
    
    db.add(db_order)
    await db.commit()
    await db.refresh(db_order)
    
    # Create order items
    for item_data in order_data.items:
        product_info = product_lookup.get(item_data.product_id)
        if not product_info:
            continue
            
        db_item = OrderItem(
            order_id=db_order.id,
            product_id=item_data.product_id,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            total_price=item_data.total_price
        )
        db.add(db_item)
    
    await db.commit()
    await db.refresh(db_order)
    
    # Publish order created event
    event = Event(
        event_type=EventType.ORDER_CREATED,
        data={
            "order_id": db_order.id,
            "user_id": db_order.user_id,
            "total_amount": float(db_order.total_amount),
            "status": db_order.status,
            "items": [
                {
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "unit_price": float(item.unit_price),
                    "total_price": float(item.total_price)
                }
                for item in db_order.items
            ]
        },
        source_service="order-service"
    )
    await message_publisher.publish_event(event)
    
    return db_order


@app.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int, db: AsyncSession = Depends(get_db)):
    """Get order by ID."""
    result = await db.execute(
        select(Order).where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return order


@app.get("/orders/user/{user_id}", response_model=PaginatedResponse)
async def get_user_orders(
    user_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get user orders with pagination."""
    # Get total count
    count_query = select(func.count(Order.id)).where(Order.user_id == user_id)
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Get paginated results
    offset = (page - 1) * size
    result = await db.execute(
        select(Order)
        .where(Order.user_id == user_id)
        .offset(offset)
        .limit(size)
        .order_by(Order.created_at.desc())
    )
    orders = result.scalars().all()
    
    return PaginatedResponse(
        items=[OrderResponse.model_validate(order) for order in orders],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )


@app.put("/orders/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    status_update: OrderUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update order status."""
    result = await db.execute(
        select(Order).where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Update order fields
    update_data = status_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(order, field, value)
    
    await db.commit()
    await db.refresh(order)
    
    # Publish order updated event
    event = Event(
        event_type=EventType.ORDER_UPDATED,
        data={
            "order_id": order.id,
            "user_id": order.user_id,
            "total_amount": float(order.total_amount),
            "status": order.status,
            "items": [
                {
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "unit_price": float(item.unit_price),
                    "total_price": float(item.total_price)
                }
                for item in order.items
            ]
        },
        source_service="order-service"
    )
    await message_publisher.publish_event(event)
    
    return order


@app.post("/orders/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Cancel an order."""
    result = await db.execute(
        select(Order).where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.status in ["shipped", "delivered"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel order in current status"
        )
    
    order.status = "cancelled"
    await db.commit()
    await db.refresh(order)
    
    # Publish order cancelled event
    event = Event(
        event_type=EventType.ORDER_CANCELLED,
        data={
            "order_id": order.id,
            "user_id": order.user_id,
            "total_amount": float(order.total_amount),
            "status": order.status,
            "items": [
                {
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "unit_price": float(item.unit_price),
                    "total_price": float(item.total_price)
                }
                for item in order.items
            ]
        },
        source_service="order-service"
    )
    await message_publisher.publish_event(event)
    
    return order


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
