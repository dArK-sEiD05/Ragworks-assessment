"""
Performance monitoring and metrics collection service.
"""

import time
import psutil
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
import json

from core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Performance metric data structure."""
    endpoint: str
    method: str
    response_time: float
    status_code: int
    timestamp: datetime
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    cache_hit: bool = False
    database_queries: int = 0
    database_time: float = 0.0
    memory_usage: Optional[int] = None
    cpu_usage: Optional[float] = None


class PerformanceMonitor:
    """Advanced performance monitoring service."""
    
    def __init__(self):
        self.metrics: deque = deque(maxlen=10000)  # Keep last 10k metrics
        self.endpoint_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "total_requests": 0,
            "total_response_time": 0.0,
            "min_response_time": float('inf'),
            "max_response_time": 0.0,
            "status_codes": defaultdict(int),
            "cache_hits": 0,
            "database_queries": 0,
            "database_time": 0.0,
            "errors": 0
        })
        self.cache_stats: Dict[str, int] = defaultdict(int)
        self.error_rates: Dict[str, float] = defaultdict(float)
        self.throughput: Dict[str, float] = defaultdict(float)
        self.database_performance: Dict[str, Any] = {
            "total_queries": 0,
            "total_time": 0.0,
            "average_time": 0.0,
            "slow_queries": 0
        }
        self.memory_usage: List[Dict[str, Any]] = []
        self.cpu_usage: List[Dict[str, Any]] = []
        self.start_time = time.time()
        self.last_cleanup = time.time()
    
    async def initialize(self):
        """Initialize performance monitoring."""
        logger.info("Performance monitoring initialized")
        
        # Start background monitoring tasks
        if settings.ENABLE_METRICS:
            asyncio.create_task(self._monitor_system_resources())
            asyncio.create_task(self._cleanup_old_metrics())
    
    async def close(self):
        """Close performance monitoring."""
        logger.info("Performance monitoring closed")
    
    def record_request(
        self, 
        endpoint: str, 
        response_time: float, 
        status_code: int = 200,
        method: str = "GET",
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        cache_hit: bool = False,
        database_queries: int = 0,
        database_time: float = 0.0
    ):
        """Record a request metric."""
        try:
            # Get current system metrics
            memory_usage = psutil.virtual_memory().percent if settings.ENABLE_METRICS else None
            cpu_usage = psutil.cpu_percent() if settings.ENABLE_METRICS else None
            
            # Create metric
            metric = PerformanceMetric(
                endpoint=endpoint,
                method=method,
                response_time=response_time,
                status_code=status_code,
                timestamp=datetime.utcnow(),
                user_id=user_id,
                ip_address=ip_address,
                cache_hit=cache_hit,
                database_queries=database_queries,
                database_time=database_time,
                memory_usage=memory_usage,
                cpu_usage=cpu_usage
            )
            
            # Store metric
            self.metrics.append(metric)
            
            # Update endpoint stats
            stats = self.endpoint_stats[endpoint]
            stats["total_requests"] += 1
            stats["total_response_time"] += response_time
            stats["min_response_time"] = min(stats["min_response_time"], response_time)
            stats["max_response_time"] = max(stats["max_response_time"], response_time)
            stats["status_codes"][status_code] += 1
            stats["cache_hits"] += 1 if cache_hit else 0
            stats["database_queries"] += database_queries
            stats["database_time"] += database_time
            stats["errors"] += 1 if status_code >= 400 else 0
            
            # Update database performance
            self.database_performance["total_queries"] += database_queries
            self.database_performance["total_time"] += database_time
            if database_time > settings.SLOW_QUERY_THRESHOLD:
                self.database_performance["slow_queries"] += 1
            
            # Update error rates
            if status_code >= 400:
                self.error_rates[endpoint] = stats["errors"] / stats["total_requests"]
            
            # Update throughput (requests per second)
            current_time = time.time()
            time_window = 60  # 1 minute window
            recent_requests = [
                m for m in self.metrics 
                if (current_time - m.timestamp.timestamp()) <= time_window
            ]
            self.throughput[endpoint] = len(recent_requests) / time_window
            
        except Exception as e:
            logger.error(f"Error recording request metric: {e}")
    
    def record_cache_hit(self, cache_type: str):
        """Record a cache hit."""
        self.cache_stats[cache_type] += 1
    
    def record_database_query(self, query_time: float, query_type: str = "select"):
        """Record a database query."""
        self.database_performance["total_queries"] += 1
        self.database_performance["total_time"] += query_time
        
        if query_time > settings.SLOW_QUERY_THRESHOLD:
            self.database_performance["slow_queries"] += 1
            logger.warning(f"Slow query detected: {query_time:.3f}s")
    
    async def _monitor_system_resources(self):
        """Monitor system resources in background."""
        while True:
            try:
                # Memory usage
                memory = psutil.virtual_memory()
                self.memory_usage.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "used_percent": memory.percent,
                    "used_mb": memory.used / 1024 / 1024,
                    "available_mb": memory.available / 1024 / 1024
                })
                
                # Keep only last 1000 memory readings
                if len(self.memory_usage) > 1000:
                    self.memory_usage = self.memory_usage[-1000:]
                
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                self.cpu_usage.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "cpu_percent": cpu_percent
                })
                
                # Keep only last 1000 CPU readings
                if len(self.cpu_usage) > 1000:
                    self.cpu_usage = self.cpu_usage[-1000:]
                
                # Check for memory warnings
                if memory.percent > settings.MEMORY_WARNING_THRESHOLD * 100:
                    logger.warning(f"High memory usage: {memory.percent:.1f}%")
                
                # Sleep for monitoring interval
                await asyncio.sleep(30)  # Monitor every 30 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring system resources: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _cleanup_old_metrics(self):
        """Clean up old metrics to prevent memory leaks."""
        while True:
            try:
                current_time = time.time()
                
                # Clean up metrics older than 1 hour
                cutoff_time = current_time - 3600
                self.metrics = deque(
                    [m for m in self.metrics if m.timestamp.timestamp() > cutoff_time],
                    maxlen=10000
                )
                
                # Clean up memory usage data older than 1 hour
                cutoff_datetime = datetime.fromtimestamp(cutoff_time)
                self.memory_usage = [
                    m for m in self.memory_usage 
                    if datetime.fromisoformat(m["timestamp"]) > cutoff_datetime
                ]
                
                # Clean up CPU usage data older than 1 hour
                self.cpu_usage = [
                    c for c in self.cpu_usage 
                    if datetime.fromisoformat(c["timestamp"]) > cutoff_datetime
                ]
                
                self.last_cleanup = current_time
                
                # Sleep for cleanup interval
                await asyncio.sleep(300)  # Cleanup every 5 minutes
                
            except Exception as e:
                logger.error(f"Error cleaning up metrics: {e}")
                await asyncio.sleep(600)  # Wait longer on error
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics."""
        try:
            current_time = time.time()
            uptime = current_time - self.start_time
            
            # Calculate response time percentiles
            response_times = [m.response_time for m in self.metrics]
            response_times.sort()
            
            percentiles = {}
            if response_times:
                n = len(response_times)
                percentiles = {
                    "p50": response_times[int(n * 0.5)],
                    "p90": response_times[int(n * 0.9)],
                    "p95": response_times[int(n * 0.95)],
                    "p99": response_times[int(n * 0.99)],
                    "min": min(response_times),
                    "max": max(response_times),
                    "avg": sum(response_times) / n
                }
            
            # Calculate endpoint-specific metrics
            endpoint_metrics = {}
            for endpoint, stats in self.endpoint_stats.items():
                if stats["total_requests"] > 0:
                    endpoint_metrics[endpoint] = {
                        "total_requests": stats["total_requests"],
                        "average_response_time": stats["total_response_time"] / stats["total_requests"],
                        "min_response_time": stats["min_response_time"] if stats["min_response_time"] != float('inf') else 0,
                        "max_response_time": stats["max_response_time"],
                        "cache_hit_rate": (stats["cache_hits"] / stats["total_requests"]) * 100,
                        "error_rate": (stats["errors"] / stats["total_requests"]) * 100,
                        "throughput": self.throughput.get(endpoint, 0),
                        "status_codes": dict(stats["status_codes"])
                    }
            
            # Calculate cache hit rates
            total_cache_requests = sum(self.cache_stats.values())
            cache_hit_rates = {}
            if total_cache_requests > 0:
                for cache_type, hits in self.cache_stats.items():
                    cache_hit_rates[cache_type] = (hits / total_cache_requests) * 100
            
            # Calculate database performance
            db_performance = {
                "total_queries": self.database_performance["total_queries"],
                "total_time": self.database_performance["total_time"],
                "average_time": (
                    self.database_performance["total_time"] / self.database_performance["total_queries"]
                    if self.database_performance["total_queries"] > 0 else 0
                ),
                "slow_queries": self.database_performance["slow_queries"],
                "slow_query_rate": (
                    self.database_performance["slow_queries"] / self.database_performance["total_queries"] * 100
                    if self.database_performance["total_queries"] > 0 else 0
                )
            }
            
            # Get current system metrics
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent()
            
            # Calculate memory usage trend
            memory_trend = []
            if len(self.memory_usage) > 0:
                recent_memory = self.memory_usage[-10:]  # Last 10 readings
                memory_trend = [m["used_percent"] for m in recent_memory]
            
            # Calculate CPU usage trend
            cpu_trend = []
            if len(self.cpu_usage) > 0:
                recent_cpu = self.cpu_usage[-10:]  # Last 10 readings
                cpu_trend = [c["cpu_percent"] for c in recent_cpu]
            
            return {
                "response_times": percentiles,
                "endpoints": endpoint_metrics,
                "cache_hit_rates": cache_hit_rates,
                "error_rates": dict(self.error_rates),
                "throughput": dict(self.throughput),
                "database_performance": db_performance,
                "memory_usage": {
                    "current_percent": memory.percent,
                    "current_mb": memory.used / 1024 / 1024,
                    "available_mb": memory.available / 1024 / 1024,
                    "trend": memory_trend
                },
                "cpu_usage": {
                    "current_percent": cpu_percent,
                    "trend": cpu_trend
                },
                "system_info": {
                    "uptime_seconds": uptime,
                    "total_metrics": len(self.metrics),
                    "last_cleanup": self.last_cleanup,
                    "monitoring_enabled": settings.ENABLE_METRICS
                },
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat()
            }
    
    def get_endpoint_metrics(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Get metrics for a specific endpoint."""
        if endpoint not in self.endpoint_stats:
            return None
        
        stats = self.endpoint_stats[endpoint]
        if stats["total_requests"] == 0:
            return None
        
        return {
            "endpoint": endpoint,
            "total_requests": stats["total_requests"],
            "average_response_time": stats["total_response_time"] / stats["total_requests"],
            "min_response_time": stats["min_response_time"] if stats["min_response_time"] != float('inf') else 0,
            "max_response_time": stats["max_response_time"],
            "cache_hit_rate": (stats["cache_hits"] / stats["total_requests"]) * 100,
            "error_rate": (stats["errors"] / stats["total_requests"]) * 100,
            "throughput": self.throughput.get(endpoint, 0),
            "status_codes": dict(stats["status_codes"])
        }
    
    def get_slow_queries(self) -> List[Dict[str, Any]]:
        """Get information about slow queries."""
        slow_queries = []
        for metric in self.metrics:
            if metric.database_time > settings.SLOW_QUERY_THRESHOLD:
                slow_queries.append({
                    "endpoint": metric.endpoint,
                    "database_time": metric.database_time,
                    "timestamp": metric.timestamp.isoformat(),
                    "user_id": metric.user_id
                })
        
        # Sort by database time descending
        slow_queries.sort(key=lambda x: x["database_time"], reverse=True)
        return slow_queries[:50]  # Return top 50 slow queries
    
    def reset_metrics(self):
        """Reset all metrics."""
        self.metrics.clear()
        self.endpoint_stats.clear()
        self.cache_stats.clear()
        self.error_rates.clear()
        self.throughput.clear()
        self.database_performance = {
            "total_queries": 0,
            "total_time": 0.0,
            "average_time": 0.0,
            "slow_queries": 0
        }
        self.memory_usage.clear()
        self.cpu_usage.clear()
        self.start_time = time.time()
        self.last_cleanup = time.time()
        
        logger.info("Performance metrics reset")
    
    def export_metrics(self, filepath: str) -> bool:
        """Export metrics to JSON file."""
        try:
            metrics_data = {
                "metrics": [asdict(m) for m in self.metrics],
                "endpoint_stats": dict(self.endpoint_stats),
                "cache_stats": dict(self.cache_stats),
                "error_rates": dict(self.error_rates),
                "throughput": dict(self.throughput),
                "database_performance": self.database_performance,
                "memory_usage": self.memory_usage,
                "cpu_usage": self.cpu_usage,
                "exported_at": datetime.utcnow().isoformat()
            }
            
            with open(filepath, 'w') as f:
                json.dump(metrics_data, f, indent=2, default=str)
            
            logger.info(f"Metrics exported to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
            return False
