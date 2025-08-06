"""
Rate limiting utilities for the arXiv scraper project.
"""

import asyncio
import time
from typing import Optional


class RateLimiter:
    """
    Simple rate limiter for API calls and web requests.
    """
    
    def __init__(self, delay: float = 1.0, burst_size: Optional[int] = None):
        """
        Initialize rate limiter.
        
        Args:
            delay: Minimum delay between calls in seconds
            burst_size: Optional burst allowance (not implemented yet)
        """
        self.delay = delay
        self.burst_size = burst_size
        self.last_call_time = 0.0
        
    async def wait(self) -> None:
        """
        Wait if necessary to maintain rate limit.
        """
        current_time = time.time()
        time_since_last_call = current_time - self.last_call_time
        
        if time_since_last_call < self.delay:
            wait_time = self.delay - time_since_last_call
            await asyncio.sleep(wait_time)
        
        self.last_call_time = time.time()
    
    def can_proceed(self) -> bool:
        """
        Check if we can proceed without waiting.
        
        Returns:
            True if we can proceed immediately
        """
        current_time = time.time()
        time_since_last_call = current_time - self.last_call_time
        return time_since_last_call >= self.delay
    
    def time_until_next_call(self) -> float:
        """
        Get time remaining until next call is allowed.
        
        Returns:
            Seconds until next call is allowed (0 if can proceed now)
        """
        current_time = time.time()
        time_since_last_call = current_time - self.last_call_time
        
        if time_since_last_call >= self.delay:
            return 0.0
        else:
            return self.delay - time_since_last_call