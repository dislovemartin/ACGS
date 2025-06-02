"""
Incremental Policy Compilation Engine for ACGS-PGP Task 8

Implements intelligent incremental compilation of policies to minimize
compilation overhead and improve performance for policy updates.

Key Features:
- Dependency tracking between policies
- Partial evaluation optimization
- Intelligent cache invalidation
- Performance monitoring and metrics
"""

import asyncio
import hashlib
import json
import logging
import time
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import networkx as nx

from .opa_client import OPAClient, PolicyBundle, CompilationMetrics, get_opa_client
from ..services.integrity_client import IntegrityPolicyRule

logger = logging.getLogger(__name__)


class CompilationStrategy(Enum):
    """Compilation strategies for different scenarios."""
    FULL = "full"           # Complete recompilation
    INCREMENTAL = "incremental"  # Only changed policies
    PARTIAL = "partial"     # Changed policies + dependencies
    OPTIMIZED = "optimized" # Smart dependency-based compilation


@dataclass
class PolicyDependency:
    """Represents a dependency between policies."""
    source_policy: str
    target_policy: str
    dependency_type: str  # import, data, rule_reference
    strength: float = 1.0  # Dependency strength (0.0 to 1.0)


@dataclass
class CompilationPlan:
    """Plan for incremental compilation."""
    strategy: CompilationStrategy
    policies_to_compile: Set[str]
    compilation_order: List[str]
    estimated_time_ms: float
    cache_invalidations: Set[str]
    dependencies_affected: Set[str]


@dataclass
class PolicyChangeSet:
    """Set of policy changes for compilation."""
    added: Dict[str, str] = field(default_factory=dict)
    modified: Dict[str, str] = field(default_factory=dict)
    deleted: Set[str] = field(default_factory=set)
    metadata_changed: Set[str] = field(default_factory=set)


