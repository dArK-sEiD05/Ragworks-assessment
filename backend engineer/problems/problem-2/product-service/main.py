"""
Product Service for E-commerce Microservices
Handles product catalog, inventory management, and search.
"""

from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import select, func, or_
from datetime import datetime
from typing import Optional, List
import logging

from shared.schemas import Event, EventType, ServiceHealth, PaginatedResponse
from shared.messaging import MessagePublisher, MessageConsumer
from models.product import Product, Category
from schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse,
    CategoryCreate, CategoryResponse
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
    title="Product Service",
    description="Product catalog and inventory management service",
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
message_consumer = MessageConsumer(settings.RABBITMQ_URL, "product-service")

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
    
    logger.info("Product service started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    await message_publisher.close()
    await message_consumer.close()
    logger.info("Product service stopped")


async def handle_user_created(event: Event):
    """Handle user created event."""
    logger.info(f"User created: {event.data}")
    # Could create user-specific product recommendations, wishlists, etc.


async def handle_user_updated(event: Event):
    """Handle user updated event."""
    logger.info(f"User updated: {event.data}")
    # Could update user-specific data


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return ServiceHealth(
        service_name="product-service",
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0"
    )


@app.get("/products", response_model=PaginatedResponse)
async def get_products(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get products with pagination and filtering."""
    # Build query
    query = select(Product).where(Product.is_active == True)
    
    if category_id:
        query = query.where(Product.category_id == category_id)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Product.name.ilike(search_term),
                Product.description.ilike(search_term)
            )
        )
    
    if min_price is not None:
        query = query.where(Product.price >= min_price)
    
    if max_price is not None:
        query = query.where(Product.price <= max_price)
    
    # Get total count
    count_query = select(func.count(Product.id)).where(Product.is_active == True)
    if category_id:
        count_query = count_query.where(Product.category_id == category_id)
    if search:
        search_term = f"%{search}%"
        count_query = count_query.where(
            or_(
                Product.name.ilike(search_term),
                Product.description.ilike(search_term)
            )
        )
    if min_price is not None:
        count_query = count_query.where(Product.price >= min_price)
    if max_price is not None:
        count_query = count_query.where(Product.price <= max_price)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Get paginated results
    offset = (page - 1) * size
    result = await db.execute(
        query.offset(offset).limit(size).order_by(Product.created_at.desc())
    )
    products = result.scalars().all()
    
    return PaginatedResponse(
        items=[ProductResponse.model_validate(product) for product in products],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )


@app.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    """Get product by ID."""
    result = await db.execute(
        select(Product).where(Product.id == product_id, Product.is_active == True)
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return product


@app.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new product (admin only)."""
    # Verify category exists
    result = await db.execute(
        select(Category).where(Category.id == product_data.category_id)
    )
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category not found"
        )
    
    # Check if SKU already exists
    result = await db.execute(
        select(Product).where(Product.sku == product_data.sku)
    )
    existing_product = result.scalar_one_or_none()
    
    if existing_product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SKU already exists"
        )
    
    # Create product
    db_product = Product(
        name=product_data.name,
        description=product_data.description,
        price=product_data.price,
        category_id=product_data.category_id,
        stock_quantity=product_data.stock_quantity,
        sku=product_data.sku
    )
    
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    
    # Publish product created event
    event = Event(
        event_type=EventType.PRODUCT_CREATED,
        data={
            "product_id": db_product.id,
            "name": db_product.name,
            "price": float(db_product.price),
            "category_id": db_product.category_id,
            "stock_quantity": db_product.stock_quantity,
            "sku": db_product.sku
        },
        source_service="product-service"
    )
    await message_publisher.publish_event(event)
    
    return db_product


@app.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_update: ProductUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a product (admin only)."""
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Update product fields
    update_data = product_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    await db.commit()
    await db.refresh(product)
    
    # Publish product updated event
    event = Event(
        event_type=EventType.PRODUCT_UPDATED,
        data={
            "product_id": product.id,
            "name": product.name,
            "price": float(product.price),
            "category_id": product.category_id,
            "stock_quantity": product.stock_quantity,
            "sku": product.sku
        },
        source_service="product-service"
    )
    await message_publisher.publish_event(event)
    
    return product


@app.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a product (admin only)."""
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Soft delete by setting is_active to False
    product.is_active = False
    await db.commit()
    
    # Publish product deleted event
    event = Event(
        event_type=EventType.PRODUCT_DELETED,
        data={
            "product_id": product.id,
            "name": product.name,
            "sku": product.sku
        },
        source_service="product-service"
    )
    await message_publisher.publish_event(event)
    
    return None


@app.get("/products/search")
async def search_products(
    q: str = Query(..., min_length=1),
    category_id: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    db: AsyncSession = Depends(get_db)
):
    """Search products."""
    # This is similar to get_products but with different response format
    query = select(Product).where(Product.is_active == True)
    
    search_term = f"%{q}%"
    query = query.where(
        or_(
            Product.name.ilike(search_term),
            Product.description.ilike(search_term),
            Product.sku.ilike(search_term)
        )
    )
    
    if category_id:
        query = query.where(Product.category_id == category_id)
    
    if min_price is not None:
        query = query.where(Product.price >= min_price)
    
    if max_price is not None:
        query = query.where(Product.price <= max_price)
    
    result = await db.execute(query.limit(50).order_by(Product.name))
    products = result.scalars().all()
    
    return {
        "query": q,
        "results": [ProductResponse.model_validate(product) for product in products],
        "total": len(products)
    }


@app.get("/categories", response_model=List[CategoryResponse])
async def get_categories(db: AsyncSession = Depends(get_db)):
    """Get all product categories."""
    result = await db.execute(select(Category).order_by(Category.name))
    categories = result.scalars().all()
    
    return categories


@app.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new category (admin only)."""
    # Check if category name already exists
    result = await db.execute(
        select(Category).where(Category.name == category_data.name)
    )
    existing_category = result.scalar_one_or_none()
    
    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category name already exists"
        )
    
    db_category = Category(
        name=category_data.name,
        description=category_data.description
    )
    
    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)
    
    return db_category


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

