"""
Initial database migration with optimized indexes for performance.
"""

import asyncio
import asyncpg
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = "postgresql://postgres:password@localhost:5432/performance_demo"

# SQL scripts for table creation with optimized indexes
CREATE_TABLES_SQL = """
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Categories table
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    parent_id INTEGER REFERENCES categories(id),
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Products table with comprehensive indexing
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    short_description VARCHAR(500),
    price DECIMAL(10,2) NOT NULL,
    compare_price DECIMAL(10,2),
    cost_price DECIMAL(10,2),
    category_id INTEGER REFERENCES categories(id),
    brand VARCHAR(100),
    sku VARCHAR(100) UNIQUE NOT NULL,
    barcode VARCHAR(50),
    weight DECIMAL(8,3),
    dimensions JSONB,
    stock_quantity INTEGER DEFAULT 0,
    reserved_quantity INTEGER DEFAULT 0,
    min_stock_level INTEGER DEFAULT 0,
    max_stock_level INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    is_featured BOOLEAN DEFAULT FALSE,
    is_digital BOOLEAN DEFAULT FALSE,
    requires_shipping BOOLEAN DEFAULT TRUE,
    tags TEXT[],
    attributes JSONB,
    seo_title VARCHAR(255),
    seo_description VARCHAR(500),
    view_count INTEGER DEFAULT 0,
    sales_count INTEGER DEFAULT 0,
    rating_average DECIMAL(3,2) DEFAULT 0,
    rating_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT check_price_positive CHECK (price >= 0),
    CONSTRAINT check_stock_positive CHECK (stock_quantity >= 0),
    CONSTRAINT check_rating_range CHECK (rating_average >= 0 AND rating_average <= 5)
);

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    date_of_birth TIMESTAMP,
    gender VARCHAR(10),
    avatar_url VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    is_premium BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP,
    login_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User addresses table
CREATE TABLE IF NOT EXISTS user_addresses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    type VARCHAR(20) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    company VARCHAR(100),
    address_line_1 VARCHAR(255) NOT NULL,
    address_line_2 VARCHAR(255),
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    postal_code VARCHAR(20) NOT NULL,
    country VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'pending',
    payment_status VARCHAR(20) DEFAULT 'pending',
    shipping_status VARCHAR(20) DEFAULT 'pending',
    subtotal DECIMAL(10,2) NOT NULL,
    tax_amount DECIMAL(10,2) DEFAULT 0,
    shipping_amount DECIMAL(10,2) DEFAULT 0,
    discount_amount DECIMAL(10,2) DEFAULT 0,
    total_amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    notes TEXT,
    internal_notes TEXT,
    shipping_address JSONB,
    billing_address JSONB,
    payment_method VARCHAR(50),
    payment_reference VARCHAR(100),
    shipped_at TIMESTAMP,
    delivered_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Order items table
CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id),
    product_name VARCHAR(255) NOT NULL,
    product_sku VARCHAR(100) NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    discount_amount DECIMAL(10,2) DEFAULT 0,
    tax_amount DECIMAL(10,2) DEFAULT 0,
    attributes JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Product reviews table
CREATE TABLE IF NOT EXISTS product_reviews (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    rating INTEGER NOT NULL,
    title VARCHAR(255),
    comment TEXT,
    is_verified_purchase BOOLEAN DEFAULT FALSE,
    is_helpful INTEGER DEFAULT 0,
    is_approved BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT check_rating_range CHECK (rating >= 1 AND rating <= 5),
    CONSTRAINT unique_user_product_review UNIQUE (product_id, user_id)
);

-- Performance logs table
CREATE TABLE IF NOT EXISTS performance_logs (
    id SERIAL PRIMARY KEY,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    response_time DECIMAL(10,3) NOT NULL,
    status_code INTEGER NOT NULL,
    user_id INTEGER,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    request_size INTEGER,
    response_size INTEGER,
    cache_hit BOOLEAN DEFAULT FALSE,
    database_queries INTEGER DEFAULT 0,
    database_time DECIMAL(10,3) DEFAULT 0,
    memory_usage INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
"""

