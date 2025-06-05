
import threading
import time
from typing import Any, Optional, Dict

class FallbackCache:
    """In-memory cache fallback when Redis is unavailable."""
    
    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.lock = threading.RLock()
    
    def set(self, key: str, value: Any, ttl: int = 600) -> bool:
        """Set a value with TTL."""
        with self.lock:
            if len(self.cache) >= self.max_size:
                # Remove oldest entries
                oldest_keys = sorted(self.cache.keys(), 
                                   key=lambda k: self.cache[k]['timestamp'])[:10]
                for old_key in oldest_keys:
                    del self.cache[old_key]
            
            self.cache[key] = {
                'value': value,
                'timestamp': time.time(),
                'ttl': ttl
            }
            return True
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value if not expired."""
        with self.lock:
            if key not in self.cache:
                return None
            
            entry = self.cache[key]
            if time.time() - entry['timestamp'] > entry['ttl']:
                del self.cache[key]
                return None
            
            return entry['value']
    
    def delete(self, key: str) -> bool:
        """Delete a key."""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    def clear(self) -> bool:
        """Clear all cache."""
        with self.lock:
            self.cache.clear()
            return True

# Global fallback cache instance
_fallback_cache = FallbackCache()

def get_fallback_cache():
    return _fallback_cache
