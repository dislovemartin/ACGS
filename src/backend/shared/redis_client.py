"""
Redis client configuration and utilities for ACGS-PGP microservices.
Provides centralized Redis connection management and caching utilities.
"""

import os
import json
import asyncio
import logging
from typing import Optional, Any, Dict, List, Union
from datetime import datetime, timedelta
import redis.asyncio as redis
from redis.asyncio import Redis
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

# Redis configuration from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_MAX_CONNECTIONS = int(os.getenv("REDIS_MAX_CONNECTIONS", "20"))
REDIS_SOCKET_TIMEOUT = int(os.getenv("REDIS_SOCKET_TIMEOUT", "5"))
REDIS_SOCKET_CONNECT_TIMEOUT = int(os.getenv("REDIS_SOCKET_CONNECT_TIMEOUT", "5"))

class ACGSRedisClient:
    """Centralized Redis client for ACGS-PGP microservices."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.redis_client: Optional[Redis] = None
        self.connection_pool = None
        
    async def initialize(self):
        """Initialize Redis connection pool."""
        try:
            self.connection_pool = redis.ConnectionPool.from_url(
                REDIS_URL,
                password=REDIS_PASSWORD,
                max_connections=REDIS_MAX_CONNECTIONS,
                socket_timeout=REDIS_SOCKET_TIMEOUT,
                socket_connect_timeout=REDIS_SOCKET_CONNECT_TIMEOUT,
                decode_responses=True
            )
            
            self.redis_client = Redis(connection_pool=self.connection_pool)
            
            # Test connection
            await self.redis_client.ping()
            logger.info(f"Redis client initialized for service: {self.service_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis client for {self.service_name}: {e}")
            raise
    
    async def close(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info(f"Redis client closed for service: {self.service_name}")
    
    @asynccontextmanager
    async def get_client(self):
        """Context manager for Redis client."""
        if not self.redis_client:
            await self.initialize()
        try:
            yield self.redis_client
        except Exception as e:
            logger.error(f"Redis operation failed: {e}")
            raise
    
    async def set_json(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set JSON value in Redis with optional TTL."""
        try:
            async with self.get_client() as client:
                json_value = json.dumps(value, default=str)
                if ttl:
                    return await client.setex(key, ttl, json_value)
                else:
                    return await client.set(key, json_value)
        except Exception as e:
            logger.error(f"Failed to set JSON key {key}: {e}")
            return False
    
    async def get_json(self, key: str) -> Optional[Any]:
        """Get JSON value from Redis."""
        try:
            async with self.get_client() as client:
                value = await client.get(key)
                if value:
                    return json.loads(value)
                return None
        except Exception as e:
            logger.error(f"Failed to get JSON key {key}: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        try:
            async with self.get_client() as client:
                return bool(await client.delete(key))
        except Exception as e:
            logger.error(f"Failed to delete key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        try:
            async with self.get_client() as client:
                return bool(await client.exists(key))
        except Exception as e:
            logger.error(f"Failed to check existence of key {key}: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter in Redis."""
        try:
            async with self.get_client() as client:
                return await client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Failed to increment key {key}: {e}")
            return None
    
    async def set_hash(self, key: str, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set hash in Redis with optional TTL."""
        try:
            async with self.get_client() as client:
                # Convert values to strings for Redis
                str_mapping = {k: json.dumps(v, default=str) for k, v in mapping.items()}
                result = await client.hset(key, mapping=str_mapping)
                if ttl:
                    await client.expire(key, ttl)
                return bool(result)
        except Exception as e:
            logger.error(f"Failed to set hash {key}: {e}")
            return False
    
    async def get_hash(self, key: str) -> Optional[Dict[str, Any]]:
        """Get hash from Redis."""
        try:
            async with self.get_client() as client:
                hash_data = await client.hgetall(key)
                if hash_data:
                    return {k: json.loads(v) for k, v in hash_data.items()}
                return None
        except Exception as e:
            logger.error(f"Failed to get hash {key}: {e}")
            return None
    
    async def add_to_list(self, key: str, value: Any, max_length: Optional[int] = None) -> bool:
        """Add value to Redis list with optional max length."""
        try:
            async with self.get_client() as client:
                json_value = json.dumps(value, default=str)
                await client.lpush(key, json_value)
                
                if max_length:
                    await client.ltrim(key, 0, max_length - 1)
                
                return True
        except Exception as e:
            logger.error(f"Failed to add to list {key}: {e}")
            return False
    
    async def get_list(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
        """Get list from Redis."""
        try:
            async with self.get_client() as client:
                list_data = await client.lrange(key, start, end)
                return [json.loads(item) for item in list_data]
        except Exception as e:
            logger.error(f"Failed to get list {key}: {e}")
            return []

    async def get_ttl(self, key: str) -> int:
        """Get TTL (time to live) for a key in seconds.

        Returns:
            - Positive integer: TTL in seconds
            - -1: Key exists but has no expiration
            - -2: Key does not exist
        """
        try:
            async with self.get_client() as client:
                ttl = await client.ttl(key)
                return ttl
        except Exception as e:
            logger.error(f"Failed to get TTL for key {key}: {e}")
            return -2  # Return -2 to indicate error (same as non-existent key)

    def generate_key(self, *parts: str) -> str:
        """Generate Redis key with service prefix."""
        return f"acgs:{self.service_name}:{':'.join(parts)}"


# Global Redis clients for each service
_redis_clients: Dict[str, ACGSRedisClient] = {}

async def get_redis_client(service_name: str) -> ACGSRedisClient:
    """Get or create Redis client for service."""
    if service_name not in _redis_clients:
        client = ACGSRedisClient(service_name)
        await client.initialize()
        _redis_clients[service_name] = client
    
    return _redis_clients[service_name]

async def close_all_redis_clients():
    """Close all Redis clients."""
    for client in _redis_clients.values():
        await client.close()
    _redis_clients.clear()
