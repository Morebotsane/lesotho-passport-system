# app/security/rate_limiting.py
"""
Rate Limiting System for Lesotho Passport Processing API
Prevents API abuse with role-based and endpoint-specific limits
"""
import time
import redis
import json
from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import hashlib

from app.core.config import settings
from app.models.user import UserRole

class RateLimitConfig:
    """Rate limiting configuration for different user roles and endpoints"""
    
    # Rate limits per minute by user role
    ROLE_LIMITS = {
        UserRole.APPLICANT: 60,     # Citizens: 60 requests per minute
        UserRole.OFFICER: 300,      # Officers: 300 requests per minute  
        UserRole.ADMIN: 1000,       # Admins: 1000 requests per minute
        "anonymous": 20,            # Unauthenticated: 20 requests per minute
    }
    
    # Endpoint-specific limits (requests per minute)
    ENDPOINT_LIMITS = {
        # Authentication endpoints (stricter limits)
        "/api/v1/auth/login": {"limit": 5, "window": 60},              # 5 attempts per minute
        "/api/v1/auth/register": {"limit": 3, "window": 300},          # 3 registrations per 5 minutes
        "/api/v1/auth/change-password": {"limit": 2, "window": 300},   # 2 password changes per 5 minutes
        
        # Application endpoints
        "/api/v1/passport-applications/": {"limit": 10, "window": 60}, # 10 applications per minute
        
        # Notification endpoints
        "/api/v1/notifications/send": {"limit": 5, "window": 60},      # 5 SMS per minute
        "/api/v1/notifications/bulk": {"limit": 1, "window": 300},     # 1 bulk SMS per 5 minutes
        
        # Dashboard/reporting (less restrictive)
        "/api/v1/passport-applications/statistics": {"limit": 30, "window": 60},
        "/api/v1/officer-dashboard": {"limit": 60, "window": 60},
    }
    
    # IP-based burst protection (requests per second)
    IP_BURST_LIMIT = 10
    IP_BURST_WINDOW = 1

