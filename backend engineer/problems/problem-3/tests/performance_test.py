"""
Performance testing utilities and benchmarks.
"""

import asyncio
import time
import statistics
import json
from typing import List, Dict, Any, Optional
import httpx
import logging

logger = logging.getLogger(__name__)


class PerformanceBenchmark:
    """Performance benchmarking utility."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[Dict[str, Any]] = []
    
    async def run_benchmark(self, test_name: str, func, *args, **kwargs) -> Dict[str, Any]:
        """Run a benchmark test."""
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            success = True
            error = None
        except Exception as e:
            result = None
            success = False
            error = str(e)
            logger.error(f"Benchmark {test_name} failed: {e}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        benchmark_result = {
            "test_name": test_name,
            "duration": duration,
            "success": success,
            "error": error,
            "timestamp": time.time()
        }
        
        self.results.append(benchmark_result)
        return benchmark_result
    
    async def test_endpoint_performance(
        self, 
        endpoint: str, 
        method: str = "GET", 
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        iterations: int = 10
    ) -> Dict[str, Any]:
        """Test endpoint performance with multiple iterations."""
        
        async def make_request():
            async with httpx.AsyncClient() as client:
                if method.upper() == "GET":
                    response = await client.get(f"{self.base_url}{endpoint}", params=params, headers=headers)
                elif method.upper() == "POST":
                    response = await client.post(f"{self.base_url}{endpoint}", json=json_data, headers=headers)
                elif method.upper() == "PUT":
                    response = await client.put(f"{self.base_url}{endpoint}", json=json_data, headers=headers)
                elif method.upper() == "DELETE":
                    response = await client.delete(f"{self.base_url}{endpoint}", headers=headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                return response.status_code, response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
        
        durations = []
        status_codes = []
        errors = []
        
        for i in range(iterations):
            start_time = time.time()
            try:
                status_code, response_data = await make_request()
                durations.append(time.time() - start_time)
                status_codes.append(status_code)
                errors.append(None)
            except Exception as e:
                durations.append(time.time() - start_time)
                status_codes.append(0)
                errors.append(str(e))
        
        # Calculate statistics
        successful_requests = [d for d, s in zip(durations, status_codes) if 200 <= s < 400]
        error_requests = [d for d, s in zip(durations, status_codes) if s >= 400 or s == 0]
        
        result = {
            "endpoint": endpoint,
            "method": method,
            "iterations": iterations,
            "successful_requests": len(successful_requests),
            "error_requests": len(error_requests),
            "success_rate": len(successful_requests) / iterations * 100,
            "average_response_time": statistics.mean(successful_requests) if successful_requests else 0,
            "min_response_time": min(successful_requests) if successful_requests else 0,
            "max_response_time": max(successful_requests) if successful_requests else 0,
            "median_response_time": statistics.median(successful_requests) if successful_requests else 0,
            "p95_response_time": self._percentile(successful_requests, 95) if successful_requests else 0,
            "p99_response_time": self._percentile(successful_requests, 99) if successful_requests else 0,
            "errors": [e for e in errors if e is not None],
            "status_codes": dict(zip(*np.unique(status_codes, return_counts=True))) if status_codes else {}
        }
        
        return result
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data."""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive performance test suite."""
        logger.info("Starting comprehensive performance test...")
        
        test_results = {}
        
        # Test 1: Health check
        logger.info("Testing health check endpoint...")
        test_results["health_check"] = await self.test_endpoint_performance("/health")
        
        # Test 2: Product search
        logger.info("Testing product search endpoint...")
        test_results["product_search"] = await self.test_endpoint_performance(
            "/products/search",
            params={"q": "laptop", "page": 1, "size": 20}
        )
        
        # Test 3: Product list
        logger.info("Testing product list endpoint...")
        test_results["product_list"] = await self.test_endpoint_performance(
            "/products",
            params={"page": 1, "size": 20}
        )
        
        # Test 4: Categories
        logger.info("Testing categories endpoint...")
        test_results["categories"] = await self.test_endpoint_performance("/products/categories")
        
        # Test 5: Popular products
        logger.info("Testing popular products endpoint...")
        test_results["popular_products"] = await self.test_endpoint_performance(
            "/products/popular",
            params={"limit": 20}
        )
        
        # Test 6: Performance metrics
        logger.info("Testing metrics endpoint...")
        test_results["metrics"] = await self.test_endpoint_performance("/metrics")
        
        # Test 7: Cache operations
        logger.info("Testing cache operations...")
        test_results["cache_warm"] = await self.test_endpoint_performance("/cache/warm", "POST")
        
        # Calculate overall statistics
        all_durations = []
        total_requests = 0
        successful_requests = 0
        
        for test_name, result in test_results.items():
            if isinstance(result, dict) and "average_response_time" in result:
                all_durations.append(result["average_response_time"])
                total_requests += result["iterations"]
                successful_requests += result["successful_requests"]
        
        overall_stats = {
            "total_tests": len(test_results),
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "overall_success_rate": (successful_requests / total_requests * 100) if total_requests > 0 else 0,
            "average_response_time": statistics.mean(all_durations) if all_durations else 0,
            "fastest_endpoint": min(test_results.items(), key=lambda x: x[1].get("average_response_time", float('inf')))[0] if test_results else None,
            "slowest_endpoint": max(test_results.items(), key=lambda x: x[1].get("average_response_time", 0))[0] if test_results else None
        }
        
        test_results["overall_stats"] = overall_stats
        
        logger.info("Comprehensive performance test completed")
        return test_results
    
    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate performance test report."""
        report = {
            "test_summary": {
                "total_tests": len(self.results),
                "successful_tests": len([r for r in self.results if r["success"]]),
                "failed_tests": len([r for r in self.results if not r["success"]]),
                "total_duration": sum(r["duration"] for r in self.results),
                "average_duration": statistics.mean([r["duration"] for r in self.results]) if self.results else 0
            },
            "test_results": self.results,
            "recommendations": self._generate_recommendations()
        }
        
        report_json = json.dumps(report, indent=2, default=str)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_json)
            logger.info(f"Performance report saved to {output_file}")
        
        return report_json
    
    def _generate_recommendations(self) -> List[str]:
        """Generate performance recommendations based on test results."""
        recommendations = []
        
        if not self.results:
            return ["No test results available for recommendations"]
        
        # Check for slow tests
        slow_tests = [r for r in self.results if r["duration"] > 2.0]
        if slow_tests:
            recommendations.append(f"Consider optimizing {len(slow_tests)} slow tests (>2s)")
        
        # Check for failed tests
        failed_tests = [r for r in self.results if not r["success"]]
        if failed_tests:
            recommendations.append(f"Fix {len(failed_tests)} failed tests")
        
        # Check for high variance in response times
        durations = [r["duration"] for r in self.results if r["success"]]
        if len(durations) > 1:
            variance = statistics.variance(durations)
            if variance > 1.0:  # High variance
                recommendations.append("High variance in response times detected - consider load balancing")
        
        # General recommendations
        recommendations.extend([
            "Monitor database query performance",
            "Implement caching for frequently accessed data",
            "Consider CDN for static content",
            "Optimize database indexes",
            "Implement connection pooling",
            "Use async processing for heavy operations"
        ])
        
        return recommendations


