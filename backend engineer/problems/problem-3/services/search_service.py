"""
Optimized search service with advanced query optimization and caching.
"""

import asyncio
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, text, Index
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.dialects.postgresql import array_agg
from datetime import datetime, timedelta

from models.database import Product, Category, ProductReview
from schemas.models import ProductSearchRequest, ProductSearchResponse, ProductResponse
from services.cache_service import CacheService
from core.config import settings

logger = logging.getLogger(__name__)


class SearchService:
    """Advanced search service with query optimization and caching."""
    
    def __init__(self, cache_service: CacheService):
        self.cache_service = cache_service
        self.search_stats = {
            "total_searches": 0,
            "cache_hits": 0,
            "average_response_time": 0.0,
            "popular_queries": {}
        }
    
    async def initialize(self):
        """Initialize search service."""
        logger.info("Search service initialized")
    
    async def close(self):
        """Close search service."""
        logger.info("Search service closed")
    
    def _build_search_query(self, request: ProductSearchRequest) -> Tuple[select, Dict[str, Any]]:
        """Build optimized search query with proper indexing."""
        query = select(Product).options(
            selectinload(Product.category),
            selectinload(Product.reviews)
        )
        
        conditions = []
        params = {}
        
        # Text search optimization
        if request.query:
            # Use full-text search if available, otherwise ILIKE
            search_terms = request.query.strip().split()
            search_conditions = []
            
            for term in search_terms:
                term_pattern = f"%{term}%"
                search_conditions.append(
                    or_(
                        Product.name.ilike(term_pattern),
                        Product.description.ilike(term_pattern),
                        Product.short_description.ilike(term_pattern),
                        Product.tags.any(term_pattern),
                        Product.brand.ilike(term_pattern),
                        Product.sku.ilike(term_pattern)
                    )
                )
            
            if search_conditions:
                conditions.append(and_(*search_conditions))
        
        # Category filter
        if request.category_id:
            conditions.append(Product.category_id == request.category_id)
        
        # Brand filter
        if request.brand:
            conditions.append(Product.brand.ilike(f"%{request.brand}%"))
        
        # Price range filter
        if request.min_price is not None:
            conditions.append(Product.price >= request.min_price)
        if request.max_price is not None:
            conditions.append(Product.price <= request.max_price)
        
        # Rating filter
        if request.min_rating is not None:
            conditions.append(Product.rating_average >= request.min_rating)
        
        # Stock filter
        if request.in_stock_only:
            conditions.append(Product.stock_quantity > 0)
        
        # Featured filter
        if request.featured_only:
            conditions.append(Product.is_featured == True)
        
        # Tags filter
        if request.tags:
            for tag in request.tags:
                conditions.append(Product.tags.any(tag))
        
        # Attributes filter
        if request.attributes:
            for key, value in request.attributes.items():
                conditions.append(Product.attributes[key].astext == str(value))
        
        # Active products only
        conditions.append(Product.is_active == True)
        
        # Apply all conditions
        if conditions:
            query = query.where(and_(*conditions))
        
        # Sorting optimization
        if request.sort_by == "relevance":
            # For relevance, we'll use a combination of factors
            # This is a simplified relevance scoring
            query = query.order_by(
                Product.is_featured.desc(),
                Product.rating_average.desc(),
                Product.sales_count.desc(),
                Product.created_at.desc()
            )
        elif request.sort_by == "price":
            if request.sort_order == "asc":
                query = query.order_by(Product.price.asc())
            else:
                query = query.order_by(Product.price.desc())
        elif request.sort_by == "rating":
            if request.sort_order == "asc":
                query = query.order_by(Product.rating_average.asc())
            else:
                query = query.order_by(Product.rating_average.desc())
        elif request.sort_by == "sales":
            if request.sort_order == "asc":
                query = query.order_by(Product.sales_count.asc())
            else:
                query = query.order_by(Product.sales_count.desc())
        elif request.sort_by == "newest":
            query = query.order_by(Product.created_at.desc())
        elif request.sort_by == "oldest":
            query = query.order_by(Product.created_at.asc())
        else:
            # Default sorting
            query = query.order_by(Product.created_at.desc())
        
        return query, params
    
    async def search_products(self, request: ProductSearchRequest, db: AsyncSession) -> ProductSearchResponse:
        """Perform optimized product search with caching."""
        start_time = time.time()
        
        # Create cache key
        cache_key = self._create_cache_key(request)
        
        # Try cache first
        cached_result = await self.cache_service.get(cache_key)
        if cached_result:
            self.search_stats["cache_hits"] += 1
            self.search_stats["total_searches"] += 1
            return ProductSearchResponse(**cached_result)
        
        # Perform search
        try:
            # Build optimized query
            query, params = self._build_search_query(request)
            
            # Get total count for pagination
            count_query = select(func.count(Product.id))
            for condition in query.whereclause.children if query.whereclause else []:
                count_query = count_query.where(condition)
            
            total_result = await db.execute(count_query)
            total = total_result.scalar()
            
            # Apply pagination
            offset = (request.page - 1) * request.size
            query = query.offset(offset).limit(request.size)
            
            # Execute query
            result = await db.execute(query)
            products = result.scalars().all()
            
            # Convert to response models
            product_responses = []
            for product in products:
                product_data = ProductResponse.model_validate(product)
                product_responses.append(product_data)
            
            # Calculate facets (simplified)
            facets = await self._calculate_facets(request, db)
            
            # Create response
            response = ProductSearchResponse(
                products=product_responses,
                total=total,
                page=request.page,
                size=request.size,
                pages=(total + request.size - 1) // request.size,
                facets=facets,
                search_time=time.time() - start_time,
                cache_hit=False
            )
            
            # Cache the result
            await self.cache_service.set(
                cache_key, 
                response.model_dump(), 
                settings.SEARCH_CACHE_TTL
            )
            
            # Update stats
            self.search_stats["total_searches"] += 1
            response_time = time.time() - start_time
            self._update_average_response_time(response_time)
            self._update_popular_queries(request.query)
            
            return response
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            raise
    
    def _create_cache_key(self, request: ProductSearchRequest) -> str:
        """Create cache key for search request."""
        key_parts = [
            "search",
            request.query,
            str(request.category_id or ""),
            str(request.brand or ""),
            str(request.min_price or ""),
            str(request.max_price or ""),
            str(request.min_rating or ""),
            str(request.in_stock_only),
            str(request.featured_only),
            str(request.tags or []),
            str(request.attributes or {}),
            request.sort_by,
            request.sort_order,
            str(request.page),
            str(request.size)
        ]
        return ":".join(key_parts)
    
    async def _calculate_facets(self, request: ProductSearchRequest, db: AsyncSession) -> Dict[str, Any]:
        """Calculate search facets for filtering."""
        try:
            facets = {}
            
            # Category facets
            category_query = select(
                Category.id,
                Category.name,
                func.count(Product.id).label('count')
            ).join(Product).where(Product.is_active == True)
            
            if request.category_id:
                category_query = category_query.where(Product.category_id == request.category_id)
            
            category_result = await db.execute(
                category_query.group_by(Category.id, Category.name).limit(10)
            )
            facets['categories'] = [
                {"id": row.id, "name": row.name, "count": row.count}
                for row in category_result
            ]
            
            # Brand facets
            brand_query = select(
                Product.brand,
                func.count(Product.id).label('count')
            ).where(Product.is_active == True)
            
            if request.category_id:
                brand_query = brand_query.where(Product.category_id == request.category_id)
            
            brand_result = await db.execute(
                brand_query.group_by(Product.brand).limit(10)
            )
            facets['brands'] = [
                {"brand": row.brand, "count": row.count}
                for row in brand_result if row.brand
            ]
            
            # Price range facets
            price_query = select(
                func.min(Product.price).label('min_price'),
                func.max(Product.price).label('max_price'),
                func.avg(Product.price).label('avg_price')
            ).where(Product.is_active == True)
            
            if request.category_id:
                price_query = price_query.where(Product.category_id == request.category_id)
            
            price_result = await db.execute(price_query)
            price_row = price_result.first()
            if price_row:
                facets['price_range'] = {
                    "min": float(price_row.min_price or 0),
                    "max": float(price_row.max_price or 0),
                    "avg": float(price_row.avg_price or 0)
                }
            
            return facets
            
        except Exception as e:
            logger.error(f"Error calculating facets: {e}")
            return {}
    
    def _update_average_response_time(self, response_time: float):
        """Update average response time."""
        total = self.search_stats["total_searches"]
        current_avg = self.search_stats["average_response_time"]
        self.search_stats["average_response_time"] = (
            (current_avg * (total - 1) + response_time) / total
        )
    
    def _update_popular_queries(self, query: str):
        """Update popular queries tracking."""
        if query:
            self.search_stats["popular_queries"][query] = (
                self.search_stats["popular_queries"].get(query, 0) + 1
            )
    
    async def get_search_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """Get search suggestions based on query."""
        try:
            if len(query) < 2:
                return []
            
            # Try cache first
            cache_key = f"suggestions:{query}:{limit}"
            cached_suggestions = await self.cache_service.get(cache_key)
            if cached_suggestions:
                return cached_suggestions
            
            # This would typically query a search index or database
            # For now, return empty list
            suggestions = []
            
            # Cache suggestions
            await self.cache_service.set(cache_key, suggestions, 300)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting search suggestions: {e}")
            return []
    
    async def get_popular_searches(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get popular search queries."""
        try:
            # Try cache first
            cache_key = f"popular_searches:{limit}"
            cached_popular = await self.cache_service.get(cache_key)
            if cached_popular:
                return cached_popular
            
            # Get popular queries from stats
            popular_queries = sorted(
                self.search_stats["popular_queries"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:limit]
            
            result = [
                {"query": query, "count": count}
                for query, count in popular_queries
            ]
            
            # Cache result
            await self.cache_service.set(cache_key, result, 600)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting popular searches: {e}")
            return []
    
    def get_search_stats(self) -> Dict[str, Any]:
        """Get search service statistics."""
        total_searches = self.search_stats["total_searches"]
        cache_hit_rate = (
            (self.search_stats["cache_hits"] / total_searches * 100)
            if total_searches > 0 else 0
        )
        
        return {
            "total_searches": total_searches,
            "cache_hits": self.search_stats["cache_hits"],
            "cache_hit_rate": round(cache_hit_rate, 2),
            "average_response_time": round(self.search_stats["average_response_time"], 3),
            "popular_queries_count": len(self.search_stats["popular_queries"])
        }
    
    async def clear_search_cache(self) -> bool:
        """Clear all search-related cache."""
        try:
            # Clear search cache patterns
            patterns = [
                "search:*",
                "suggestions:*",
                "popular_searches:*"
            ]
            
            for pattern in patterns:
                await self.cache_service.delete_pattern(pattern)
            
            logger.info("Search cache cleared")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing search cache: {e}")
            return False