class RateLimiter:
    """Core rate limiting logic using Redis"""
    
    def __init__(self, redis_url: str = None):
        self.redis_client = redis.Redis.from_url(
            redis_url or settings.REDIS_URL,
            decode_responses=True
        )
        self.config = RateLimitConfig()
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request headers"""
        # Check for forwarded headers (reverse proxy setup)
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            return real_ip.strip()
        
        # Fall back to direct connection IP
        return request.client.host if request.client else 'unknown'
    
    def _get_user_role_from_request(self, request: Request) -> Optional[str]:
        """Extract user role from JWT token in request"""
        try:
            # Get Authorization header
            auth_header = request.headers.get('authorization', '')
            if not auth_header.startswith('Bearer '):
                return None
            
            # Extract token
            token = auth_header[7:]  # Remove 'Bearer ' prefix
            
            # Here you would decode the JWT token to get user role
            # For now, we'll use a placeholder - integrate with your JWT system
            # from app.core.security import decode_access_token
            # payload = decode_access_token(token)
            # return payload.get('role')
            
            return None  # Return actual role when JWT decoding is implemented
            
        except Exception:
            return None
    
    def _generate_cache_key(self, key_type: str, identifier: str, endpoint: str = None) -> str:
        """Generate Redis cache key for rate limiting"""
        if endpoint:
            # Create hash of endpoint to handle long URLs
            endpoint_hash = hashlib.md5(endpoint.encode()).hexdigest()[:8]
            return f"rate_limit:{key_type}:{identifier}:{endpoint_hash}"
        return f"rate_limit:{key_type}:{identifier}"
    
    def check_rate_limit(self, request: Request) -> Tuple[bool, Dict[str, any]]:
        """
        Check if request should be rate limited
        
        Returns:
            Tuple[bool, dict]: (is_allowed, rate_limit_info)
        """
        client_ip = self._get_client_ip(request)
        user_role = self._get_user_role_from_request(request)
        endpoint = request.url.path
        method = request.method.upper()
        
        # Skip rate limiting for certain paths
        if self._should_skip_rate_limiting(endpoint):
            return True, {}
        
        current_time = int(time.time())
        
        # Check IP-based burst protection first
        burst_allowed, burst_info = self._check_ip_burst_limit(client_ip, current_time)
        if not burst_allowed:
            return False, burst_info
        
        # Check endpoint-specific limits
        endpoint_allowed, endpoint_info = self._check_endpoint_limit(
            client_ip, endpoint, method, current_time
        )
        if not endpoint_allowed:
            return False, endpoint_info
        
        # Check role-based limits
        role_allowed, role_info = self._check_role_based_limit(
            client_ip, user_role, current_time
        )
        if not role_allowed:
            return False, role_info
        
        # All checks passed
        return True, {
            "limit_type": "success",
            "remaining_requests": role_info.get("remaining", 0),
            "reset_time": current_time + 60
        }
    
    def _should_skip_rate_limiting(self, endpoint: str) -> bool:
        """Check if endpoint should skip rate limiting"""
        skip_paths = [
            "/health",
            "/docs", 
            "/redoc",
            "/openapi.json",
            "/favicon.ico"
        ]
        return any(endpoint.startswith(path) for path in skip_paths)
    
    def _check_ip_burst_limit(self, client_ip: str, current_time: int) -> Tuple[bool, Dict]:
        """Check IP-based burst protection (requests per second)"""
        key = self._generate_cache_key("ip_burst", client_ip)
        
        # Use sliding window for burst detection
        window_start = current_time - self.config.IP_BURST_WINDOW
        
        # Remove old entries
        self.redis_client.zremrangebyscore(key, 0, window_start)
        
        # Count current requests in window
        current_count = self.redis_client.zcard(key)
        
        if current_count >= self.config.IP_BURST_LIMIT:
            return False, {
                "limit_type": "ip_burst",
                "message": f"Too many requests from IP: {self.config.IP_BURST_LIMIT} per {self.config.IP_BURST_WINDOW} second(s)",
                "retry_after": self.config.IP_BURST_WINDOW
            }
        
        # Add current request to window
        self.redis_client.zadd(key, {str(current_time): current_time})
        self.redis_client.expire(key, self.config.IP_BURST_WINDOW * 2)
        
        return True, {"remaining_burst": self.config.IP_BURST_LIMIT - current_count - 1}
    
    def _check_endpoint_limit(self, client_ip: str, endpoint: str, method: str, current_time: int) -> Tuple[bool, Dict]:
        """Check endpoint-specific rate limits"""
        # Check if this endpoint has specific limits
        full_endpoint = f"{endpoint}"  # Could include method if needed
        
        endpoint_config = None
        for pattern, config in self.config.ENDPOINT_LIMITS.items():
            if endpoint.startswith(pattern):
                endpoint_config = config
                break
        
        if not endpoint_config:
            return True, {}  # No specific limit for this endpoint
        
        limit = endpoint_config["limit"]
        window = endpoint_config["window"]
        
        key = self._generate_cache_key("endpoint", client_ip, endpoint)
        
        # Use sliding window counter
        window_start = current_time - window
        self.redis_client.zremrangebyscore(key, 0, window_start)
        
        current_count = self.redis_client.zcard(key)
        
        if current_count >= limit:
            return False, {
                "limit_type": "endpoint",
                "message": f"Rate limit exceeded for endpoint: {limit} requests per {window} seconds",
                "retry_after": window
            }
        
        # Add current request
        self.redis_client.zadd(key, {str(current_time): current_time})
        self.redis_client.expire(key, window * 2)
        
        return True, {"remaining_endpoint": limit - current_count - 1}
    
    def _check_role_based_limit(self, client_ip: str, user_role: Optional[str], current_time: int) -> Tuple[bool, Dict]:
        """Check role-based rate limits"""
        # Determine rate limit based on user role
        if user_role and hasattr(UserRole, user_role.upper()):
            role_enum = getattr(UserRole, user_role.upper())
            limit = self.config.ROLE_LIMITS.get(role_enum, self.config.ROLE_LIMITS["anonymous"])
            identifier = f"user_role_{user_role}"
        else:
            limit = self.config.ROLE_LIMITS["anonymous"]
            identifier = f"ip_{client_ip}"
        
        window = 60  # 1 minute window
        key = self._generate_cache_key("role", identifier)
        
        # Use sliding window counter
        window_start = current_time - window
        self.redis_client.zremrangebyscore(key, 0, window_start)
        
        current_count = self.redis_client.zcard(key)
        
        if current_count >= limit:
            role_name = user_role or "anonymous"
            return False, {
                "limit_type": "role",
                "message": f"Rate limit exceeded for {role_name}: {limit} requests per minute",
                "retry_after": window
            }
        
        # Add current request
        self.redis_client.zadd(key, {str(current_time): current_time})
        self.redis_client.expire(key, window * 2)
        
        return True, {"remaining": limit - current_count - 1}
    
    def get_rate_limit_status(self, request: Request) -> Dict[str, any]:
        """Get current rate limit status for request"""
        client_ip = self._get_client_ip(request)
        user_role = self._get_user_role_from_request(request)
        
        # Get role-based limit info
        if user_role and hasattr(UserRole, user_role.upper()):
            role_enum = getattr(UserRole, user_role.upper())
            limit = self.config.ROLE_LIMITS.get(role_enum, self.config.ROLE_LIMITS["anonymous"])
            identifier = f"user_role_{user_role}"
        else:
            limit = self.config.ROLE_LIMITS["anonymous"]
            identifier = f"ip_{client_ip}"
            user_role = "anonymous"
        
        # Check current usage
        key = self._generate_cache_key("role", identifier)
        current_time = int(time.time())
        window_start = current_time - 60
        
        self.redis_client.zremrangebyscore(key, 0, window_start)
        current_count = self.redis_client.zcard(key)
        
        return {
            "user_role": user_role,
            "limit": limit,
            "used": current_count,
            "remaining": max(0, limit - current_count),
            "reset_time": current_time + 60,
            "window_seconds": 60
        }

class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting"""
    
    def __init__(self, app, redis_url: str = None):
        super().__init__(app)
        self.rate_limiter = RateLimiter(redis_url)
    
    async def dispatch(self, request: Request, call_next):
        """Process request through rate limiter"""
        
        # Check rate limits
        is_allowed, limit_info = self.rate_limiter.check_rate_limit(request)
        
        if not is_allowed:
            # Return rate limit error
            return self._create_rate_limit_response(limit_info)
        
        # Process request normally
        response = await call_next(request)
        
        # Add rate limit headers to response
        self._add_rate_limit_headers(response, request)
        
        return response
    
    def _create_rate_limit_response(self, limit_info: Dict) -> Response:
        """Create rate limit exceeded response"""
        error_response = {
            "error": "Rate limit exceeded",
            "message": limit_info.get("message", "Too many requests"),
            "type": limit_info.get("limit_type", "unknown"),
            "retry_after": limit_info.get("retry_after", 60)
        }
        
        headers = {
            "Retry-After": str(limit_info.get("retry_after", 60)),
            "X-RateLimit-Type": limit_info.get("limit_type", "unknown")
        }
        
        return Response(
            content=json.dumps(error_response),
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            headers=headers,
            media_type="application/json"
        )
    
    def _add_rate_limit_headers(self, response: Response, request: Request):
        """Add rate limit information to response headers"""
        try:
            status_info = self.rate_limiter.get_rate_limit_status(request)
            
            response.headers["X-RateLimit-Limit"] = str(status_info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(status_info["remaining"])
            response.headers["X-RateLimit-Reset"] = str(status_info["reset_time"])
            response.headers["X-RateLimit-Window"] = str(status_info["window_seconds"])
            
        except Exception:
            # Don't fail the response if header addition fails
            pass

# Utility functions for manual rate limit checking
def check_rate_limit_for_user(user_role: str, identifier: str) -> Dict[str, any]:
    """Check rate limit status for specific user"""
    limiter = RateLimiter()
    
    # Create mock request for checking
    class MockRequest:
        def __init__(self, role, ip):
            self.headers = {"authorization": f"Bearer mock_token_with_{role}"}
            self.client = type('obj', (object,), {'host': ip})
            self.url = type('obj', (object,), {'path': '/api/test'})
    
    mock_request = MockRequest(user_role, identifier)
    is_allowed, info = limiter.check_rate_limit(mock_request)
    
    return {
        "allowed": is_allowed,
        "info": info
    }

def get_rate_limit_stats() -> Dict[str, any]:
    """Get overall rate limiting statistics"""
    limiter = RateLimiter()
    
    # Get Redis info
    try:
        redis_info = limiter.redis_client.info('memory')
        key_count = limiter.redis_client.dbsize()
        
        # Count rate limit keys
        rate_limit_keys = len(limiter.redis_client.keys("rate_limit:*"))
        
        return {
            "redis_connected": True,
            "total_keys": key_count,
            "rate_limit_keys": rate_limit_keys,
            "redis_memory_used": redis_info.get('used_memory_human', 'N/A'),
            "configuration": {
                "role_limits": limiter.config.ROLE_LIMITS,
                "endpoint_limits": len(limiter.config.ENDPOINT_LIMITS),
                "ip_burst_limit": limiter.config.IP_BURST_LIMIT
            }
        }
    except Exception as e:
        return {
            "redis_connected": False,
            "error": str(e)
        }

# Testing and development utilities
def clear_rate_limits(identifier: str = None):
    """Clear rate limits for testing (development only)"""
    if settings.ENVIRONMENT != "development":
        raise ValueError("Rate limit clearing only allowed in development environment")
    
    limiter = RateLimiter()
    
    if identifier:
        # Clear specific identifier
        keys = limiter.redis_client.keys(f"rate_limit:*{identifier}*")
    else:
        # Clear all rate limit keys
        keys = limiter.redis_client.keys("rate_limit:*")
    
    if keys:
        limiter.redis_client.delete(*keys)
    
    return {"cleared_keys": len(keys)}