# Index creation SQL
CREATE_INDEXES_SQL = """
-- Basic indexes for foreign keys and unique constraints
CREATE INDEX IF NOT EXISTS idx_categories_parent_id ON categories(parent_id);
CREATE INDEX IF NOT EXISTS idx_products_category_id ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);
CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode);
CREATE INDEX IF NOT EXISTS idx_user_addresses_user_id ON user_addresses(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_order_number ON orders(order_number);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_product_reviews_product_id ON product_reviews(product_id);
CREATE INDEX IF NOT EXISTS idx_product_reviews_user_id ON product_reviews(user_id);

-- Performance-optimized composite indexes
CREATE INDEX IF NOT EXISTS idx_categories_active_sort ON categories(is_active, sort_order);
CREATE INDEX IF NOT EXISTS idx_categories_parent_active ON categories(parent_id, is_active);

CREATE INDEX IF NOT EXISTS idx_products_category_active ON products(category_id, is_active);
CREATE INDEX IF NOT EXISTS idx_products_price_range ON products(price, is_active);
CREATE INDEX IF NOT EXISTS idx_products_stock_active ON products(stock_quantity, is_active);
CREATE INDEX IF NOT EXISTS idx_products_featured_active ON products(is_featured, is_active);
CREATE INDEX IF NOT EXISTS idx_products_sales_rating ON products(sales_count, rating_average);
CREATE INDEX IF NOT EXISTS idx_products_brand_active ON products(brand, is_active);

-- Full-text search indexes
CREATE INDEX IF NOT EXISTS idx_products_name_trgm ON products USING gin(name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_products_description_trgm ON products USING gin(description gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_products_tags_gin ON products USING gin(tags);
CREATE INDEX IF NOT EXISTS idx_products_attributes_gin ON products USING gin(attributes);

-- Partial indexes for performance
CREATE INDEX IF NOT EXISTS idx_products_in_stock ON products(id) WHERE stock_quantity > 0;
CREATE INDEX IF NOT EXISTS idx_products_low_stock ON products(id, stock_quantity) WHERE stock_quantity <= min_stock_level;
CREATE INDEX IF NOT EXISTS idx_products_out_of_stock ON products(id) WHERE stock_quantity = 0;

-- User indexes
CREATE INDEX IF NOT EXISTS idx_users_active_verified ON users(is_active, is_verified);
CREATE INDEX IF NOT EXISTS idx_users_premium_active ON users(is_premium, is_active);
CREATE INDEX IF NOT EXISTS idx_users_last_login ON users(last_login, is_active);

-- Address indexes
CREATE INDEX IF NOT EXISTS idx_addresses_user_type ON user_addresses(user_id, type);
CREATE INDEX IF NOT EXISTS idx_addresses_user_default ON user_addresses(user_id, is_default);

-- Order indexes
CREATE INDEX IF NOT EXISTS idx_orders_user_status ON orders(user_id, status);
CREATE INDEX IF NOT EXISTS idx_orders_status_date ON orders(status, created_at);
CREATE INDEX IF NOT EXISTS idx_orders_payment_status ON orders(payment_status, created_at);
CREATE INDEX IF NOT EXISTS idx_orders_shipping_status ON orders(shipping_status, created_at);
CREATE INDEX IF NOT EXISTS idx_orders_total_range ON orders(total_amount, created_at);
CREATE INDEX IF NOT EXISTS idx_orders_date_range ON orders(created_at, status);

-- Order item indexes
CREATE INDEX IF NOT EXISTS idx_order_items_product ON order_items(product_id, created_at);
CREATE INDEX IF NOT EXISTS idx_order_items_order_product ON order_items(order_id, product_id);
CREATE INDEX IF NOT EXISTS idx_order_items_quantity ON order_items(quantity, created_at);
CREATE INDEX IF NOT EXISTS idx_order_items_price_range ON order_items(unit_price, created_at);

-- Review indexes
CREATE INDEX IF NOT EXISTS idx_reviews_product_rating ON product_reviews(product_id, rating);
CREATE INDEX IF NOT EXISTS idx_reviews_user_rating ON product_reviews(user_id, rating);
CREATE INDEX IF NOT EXISTS idx_reviews_verified_approved ON product_reviews(is_verified_purchase, is_approved);
CREATE INDEX IF NOT EXISTS idx_reviews_helpful ON product_reviews(is_helpful, created_at);

-- Performance log indexes
CREATE INDEX IF NOT EXISTS idx_perf_endpoint_time ON performance_logs(endpoint, created_at);
CREATE INDEX IF NOT EXISTS idx_perf_response_time ON performance_logs(response_time, created_at);
CREATE INDEX IF NOT EXISTS idx_perf_status_code ON performance_logs(status_code, created_at);
CREATE INDEX IF NOT EXISTS idx_perf_cache_hit ON performance_logs(cache_hit, created_at);
CREATE INDEX IF NOT EXISTS idx_perf_user_endpoint ON performance_logs(user_id, endpoint, created_at);
"""

