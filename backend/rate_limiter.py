"""
CHIXUS Edge Rate Limiting & Anti-Abuse Protection System
In-memory sliding window rate limiter with per-IP and per-token tracking
Environment: Termux on ARM64 Android
Master Passkey: CHIXUS-ADMIN-@)@^
"""

import time
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import threading

from fastapi import Request, HTTPException, status, Depends, Header

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RateLimitTier(str, Enum):
    """Rate limiting tiers"""
    STANDARD = "standard"
    AUTH = "auth"
    ADMIN = "admin"
    ANONYMOUS = "anonymous"


class RateLimitConfig:
    """Configuration for rate limiting"""
    
    # Requests per minute per tier
    LIMITS = {
        RateLimitTier.STANDARD: 60,
        RateLimitTier.AUTH: 10,
        RateLimitTier.ADMIN: 1000,
        RateLimitTier.ANONYMOUS: 20,
    }
    
    # Window size in seconds
    WINDOW_SIZE = 60
    
    # Cleanup interval (seconds)
    CLEANUP_INTERVAL = 300


class RateLimitExceeded(Exception):
    """Custom exception for rate limit exceeded"""
    
    def __init__(self, retry_after_seconds: int):
        self.retry_after_seconds = retry_after_seconds
        super().__init__(f"Rate limit exceeded. Retry after {retry_after_seconds}s")


