#!/usr/bin/env python3
"""
Setup Redis infrastructure with health checks and fallbacks for ACGS Phase 3 deployment.
This script configures Redis services, implements health checks, and sets up TTL policies.
"""

import asyncio
import logging
import os
import subprocess
import sys
import time
from typing import Dict, List, Optional, Any
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try to import redis with fallback
try:
    import redis
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis Python client not available - will use subprocess calls")

class RedisInfrastructureSetup:
    """Setup and configure Redis infrastructure for ACGS services."""
    
    def __init__(self):
        self.redis_configs = {
            'main_redis': {
                'host': 'localhost',
                'port': 6379,
                'db': 0,
                'description': 'Main Redis for caching and session storage'
            },
            'langgraph_redis': {
                'host': 'localhost', 
                'port': 6381,
                'db': 0,
                'description': 'LangGraph Redis for workflow state management'
            }
        }
        
        self.ttl_policies = {
            'policy_decisions': 300,    # 5 minutes
            'governance_rules': 3600,   # 1 hour
            'static_config': 86400,     # 24 hours
            'user_sessions': 1800,      # 30 minutes
            'cache_default': 600        # 10 minutes
        }
        
        self.health_check_timeout = 30
        self.connection_pool = {}
        
    async def check_redis_availability(self, host: str, port: int) -> bool:
        """Check if Redis is available at the given host:port."""
        try:
            if REDIS_AVAILABLE:
                # Use redis-py client
                client = redis.Redis(host=host, port=port, socket_timeout=5, socket_connect_timeout=5)
                response = client.ping()
                client.close()
                return response
            else:
                # Use redis-cli subprocess
                result = subprocess.run(
                    ['redis-cli', '-h', host, '-p', str(port), 'ping'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                return result.returncode == 0 and 'PONG' in result.stdout
        except Exception as e:
            logger.debug(f"Redis availability check failed for {host}:{port}: {e}")
            return False
    
    async def start_redis_service(self, port: int) -> bool:
        """Start Redis service on the specified port."""
        logger.info(f"🚀 Starting Redis service on port {port}")
        
        try:
            # Check if Redis is already running
            if await self.check_redis_availability('localhost', port):
                logger.info(f"✅ Redis already running on port {port}")
                return True
            
            # Try to start Redis using systemctl (if available)
            try:
                if port == 6379:
                    result = subprocess.run(['sudo', 'systemctl', 'start', 'redis-server'], 
                                          capture_output=True, text=True, timeout=30)
                    if result.returncode == 0:
                        logger.info("✅ Started Redis using systemctl")
                        await asyncio.sleep(2)  # Give it time to start
                        return await self.check_redis_availability('localhost', port)
            except Exception:
                pass
            
            # Try to start Redis directly
            redis_config = f"""
port {port}
bind 127.0.0.1
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec
"""
            
            config_file = f"/tmp/redis_{port}.conf"
            with open(config_file, 'w') as f:
                f.write(redis_config)
            
            # Start Redis with custom config
            cmd = ['redis-server', config_file]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait a bit and check if it started
            await asyncio.sleep(3)
            
            if await self.check_redis_availability('localhost', port):
                logger.info(f"✅ Started Redis on port {port}")
                return True
            else:
                logger.error(f"❌ Failed to start Redis on port {port}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error starting Redis on port {port}: {e}")
            return False
    
    async def configure_redis_ttl_policies(self, host: str, port: int) -> bool:
        """Configure TTL policies for Redis instance."""
        logger.info(f"⚙️ Configuring TTL policies for Redis {host}:{port}")
        
        try:
            if REDIS_AVAILABLE:
                client = redis.Redis(host=host, port=port, decode_responses=True)
                
                # Set up TTL policies as Redis keys for reference
                for policy_name, ttl_seconds in self.ttl_policies.items():
                    key = f"ttl_policy:{policy_name}"
                    client.set(key, ttl_seconds, ex=86400)  # Policy configs expire in 24h
                    logger.info(f"  Set TTL policy {policy_name}: {ttl_seconds}s")
                
                # Configure Redis settings
                client.config_set('maxmemory-policy', 'allkeys-lru')
                client.config_set('maxmemory', '2gb')
                
                client.close()
                logger.info("✅ TTL policies configured successfully")
                return True
            else:
                # Use redis-cli for configuration
                for policy_name, ttl_seconds in self.ttl_policies.items():
                    key = f"ttl_policy:{policy_name}"
                    cmd = ['redis-cli', '-h', host, '-p', str(port), 'SET', key, str(ttl_seconds), 'EX', '86400']
                    subprocess.run(cmd, check=True, capture_output=True)
                
                # Configure Redis settings
                subprocess.run(['redis-cli', '-h', host, '-p', str(port), 'CONFIG', 'SET', 'maxmemory-policy', 'allkeys-lru'], check=True)
                subprocess.run(['redis-cli', '-h', host, '-p', str(port), 'CONFIG', 'SET', 'maxmemory', '2gb'], check=True)
                
                logger.info("✅ TTL policies configured successfully")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to configure TTL policies: {e}")
            return False
    
    async def setup_health_checks(self) -> Dict[str, bool]:
        """Setup health checks for all Redis instances."""
        logger.info("🏥 Setting up Redis health checks")
        
        health_status = {}
        
        for name, config in self.redis_configs.items():
            logger.info(f"Checking health of {name} ({config['host']}:{config['port']})")
            
            try:
                # Basic connectivity check
                is_available = await self.check_redis_availability(config['host'], config['port'])
                
                if is_available:
                    # Extended health check
                    if REDIS_AVAILABLE:
                        client = redis.Redis(host=config['host'], port=config['port'])
                        
                        # Test basic operations
                        test_key = f"health_check:{int(time.time())}"
                        client.set(test_key, "test_value", ex=60)
                        retrieved_value = client.get(test_key)
                        client.delete(test_key)
                        
                        # Check memory usage
                        info = client.info('memory')
                        memory_usage = info.get('used_memory_human', 'unknown')
                        
                        client.close()
                        
                        health_status[name] = True
                        logger.info(f"✅ {name} is healthy (Memory: {memory_usage})")
                    else:
                        # Basic health check with redis-cli
                        result = subprocess.run(
                            ['redis-cli', '-h', config['host'], '-p', str(config['port']), 'ping'],
                            capture_output=True, text=True, timeout=5
                        )
                        health_status[name] = result.returncode == 0
                        status = "✅ healthy" if health_status[name] else "❌ unhealthy"
                        logger.info(f"{status} {name}")
                else:
                    health_status[name] = False
                    logger.warning(f"⚠️ {name} is not available")
                    
            except Exception as e:
                health_status[name] = False
                logger.error(f"❌ Health check failed for {name}: {e}")
        
        return health_status
    
    async def implement_fallback_caching(self) -> bool:
        """Implement in-memory fallback caching when Redis is unavailable."""
        logger.info("🔄 Setting up fallback caching mechanism")
        
        fallback_cache_code = '''
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
'''
        
        # Save fallback cache implementation
        fallback_file = os.path.join(os.path.dirname(__file__), '..', 'src', 'backend', 'shared', 'fallback_cache.py')
        os.makedirs(os.path.dirname(fallback_file), exist_ok=True)
        
        with open(fallback_file, 'w') as f:
            f.write(fallback_cache_code)
        
        logger.info(f"✅ Fallback cache implementation saved to {fallback_file}")
        return True
    
    async def setup_complete_infrastructure(self) -> Dict[str, Any]:
        """Setup complete Redis infrastructure."""
        logger.info("🏗️ Setting up complete Redis infrastructure")
        logger.info("=" * 60)
        
        results = {
            'redis_services': {},
            'health_checks': {},
            'ttl_policies': {},
            'fallback_cache': False,
            'overall_status': 'PENDING'
        }
        
        # Step 1: Start Redis services
        for name, config in self.redis_configs.items():
            logger.info(f"Setting up {name}...")
            started = await self.start_redis_service(config['port'])
            results['redis_services'][name] = started
            
            if started:
                # Configure TTL policies
                ttl_configured = await self.configure_redis_ttl_policies(config['host'], config['port'])
                results['ttl_policies'][name] = ttl_configured
        
        # Step 2: Health checks
        results['health_checks'] = await self.setup_health_checks()
        
        # Step 3: Fallback caching
        results['fallback_cache'] = await self.implement_fallback_caching()
        
        # Determine overall status
        redis_healthy = all(results['health_checks'].values())
        ttl_configured = all(results['ttl_policies'].values())
        
        if redis_healthy and ttl_configured and results['fallback_cache']:
            results['overall_status'] = 'SUCCESS'
            logger.info("✅ Redis infrastructure setup completed successfully")
        elif any(results['health_checks'].values()):
            results['overall_status'] = 'PARTIAL'
            logger.warning("⚠️ Redis infrastructure partially operational")
        else:
            results['overall_status'] = 'FAILED'
            logger.error("❌ Redis infrastructure setup failed")
        
        # Summary
        logger.info("=" * 60)
        logger.info("📊 REDIS INFRASTRUCTURE SETUP SUMMARY")
        logger.info("=" * 60)
        for name, status in results['health_checks'].items():
            status_icon = "✅" if status else "❌"
            logger.info(f"{status_icon} {name}: {'Healthy' if status else 'Unhealthy'}")
        
        logger.info(f"Fallback cache: {'✅ Ready' if results['fallback_cache'] else '❌ Failed'}")
        logger.info(f"Overall status: {results['overall_status']}")
        
        return results

async def main():
    """Main function."""
    setup = RedisInfrastructureSetup()
    results = await setup.setup_complete_infrastructure()
    
    # Exit with appropriate code
    if results['overall_status'] == 'SUCCESS':
        sys.exit(0)
    elif results['overall_status'] == 'PARTIAL':
        logger.warning("Redis infrastructure partially operational - proceeding with warnings")
        sys.exit(0)  # Allow partial success for now
    else:
        logger.error("Redis infrastructure setup failed")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