# Sample data SQL
SAMPLE_DATA_SQL = """
-- Insert sample categories
INSERT INTO categories (name, slug, description, is_active, sort_order) VALUES
('Electronics', 'electronics', 'Electronic devices and accessories', true, 1),
('Clothing', 'clothing', 'Fashion and apparel', true, 2),
('Books', 'books', 'Books and educational materials', true, 3),
('Home & Garden', 'home-garden', 'Home improvement and gardening', true, 4),
('Sports', 'sports', 'Sports equipment and accessories', true, 5),
('Health & Beauty', 'health-beauty', 'Health and beauty products', true, 6),
('Toys & Games', 'toys-games', 'Toys and games for all ages', true, 7),
('Automotive', 'automotive', 'Automotive parts and accessories', true, 8)
ON CONFLICT (slug) DO NOTHING;

-- Insert sample products
INSERT INTO products (name, slug, description, short_description, price, category_id, brand, sku, stock_quantity, is_active, is_featured, tags) VALUES
('Laptop Pro 15"', 'laptop-pro-15', 'High-performance laptop with 16GB RAM and SSD storage', 'Powerful laptop for professionals', 1299.99, 1, 'TechBrand', 'LAPTOP-PRO-15', 50, true, true, ARRAY['laptop', 'computer', 'professional']),
('Wireless Mouse', 'wireless-mouse', 'Ergonomic wireless mouse with precision tracking', 'Comfortable wireless mouse', 29.99, 1, 'TechBrand', 'MOUSE-WIRELESS-001', 100, true, false, ARRAY['mouse', 'wireless', 'ergonomic']),
('Cotton T-Shirt', 'cotton-t-shirt', 'Comfortable cotton t-shirt in various colors', 'Soft cotton t-shirt', 19.99, 2, 'FashionBrand', 'TSHIRT-COTTON-001', 200, true, false, ARRAY['t-shirt', 'cotton', 'casual']),
('Jeans Classic', 'jeans-classic', 'Classic blue jeans with modern fit', 'Classic blue jeans', 49.99, 2, 'FashionBrand', 'JEANS-CLASSIC-001', 150, true, false, ARRAY['jeans', 'denim', 'classic']),
('Python Programming Book', 'python-programming-book', 'Complete guide to Python programming', 'Learn Python programming', 39.99, 3, 'TechBooks', 'BOOK-PYTHON-001', 75, true, true, ARRAY['book', 'programming', 'python']),
('Garden Tools Set', 'garden-tools-set', 'Complete garden tools set for all gardening needs', 'Professional garden tools', 89.99, 4, 'GardenPro', 'GARDEN-TOOLS-001', 30, true, false, ARRAY['garden', 'tools', 'outdoor']),
('Tennis Racket', 'tennis-racket', 'Professional tennis racket for all skill levels', 'High-quality tennis racket', 129.99, 5, 'SportsPro', 'TENNIS-RACKET-001', 25, true, false, ARRAY['tennis', 'racket', 'sports']),
('Skincare Set', 'skincare-set', 'Complete skincare routine set', 'Natural skincare products', 79.99, 6, 'BeautyBrand', 'SKINCARE-SET-001', 40, true, false, ARRAY['skincare', 'beauty', 'natural']),
('Board Game Collection', 'board-game-collection', 'Collection of popular board games', 'Fun board games for family', 59.99, 7, 'GameMaster', 'BOARD-GAMES-001', 20, true, false, ARRAY['board-games', 'family', 'entertainment']),
('Car Phone Mount', 'car-phone-mount', 'Universal car phone mount with wireless charging', 'Secure phone mount for car', 34.99, 8, 'AutoTech', 'CAR-MOUNT-001', 60, true, false, ARRAY['car', 'phone-mount', 'wireless'])
ON CONFLICT (sku) DO NOTHING;

-- Insert sample users
INSERT INTO users (email, username, first_name, last_name, is_active, is_verified, is_premium) VALUES
('admin@example.com', 'admin', 'Admin', 'User', true, true, true),
('user1@example.com', 'user1', 'John', 'Doe', true, true, false),
('user2@example.com', 'user2', 'Jane', 'Smith', true, true, true),
('user3@example.com', 'user3', 'Bob', 'Johnson', true, false, false),
('user4@example.com', 'user4', 'Alice', 'Brown', true, true, false)
ON CONFLICT (email) DO NOTHING;

-- Insert sample orders
INSERT INTO orders (order_number, user_id, status, payment_status, subtotal, total_amount, currency) VALUES
('ORD-001', 2, 'delivered', 'paid', 1349.98, 1349.98, 'USD'),
('ORD-002', 3, 'shipped', 'paid', 69.98, 69.98, 'USD'),
('ORD-003', 4, 'processing', 'paid', 129.98, 129.98, 'USD'),
('ORD-004', 5, 'pending', 'pending', 89.99, 89.99, 'USD')
ON CONFLICT (order_number) DO NOTHING;

-- Insert sample order items
INSERT INTO order_items (order_id, product_id, product_name, product_sku, quantity, unit_price, total_price) VALUES
(1, 1, 'Laptop Pro 15"', 'LAPTOP-PRO-15', 1, 1299.99, 1299.99),
(1, 2, 'Wireless Mouse', 'MOUSE-WIRELESS-001', 1, 29.99, 29.99),
(2, 3, 'Cotton T-Shirt', 'TSHIRT-COTTON-001', 2, 19.99, 39.98),
(2, 4, 'Jeans Classic', 'JEANS-CLASSIC-001', 1, 49.99, 49.99),
(3, 5, 'Python Programming Book', 'BOOK-PYTHON-001', 1, 39.99, 39.99),
(3, 6, 'Garden Tools Set', 'GARDEN-TOOLS-001', 1, 89.99, 89.99),
(4, 7, 'Tennis Racket', 'TENNIS-RACKET-001', 1, 129.99, 129.99)
ON CONFLICT DO NOTHING;

-- Insert sample product reviews
INSERT INTO product_reviews (product_id, user_id, rating, title, comment, is_verified_purchase) VALUES
(1, 2, 5, 'Excellent laptop!', 'Great performance and build quality.', true),
(2, 2, 4, 'Good mouse', 'Comfortable and responsive.', true),
(3, 3, 5, 'Love this shirt', 'Very comfortable and good quality.', true),
(4, 3, 4, 'Nice jeans', 'Good fit and quality.', true),
(5, 4, 5, 'Great book', 'Very informative and well-written.', true),
(6, 4, 4, 'Good tools', 'Solid construction and easy to use.', true),
(7, 5, 3, 'Decent racket', 'Good for beginners.', false)
ON CONFLICT (product_id, user_id) DO NOTHING;
"""


async def run_migration():
    """Run the database migration."""
    try:
        # Connect to database
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Create tables
        logger.info("Creating tables...")
        await conn.execute(CREATE_TABLES_SQL)
        logger.info("Tables created successfully")
        
        # Create indexes
        logger.info("Creating indexes...")
        await conn.execute(CREATE_INDEXES_SQL)
        logger.info("Indexes created successfully")
        
        # Insert sample data
        logger.info("Inserting sample data...")
        await conn.execute(SAMPLE_DATA_SQL)
        logger.info("Sample data inserted successfully")
        
        # Close connection
        await conn.close()
        
        logger.info("Database migration completed successfully")
        
    except Exception as e:
        logger.error(f"Database migration failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(run_migration())
