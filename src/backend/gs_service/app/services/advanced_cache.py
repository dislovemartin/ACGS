"""
Advanced Multi-Tier Caching Service for ACGS Governance Synthesis

This service implements a sophisticated caching strategy with in-memory LRU cache,
Redis distributed caching, and intelligent cache invalidation for optimal performance.

Phase 3: Performance Optimization and Security Compliance
"""

import asyncio
import time
import logging
import hashlib
import json
import pickle
from typing import Dict, Any, Optional, Union, List, Callable, TypeVar, Generic
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from functools import wraps
from collections import OrderedDict
import threading

import redis.asyncio as redis
from redis.exceptions import RedisError
import structlog

logger = structlog.get_logger(__name__)

T = TypeVar('T')


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime]
    access_count: int
    last_accessed: datetime
    size_bytes: int
    tags: List[str]


@dataclass
class CacheStats:
    """Cache statistics."""
    total_requests: int
    cache_hits: int
    cache_misses: int
    hit_rate: float
    memory_usage_bytes: int
    entry_count: int
    evictions: int
    errors: int


class LRUCache(Generic[T]):
    """Thread-safe LRU cache with TTL support."""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stats = CacheStats(0, 0, 0, 0.0, 0, 0, 0, 0)
        self._lock = threading.RLock()
    
    def _generate_key(self, key: Union[str, Dict[str, Any]]) -> str:
        """Generate cache key from input."""
        if isinstance(key, str):
            return key
        key_str = json.dumps(key, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if cache entry is expired."""
        if entry.expires_at is None:
            return False
        return datetime.now() > entry.expires_at
    
    def _evict_expired(self):
        """Remove expired entries."""
        now = datetime.now()
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry.expires_at and now > entry.expires_at
        ]
        for key in expired_keys:
            del self.cache[key]
            self.stats.evictions += 1
    
    def _evict_lru(self):
        """Evict least recently used entries."""
        while len(self.cache) >= self.max_size:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            self.stats.evictions += 1
    
    def get(self, key: Union[str, Dict[str, Any]]) -> Optional[T]:
        """Get value from cache."""
        cache_key = self._generate_key(key)
        
        with self._lock:
            self.stats.total_requests += 1
            
            if cache_key not in self.cache:
                self.stats.cache_misses += 1
                self._update_hit_rate()
                return None
            
            entry = self.cache[cache_key]
            
            # Check expiration
            if self._is_expired(entry):
                del self.cache[cache_key]
                self.stats.cache_misses += 1
                self.stats.evictions += 1
                self._update_hit_rate()
                return None
            
            # Update access info and move to end (most recent)
            entry.access_count += 1
            entry.last_accessed = datetime.now()
            self.cache.move_to_end(cache_key)
            
            self.stats.cache_hits += 1
            self._update_hit_rate()
            
            logger.debug("Cache hit", key=cache_key, access_count=entry.access_count)
            return entry.value
    
    def put(self, key: Union[str, Dict[str, Any]], value: T, ttl: Optional[int] = None, tags: Optional[List[str]] = None) -> bool:
        """Put value in cache."""
        cache_key = self._generate_key(key)
        ttl = ttl or self.default_ttl
        tags = tags or []
        
        with self._lock:
            # Clean up expired entries
            self._evict_expired()
            
            # Evict LRU if necessary
            if cache_key not in self.cache:
                self._evict_lru()
            
            # Calculate size (rough estimate)
            try:
                size_bytes = len(pickle.dumps(value))
            except Exception:
                size_bytes = len(str(value).encode('utf-8'))
            
            # Create cache entry
            entry = CacheEntry(
                key=cache_key,
                value=value,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(seconds=ttl) if ttl > 0 else None,
                access_count=0,
                last_accessed=datetime.now(),
                size_bytes=size_bytes,
                tags=tags
            )
            
            self.cache[cache_key] = entry
            self.cache.move_to_end(cache_key)
            
            # Update stats
            self.stats.entry_count = len(self.cache)
            self.stats.memory_usage_bytes = sum(entry.size_bytes for entry in self.cache.values())
            
            logger.debug("Cache put", key=cache_key, ttl=ttl, size_bytes=size_bytes)
            return True
    
    def delete(self, key: Union[str, Dict[str, Any]]) -> bool:
        """Delete value from cache."""
        cache_key = self._generate_key(key)
        
        with self._lock:
            if cache_key in self.cache:
                del self.cache[cache_key]
                self.stats.entry_count = len(self.cache)
                self.stats.memory_usage_bytes = sum(entry.size_bytes for entry in self.cache.values())
                logger.debug("Cache delete", key=cache_key)
                return True
            return False
    
    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            self.cache.clear()
            self.stats.entry_count = 0
            self.stats.memory_usage_bytes = 0
            logger.info("Cache cleared")
    
    def invalidate_by_tags(self, tags: List[str]):
        """Invalidate cache entries by tags."""
        with self._lock:
            keys_to_delete = [
                key for key, entry in self.cache.items()
                if any(tag in entry.tags for tag in tags)
            ]
            for key in keys_to_delete:
                del self.cache[key]
            
            self.stats.entry_count = len(self.cache)
            self.stats.memory_usage_bytes = sum(entry.size_bytes for entry in self.cache.values())
            logger.info("Cache invalidated by tags", tags=tags, deleted_count=len(keys_to_delete))
    
    def _update_hit_rate(self):
        """Update cache hit rate."""
        if self.stats.total_requests > 0:
            self.stats.hit_rate = self.stats.cache_hits / self.stats.total_requests
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        with self._lock:
            return CacheStats(
                total_requests=self.stats.total_requests,
                cache_hits=self.stats.cache_hits,
                cache_misses=self.stats.cache_misses,
                hit_rate=self.stats.hit_rate,
                memory_usage_bytes=self.stats.memory_usage_bytes,
                entry_count=len(self.cache),
                evictions=self.stats.evictions,
                errors=self.stats.errors
            )


class RedisCache:
    """Redis-based distributed cache."""
    
    def __init__(self, redis_client: redis.Redis, key_prefix: str = "acgs:cache:"):
        self.redis_client = redis_client
        self.key_prefix = key_prefix
        self.stats = CacheStats(0, 0, 0, 0.0, 0, 0, 0, 0)
    
    def _generate_key(self, key: Union[str, Dict[str, Any]]) -> str:
        """Generate Redis key."""
        if isinstance(key, str):
            cache_key = key
        else:
            key_str = json.dumps(key, sort_keys=True)
            cache_key = hashlib.md5(key_str.encode()).hexdigest()
        return f"{self.key_prefix}{cache_key}"
    
    async def get(self, key: Union[str, Dict[str, Any]]) -> Optional[Any]:
        """Get value from Redis cache."""
        redis_key = self._generate_key(key)
        
        try:
            self.stats.total_requests += 1
            
            data = await self.redis_client.get(redis_key)
            if data is None:
                self.stats.cache_misses += 1
                self._update_hit_rate()
                return None
            
            # Deserialize data
            try:
                value = pickle.loads(data)
            except Exception:
                value = json.loads(data.decode('utf-8'))
            
            self.stats.cache_hits += 1
            self._update_hit_rate()
            
            logger.debug("Redis cache hit", key=redis_key)
            return value
            
        except RedisError as e:
            self.stats.errors += 1
            logger.error("Redis cache get error", key=redis_key, error=str(e))
            return None
    
    async def put(self, key: Union[str, Dict[str, Any]], value: Any, ttl: Optional[int] = None) -> bool:
        """Put value in Redis cache."""
        redis_key = self._generate_key(key)
        
        try:
            # Serialize data
            try:
                data = pickle.dumps(value)
            except Exception:
                data = json.dumps(value).encode('utf-8')
            
            if ttl:
                await self.redis_client.setex(redis_key, ttl, data)
            else:
                await self.redis_client.set(redis_key, data)
            
            logger.debug("Redis cache put", key=redis_key, ttl=ttl)
            return True
            
        except RedisError as e:
            self.stats.errors += 1
            logger.error("Redis cache put error", key=redis_key, error=str(e))
            return False
    
    async def delete(self, key: Union[str, Dict[str, Any]]) -> bool:
        """Delete value from Redis cache."""
        redis_key = self._generate_key(key)
        
        try:
            result = await self.redis_client.delete(redis_key)
            logger.debug("Redis cache delete", key=redis_key, deleted=bool(result))
            return bool(result)
            
        except RedisError as e:
            self.stats.errors += 1
            logger.error("Redis cache delete error", key=redis_key, error=str(e))
            return False
    
    async def clear_pattern(self, pattern: str):
        """Clear cache entries matching pattern."""
        try:
            pattern_key = f"{self.key_prefix}{pattern}"
            keys = await self.redis_client.keys(pattern_key)
            if keys:
                await self.redis_client.delete(*keys)
                logger.info("Redis cache pattern cleared", pattern=pattern, deleted_count=len(keys))
        except RedisError as e:
            self.stats.errors += 1
            logger.error("Redis cache clear pattern error", pattern=pattern, error=str(e))
    
    def _update_hit_rate(self):
        """Update cache hit rate."""
        if self.stats.total_requests > 0:
            self.stats.hit_rate = self.stats.cache_hits / self.stats.total_requests
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        return CacheStats(
            total_requests=self.stats.total_requests,
            cache_hits=self.stats.cache_hits,
            cache_misses=self.stats.cache_misses,
            hit_rate=self.stats.hit_rate,
            memory_usage_bytes=0,  # Not tracked for Redis
            entry_count=0,  # Not tracked for Redis
            evictions=0,  # Not tracked for Redis
            errors=self.stats.errors
        )


class MultiTierCache:
    """Multi-tier cache with L1 (memory) and L2 (Redis) layers."""
    
    def __init__(self, l1_cache: LRUCache, l2_cache: RedisCache):
        self.l1_cache = l1_cache
        self.l2_cache = l2_cache
        self.stats = CacheStats(0, 0, 0, 0.0, 0, 0, 0, 0)
    
    async def get(self, key: Union[str, Dict[str, Any]]) -> Optional[Any]:
        """Get value from multi-tier cache."""
        self.stats.total_requests += 1
        
        # Try L1 cache first
        value = self.l1_cache.get(key)
        if value is not None:
            self.stats.cache_hits += 1
            self._update_hit_rate()
            logger.debug("L1 cache hit", key=str(key))
            return value
        
        # Try L2 cache
        value = await self.l2_cache.get(key)
        if value is not None:
            # Promote to L1 cache
            self.l1_cache.put(key, value)
            self.stats.cache_hits += 1
            self._update_hit_rate()
            logger.debug("L2 cache hit, promoted to L1", key=str(key))
            return value
        
        self.stats.cache_misses += 1
        self._update_hit_rate()
        return None
    
    async def put(self, key: Union[str, Dict[str, Any]], value: Any, ttl: Optional[int] = None, tags: Optional[List[str]] = None) -> bool:
        """Put value in multi-tier cache."""
        # Store in both L1 and L2
        l1_success = self.l1_cache.put(key, value, ttl, tags)
        l2_success = await self.l2_cache.put(key, value, ttl)
        
        logger.debug("Multi-tier cache put", key=str(key), l1_success=l1_success, l2_success=l2_success)
        return l1_success or l2_success
    
    async def delete(self, key: Union[str, Dict[str, Any]]) -> bool:
        """Delete value from multi-tier cache."""
        l1_deleted = self.l1_cache.delete(key)
        l2_deleted = await self.l2_cache.delete(key)
        
        logger.debug("Multi-tier cache delete", key=str(key), l1_deleted=l1_deleted, l2_deleted=l2_deleted)
        return l1_deleted or l2_deleted
    
    def invalidate_by_tags(self, tags: List[str]):
        """Invalidate cache entries by tags (L1 only)."""
        self.l1_cache.invalidate_by_tags(tags)
    
    async def clear(self):
        """Clear all cache entries."""
        self.l1_cache.clear()
        await self.l2_cache.clear_pattern("*")
        logger.info("Multi-tier cache cleared")
    
    def _update_hit_rate(self):
        """Update cache hit rate."""
        if self.stats.total_requests > 0:
            self.stats.hit_rate = self.stats.cache_hits / self.stats.total_requests
    
    def get_stats(self) -> Dict[str, CacheStats]:
        """Get comprehensive cache statistics."""
        return {
            'multi_tier': CacheStats(
                total_requests=self.stats.total_requests,
                cache_hits=self.stats.cache_hits,
                cache_misses=self.stats.cache_misses,
                hit_rate=self.stats.hit_rate,
                memory_usage_bytes=0,
                entry_count=0,
                evictions=0,
                errors=0
            ),
            'l1_cache': self.l1_cache.get_stats(),
            'l2_cache': self.l2_cache.get_stats()
        }


def cache_decorator(cache: MultiTierCache, ttl: int = 300, tags: Optional[List[str]] = None):
    """Decorator for caching function results."""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = {
                'function': func.__name__,
                'args': args,
                'kwargs': kwargs
            }
            
            # Try to get from cache
            result = await cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.put(cache_key, result, ttl, tags)
            return result
        
        return async_wrapper
    return decorator
