"""
Advanced analytics service with pre-computed metrics and real-time processing.
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, text, case, literal_column
from sqlalchemy.orm import selectinload
from sqlalchemy.dialects.postgresql import array_agg

from models.database import User, Product, Order, OrderItem, Category, ProductReview
from schemas.models import UserAnalyticsResponse, ProductAnalyticsResponse
from services.cache_service import CacheService
from core.config import settings

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Advanced analytics service with pre-computed metrics and caching."""
    
    def __init__(self, cache_service: CacheService):
        self.cache_service = cache_service
        self.analytics_stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "average_response_time": 0.0,
            "last_computation": None
        }
    
    async def initialize(self):
        """Initialize analytics service."""
        logger.info("Analytics service initialized")
    
    async def close(self):
        """Close analytics service."""
        logger.info("Analytics service closed")
    
    async def get_user_analytics(
        self, 
        start_date: datetime, 
        end_date: datetime, 
        db: AsyncSession
    ) -> UserAnalyticsResponse:
        """Get comprehensive user analytics with caching."""
        start_time = time.time()
        
        # Create cache key
        cache_key = f"analytics:users:{start_date.date()}:{end_date.date()}"
        
        # Try cache first
        cached_result = await self.cache_service.get(cache_key)
        if cached_result:
            self.analytics_stats["cache_hits"] += 1
            self.analytics_stats["total_requests"] += 1
            return UserAnalyticsResponse(**cached_result)
        
        try:
            # Calculate all metrics in parallel for better performance
            metrics = await asyncio.gather(
                self._get_user_counts(db, start_date, end_date),
                self._get_user_growth_rate(db, start_date, end_date),
                self._get_retention_rate(db, start_date, end_date),
                self._get_average_session_duration(db, start_date, end_date),
                self._get_top_countries(db, start_date, end_date),
                self._get_user_activity_trend(db, start_date, end_date)
            )
            
            (
                user_counts,
                growth_rate,
                retention_rate,
                avg_session_duration,
                top_countries,
                activity_trend
            ) = metrics
            
            # Create response
            response = UserAnalyticsResponse(
                total_users=user_counts["total_users"],
                active_users=user_counts["active_users"],
                new_users=user_counts["new_users"],
                premium_users=user_counts["premium_users"],
                user_growth_rate=growth_rate,
                retention_rate=retention_rate,
                average_session_duration=avg_session_duration,
                top_countries=top_countries,
                user_activity_trend=activity_trend,
                generated_at=datetime.utcnow()
            )
            
            # Cache the result
            await self.cache_service.set(
                cache_key, 
                response.model_dump(), 
                settings.ANALYTICS_CACHE_TTL
            )
            
            # Update stats
            self.analytics_stats["total_requests"] += 1
            response_time = time.time() - start_time
            self._update_average_response_time(response_time)
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting user analytics: {e}")
            raise
    
    async def get_product_analytics(
        self, 
        start_date: datetime, 
        end_date: datetime, 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Get comprehensive product analytics with caching."""
        start_time = time.time()
        
        # Create cache key
        cache_key = f"analytics:products:{start_date.date()}:{end_date.date()}"
        
        # Try cache first
        cached_result = await self.cache_service.get(cache_key)
        if cached_result:
            self.analytics_stats["cache_hits"] += 1
            self.analytics_stats["total_requests"] += 1
            return cached_result
        
        try:
            # Calculate all metrics in parallel
            metrics = await asyncio.gather(
                self._get_product_counts(db, start_date, end_date),
                self._get_revenue_metrics(db, start_date, end_date),
                self._get_top_selling_products(db, start_date, end_date),
                self._get_category_performance(db, start_date, end_date),
                self._get_sales_trend(db, start_date, end_date)
            )
            
            (
                product_counts,
                revenue_metrics,
                top_products,
                category_performance,
                sales_trend
            ) = metrics
            
            # Create response
            response = {
                "total_products": product_counts["total_products"],
                "active_products": product_counts["active_products"],
                "low_stock_products": product_counts["low_stock_products"],
                "out_of_stock_products": product_counts["out_of_stock_products"],
                "total_revenue": float(revenue_metrics["total_revenue"]),
                "average_order_value": float(revenue_metrics["average_order_value"]),
                "top_selling_products": top_products,
                "category_performance": category_performance,
                "sales_trend": sales_trend,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            # Cache the result
            await self.cache_service.set(
                cache_key, 
                response, 
                settings.ANALYTICS_CACHE_TTL
            )
            
            # Update stats
            self.analytics_stats["total_requests"] += 1
            response_time = time.time() - start_time
            self._update_average_response_time(response_time)
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting product analytics: {e}")
            raise
    
    async def _get_user_counts(self, db: AsyncSession, start_date: datetime, end_date: datetime) -> Dict[str, int]:
        """Get user count metrics."""
        try:
            # Total users
            total_users_result = await db.execute(select(func.count(User.id)))
            total_users = total_users_result.scalar()
            
            # Active users (logged in within the period)
            active_users_result = await db.execute(
                select(func.count(User.id)).where(
                    and_(
                        User.last_login >= start_date,
                        User.last_login <= end_date,
                        User.is_active == True
                    )
                )
            )
            active_users = active_users_result.scalar()
            
            # New users
            new_users_result = await db.execute(
                select(func.count(User.id)).where(
                    and_(
                        User.created_at >= start_date,
                        User.created_at <= end_date
                    )
                )
            )
            new_users = new_users_result.scalar()
            
            # Premium users
            premium_users_result = await db.execute(
                select(func.count(User.id)).where(
                    and_(
                        User.is_premium == True,
                        User.is_active == True
                    )
                )
            )
            premium_users = premium_users_result.scalar()
            
            return {
                "total_users": total_users,
                "active_users": active_users,
                "new_users": new_users,
                "premium_users": premium_users
            }
            
        except Exception as e:
            logger.error(f"Error getting user counts: {e}")
            return {"total_users": 0, "active_users": 0, "new_users": 0, "premium_users": 0}
    
    async def _get_user_growth_rate(self, db: AsyncSession, start_date: datetime, end_date: datetime) -> float:
        """Calculate user growth rate."""
        try:
            # Get user count at start of period
            start_count_result = await db.execute(
                select(func.count(User.id)).where(User.created_at < start_date)
            )
            start_count = start_count_result.scalar()
            
            # Get user count at end of period
            end_count_result = await db.execute(
                select(func.count(User.id)).where(User.created_at <= end_date)
            )
            end_count = end_count_result.scalar()
            
            if start_count == 0:
                return 100.0 if end_count > 0 else 0.0
            
            growth_rate = ((end_count - start_count) / start_count) * 100
            return round(growth_rate, 2)
            
        except Exception as e:
            logger.error(f"Error calculating user growth rate: {e}")
            return 0.0
    
    async def _get_retention_rate(self, db: AsyncSession, start_date: datetime, end_date: datetime) -> float:
        """Calculate user retention rate."""
        try:
            # Get users who registered in the period
            new_users_result = await db.execute(
                select(User.id).where(
                    and_(
                        User.created_at >= start_date,
                        User.created_at <= end_date
                    )
                )
            )
            new_user_ids = [row[0] for row in new_users_result]
            
            if not new_user_ids:
                return 0.0
            
            # Get users who are still active
            retained_users_result = await db.execute(
                select(func.count(User.id)).where(
                    and_(
                        User.id.in_(new_user_ids),
                        User.is_active == True,
                        User.last_login >= start_date
                    )
                )
            )
            retained_users = retained_users_result.scalar()
            
            retention_rate = (retained_users / len(new_user_ids)) * 100
            return round(retention_rate, 2)
            
        except Exception as e:
            logger.error(f"Error calculating retention rate: {e}")
            return 0.0
    
    async def _get_average_session_duration(self, db: AsyncSession, start_date: datetime, end_date: datetime) -> float:
        """Calculate average session duration (simplified)."""
        try:
            # This is a simplified calculation
            # In a real system, you'd track actual session data
            return 15.5  # minutes
            
        except Exception as e:
            logger.error(f"Error calculating session duration: {e}")
            return 0.0
    
    async def _get_top_countries(self, db: AsyncSession, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get top countries by user count."""
        try:
            # This would typically query user address data
            # For now, return sample data
            return [
                {"country": "United States", "user_count": 1250, "percentage": 45.2},
                {"country": "Canada", "user_count": 320, "percentage": 11.6},
                {"country": "United Kingdom", "user_count": 280, "percentage": 10.1},
                {"country": "Germany", "user_count": 195, "percentage": 7.0},
                {"country": "France", "user_count": 165, "percentage": 6.0}
            ]
            
        except Exception as e:
            logger.error(f"Error getting top countries: {e}")
            return []
    
    async def _get_user_activity_trend(self, db: AsyncSession, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get user activity trend over time."""
        try:
            # Get daily user activity
            trend_data = []
            current_date = start_date
            
            while current_date <= end_date:
                next_date = current_date + timedelta(days=1)
                
                # Count active users for this day
                activity_result = await db.execute(
                    select(func.count(User.id)).where(
                        and_(
                            User.last_login >= current_date,
                            User.last_login < next_date,
                            User.is_active == True
                        )
                    )
                )
                active_count = activity_result.scalar()
                
                trend_data.append({
                    "date": current_date.date().isoformat(),
                    "active_users": active_count
                })
                
                current_date = next_date
            
            return trend_data
            
        except Exception as e:
            logger.error(f"Error getting user activity trend: {e}")
            return []
    
    async def _get_product_counts(self, db: AsyncSession, start_date: datetime, end_date: datetime) -> Dict[str, int]:
        """Get product count metrics."""
        try:
            # Total products
            total_products_result = await db.execute(select(func.count(Product.id)))
            total_products = total_products_result.scalar()
            
            # Active products
            active_products_result = await db.execute(
                select(func.count(Product.id)).where(Product.is_active == True)
            )
            active_products = active_products_result.scalar()
            
            # Low stock products
            low_stock_result = await db.execute(
                select(func.count(Product.id)).where(
                    and_(
                        Product.stock_quantity <= Product.min_stock_level,
                        Product.stock_quantity > 0
                    )
                )
            )
            low_stock_products = low_stock_result.scalar()
            
            # Out of stock products
            out_of_stock_result = await db.execute(
                select(func.count(Product.id)).where(Product.stock_quantity == 0)
            )
            out_of_stock_products = out_of_stock_result.scalar()
            
            return {
                "total_products": total_products,
                "active_products": active_products,
                "low_stock_products": low_stock_products,
                "out_of_stock_products": out_of_stock_products
            }
            
        except Exception as e:
            logger.error(f"Error getting product counts: {e}")
            return {"total_products": 0, "active_products": 0, "low_stock_products": 0, "out_of_stock_products": 0}
    
    async def _get_revenue_metrics(self, db: AsyncSession, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get revenue metrics."""
        try:
            # Total revenue
            revenue_result = await db.execute(
                select(func.sum(Order.total_amount)).where(
                    and_(
                        Order.created_at >= start_date,
                        Order.created_at <= end_date,
                        Order.payment_status == "paid"
                    )
                )
            )
            total_revenue = revenue_result.scalar() or 0
            
            # Average order value
            aov_result = await db.execute(
                select(func.avg(Order.total_amount)).where(
                    and_(
                        Order.created_at >= start_date,
                        Order.created_at <= end_date,
                        Order.payment_status == "paid"
                    )
                )
            )
            average_order_value = aov_result.scalar() or 0
            
            return {
                "total_revenue": total_revenue,
                "average_order_value": average_order_value
            }
            
        except Exception as e:
            logger.error(f"Error getting revenue metrics: {e}")
            return {"total_revenue": 0, "average_order_value": 0}
    
    async def _get_top_selling_products(self, db: AsyncSession, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get top selling products."""
        try:
            top_products_result = await db.execute(
                select(
                    Product.id,
                    Product.name,
                    Product.sku,
                    func.sum(OrderItem.quantity).label('total_quantity'),
                    func.sum(OrderItem.total_price).label('total_revenue')
                )
                .join(OrderItem, Product.id == OrderItem.product_id)
                .join(Order, OrderItem.order_id == Order.id)
                .where(
                    and_(
                        Order.created_at >= start_date,
                        Order.created_at <= end_date,
                        Order.payment_status == "paid"
                    )
                )
                .group_by(Product.id, Product.name, Product.sku)
                .order_by(func.sum(OrderItem.quantity).desc())
                .limit(10)
            )
            
            return [
                {
                    "id": row.id,
                    "name": row.name,
                    "sku": row.sku,
                    "quantity_sold": int(row.total_quantity),
                    "revenue": float(row.total_revenue)
                }
                for row in top_products_result
            ]
            
        except Exception as e:
            logger.error(f"Error getting top selling products: {e}")
            return []
    
    async def _get_category_performance(self, db: AsyncSession, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get category performance metrics."""
        try:
            category_performance_result = await db.execute(
                select(
                    Category.id,
                    Category.name,
                    func.count(Product.id).label('product_count'),
                    func.sum(OrderItem.total_price).label('total_revenue'),
                    func.sum(OrderItem.quantity).label('total_quantity')
                )
                .join(Product, Category.id == Product.category_id)
                .join(OrderItem, Product.id == OrderItem.product_id)
                .join(Order, OrderItem.order_id == Order.id)
                .where(
                    and_(
                        Order.created_at >= start_date,
                        Order.created_at <= end_date,
                        Order.payment_status == "paid"
                    )
                )
                .group_by(Category.id, Category.name)
                .order_by(func.sum(OrderItem.total_price).desc())
            )
            
            return [
                {
                    "category_id": row.id,
                    "category_name": row.name,
                    "product_count": int(row.product_count),
                    "revenue": float(row.total_revenue or 0),
                    "quantity_sold": int(row.total_quantity or 0)
                }
                for row in category_performance_result
            ]
            
        except Exception as e:
            logger.error(f"Error getting category performance: {e}")
            return []
    
    async def _get_sales_trend(self, db: AsyncSession, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get sales trend over time."""
        try:
            trend_data = []
            current_date = start_date
            
            while current_date <= end_date:
                next_date = current_date + timedelta(days=1)
                
                # Get sales for this day
                daily_sales_result = await db.execute(
                    select(
                        func.count(Order.id).label('order_count'),
                        func.sum(Order.total_amount).label('total_revenue')
                    ).where(
                        and_(
                            Order.created_at >= current_date,
                            Order.created_at < next_date,
                            Order.payment_status == "paid"
                        )
                    )
                )
                
                daily_sales = daily_sales_result.first()
                
                trend_data.append({
                    "date": current_date.date().isoformat(),
                    "order_count": int(daily_sales.order_count or 0),
                    "revenue": float(daily_sales.total_revenue or 0)
                })
                
                current_date = next_date
            
            return trend_data
            
        except Exception as e:
            logger.error(f"Error getting sales trend: {e}")
            return []
    
    def _update_average_response_time(self, response_time: float):
        """Update average response time."""
        total = self.analytics_stats["total_requests"]
        current_avg = self.analytics_stats["average_response_time"]
        self.analytics_stats["average_response_time"] = (
            (current_avg * (total - 1) + response_time) / total
        )
    
    def get_analytics_stats(self) -> Dict[str, Any]:
        """Get analytics service statistics."""
        total_requests = self.analytics_stats["total_requests"]
        cache_hit_rate = (
            (self.analytics_stats["cache_hits"] / total_requests * 100)
            if total_requests > 0 else 0
        )
        
        return {
            "total_requests": total_requests,
            "cache_hits": self.analytics_stats["cache_hits"],
            "cache_hit_rate": round(cache_hit_rate, 2),
            "average_response_time": round(self.analytics_stats["average_response_time"], 3),
            "last_computation": self.analytics_stats["last_computation"]
        }
    
    async def clear_analytics_cache(self) -> bool:
        """Clear all analytics cache."""
        try:
            patterns = [
                "analytics:users:*",
                "analytics:products:*"
            ]
            
            for pattern in patterns:
                await self.cache_service.delete_pattern(pattern)
            
            logger.info("Analytics cache cleared")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing analytics cache: {e}")
            return False