async def run_performance_tests():
    """Run all performance tests."""
    benchmark = PerformanceBenchmark()
    
    # Run comprehensive test
    results = await benchmark.run_comprehensive_test()
    
    # Generate report
    report = benchmark.generate_report("performance_report.json")
    
    # Print summary
    print("\n" + "="*50)
    print("PERFORMANCE TEST SUMMARY")
    print("="*50)
    
    for test_name, result in results.items():
        if isinstance(result, dict) and "average_response_time" in result:
            print(f"\n{test_name.upper()}:")
            print(f"  Success Rate: {result['success_rate']:.1f}%")
            print(f"  Avg Response Time: {result['average_response_time']:.3f}s")
            print(f"  P95 Response Time: {result['p95_response_time']:.3f}s")
            print(f"  P99 Response Time: {result['p99_response_time']:.3f}s")
    
    if "overall_stats" in results:
        stats = results["overall_stats"]
        print(f"\nOVERALL STATISTICS:")
        print(f"  Total Requests: {stats['total_requests']}")
        print(f"  Success Rate: {stats['overall_success_rate']:.1f}%")
        print(f"  Average Response Time: {stats['average_response_time']:.3f}s")
        print(f"  Fastest Endpoint: {stats['fastest_endpoint']}")
        print(f"  Slowest Endpoint: {stats['slowest_endpoint']}")
    
    print("\n" + "="*50)
    
    return results


if __name__ == "__main__":
    asyncio.run(run_performance_tests())
