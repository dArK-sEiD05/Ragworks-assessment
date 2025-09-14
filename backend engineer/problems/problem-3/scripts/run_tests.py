#!/usr/bin/env python3
"""
Comprehensive test runner for performance optimization demo.
"""

import asyncio
import subprocess
import sys
import time
import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_performance_tests():
    """Run comprehensive performance tests."""
    logger.info("Starting performance tests...")
    
    try:
        # Run unit tests
        logger.info("Running unit tests...")
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/", 
            "-v", 
            "--tb=short",
            "--cov=.",
            "--cov-report=html",
            "--cov-report=term"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Unit tests failed: {result.stderr}")
            return False
        
        logger.info("Unit tests passed!")
        
        # Run performance benchmarks
        logger.info("Running performance benchmarks...")
        from tests.performance_test import run_performance_tests as run_benchmarks
        
        benchmark_results = await run_benchmarks()
        
        # Check performance targets
        overall_stats = benchmark_results.get("overall_stats", {})
        avg_response_time = overall_stats.get("average_response_time", 0)
        success_rate = overall_stats.get("overall_success_rate", 0)
        
        logger.info(f"Average response time: {avg_response_time:.3f}s")
        logger.info(f"Success rate: {success_rate:.1f}%")
        
        # Performance targets
        if avg_response_time > 0.2:  # 200ms target
            logger.warning(f"Response time {avg_response_time:.3f}s exceeds target of 0.2s")
        
        if success_rate < 95:  # 95% success rate target
            logger.warning(f"Success rate {success_rate:.1f}% below target of 95%")
        
        # Run load tests with Locust
        logger.info("Running load tests...")
        locust_process = subprocess.Popen([
            "locust",
            "-f", "tests/load_test.py",
            "--host=http://localhost:8000",
            "--users=100",
            "--spawn-rate=10",
            "--run-time=60s",
            "--headless",
            "--html=load_test_report.html"
        ])
        
        locust_process.wait()
        
        if locust_process.returncode != 0:
            logger.error("Load tests failed")
            return False
        
        logger.info("Load tests completed!")
        
        # Generate test report
        report = {
            "timestamp": time.time(),
            "unit_tests": "passed",
            "performance_benchmarks": benchmark_results,
            "load_tests": "completed",
            "summary": {
                "avg_response_time": avg_response_time,
                "success_rate": success_rate,
                "meets_targets": avg_response_time <= 0.2 and success_rate >= 95
            }
        }
        
        with open("test_report.json", "w") as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info("Test report saved to test_report.json")
        
        return True
        
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        return False


async def run_database_migration():
    """Run database migration."""
    logger.info("Running database migration...")
    
    try:
        from migrations.migration_runner import run_migration
        await run_migration()
        logger.info("Database migration completed!")
        return True
    except Exception as e:
        logger.error(f"Database migration failed: {e}")
        return False


async def main():
    """Main test runner."""
    logger.info("Starting comprehensive test suite...")
    
    # Run database migration
    if not await run_database_migration():
        logger.error("Database migration failed, aborting tests")
        sys.exit(1)
    
    # Run performance tests
    if not await run_performance_tests():
        logger.error("Performance tests failed")
        sys.exit(1)
    
    logger.info("All tests completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
