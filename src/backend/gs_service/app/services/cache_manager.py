"""
Cache Manager Service for ACGS Phase 3 Performance Enhancement

Provides centralized cache management with Redis integration, cache warming,
and intelligent invalidation strategies for optimal performance.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import json

import redis.asyncio as redis
from redis.exceptions import RedisError
import structlog

from .advanced_cache import MultiTierCache, LRUCache, RedisCache, CACHE_TTL_POLICIES
from ..config.opa_config import OPAConfig

logger = structlog.get_logger(__name__)


class CacheManager:
    """Centralized cache management service for ACGS."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.caches: Dict[str, MultiTierCache] = {}
        self.warming_tasks: List[asyncio.Task] = []
        self._initialized = False
    
    async def initialize(self):
        """Initialize cache manager and Redis connection."""
        if self._initialized:
            return
            
        try:
            # Initialize Redis client
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=False,  # Keep binary for pickle support
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Redis connection established", url=self.redis_url)
            
            # Initialize cache instances
            await self._initialize_caches()
            
            # Start cache warming
            await self._start_cache_warming()
            
            self._initialized = True
            logger.info("Cache manager initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize cache manager", error=str(e))
            raise
    
    async def _initialize_caches(self):
        """Initialize different cache instances for different use cases."""
        
        # Policy decision cache - high performance, short TTL
        policy_l1 = LRUCache(max_size=500, default_ttl=CACHE_TTL_POLICIES['policy_decisions'])
        policy_l2 = RedisCache(self.redis_client, key_prefix="acgs:policy:", enable_pubsub=True)
        self.caches['policy_decisions'] = MultiTierCache(policy_l1, policy_l2)
        
        # Governance rules cache - medium performance, longer TTL
        rules_l1 = LRUCache(max_size=1000, default_ttl=CACHE_TTL_POLICIES['governance_rules'])
        rules_l2 = RedisCache(self.redis_client, key_prefix="acgs:rules:", enable_pubsub=True)
        self.caches['governance_rules'] = MultiTierCache(rules_l1, rules_l2)
        
        # Static configuration cache - low frequency, very long TTL
        config_l1 = LRUCache(max_size=200, default_ttl=CACHE_TTL_POLICIES['static_configuration'])
        config_l2 = RedisCache(self.redis_client, key_prefix="acgs:config:", enable_pubsub=True)
        self.caches['static_configuration'] = MultiTierCache(config_l1, config_l2)
        
        # User sessions cache - medium frequency, medium TTL
        session_l1 = LRUCache(max_size=2000, default_ttl=CACHE_TTL_POLICIES['user_sessions'])
        session_l2 = RedisCache(self.redis_client, key_prefix="acgs:sessions:", enable_pubsub=True)
        self.caches['user_sessions'] = MultiTierCache(session_l1, session_l2)
        
        # API responses cache - high frequency, short TTL
        api_l1 = LRUCache(max_size=1500, default_ttl=CACHE_TTL_POLICIES['api_responses'])
        api_l2 = RedisCache(self.redis_client, key_prefix="acgs:api:", enable_pubsub=True)
        self.caches['api_responses'] = MultiTierCache(api_l1, api_l2)
        
        logger.info("Cache instances initialized", cache_types=list(self.caches.keys()))
    
    async def _start_cache_warming(self):
        """Start cache warming tasks for critical data."""
        
        # Warm governance rules cache
        warming_task = asyncio.create_task(self._warm_governance_rules())
        self.warming_tasks.append(warming_task)
        
        # Warm static configuration cache
        warming_task = asyncio.create_task(self._warm_static_configuration())
        self.warming_tasks.append(warming_task)
        
        logger.info("Cache warming tasks started", tasks=len(self.warming_tasks))
    
    async def _warm_governance_rules(self):
        """Warm governance rules cache with critical rules."""
        try:
            # Sample governance rules for warming
            critical_rules = [
                {
                    'id': 'constitutional_compliance',
                    'category': 'constitutional',
                    'rule': 'All policies must comply with constitutional principles',
                    'priority': 'high',
                    'active': True
                },
                {
                    'id': 'bias_prevention',
                    'category': 'fairness',
                    'rule': 'Policies must be evaluated for bias and discrimination',
                    'priority': 'high',
                    'active': True
                },
                {
                    'id': 'transparency_requirement',
                    'category': 'transparency',
                    'rule': 'Policy decisions must be explainable and auditable',
                    'priority': 'medium',
                    'active': True
                }
            ]
            
            cache = self.caches.get('governance_rules')
            if cache:
                await cache.warm_governance_rules(critical_rules)
                logger.info("Governance rules cache warmed", rules=len(critical_rules))
                
        except Exception as e:
            logger.error("Failed to warm governance rules cache", error=str(e))
    
    async def _warm_static_configuration(self):
        """Warm static configuration cache."""
        try:
            # Sample static configuration for warming
            config_items = [
                {
                    'key': 'opa_config',
                    'value': {
                        'server_url': 'http://localhost:8181',
                        'timeout': 5000,
                        'max_retries': 3
                    }
                },
                {
                    'key': 'performance_thresholds',
                    'value': {
                        'max_latency_ms': 50,
                        'cache_hit_rate_target': 0.8,
                        'max_concurrent_requests': 100
                    }
                }
            ]
            
            cache = self.caches.get('static_configuration')
            if cache:
                warming_data = []
                for item in config_items:
                    warming_data.append({
                        'key': item['key'],
                        'value': item['value'],
                        'ttl': CACHE_TTL_POLICIES['static_configuration'],
                        'tags': ['configuration']
                    })
                
                await cache.warm_cache(warming_data)
                logger.info("Static configuration cache warmed", items=len(config_items))
                
        except Exception as e:
            logger.error("Failed to warm static configuration cache", error=str(e))
    
    async def get_cache(self, cache_type: str) -> Optional[MultiTierCache]:
        """Get cache instance by type."""
        if not self._initialized:
            await self.initialize()
        
        return self.caches.get(cache_type)
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        if not self._initialized:
            return {}
        
        stats = {}
        for cache_type, cache in self.caches.items():
            stats[cache_type] = cache.get_stats()
        
        return stats
    
    async def invalidate_cache_pattern(self, cache_type: str, pattern: str):
        """Invalidate cache entries matching pattern."""
        cache = await self.get_cache(cache_type)
        if cache:
            await cache.delete_by_pattern(pattern)
            logger.info("Cache pattern invalidated", cache_type=cache_type, pattern=pattern)
    
    async def invalidate_cache_tag(self, cache_type: str, tag: str):
        """Invalidate cache entries with specific tag."""
        cache = await self.get_cache(cache_type)
        if cache:
            await cache.delete_by_tag(tag)
            logger.info("Cache tag invalidated", cache_type=cache_type, tag=tag)
    
    async def clear_all_caches(self):
        """Clear all cache instances."""
        for cache_type, cache in self.caches.items():
            await cache.clear()
            logger.info("Cache cleared", cache_type=cache_type)
    
    async def shutdown(self):
        """Shutdown cache manager and cleanup resources."""
        # Cancel warming tasks
        for task in self.warming_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.warming_tasks:
            await asyncio.gather(*self.warming_tasks, return_exceptions=True)
        
        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("Cache manager shutdown completed")


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


async def get_cache_manager() -> CacheManager:
    """Get global cache manager instance."""
    global _cache_manager
    
    if _cache_manager is None:
        _cache_manager = CacheManager()
        await _cache_manager.initialize()
    
    return _cache_manager


async def shutdown_cache_manager():
    """Shutdown global cache manager."""
    global _cache_manager
    
    if _cache_manager:
        await _cache_manager.shutdown()
        _cache_manager = None
