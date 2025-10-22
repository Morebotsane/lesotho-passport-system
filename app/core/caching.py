# app/core/caching.py
"""
Smart caching decorators for FastAPI endpoints
Automatic cache key generation and invalidation
"""
import functools
import hashlib
import json
from typing import Any, Optional, Callable, Union, List
from fastapi import Request, Response
from fastapi.encoders import jsonable_encoder
import inspect
import logging

from app.core.redis_config import cache_service
from app.core.config import settings

logger = logging.getLogger(__name__)

def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Generate a deterministic cache key from function arguments
    
    Args:
        prefix: Cache key prefix
        *args: Function positional arguments
        **kwargs: Function keyword arguments
    
    Returns:
        SHA256 hash-based cache key
    """
    # Create a deterministic string from arguments
    key_data = {
        'args': args,
        'kwargs': {k: v for k, v in kwargs.items() if k not in ['db', 'current_user', 'request', 'response']}
    }
    
    # JSON serialize for consistent hashing
    key_string = json.dumps(key_data, sort_keys=True, default=str)
    
    # Generate hash
    hash_object = hashlib.sha256(key_string.encode())
    hash_hex = hash_object.hexdigest()[:16]  # Use first 16 chars
    
    return f"{prefix}:{hash_hex}"

def cache_response(
    ttl: int = None,
    prefix: str = "api",
    key_builder: Optional[Callable] = None,
    skip_if: Optional[Callable] = None,
    vary_on_user: bool = True
):
    """
    Cache API endpoint responses with smart key generation
    
    Args:
        ttl: Time to live in seconds (uses default if None)
        prefix: Cache key prefix
        key_builder: Custom function to build cache key
        skip_if: Function that returns True to skip caching
        vary_on_user: Include user ID in cache key
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Skip caching in certain conditions
            if skip_if and skip_if(*args, **kwargs):
                return await func(*args, **kwargs)
            
            # Extract user info if needed
            user_id = None
            if vary_on_user:
                # Look for current_user in kwargs
                current_user = kwargs.get('current_user')
                if current_user:
                    user_id = str(getattr(current_user, 'id', ''))
            
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                key_suffix = f":user:{user_id}" if user_id else ""
                cache_key = generate_cache_key(prefix, *args, **kwargs) + key_suffix
            
            # Try to get from cache
            if cache_service: 
                cached_result = cache_service.get(cache_key) 
            else: 
                cached_result = None

            if cached_result is not None:
                logger.debug(f"Cache HIT for key: {cache_key}")
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache the result
            if cache_service:
                cache_ttl = ttl or settings.CACHE_DEFAULT_TTL
                if cache_service.set(cache_key, jsonable_encoder(result), cache_ttl):
                    logger.debug(f"Cached result for key: {cache_key} (TTL: {cache_ttl}s)")
                else:
                    logger.warning(f"Failed to cache result for key: {cache_key}")
            
            return result
            
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Same logic for sync functions
            if skip_if and skip_if(*args, **kwargs):
                return func(*args, **kwargs)
            
            user_id = None
            if vary_on_user:
                current_user = kwargs.get('current_user')
                if current_user:
                    user_id = str(getattr(current_user, 'id', ''))
            
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                key_suffix = f":user:{user_id}" if user_id else ""
                cache_key = generate_cache_key(prefix, *args, **kwargs) + key_suffix
            
            if cache_service: 
                cached_result = cache_service.get(cache_key) 
            else: 
                cached_result = None

            if cached_result is not None:
                logger.debug(f"Cache HIT for key: {cache_key}")
                return cached_result
            
            result = func(*args, **kwargs)
            
            if cache_service:
                cache_ttl = ttl or settings.CACHE_DEFAULT_TTL
                if cache_service.set(cache_key, jsonable_encoder(result), cache_ttl):
                    logger.debug(f"Cached result for key: {cache_key} (TTL: {cache_ttl}s)")
            
            return result
        
        # Return appropriate wrapper based on function type
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def cache_invalidate(patterns: Union[str, List[str]]):
    """
    Decorator to invalidate cache patterns after function execution
    
    Args:
        patterns: Cache key pattern(s) to invalidate
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            # Invalidate cache patterns
            pattern_list = patterns if isinstance(patterns, list) else [patterns]
            for pattern in pattern_list:
                deleted_count = cache_service.delete_pattern(pattern)
                logger.debug(f"Invalidated {deleted_count} cache keys matching pattern: {pattern}")
            
            return result
            
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            pattern_list = patterns if isinstance(patterns, list) else [patterns]
            for pattern in pattern_list:
                deleted_count = cache_service.delete_pattern(pattern)
                logger.debug(f"Invalidated {deleted_count} cache keys matching pattern: {pattern}")
            
            return result
        
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

# Specialized caching decorators for common patterns
def cache_user_data(ttl: int = None):
    """Cache user-specific data"""
    return cache_response(
        ttl=ttl or settings.CACHE_USER_TTL,
        prefix="user",
        vary_on_user=True
    )

def cache_application_data(ttl: int = None):
    """Cache application-related data"""
    return cache_response(
        ttl=ttl or settings.CACHE_DEFAULT_TTL,
        prefix="app",
        vary_on_user=False
    )

def cache_statistics(ttl: int = None):
    """Cache statistics and analytics data"""
    return cache_response(
        ttl=ttl or settings.CACHE_STATS_TTL,
        prefix="stats",
        vary_on_user=False
    )

def skip_cache_for_mutations(func_name: str = None):
    """Skip caching for POST, PUT, DELETE operations"""
    def skip_condition(*args, **kwargs):
        # Look for HTTP method indicators
        request = kwargs.get('request')
        if request and hasattr(request, 'method'):
            return request.method in ['POST', 'PUT', 'DELETE', 'PATCH']
        
        # Fallback: check function name
        if func_name:
            mutation_indicators = ['create', 'update', 'delete', 'post', 'put']
            return any(indicator in func_name.lower() for indicator in mutation_indicators)
        
        return False
    
    return skip_condition

# Cache warming utilities
def warm_cache():
    """Pre-populate cache with frequently accessed data"""
    logger.info("Starting cache warming...")
    
    # TODO: Add cache warming logic for your application
    # Examples:
    # - Pre-load application statistics
    # - Cache commonly accessed user data
    # - Pre-compute expensive queries
    
    logger.info("Cache warming completed")

def cache_health_check() -> dict:
    """Check cache system health"""
    try:
        # Test basic operations
        test_key = "health_check_test"
        test_value = {"timestamp": "test"}
        
        # Test set
        set_success = cache_service.set(test_key, test_value, 60)
        
        # Test get
        retrieved_value = cache_service.get(test_key)
        get_success = retrieved_value == test_value
        
        # Test delete
        delete_success = cache_service.delete(test_key)
        
        return {
            "status": "healthy" if all([set_success, get_success, delete_success]) else "degraded",
            "operations": {
                "set": set_success,
                "get": get_success,
                "delete": delete_success
            },
            "redis_info": {
                "connected": cache_service.redis.ping(),
                "memory_usage": cache_service.redis.info().get("used_memory_human", "unknown")
            }
        }
        
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }