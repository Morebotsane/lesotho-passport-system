# app/core/redis_config.py
"""
Redis connection and configuration management
Centralized Redis setup for caching, sessions, and task queues
"""
import redis
from redis.connection import ConnectionPool
from typing import Optional
import json
import pickle
from datetime import timedelta
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

class RedisManager:
    """Centralized Redis connection manager with connection pooling"""
    
    def __init__(self):
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[redis.Redis] = None
        self._cache_client: Optional[redis.Redis] = None
        
    def initialize(self):
        """Initialize Redis connections with connection pooling"""
        try:
            # Create connection pool for better performance
            self._pool = ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=False,  # We'll handle encoding ourselves
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            
            # Main Redis client
            self._client = redis.Redis(connection_pool=self._pool)
            
            # Separate client for caching (different DB)
            cache_pool = ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_CACHE_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,  # Cache can use decoded responses
                max_connections=10
            )
            self._cache_client = redis.Redis(connection_pool=cache_pool)
            
            # Test connections
            self._client.ping()
            self._cache_client.ping()
            
            logger.info("Redis connections initialized successfully")
            
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
        except Exception as e:
            logger.error(f"Redis initialization error: {e}")
            raise
    
    @property
    def client(self) -> redis.Redis:
        """Get main Redis client"""
        if not self._client:
            self.initialize()
        return self._client
    
    @property
    def cache(self) -> redis.Redis:
        """Get cache Redis client"""
        if not self._cache_client:
            self.initialize()
        return self._cache_client
    
    def health_check(self) -> bool:
        """Check if Redis is healthy"""
        try:
            return self._client.ping() and self._cache_client.ping()
        except:
            return False

# Global Redis manager instance
redis_manager = RedisManager()

class CacheService:
    """High-level caching service with serialization and TTL management"""
    
    def __init__(self, redis_client: redis.Redis = None):
        self.redis = redis_client or redis_manager.cache
        
    def set(self, key: str, value: any, ttl: int = 3600) -> bool:
        """
        Set a cached value with TTL
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (default 1 hour)
        """
        try:
            # JSON serialize the value
            serialized_value = json.dumps(value, default=str)
            return self.redis.setex(key, ttl, serialized_value)
        except (redis.RedisError, json.JSONDecodeError) as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def get(self, key: str) -> any:
        """
        Get a cached value
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        try:
            value = self.redis.get(key)
            if value is None:
                return None
            return json.loads(value)
        except (redis.RedisError, json.JSONDecodeError) as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete a cached value"""
        try:
            return bool(self.redis.delete(key))
        except redis.RedisError as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern
        
        Args:
            pattern: Redis pattern (e.g., "user:*", "app:stats:*")
            
        Returns:
            Number of keys deleted
        """
        try:
            keys = self.redis.keys(pattern)
            if keys:
                return self.redis.delete(*keys)
            return 0
        except redis.RedisError as e:
            logger.error(f"Cache delete pattern error for {pattern}: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in cache"""
        try:
            return bool(self.redis.exists(key))
        except redis.RedisError:
            return False
    
    def ttl(self, key: str) -> int:
        """Get TTL for a key (-1 if no expiry, -2 if not exists)"""
        try:
            return self.redis.ttl(key)
        except redis.RedisError:
            return -2
    
    def set_if_not_exists(self, key: str, value: any, ttl: int = 3600) -> bool:
        """Set value only if key doesn't exist (atomic operation)"""
        try:
            serialized_value = json.dumps(value, default=str)
            # Using SET with NX (only if not exists) and EX (expiry)
            return self.redis.set(key, serialized_value, nx=True, ex=ttl)
        except (redis.RedisError, json.JSONDecodeError) as e:
            logger.error(f"Cache set_if_not_exists error for key {key}: {e}")
            return False

class SessionStore:
    """Redis-based session storage for user sessions"""
    
    def __init__(self, redis_client: redis.Redis = None):
        self.redis = redis_client or redis_manager.client
        self.prefix = "session:"
        
    def create_session(self, session_id: str, user_data: dict, ttl: int = 86400) -> bool:
        """
        Create a new session
        
        Args:
            session_id: Unique session identifier
            user_data: User data to store in session
            ttl: Session TTL in seconds (default 24 hours)
        """
        try:
            key = f"{self.prefix}{session_id}"
            serialized_data = pickle.dumps(user_data)
            return self.redis.setex(key, ttl, serialized_data)
        except (redis.RedisError, pickle.PickleError) as e:
            logger.error(f"Session create error for {session_id}: {e}")
            return False
    
    def get_session(self, session_id: str) -> Optional[dict]:
        """Get session data"""
        try:
            key = f"{self.prefix}{session_id}"
            data = self.redis.get(key)
            if data is None:
                return None
            return pickle.loads(data)
        except (redis.RedisError, pickle.PickleError) as e:
            logger.error(f"Session get error for {session_id}: {e}")
            return None
    
    def update_session(self, session_id: str, user_data: dict, extend_ttl: bool = True) -> bool:
        """Update session data"""
        try:
            key = f"{self.prefix}{session_id}"
            serialized_data = pickle.dumps(user_data)
            
            if extend_ttl:
                # Reset TTL to 24 hours
                return self.redis.setex(key, 86400, serialized_data)
            else:
                # Keep existing TTL
                ttl = self.redis.ttl(key)
                if ttl > 0:
                    return self.redis.setex(key, ttl, serialized_data)
                else:
                    return self.redis.set(key, serialized_data)
        except (redis.RedisError, pickle.PickleError) as e:
            logger.error(f"Session update error for {session_id}: {e}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        try:
            key = f"{self.prefix}{session_id}"
            return bool(self.redis.delete(key))
        except redis.RedisError as e:
            logger.error(f"Session delete error for {session_id}: {e}")
            return False
    
    def refresh_session_ttl(self, session_id: str, ttl: int = 86400) -> bool:
        """Refresh session TTL without changing data"""
        try:
            key = f"{self.prefix}{session_id}"
            return bool(self.redis.expire(key, ttl))
        except redis.RedisError as e:
            logger.error(f"Session TTL refresh error for {session_id}: {e}")
            return False

# Global cache service instance
cache_service = CacheService()
session_store = SessionStore()

# Utility functions for common caching patterns
def cache_user_data(user_id: str, user_data: dict, ttl: int = 1800):
    """Cache user data for 30 minutes"""
    return cache_service.set(f"user:{user_id}", user_data, ttl)

def get_cached_user_data(user_id: str) -> Optional[dict]:
    """Get cached user data"""
    return cache_service.get(f"user:{user_id}")

def cache_application_stats(stats: dict, ttl: int = 300):
    """Cache application statistics for 5 minutes"""
    return cache_service.set("app:stats", stats, ttl)

def get_cached_application_stats() -> Optional[dict]:
    """Get cached application statistics"""
    return cache_service.get("app:stats")

def invalidate_user_cache(user_id: str):
    """Invalidate all user-related cache"""
    cache_service.delete_pattern(f"user:{user_id}*")

def invalidate_application_cache():
    """Invalidate application-related cache"""
    cache_service.delete_pattern("app:*")