#!/usr/bin/env python3
"""
Performance benchmarking script for optimization demo.
"""

import asyncio
import time
import statistics
import json
from datetime import datetime
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PerformanceBenchmark:
    """Comprehensive performance benchmark."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = {}
    
    async def benchmark_endpoint(self, name: str, endpoint: str, method: str = "GET", 
                                params: dict = None, headers: dict = None, 
                                iterations: int = 100):
        """Benchmark a specific endpoint."""
        logger.info(f"Benchmarking {name}...")
        
        durations = []
        errors = 0
        
        async with httpx.AsyncClient() as client:
            for i in range(iterations):
                start_time = time.time()
                
                try:
                    if method.upper() == "GET":
                        response = await client.get(f"{self.base_url}{endpoint}", 
                                                  params=params, headers=headers)
                    elif method.upper() == "POST":
                        response = await client.post(f"{self.base_url}{endpoint}", 
                                                   json=params, headers=headers)
                    else:
                        raise ValueError(f"Unsupported method: {method}")
                    
                    if response.status_code >= 400:
                        errors += 1
                    
                except Exception as e:
                    logger.error(f"Request failed: {e}")
                    errors += 1
                
                duration = time.time() - start_time
                durations.append(duration)
        
        # Calculate statistics
        successful_requests = iterations - errors
        success_rate = (successful_requests / iterations) * 100
        
        if durations:
            stats = {
                "iterations": iterations,
                "successful_requests": successful_requests,
                "errors": errors,
                "success_rate": success_rate,
                "min_duration": min(durations),
                "max_duration": max(durations),
                "avg_duration": statistics.mean(durations),
                "median_duration": statistics.median(durations),
                "p95_duration": self._percentile(durations, 95),
                "p99_duration": self._percentile(durations, 99),
                "std_deviation": statistics.stdev(durations) if len(durations) > 1 else 0
            }
        else:
            stats = {
                "iterations": iterations,
                "successful_requests": 0,
                "errors": errors,
                "success_rate": 0,
                "min_duration": 0,
                "max_duration": 0,
                "avg_duration": 0,
                "median_duration": 0,
                "p95_duration": 0,
                "p99_duration": 0,
                "std_deviation": 0
            }
        
        self.results[name] = stats
        logger.info(f"{name}: {stats['avg_duration']:.3f}s avg, {success_rate:.1f}% success")
        
        return stats
    
    def _percentile(self, data, percentile):
        """Calculate percentile."""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    async def run_comprehensive_benchmark(self):
        """Run comprehensive benchmark suite."""
        logger.info("Starting comprehensive performance benchmark...")
        
        # Test endpoints
        endpoints = [
            ("health_check", "/health", "GET"),
            ("product_search", "/products/search", "GET", {"q": "laptop", "page": 1, "size": 20}),
            ("product_list", "/products", "GET", {"page": 1, "size": 20}),
            ("categories", "/products/categories", "GET"),
            ("popular_products", "/products/popular", "GET", {"limit": 20}),
            ("metrics", "/metrics", "GET"),
            ("cache_stats", "/cache/stats", "GET"),
            ("search_stats", "/search/stats", "GET"),
            ("analytics_stats", "/analytics/stats", "GET"),
            ("trending_products", "/products/trending", "GET", {"limit": 20}),
        ]
        
        # Run benchmarks
        for endpoint_info in endpoints:
            name = endpoint_info[0]
            endpoint = endpoint_info[1]
            method = endpoint_info[2]
            params = endpoint_info[3] if len(endpoint_info) > 3 else None
            
            await self.benchmark_endpoint(name, endpoint, method, params)
        
        # Generate summary
        self._generate_summary()
        
        # Save results
        self._save_results()
        
        logger.info("Benchmark completed!")
    
    def _generate_summary(self):
        """Generate benchmark summary."""
        if not self.results:
            return
        
        # Calculate overall statistics
        all_avg_durations = [r["avg_duration"] for r in self.results.values()]
        all_success_rates = [r["success_rate"] for r in self.results.values()]
        
        summary = {
            "total_endpoints": len(self.results),
            "overall_avg_duration": statistics.mean(all_avg_durations),
            "overall_success_rate": statistics.mean(all_success_rates),
            "fastest_endpoint": min(self.results.items(), key=lambda x: x[1]["avg_duration"]),
            "slowest_endpoint": max(self.results.items(), key=lambda x: x[1]["avg_duration"]),
            "most_reliable_endpoint": max(self.results.items(), key=lambda x: x[1]["success_rate"]),
            "performance_targets": {
                "avg_response_time_target": 0.2,  # 200ms
                "success_rate_target": 95.0,  # 95%
                "meets_avg_response_time": statistics.mean(all_avg_durations) <= 0.2,
                "meets_success_rate": statistics.mean(all_success_rates) >= 95.0
            }
        }
        
        self.results["_summary"] = summary
        
        # Log summary
        logger.info("=" * 50)
        logger.info("BENCHMARK SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Total endpoints tested: {summary['total_endpoints']}")
        logger.info(f"Overall average duration: {summary['overall_avg_duration']:.3f}s")
        logger.info(f"Overall success rate: {summary['overall_success_rate']:.1f}%")
        logger.info(f"Fastest endpoint: {summary['fastest_endpoint'][0]} ({summary['fastest_endpoint'][1]['avg_duration']:.3f}s)")
        logger.info(f"Slowest endpoint: {summary['slowest_endpoint'][0]} ({summary['slowest_endpoint'][1]['avg_duration']:.3f}s)")
        logger.info(f"Most reliable endpoint: {summary['most_reliable_endpoint'][0]} ({summary['most_reliable_endpoint'][1]['success_rate']:.1f}%)")
        
        # Performance targets
        targets = summary["performance_targets"]
        logger.info(f"Meets response time target (≤200ms): {targets['meets_avg_response_time']}")
        logger.info(f"Meets success rate target (≥95%): {targets['meets_success_rate']}")
        
        if targets["meets_avg_response_time"] and targets["meets_success_rate"]:
            logger.info("✅ All performance targets met!")
        else:
            logger.warning("⚠️  Some performance targets not met")
        
        logger.info("=" * 50)
    
    def _save_results(self):
        """Save benchmark results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_results_{timestamp}.json"
        
        with open(filename, "w") as f:
            json.dump(self.results, f, indent=2, default=str)
        
        logger.info(f"Benchmark results saved to {filename}")


async def main():
    """Main benchmark runner."""
    benchmark = PerformanceBenchmark()
    await benchmark.run_comprehensive_benchmark()


if __name__ == "__main__":
    asyncio.run(main())
