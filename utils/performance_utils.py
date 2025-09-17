"""
Performance optimization utilities for the Telegram bot
"""
import asyncio
import time
from functools import wraps
from typing import Any, Callable, Dict, Tuple
from telegram import Update
from telegram.ext import ContextTypes


class PerformanceMonitor:
    """Monitor and log performance metrics"""
    
    def __init__(self):
        self.metrics = {}
        self.slow_operations = []
    
    def log_execution_time(self, func_name: str, duration: float):
        """Log execution time for monitoring"""
        if func_name not in self.metrics:
            self.metrics[func_name] = []
        
        self.metrics[func_name].append(duration)
        
        # Log slow operations
        if duration > 1.0:
            self.slow_operations.append({
                'function': func_name,
                'duration': duration,
                'timestamp': time.time()
            })
            print(f"⚠️ SLOW OPERATION: {func_name} took {duration:.2f}s")
        
        # Log critical operations
        if duration > 5.0:
            print(f"🚨 CRITICAL SLOW: {func_name} took {duration:.2f}s")


# Global performance monitor
perf_monitor = PerformanceMonitor()


def answer_callback_immediately(func: Callable) -> Callable:
    """
    Decorator to answer callback queries immediately to prevent timeout errors
    """
    @wraps(func)
    async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        query = update.callback_query
        
        # Answer callback query IMMEDIATELY to prevent timeout
        if query:
            try:
                await query.answer()
            except Exception as e:
                print(f"Warning: Could not answer callback query: {e}")
        
        # Execute the original function
        return await func(self, update, context, *args, **kwargs)
    
    return wrapper


def measure_performance(func_name: str = None):
    """
    Decorator to measure and log function execution time
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Use provided name or function name
                name = func_name or f"{func.__module__}.{func.__name__}"
                perf_monitor.log_execution_time(name, duration)
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                name = func_name or f"{func.__module__}.{func.__name__}"
                print(f"❌ ERROR in {name}: {e} (took {duration:.2f}s)")
                raise
        
        return wrapper
    return decorator


class CacheManager:
    """Simple in-memory cache with TTL support"""
    
    def __init__(self, default_ttl: int = 300):
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self.default_ttl = default_ttl
    
    async def get_or_set(self, key: str, fetch_func: Callable, ttl: int = None) -> Any:
        """
        Get value from cache or fetch and cache it
        
        Args:
            key: Cache key
            fetch_func: Function to fetch data if not in cache
            ttl: Time to live in seconds (uses default if None)
        
        Returns:
            Cached or fetched data
        """
        current_time = time.time()
        ttl = ttl or self.default_ttl
        
        # Check if key exists and is not expired
        if key in self._cache:
            data, timestamp = self._cache[key]
            if current_time - timestamp < ttl:
                return data
        
        # Fetch new data
        try:
            data = await fetch_func()
            self._cache[key] = (data, current_time)
            return data
        except Exception as e:
            print(f"❌ Cache fetch error for key '{key}': {e}")
            raise
    
    def clear(self, key: str = None):
        """Clear cache entry or entire cache"""
        if key:
            self._cache.pop(key, None)
        else:
            self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        current_time = time.time()
        active_entries = sum(
            1 for _, (_, timestamp) in self._cache.items() 
            if current_time - timestamp < self.default_ttl
        )
        
        return {
            'total_entries': len(self._cache),
            'active_entries': active_entries,
            'expired_entries': len(self._cache) - active_entries
        }


# Global cache manager
cache_manager = CacheManager()


async def run_async_task(task_func: Callable, *args, **kwargs):
    """
    Run a task asynchronously without blocking the main thread
    
    Args:
        task_func: Function to run asynchronously
        *args: Arguments for the function
        **kwargs: Keyword arguments for the function
    """
    try:
        asyncio.create_task(task_func(*args, **kwargs))
    except Exception as e:
        print(f"❌ Async task error: {e}")


def get_performance_stats() -> Dict[str, Any]:
    """Get performance statistics"""
    return {
        'metrics': perf_monitor.metrics,
        'slow_operations': perf_monitor.slow_operations[-10:],  # Last 10 slow operations
        'cache_stats': cache_manager.get_stats()
    }
