"""Performance tests and profiling for critical framework operations.

This module contains performance tests that profile critical operations in the
framework, particularly focusing on memory management and concurrency control.
"""

import cProfile
import pstats
from functools import lru_cache
import threading
from typing import List, Optional

from src.core.base import ModFramework
from src.security.validation import SecurityValidator


def profile_concurrent_memory_operations(num_threads: int = 5, iterations: int = 1000):
    """Profile concurrent memory operations for performance analysis."""
    framework = ModFramework()
    validator = SecurityValidator()
    results: List[bool] = []
    
    def perform_operations():
        """Execute memory operations in a thread."""
        for i in range(iterations):
            address = 0x1000 + (i * 0x1000)  # Separate pages
            is_valid, _ = framework.validate_memory_region(address, 16)
            if is_valid:
                success, _ = validator.validate_modification(
                    address, b"test data"
                )
                results.append(success)
    
    # Create and start threads
    threads = [
        threading.Thread(target=perform_operations)
        for _ in range(num_threads)
    ]
    
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Start threads
    for thread in threads:
        thread.start()
    
    # Wait for completion
    for thread in threads:
        thread.join()
    
    profiler.disable()
    
    # Print profiling stats
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats()
    
    return len([r for r in results if r])  # Return successful operations


class CachedModFramework(ModFramework):
    """ModFramework with caching optimizations."""
    
    def __init__(self) -> None:
        """Initialize with caching enabled."""
        super().__init__()
        self._region_cache = {}
    
    @lru_cache(maxsize=1024)
    def validate_memory_region(self, address: int, size: int) -> tuple[bool, Optional[str]]:
        """Cached version of memory region validation.
        
        Uses LRU cache to avoid recomputing validation for frequently
        accessed regions.
        
        Returns:
            tuple[bool, Optional[str]]: Tuple containing:
                - bool: True if region is safe to modify
                - Optional[str]: Error message if validation failed
        """
        return super().validate_memory_region(address, size)


def compare_framework_performance():
    """Compare performance between regular and cached frameworks."""
    standard = ModFramework()
    cached = CachedModFramework()
    
    def test_framework(framework, name: str):
        """Profile operations on a framework instance."""
        profiler = cProfile.Profile()
        profiler.enable()
        
        # Perform repeated validations
        results = []
        for i in range(1000):
            # Test same regions multiple times
            address = 0x1000 + (i % 10 * 0x1000)
            is_valid, _ = framework.validate_memory_region(address, 16)
            results.append(is_valid)
        
        profiler.disable()
        
        print(f"\nProfiling results for {name}:")
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')
        stats.print_stats()
        
        return sum(results)
    
    # Profile both implementations
    standard_results = test_framework(standard, "Standard Framework")
    cached_results = test_framework(cached, "Cached Framework")
    
    return standard_results, cached_results


def test_concurrent_memory_performance():
    """Test and profile concurrent memory operations."""
    # Profile concurrent operations
    print("\nProfiling concurrent memory operations:")
    successful_ops = profile_concurrent_memory_operations(num_threads=3, iterations=100)
    assert successful_ops > 0, "No successful operations completed"
    
def test_caching_performance():
    """Test and profile caching optimizations."""
    # Compare implementations
    print("\nComparing framework implementations:")
    std_res, cache_res = compare_framework_performance()
    assert std_res > 0, "Standard framework failed all operations"
    assert cache_res > 0, "Cached framework failed all operations"
    # Cached version should handle at least as many operations
    assert cache_res >= std_res, "Cached version performed worse than standard"
