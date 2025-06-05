#!/usr/bin/env python3
"""
Cache Warming Service for ACGS-master Phase 3
Implements cache warming strategies to achieve >80% cache hit rate target.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)

class CacheWarmingStrategy(Enum):
    """Cache warming strategies."""
    IMMEDIATE = "immediate"  # Warm cache immediately
    SCHEDULED = "scheduled"  # Warm cache on schedule
    PREDICTIVE = "predictive"  # Warm cache based on usage patterns
    ON_DEMAND = "on_demand"  # Warm cache when requested

@dataclass
class CacheWarmingConfig:
    """Cache warming configuration."""
    strategy: CacheWarmingStrategy = CacheWarmingStrategy.IMMEDIATE
    warm_on_startup: bool = True
    warming_interval_minutes: int = 60
    max_warming_items: int = 1000
    warming_batch_size: int = 50
    warming_delay_ms: int = 10  # Delay between batches
    enable_predictive_warming: bool = True
    usage_pattern_window_hours: int = 24

@dataclass
class CacheWarmingItem:
    """Item to be warmed in cache."""
    key: str
    value: Any
    ttl: int
    tags: List[str]
    priority: int = 1  # 1=high, 2=medium, 3=low
    category: str = "general"

@dataclass
class WarmingMetrics:
    """Cache warming metrics."""
    total_items_warmed: int
    successful_warmings: int
    failed_warmings: int
    warming_duration_seconds: float
    cache_hit_rate_improvement: float
    timestamp: datetime

class CacheWarmingService:
    """
    Cache warming service to improve cache hit rates.
    
    Features:
    - Multiple warming strategies
    - Predictive warming based on usage patterns
    - Scheduled warming
    - Priority-based warming
    - Performance metrics tracking
    """
    
    def __init__(self, cache_client, config: Optional[CacheWarmingConfig] = None):
        self.cache_client = cache_client
        self.config = config or CacheWarmingConfig()
        self.warming_active = False
        self.warming_task: Optional[asyncio.Task] = None
        
        # Warming data sources
        self.warming_sources: Dict[str, callable] = {}
        self.usage_patterns: Dict[str, List[Tuple[str, datetime]]] = {}
        
        # Metrics
        self.warming_metrics: List[WarmingMetrics] = []
        self.last_warming_time: Optional[datetime] = None
        
        # Predictive warming
        self.access_frequency: Dict[str, int] = {}
        self.access_times: Dict[str, List[datetime]] = {}
        
    async def initialize(self):
        """Initialize cache warming service."""
        try:
            logger.info("Initializing cache warming service")
            
            # Register default warming sources
            await self._register_default_warming_sources()
            
            # Start warming if configured
            if self.config.warm_on_startup:
                await self.warm_cache_immediate()
            
            # Start scheduled warming
            if self.config.strategy in [CacheWarmingStrategy.SCHEDULED, CacheWarmingStrategy.PREDICTIVE]:
                await self.start_scheduled_warming()
            
            logger.info("Cache warming service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize cache warming service: {e}")
            raise
    
    async def _register_default_warming_sources(self):
        """Register default warming data sources."""
        # Constitutional principles
        self.warming_sources["constitutional_principles"] = self._get_constitutional_principles
        
        # Governance rules
        self.warming_sources["governance_rules"] = self._get_governance_rules
        
        # Policy decisions
        self.warming_sources["policy_decisions"] = self._get_frequent_policy_decisions
        
        # User sessions
        self.warming_sources["user_sessions"] = self._get_active_user_sessions
        
        # Static configuration
        self.warming_sources["static_config"] = self._get_static_configuration
    
    async def warm_cache_immediate(self) -> WarmingMetrics:
        """Perform immediate cache warming."""
        logger.info("Starting immediate cache warming")
        start_time = time.time()
        
        warming_items = await self._collect_warming_items()
        metrics = await self._execute_warming(warming_items)
        
        duration = time.time() - start_time
        metrics.warming_duration_seconds = duration
        
        self.warming_metrics.append(metrics)
        self.last_warming_time = datetime.now()
        
        logger.info(
            f"Immediate cache warming completed: {metrics.successful_warmings}/{metrics.total_items_warmed} "
            f"items in {duration:.2f}s"
        )
        
        return metrics
    
    async def start_scheduled_warming(self):
        """Start scheduled cache warming."""
        if self.warming_active:
            logger.warning("Scheduled warming already active")
            return
        
        self.warming_active = True
        self.warming_task = asyncio.create_task(self._scheduled_warming_loop())
        logger.info(f"Started scheduled warming with {self.config.warming_interval_minutes}min interval")
    
    async def stop_scheduled_warming(self):
        """Stop scheduled cache warming."""
        self.warming_active = False
        if self.warming_task:
            self.warming_task.cancel()
            try:
                await self.warming_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped scheduled warming")
    
    async def _scheduled_warming_loop(self):
        """Scheduled warming loop."""
        while self.warming_active:
            try:
                await asyncio.sleep(self.config.warming_interval_minutes * 60)
                
                if self.warming_active:
                    if self.config.strategy == CacheWarmingStrategy.PREDICTIVE:
                        await self.warm_cache_predictive()
                    else:
                        await self.warm_cache_immediate()
                
            except Exception as e:
                logger.error(f"Error in scheduled warming loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def warm_cache_predictive(self) -> WarmingMetrics:
        """Perform predictive cache warming based on usage patterns."""
        logger.info("Starting predictive cache warming")
        start_time = time.time()
        
        # Analyze usage patterns
        predicted_items = await self._predict_warming_items()
        
        # Execute warming
        metrics = await self._execute_warming(predicted_items)
        
        duration = time.time() - start_time
        metrics.warming_duration_seconds = duration
        
        self.warming_metrics.append(metrics)
        self.last_warming_time = datetime.now()
        
        logger.info(
            f"Predictive cache warming completed: {metrics.successful_warmings}/{metrics.total_items_warmed} "
            f"items in {duration:.2f}s"
        )
        
        return metrics
    
    async def _collect_warming_items(self) -> List[CacheWarmingItem]:
        """Collect items for cache warming."""
        warming_items = []
        
        for source_name, source_func in self.warming_sources.items():
            try:
                items = await source_func()
                warming_items.extend(items)
                logger.debug(f"Collected {len(items)} items from {source_name}")
            except Exception as e:
                logger.error(f"Failed to collect warming items from {source_name}: {e}")
        
        # Sort by priority and limit
        warming_items.sort(key=lambda x: x.priority)
        return warming_items[:self.config.max_warming_items]
    
    async def _predict_warming_items(self) -> List[CacheWarmingItem]:
        """Predict items to warm based on usage patterns."""
        predicted_items = []
        
        # Analyze access frequency
        frequent_keys = sorted(
            self.access_frequency.items(),
            key=lambda x: x[1],
            reverse=True
        )[:self.config.max_warming_items // 2]
        
        # Analyze access timing patterns
        time_based_keys = await self._analyze_time_patterns()
        
        # Combine predictions
        all_predicted_keys = set([key for key, _ in frequent_keys] + time_based_keys)
        
        # Convert to warming items
        for key in all_predicted_keys:
            # Try to get value from warming sources
            for source_name, source_func in self.warming_sources.items():
                try:
                    items = await source_func()
                    for item in items:
                        if item.key == key:
                            predicted_items.append(item)
                            break
                except Exception:
                    continue
        
        return predicted_items[:self.config.max_warming_items]
    
    async def _analyze_time_patterns(self) -> List[str]:
        """Analyze time-based access patterns."""
        current_hour = datetime.now().hour
        current_day = datetime.now().weekday()
        
        time_based_keys = []
        
        for key, access_times in self.access_times.items():
            # Filter recent access times
            recent_accesses = [
                t for t in access_times
                if t > datetime.now() - timedelta(hours=self.config.usage_pattern_window_hours)
            ]
            
            if not recent_accesses:
                continue
            
            # Check if key is frequently accessed at this time
            same_hour_accesses = [
                t for t in recent_accesses
                if t.hour == current_hour
            ]
            
            same_day_accesses = [
                t for t in recent_accesses
                if t.weekday() == current_day
            ]
            
            # Predict if likely to be accessed soon
            if len(same_hour_accesses) >= 2 or len(same_day_accesses) >= 3:
                time_based_keys.append(key)
        
        return time_based_keys
    
    async def _execute_warming(self, warming_items: List[CacheWarmingItem]) -> WarmingMetrics:
        """Execute cache warming for items."""
        total_items = len(warming_items)
        successful = 0
        failed = 0
        
        # Process in batches
        for i in range(0, total_items, self.config.warming_batch_size):
            batch = warming_items[i:i + self.config.warming_batch_size]
            
            # Warm batch
            for item in batch:
                try:
                    await self.cache_client.put(item.key, item.value, item.ttl, item.tags)
                    successful += 1
                except Exception as e:
                    logger.error(f"Failed to warm cache item {item.key}: {e}")
                    failed += 1
            
            # Delay between batches to avoid overwhelming
            if i + self.config.warming_batch_size < total_items:
                await asyncio.sleep(self.config.warming_delay_ms / 1000)
        
        return WarmingMetrics(
            total_items_warmed=total_items,
            successful_warmings=successful,
            failed_warmings=failed,
            warming_duration_seconds=0.0,  # Will be set by caller
            cache_hit_rate_improvement=0.0,  # Could be calculated if baseline available
            timestamp=datetime.now()
        )
    
    def record_cache_access(self, key: str):
        """Record cache access for predictive warming."""
        # Update access frequency
        self.access_frequency[key] = self.access_frequency.get(key, 0) + 1
        
        # Update access times
        if key not in self.access_times:
            self.access_times[key] = []
        
        self.access_times[key].append(datetime.now())
        
        # Limit access time history
        if len(self.access_times[key]) > 100:
            self.access_times[key] = self.access_times[key][-50:]
    
    async def _get_constitutional_principles(self) -> List[CacheWarmingItem]:
        """Get constitutional principles for warming."""
        # This would typically query the database
        principles = [
            {
                "id": 1,
                "name": "Human Dignity",
                "description": "Respect for human dignity in all decisions",
                "category": "fundamental"
            },
            {
                "id": 2,
                "name": "Fairness",
                "description": "Ensure fairness and non-discrimination",
                "category": "fundamental"
            },
            {
                "id": 3,
                "name": "Privacy",
                "description": "Protect individual privacy rights",
                "category": "rights"
            }
        ]
        
        warming_items = []
        for principle in principles:
            warming_items.append(CacheWarmingItem(
                key=f"constitutional_principle:{principle['id']}",
                value=principle,
                ttl=86400,  # 24 hours for static config
                tags=["constitutional_principles", principle["category"]],
                priority=1,  # High priority
                category="constitutional"
            ))
        
        return warming_items
    
    async def _get_governance_rules(self) -> List[CacheWarmingItem]:
        """Get governance rules for warming."""
        # Mock governance rules
        rules = [
            {
                "id": "rule_001",
                "name": "Policy Approval Process",
                "content": "All policies must be approved by constitutional council",
                "category": "approval"
            },
            {
                "id": "rule_002",
                "name": "Stakeholder Consultation",
                "content": "Major decisions require stakeholder consultation",
                "category": "consultation"
            }
        ]
        
        warming_items = []
        for rule in rules:
            warming_items.append(CacheWarmingItem(
                key=f"governance_rule:{rule['id']}",
                value=rule,
                ttl=3600,  # 1 hour for governance rules
                tags=["governance_rules", rule["category"]],
                priority=1,
                category="governance"
            ))
        
        return warming_items
    
    async def _get_frequent_policy_decisions(self) -> List[CacheWarmingItem]:
        """Get frequent policy decisions for warming."""
        # Mock frequent decisions
        decisions = [
            {
                "policy": "allow_read_access",
                "result": {"allow": True, "reason": "Standard read access"},
                "frequency": 100
            },
            {
                "policy": "allow_write_access",
                "result": {"allow": False, "reason": "Requires elevated permissions"},
                "frequency": 50
            }
        ]
        
        warming_items = []
        for decision in decisions:
            warming_items.append(CacheWarmingItem(
                key=f"policy_decision:{decision['policy']}",
                value=decision["result"],
                ttl=300,  # 5 minutes for policy decisions
                tags=["policy_decisions"],
                priority=2,  # Medium priority
                category="policy"
            ))
        
        return warming_items
    
    async def _get_active_user_sessions(self) -> List[CacheWarmingItem]:
        """Get active user sessions for warming."""
        # Mock active sessions
        sessions = [
            {"user_id": "user_001", "session_data": {"role": "admin", "permissions": ["read", "write"]}},
            {"user_id": "user_002", "session_data": {"role": "user", "permissions": ["read"]}}
        ]
        
        warming_items = []
        for session in sessions:
            warming_items.append(CacheWarmingItem(
                key=f"user_session:{session['user_id']}",
                value=session["session_data"],
                ttl=1800,  # 30 minutes for user sessions
                tags=["user_sessions"],
                priority=2,
                category="session"
            ))
        
        return warming_items
    
    async def _get_static_configuration(self) -> List[CacheWarmingItem]:
        """Get static configuration for warming."""
        config = {
            "app_settings": {"debug": False, "log_level": "INFO"},
            "feature_flags": {"new_ui": True, "beta_features": False}
        }
        
        warming_items = []
        for key, value in config.items():
            warming_items.append(CacheWarmingItem(
                key=f"static_config:{key}",
                value=value,
                ttl=86400,  # 24 hours for static config
                tags=["static_configuration"],
                priority=3,  # Low priority
                category="config"
            ))
        
        return warming_items
    
    def get_warming_stats(self) -> Dict[str, Any]:
        """Get cache warming statistics."""
        if not self.warming_metrics:
            return {"error": "No warming data available"}
        
        latest = self.warming_metrics[-1]
        
        return {
            "latest_warming": {
                "total_items": latest.total_items_warmed,
                "successful": latest.successful_warmings,
                "failed": latest.failed_warmings,
                "success_rate": (latest.successful_warmings / latest.total_items_warmed * 100) if latest.total_items_warmed > 0 else 0,
                "duration_seconds": latest.warming_duration_seconds,
                "timestamp": latest.timestamp.isoformat()
            },
            "configuration": {
                "strategy": self.config.strategy.value,
                "warming_interval_minutes": self.config.warming_interval_minutes,
                "max_warming_items": self.config.max_warming_items,
                "warming_active": self.warming_active
            },
            "usage_patterns": {
                "tracked_keys": len(self.access_frequency),
                "total_accesses": sum(self.access_frequency.values()),
                "predictive_enabled": self.config.enable_predictive_warming
            },
            "last_warming": self.last_warming_time.isoformat() if self.last_warming_time else None
        }

# Global cache warming service instance
_cache_warming_service: Optional[CacheWarmingService] = None

def get_cache_warming_service(cache_client) -> CacheWarmingService:
    """Get or create cache warming service instance."""
    global _cache_warming_service
    if _cache_warming_service is None:
        _cache_warming_service = CacheWarmingService(cache_client)
    return _cache_warming_service