class IncrementalCompiler:
    """
    Intelligent incremental policy compilation engine.
    
    Optimizes policy compilation by:
    1. Tracking dependencies between policies
    2. Identifying minimal compilation sets
    3. Using partial evaluation when possible
    4. Caching compilation results
    5. Monitoring performance metrics
    """
    
    def __init__(self, opa_client: Optional[OPAClient] = None):
        self.opa_client = opa_client
        
        # Dependency tracking
        self.dependency_graph = nx.DiGraph()
        self.policy_hashes: Dict[str, str] = {}
        self.policy_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Compilation cache
        self.compilation_cache: Dict[str, Any] = {}
        self.cache_timestamps: Dict[str, float] = {}
        
        # Performance metrics
        self.metrics = {
            "total_compilations": 0,
            "incremental_compilations": 0,
            "full_compilations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "average_compilation_time_ms": 0.0,
            "dependency_analysis_time_ms": 0.0,
            "policies_compiled": 0,
            "compilation_savings_percent": 0.0
        }
    
    async def initialize(self) -> None:
        """Initialize the compiler with OPA client."""
        if not self.opa_client:
            self.opa_client = await get_opa_client()
    
    async def compile_policies(
        self,
        policies: List[IntegrityPolicyRule],
        force_full: bool = False
    ) -> CompilationMetrics:
        """
        Compile policies using optimal incremental strategy.
        
        Args:
            policies: List of policy rules to compile
            force_full: Force full compilation regardless of changes
            
        Returns:
            CompilationMetrics with performance data
        """
        start_time = time.time()
        
        try:
            # Ensure OPA client is initialized
            await self.initialize()
            
            # Analyze changes
            change_set = await self._analyze_policy_changes(policies)
            
            # Create compilation plan
            plan = await self._create_compilation_plan(change_set, force_full)
            
            # Execute compilation
            compilation_metrics = await self._execute_compilation_plan(plan, policies)
            
            # Update metrics
            total_time = (time.time() - start_time) * 1000
            self._update_compilation_metrics(total_time, plan.strategy)
            
            # Update internal state
            await self._update_policy_state(policies)
            
            logger.info(
                f"Compilation completed: {plan.strategy.value} strategy, "
                f"{len(plan.policies_to_compile)} policies, "
                f"{total_time:.2f}ms"
            )
            
            return compilation_metrics
            
        except Exception as e:
            logger.error(f"Policy compilation failed: {e}")
            raise
    
    async def _analyze_policy_changes(
        self,
        policies: List[IntegrityPolicyRule]
    ) -> PolicyChangeSet:
        """Analyze what has changed since last compilation."""
        change_set = PolicyChangeSet()
        
        current_policies = {
            self._get_policy_id(policy): policy.rule_content 
            for policy in policies
        }
        
        # Find added and modified policies
        for policy_id, content in current_policies.items():
            content_hash = self._compute_content_hash(content)
            
            if policy_id not in self.policy_hashes:
                # New policy
                change_set.added[policy_id] = content
            elif self.policy_hashes[policy_id] != content_hash:
                # Modified policy
                change_set.modified[policy_id] = content
        
        # Find deleted policies
        for policy_id in self.policy_hashes:
            if policy_id not in current_policies:
                change_set.deleted.add(policy_id)
        
        logger.info(
            f"Policy changes: {len(change_set.added)} added, "
            f"{len(change_set.modified)} modified, "
            f"{len(change_set.deleted)} deleted"
        )
        
        return change_set
    
    async def _create_compilation_plan(
        self,
        change_set: PolicyChangeSet,
        force_full: bool
    ) -> CompilationPlan:
        """Create optimal compilation plan based on changes."""
        
        if force_full or self._should_use_full_compilation(change_set):
            return CompilationPlan(
                strategy=CompilationStrategy.FULL,
                policies_to_compile=set(self.policy_hashes.keys()) | 
                                  set(change_set.added.keys()) | 
                                  set(change_set.modified.keys()),
                compilation_order=list(self.policy_hashes.keys()),
                estimated_time_ms=self._estimate_full_compilation_time(),
                cache_invalidations=set(self.compilation_cache.keys()),
                dependencies_affected=set()
            )
        
        # Incremental compilation
        policies_to_compile = set()
        dependencies_affected = set()
        
        # Add directly changed policies
        policies_to_compile.update(change_set.added.keys())
        policies_to_compile.update(change_set.modified.keys())
        
        # Add policies that depend on changed policies
        for policy_id in change_set.added.keys() | change_set.modified.keys():
            dependents = self._get_dependent_policies(policy_id)
            dependencies_affected.update(dependents)
            policies_to_compile.update(dependents)
        
        # Determine compilation order based on dependencies
        compilation_order = self._topological_sort(policies_to_compile)
        
        # Determine cache invalidations
        cache_invalidations = self._determine_cache_invalidations(
            policies_to_compile, dependencies_affected
        )
        
        strategy = (
            CompilationStrategy.INCREMENTAL if len(policies_to_compile) < 5
            else CompilationStrategy.PARTIAL
        )
        
        return CompilationPlan(
            strategy=strategy,
            policies_to_compile=policies_to_compile,
            compilation_order=compilation_order,
            estimated_time_ms=self._estimate_incremental_compilation_time(
                len(policies_to_compile)
            ),
            cache_invalidations=cache_invalidations,
            dependencies_affected=dependencies_affected
        )
    
    async def _execute_compilation_plan(
        self,
        plan: CompilationPlan,
        policies: List[IntegrityPolicyRule]
    ) -> CompilationMetrics:
        """Execute the compilation plan."""
        
        # Invalidate affected cache entries
        for cache_key in plan.cache_invalidations:
            if cache_key in self.compilation_cache:
                del self.compilation_cache[cache_key]
                del self.cache_timestamps[cache_key]
        
        # Prepare policy bundle
        policy_dict = {
            self._get_policy_id(policy): policy.rule_content
            for policy in policies
            if self._get_policy_id(policy) in plan.policies_to_compile
        }
        
        bundle = PolicyBundle(
            name="acgs_policies",
            policies=policy_dict,
            revision=str(int(time.time()))
        )
        
        # Upload to OPA
        incremental = plan.strategy in [
            CompilationStrategy.INCREMENTAL,
            CompilationStrategy.PARTIAL
        ]
        
        compilation_metrics = await self.opa_client.upload_policy_bundle(
            bundle, incremental=incremental
        )
        
        # Update compilation cache
        for policy_id in plan.policies_to_compile:
            cache_key = f"compiled:{policy_id}"
            self.compilation_cache[cache_key] = True
            self.cache_timestamps[cache_key] = time.time()
        
        return compilation_metrics
    
    def _should_use_full_compilation(self, change_set: PolicyChangeSet) -> bool:
        """Determine if full compilation is necessary."""
        total_changes = (
            len(change_set.added) + 
            len(change_set.modified) + 
            len(change_set.deleted)
        )
        
        # Use full compilation if:
        # 1. More than 50% of policies changed
        # 2. Core dependency policies changed
        # 3. First compilation (no existing state)
        
        if not self.policy_hashes:
            return True
        
        change_ratio = total_changes / max(1, len(self.policy_hashes))
        if change_ratio > 0.5:
            return True
        
        # Check for core policy changes (policies with many dependents)
        for policy_id in change_set.modified.keys() | change_set.deleted:
            if len(self._get_dependent_policies(policy_id)) > 5:
                return True
        
        return False
    
    def _get_dependent_policies(self, policy_id: str) -> Set[str]:
        """Get all policies that depend on the given policy."""
        if policy_id not in self.dependency_graph:
            return set()
        
        # Get all nodes reachable from this policy
        dependents = set()
        for successor in self.dependency_graph.successors(policy_id):
            dependents.add(successor)
            dependents.update(self._get_dependent_policies(successor))
        
        return dependents
    
    def _topological_sort(self, policies: Set[str]) -> List[str]:
        """Sort policies in dependency order for compilation."""
        subgraph = self.dependency_graph.subgraph(policies)
        try:
            return list(nx.topological_sort(subgraph))
        except nx.NetworkXError:
            # Handle cycles by using a simple ordering
            logger.warning("Dependency cycle detected, using simple ordering")
            return sorted(policies)
    
    def _determine_cache_invalidations(
        self,
        policies_to_compile: Set[str],
        dependencies_affected: Set[str]
    ) -> Set[str]:
        """Determine which cache entries need invalidation."""
        invalidations = set()
        
        # Invalidate cache for policies being compiled
        for policy_id in policies_to_compile:
            invalidations.add(f"compiled:{policy_id}")
            invalidations.add(f"evaluated:{policy_id}")
        
        # Invalidate cache for dependent policies
        for policy_id in dependencies_affected:
            invalidations.add(f"evaluated:{policy_id}")
        
        return invalidations
    
    def _estimate_full_compilation_time(self) -> float:
        """Estimate time for full compilation."""
        policy_count = len(self.policy_hashes)
        # Base estimate: 10ms per policy + 100ms overhead
        return max(100, policy_count * 10 + 100)
    
    def _estimate_incremental_compilation_time(self, policy_count: int) -> float:
        """Estimate time for incremental compilation."""
        # Base estimate: 5ms per policy + 50ms overhead
        return max(50, policy_count * 5 + 50)
    
    async def _update_policy_state(self, policies: List[IntegrityPolicyRule]) -> None:
        """Update internal policy state after compilation."""
        # Update policy hashes
        self.policy_hashes.clear()
        for policy in policies:
            policy_id = self._get_policy_id(policy)
            content_hash = self._compute_content_hash(policy.rule_content)
            self.policy_hashes[policy_id] = content_hash
        
        # Update dependency graph (simplified - would need actual dependency analysis)
        await self._update_dependency_graph(policies)
    
    async def _update_dependency_graph(self, policies: List[IntegrityPolicyRule]) -> None:
        """Update the policy dependency graph."""
        # Clear existing graph
        self.dependency_graph.clear()
        
        # Add all policies as nodes
        for policy in policies:
            policy_id = self._get_policy_id(policy)
            self.dependency_graph.add_node(policy_id)
        
        # Analyze dependencies (simplified - would need proper Rego parsing)
        for policy in policies:
            policy_id = self._get_policy_id(policy)
            dependencies = self._extract_policy_dependencies(policy.rule_content)
            
            for dep in dependencies:
                if dep in self.policy_hashes:
                    self.dependency_graph.add_edge(dep, policy_id)
    
    def _extract_policy_dependencies(self, policy_content: str) -> List[str]:
        """Extract policy dependencies from Rego content."""
        # Simplified dependency extraction
        # In practice, would need proper Rego AST parsing
        dependencies = []
        
        # Look for import statements
        import_pattern = r'import\s+data\.([a-zA-Z_][a-zA-Z0-9_]*)'
        import re
        matches = re.findall(import_pattern, policy_content)
        dependencies.extend(matches)
        
        # Look for data references
        data_pattern = r'data\.([a-zA-Z_][a-zA-Z0-9_]*)'
        matches = re.findall(data_pattern, policy_content)
        dependencies.extend(matches)
        
        return list(set(dependencies))
    
    def _get_policy_id(self, policy: IntegrityPolicyRule) -> str:
        """Get unique identifier for a policy."""
        return getattr(policy, 'id', str(hash(policy.rule_content)))
    
    def _compute_content_hash(self, content: str) -> str:
        """Compute hash of policy content."""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _update_compilation_metrics(
        self,
        compilation_time_ms: float,
        strategy: CompilationStrategy
    ) -> None:
        """Update compilation performance metrics."""
        self.metrics["total_compilations"] += 1
        
        if strategy == CompilationStrategy.FULL:
            self.metrics["full_compilations"] += 1
        else:
            self.metrics["incremental_compilations"] += 1
        
        # Update average compilation time
        current_avg = self.metrics["average_compilation_time_ms"]
        total_compilations = self.metrics["total_compilations"]
        
        self.metrics["average_compilation_time_ms"] = (
            (current_avg * (total_compilations - 1) + compilation_time_ms) / 
            total_compilations
        )
        
        # Calculate compilation savings
        if strategy != CompilationStrategy.FULL:
            estimated_full_time = self._estimate_full_compilation_time()
            savings = max(0, (estimated_full_time - compilation_time_ms) / estimated_full_time)
            self.metrics["compilation_savings_percent"] = savings * 100
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get compilation performance metrics."""
        return {
            **self.metrics,
            "dependency_graph_size": self.dependency_graph.number_of_nodes(),
            "dependency_edges": self.dependency_graph.number_of_edges(),
            "cache_size": len(self.compilation_cache),
            "policy_count": len(self.policy_hashes)
        }


# Global incremental compiler instance
_incremental_compiler: Optional[IncrementalCompiler] = None


async def get_incremental_compiler() -> IncrementalCompiler:
    """Get or create the global incremental compiler instance."""
    global _incremental_compiler
    
    if _incremental_compiler is None:
        _incremental_compiler = IncrementalCompiler()
        await _incremental_compiler.initialize()
    
    return _incremental_compiler