class SlidingWindowLimiter:
    """
    In-memory sliding window rate limiter
    Tracks request timestamps per identifier (IP + optional token)
    """
    
    def __init__(self, config: RateLimitConfig = None):
        """
        Initialize the rate limiter
        
        Args:
            config: RateLimitConfig instance
        """
        self.config = config or RateLimitConfig()
        
        # Storage: {identifier: [timestamps]}
        self.request_history: Dict[str, List[float]] = defaultdict(list)
        
        # Lock for thread safety
        self.lock = threading.RLock()
        
        # Last cleanup time
        self.last_cleanup = time.time()
        
        logger.info("SlidingWindowLimiter initialized")

    def _get_identifier(self, client_ip: str, token: Optional[str] = None) -> str:
        """
        Generate a unique identifier for rate limiting
        
        Args:
            client_ip: Client IP address
            token: Optional access token
            
        Returns:
            Unique identifier string
        """
        if token:
            return f"token:{token}"
        return f"ip:{client_ip}"

    def _cleanup_old_entries(self) -> None:
        """
        Periodically clean up old request history entries
        Removes entries older than the window size
        """
        now = time.time()
        
        # Only cleanup every CLEANUP_INTERVAL seconds
        if now - self.last_cleanup < self.config.CLEANUP_INTERVAL:
            return
        
        try:
            with self.lock:
                cutoff_time = now - self.config.WINDOW_SIZE
                identifiers_to_remove = []
                
                for identifier, timestamps in self.request_history.items():
                    # Remove old timestamps
                    self.request_history[identifier] = [
                        ts for ts in timestamps if ts > cutoff_time
                    ]
                    
                    # Mark identifier for removal if no recent requests
                    if not self.request_history[identifier]:
                        identifiers_to_remove.append(identifier)
                
                # Remove empty identifiers
                for identifier in identifiers_to_remove:
                    del self.request_history[identifier]
                
                self.last_cleanup = now
                
                if identifiers_to_remove:
                    logger.debug(f"Cleaned up {len(identifiers_to_remove)} rate limit entries")
        
        except Exception as e:
            logger.error(f"Error during rate limiter cleanup: {e}")

    def check_rate_limit(
        self,
        client_ip: str,
        tier: RateLimitTier = RateLimitTier.STANDARD,
        token: Optional[str] = None
    ) -> Tuple[bool, int, int]:
        """
        Check if request is within rate limit
        
        Args:
            client_ip: Client IP address
            tier: Rate limit tier
            token: Optional access token (takes precedence over IP)
            
        Returns:
            Tuple of (is_allowed: bool, requests_made: int, retry_after_seconds: int)
        """
        identifier = self._get_identifier(client_ip, token)
        limit = self.config.LIMITS[tier]
        now = time.time()
        cutoff_time = now - self.config.WINDOW_SIZE
        
        try:
            with self.lock:
                # Clean up old entries periodically
                self._cleanup_old_entries()
                
                # Remove old requests outside the sliding window
                if identifier in self.request_history:
                    self.request_history[identifier] = [
                        ts for ts in self.request_history[identifier] if ts > cutoff_time
                    ]
                else:
                    self.request_history[identifier] = []
                
                current_count = len(self.request_history[identifier])
                
                # Check if limit exceeded
                if current_count >= limit:
                    # Find retry_after: oldest timestamp + window size
                    oldest_timestamp = min(self.request_history[identifier])
                    retry_after = max(1, int(oldest_timestamp + self.config.WINDOW_SIZE - now) + 1)
                    
                    logger.warning(
                        f"Rate limit exceeded for {identifier} "
                        f"({current_count}/{limit} requests in window). "
                        f"Retry after {retry_after}s"
                    )
                    
                    return False, current_count, retry_after
                
                # Add current request timestamp
                self.request_history[identifier].append(now)
                
                logger.debug(
                    f"Rate limit check passed for {identifier} "
                    f"({current_count + 1}/{limit} requests)"
                )
                
                return True, current_count + 1, 0
        
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            # Fail open: allow request on error
            return True, 0, 0

    def get_status(self, client_ip: str, token: Optional[str] = None) -> Dict:
        """
        Get current rate limit status for an identifier
        
        Args:
            client_ip: Client IP address
            token: Optional access token
            
        Returns:
            Dictionary with status information
        """
        identifier = self._get_identifier(client_ip, token)
        now = time.time()
        cutoff_time = now - self.config.WINDOW_SIZE
        
        try:
            with self.lock:
                if identifier not in self.request_history:
                    return {
                        "identifier": identifier,
                        "requests_in_window": 0,
                        "window_size_seconds": self.config.WINDOW_SIZE,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                
                recent_timestamps = [
                    ts for ts in self.request_history[identifier] if ts > cutoff_time
                ]
                
                return {
                    "identifier": identifier,
                    "requests_in_window": len(recent_timestamps),
                    "window_size_seconds": self.config.WINDOW_SIZE,
                    "oldest_request_timestamp": datetime.fromtimestamp(min(recent_timestamps)).isoformat() if recent_timestamps else None,
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        except Exception as e:
            logger.error(f"Error getting rate limit status: {e}")
            return {"error": str(e)}

    def reset_identifier(self, client_ip: str, token: Optional[str] = None) -> bool:
        """
        Reset rate limit for a specific identifier (admin operation)
        
        Args:
            client_ip: Client IP address
            token: Optional access token
            
        Returns:
            True if reset was successful
        """
        identifier = self._get_identifier(client_ip, token)
        
        try:
            with self.lock:
                if identifier in self.request_history:
                    del self.request_history[identifier]
                    logger.info(f"Rate limit reset for {identifier}")
                    return True
                return False
        
        except Exception as e:
            logger.error(f"Error resetting rate limit: {e}")
            return False


# Singleton instance
_rate_limiter_instance: Optional[SlidingWindowLimiter] = None


def get_rate_limiter(config: Optional[RateLimitConfig] = None) -> SlidingWindowLimiter:
    """
    Get or create singleton rate limiter instance
    
    Args:
        config: Optional RateLimitConfig instance
        
    Returns:
        SlidingWindowLimiter instance
    """
    global _rate_limiter_instance
    if _rate_limiter_instance is None:
        _rate_limiter_instance = SlidingWindowLimiter(config)
    return _rate_limiter_instance


# ============================================================================
# FastAPI Dependencies
# ============================================================================

async def rate_limit_standard(
    request: Request,
    rate_limiter: SlidingWindowLimiter = Depends(get_rate_limiter),
    x_access_token: Optional[str] = Header(None)
) -> bool:
    """
    Standard rate limiting dependency (60 requests/minute)
    
    Args:
        request: FastAPI request object
        rate_limiter: Rate limiter instance
        x_access_token: Optional access token from header
        
    Returns:
        True if request is allowed
        
    Raises:
        HTTPException: 429 if rate limit exceeded
    """
    client_ip = request.client.host if request.client else "unknown"
    
    is_allowed, _, retry_after = rate_limiter.check_rate_limit(
        client_ip=client_ip,
        tier=RateLimitTier.STANDARD,
        token=x_access_token
    )
    
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": True,
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Too many requests. Please try again later.",
                "retry_after_seconds": retry_after,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    return True


async def rate_limit_auth(
    request: Request,
    rate_limiter: SlidingWindowLimiter = Depends(get_rate_limiter),
    x_access_token: Optional[str] = Header(None)
) -> bool:
    """
    Strict rate limiting for auth endpoints (10 requests/minute)
    
    Args:
        request: FastAPI request object
        rate_limiter: Rate limiter instance
        x_access_token: Optional access token from header
        
    Returns:
        True if request is allowed
        
    Raises:
        HTTPException: 429 if rate limit exceeded
    """
    client_ip = request.client.host if request.client else "unknown"
    
    is_allowed, _, retry_after = rate_limiter.check_rate_limit(
        client_ip=client_ip,
        tier=RateLimitTier.AUTH,
        token=x_access_token
    )
    
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": True,
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Too many authentication requests. Please try again later.",
                "retry_after_seconds": retry_after,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    return True


async def rate_limit_admin(
    request: Request,
    rate_limiter: SlidingWindowLimiter = Depends(get_rate_limiter),
    x_access_token: Optional[str] = Header(None)
) -> bool:
    """
    Permissive rate limiting for admin endpoints (1000 requests/minute)
    
    Args:
        request: FastAPI request object
        rate_limiter: Rate limiter instance
        x_access_token: Optional access token from header
        
    Returns:
        True if request is allowed
        
    Raises:
        HTTPException: 429 if rate limit exceeded
    """
    client_ip = request.client.host if request.client else "unknown"
    
    is_allowed, _, retry_after = rate_limiter.check_rate_limit(
        client_ip=client_ip,
        tier=RateLimitTier.ADMIN,
        token=x_access_token
    )
    
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": True,
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Admin rate limit exceeded. Please try again later.",
                "retry_after_seconds": retry_after,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    return True


async def rate_limit_anonymous(
    request: Request,
    rate_limiter: SlidingWindowLimiter = Depends(get_rate_limiter)
) -> bool:
    """
    Strict rate limiting for anonymous users (20 requests/minute)
    
    Args:
        request: FastAPI request object
        rate_limiter: Rate limiter instance
        
    Returns:
        True if request is allowed
        
    Raises:
        HTTPException: 429 if rate limit exceeded
    """
    client_ip = request.client.host if request.client else "unknown"
    
    is_allowed, _, retry_after = rate_limiter.check_rate_limit(
        client_ip=client_ip,
        tier=RateLimitTier.ANONYMOUS
    )
    
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": True,
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Too many requests from your IP. Please try again later.",
                "retry_after_seconds": retry_after,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    return True


__all__ = [
    "SlidingWindowLimiter",
    "RateLimitTier",
    "RateLimitConfig",
    "RateLimitExceeded",
    "get_rate_limiter",
    "rate_limit_standard",
    "rate_limit_auth",
    "rate_limit_admin",
    "rate_limit_anonymous",
]
