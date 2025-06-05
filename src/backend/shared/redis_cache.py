#!/usr/bin/env python3
"""
Redis Cache Implementation for ACGS Services
Provides distributed caching with TTL policies for improved performance.
"""

import redis
import json
import hashlib
import logging
from typing import Any, Optional, Dict
from datetime import timedelta
import os

logger = logging.getLogger(__name__)

class RedisCache:
    """Redis-based distributed cache with TTL policies."""
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        """Initialize Redis cache connection."""
        try:
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"Redis cache connected successfully to {host}:{port}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    def _generate_key(self, prefix: str, data: Any) -> str:
        """Generate a consistent cache key from data."""
        if isinstance(data, dict):
            # Sort dict keys for consistent hashing
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        
        # Create hash of the data
        hash_obj = hashlib.md5(data_str.encode())
        return f"{prefix}:{hash_obj.hexdigest()}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.redis_client:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> bool:
        """Set value in cache with TTL."""
        if not self.redis_client:
            return False
        
        try:
            json_value = json.dumps(value)
            return self.redis_client.setex(key, ttl_seconds, json_value)
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def get_or_set(self, key: str, value_func, ttl_seconds: int = 300) -> Any:
        """Get value from cache or set it if not exists."""
        # Try to get from cache first
        cached_value = self.get(key)
        if cached_value is not None:
            return cached_value
        
        # Generate value and cache it
        try:
            value = value_func()
            self.set(key, value, ttl_seconds)
            return value
        except Exception as e:
            logger.error(f"Error in get_or_set for key {key}: {e}")
            return None
    
    def cache_policy_decision(self, policy_content: str, input_data: Dict, result: Any) -> str:
        """Cache a policy decision with 5-minute TTL."""
        cache_data = {
            "policy_content": policy_content,
            "input_data": input_data
        }
        key = self._generate_key("policy_decision", cache_data)
        self.set(key, result, ttl_seconds=300)  # 5 minutes
        return key
    
    def get_cached_policy_decision(self, policy_content: str, input_data: Dict) -> Optional[Any]:
        """Get cached policy decision."""
        cache_data = {
            "policy_content": policy_content,
            "input_data": input_data
        }
        key = self._generate_key("policy_decision", cache_data)
        return self.get(key)
    
    def cache_governance_rule(self, rule_id: str, rule_data: Any) -> str:
        """Cache a governance rule with 1-hour TTL."""
        key = self._generate_key("governance_rule", rule_id)
        self.set(key, rule_data, ttl_seconds=3600)  # 1 hour
        return key
    
    def get_cached_governance_rule(self, rule_id: str) -> Optional[Any]:
        """Get cached governance rule."""
        key = self._generate_key("governance_rule", rule_id)
        return self.get(key)
    
    def cache_static_config(self, config_key: str, config_data: Any) -> str:
        """Cache static configuration with 24-hour TTL."""
        key = self._generate_key("static_config", config_key)
        self.set(key, config_data, ttl_seconds=86400)  # 24 hours
        return key
    
    def get_cached_static_config(self, config_key: str) -> Optional[Any]:
        """Get cached static configuration."""
        key = self._generate_key("static_config", config_key)
        return self.get(key)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.redis_client:
            return {"error": "Redis not connected"}
        
        try:
            info = self.redis_client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0)
                )
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"error": str(e)}
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage."""
        total = hits + misses
        if total == 0:
            return 0.0
        return (hits / total) * 100
    
    def flush_all(self) -> bool:
        """Flush all cache data (use with caution)."""
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.flushdb()
            logger.info("Cache flushed successfully")
            return True
        except Exception as e:
            logger.error(f"Error flushing cache: {e}")
            return False

# Global cache instance
_cache_instance = None

def get_cache() -> RedisCache:
    """Get global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_db = int(os.getenv("REDIS_DB", "0"))
        _cache_instance = RedisCache(host=redis_host, port=redis_port, db=redis_db)
    return _cache_instance

def cache_response(cache_key: str, ttl_seconds: int = 300):
    """Decorator for caching function responses."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache = get_cache()
            
            # Generate cache key from function name and arguments
            key_data = {
                "function": func.__name__,
                "args": str(args),
                "kwargs": str(kwargs)
            }
            key = cache._generate_key(cache_key, key_data)
            
            # Try to get from cache
            cached_result = cache.get(key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache.set(key, result, ttl_seconds)
            logger.debug(f"Cache miss for {func.__name__}, result cached")
            return result
        
        return wrapper
    return decorator
