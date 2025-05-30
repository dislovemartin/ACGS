"""
Safety and Conflict Checking for ACGS-PGP Phase 3
Implements real-time safety property verification and conflict detection
"""

import time
import logging
import hashlib
from typing import List, Dict, Any, Optional, Set, Tuple
from ..schemas import (
    SafetyCheckRequest, SafetyCheckResponse, SafetyCheckResult,
    ConflictCheckRequest, ConflictCheckResponse, ConflictDetectionResult,
    ConflictType, SafetyProperty, PolicyRule
)

logger = logging.getLogger(__name__)

class SafetyPropertyChecker:
    """
    Implements safety property verification for policy rules.
    """
    
    def __init__(self):
        self.safety_cache = {}  # Cache for safety check results
        
    async def check_safety_properties(
        self,
        request: SafetyCheckRequest,
        policy_rules: List[PolicyRule]
    ) -> SafetyCheckResponse:
        """
        Check safety properties against policy rules.
        """
        start_time = time.time()
        
        logger.info(f"Starting safety property checking for {len(request.safety_properties)} properties")
        
        results = []
        critical_violations = []
        
        for safety_property in request.safety_properties:
            result = await self._check_single_property(
                safety_property, 
                policy_rules, 
                request.verification_method,
                request.depth_limit,
                request.time_limit_seconds
            )
            
            results.append(result)
            
            # Track critical violations
            if result.status == "violated" and safety_property.criticality_level == "critical":
                critical_violations.append(f"Critical violation: {safety_property.property_description}")
        
        # Determine overall safety status
        overall_status = self._determine_safety_status(results)
        summary = self._generate_safety_summary(results, critical_violations)
        
        total_time = int((time.time() - start_time) * 1000)
        logger.info(f"Safety property checking completed in {total_time}ms")
        
        return SafetyCheckResponse(
            results=results,
            overall_safety_status=overall_status,
            critical_violations=critical_violations,
            summary=summary
        )
    
    async def _check_single_property(
        self,
        safety_property: SafetyProperty,
        policy_rules: List[PolicyRule],
        verification_method: str,
        depth_limit: Optional[int],
        time_limit: Optional[int]
    ) -> SafetyCheckResult:
        """
        Check a single safety property against all policy rules.
        """
        start_time = time.time()
        
        try:
            # Generate cache key
            rules_hash = hashlib.md5(
                "".join(rule.rule_content for rule in policy_rules).encode()
            ).hexdigest()
            cache_key = f"{safety_property.property_id}_{rules_hash}_{verification_method}"
            
            # Check cache
            if cache_key in self.safety_cache:
                logger.debug(f"Using cached result for property {safety_property.property_id}")
                return self.safety_cache[cache_key]
            
            # Perform verification based on method
            if verification_method == "bounded_model_checking":
                result = await self._bounded_model_check_property(
                    safety_property, policy_rules, depth_limit
                )
            elif verification_method == "symbolic_execution":
                result = await self._symbolic_execution_check(
                    safety_property, policy_rules
                )
            elif verification_method == "abstract_interpretation":
                result = await self._abstract_interpretation_check(
                    safety_property, policy_rules
                )
            else:
                # Default to pattern-based checking
                result = await self._pattern_based_check(
                    safety_property, policy_rules
                )
            
            verification_time = int((time.time() - start_time) * 1000)
            result.verification_time_ms = verification_time
            
            # Cache result
            self.safety_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            logger.error(f"Safety property check failed for {safety_property.property_id}: {str(e)}")
            return SafetyCheckResult(
                property_id=safety_property.property_id,
                status="unknown",
                counter_example_trace=f"Verification error: {str(e)}",
                verification_time_ms=int((time.time() - start_time) * 1000)
            )
    
    async def _bounded_model_check_property(
        self,
        safety_property: SafetyProperty,
        policy_rules: List[PolicyRule],
        depth_limit: Optional[int]
    ) -> SafetyCheckResult:
        """
        Simulate bounded model checking for safety property.
        """
        # Simulate BMC analysis
        depth = depth_limit or 100
        
        # Check for common safety violations
        violations = []
        witness_traces = []
        
        for rule in policy_rules:
            rule_content = rule.rule_content.lower()
            
            # Check for specific safety property violations
            if safety_property.property_type == "safety":
                if "unsafe" in rule_content and "safety" in safety_property.formal_specification.lower():
                    violations.append(f"Rule {rule.id} contains unsafe operations")
                    
            elif safety_property.property_type == "security":
                if "unauthorized" in rule_content and "security" in safety_property.formal_specification.lower():
                    violations.append(f"Rule {rule.id} may allow unauthorized access")
                    
            elif safety_property.property_type == "fairness":
                if "discriminate" in rule_content and "fairness" in safety_property.formal_specification.lower():
                    violations.append(f"Rule {rule.id} may contain discriminatory logic")
        
        if violations:
            return SafetyCheckResult(
                property_id=safety_property.property_id,
                status="violated",
                counter_example_trace="; ".join(violations),
                verification_depth=depth
            )
        else:
            return SafetyCheckResult(
                property_id=safety_property.property_id,
                status="satisfied",
                witness_trace=f"Property verified up to depth {depth}",
                verification_depth=depth
            )
    
    async def _symbolic_execution_check(
        self,
        safety_property: SafetyProperty,
        policy_rules: List[PolicyRule]
    ) -> SafetyCheckResult:
        """
        Simulate symbolic execution for safety property checking.
        """
        # Simulate symbolic execution analysis
        paths_explored = len(policy_rules) * 10  # Simulate path explosion
        
        # Simple pattern matching for demonstration
        violations = []
        for rule in policy_rules:
            if "null" in rule.rule_content.lower() and "null_pointer" in safety_property.formal_specification.lower():
                violations.append(f"Potential null pointer dereference in rule {rule.id}")
        
        status = "violated" if violations else "satisfied"
        trace = "; ".join(violations) if violations else f"Explored {paths_explored} symbolic paths"
        
        return SafetyCheckResult(
            property_id=safety_property.property_id,
            status=status,
            witness_trace=trace if status == "satisfied" else None,
            counter_example_trace=trace if status == "violated" else None
        )
    
    async def _abstract_interpretation_check(
        self,
        safety_property: SafetyProperty,
        policy_rules: List[PolicyRule]
    ) -> SafetyCheckResult:
        """
        Simulate abstract interpretation for safety property checking.
        """
        # Simulate abstract interpretation analysis
        abstract_states = len(policy_rules) * 5
        
        # Check for abstract property violations
        violations = []
        for rule in policy_rules:
            if "overflow" in rule.rule_content.lower() and "bounds" in safety_property.formal_specification.lower():
                violations.append(f"Potential buffer overflow in rule {rule.id}")
        
        status = "violated" if violations else "satisfied"
        trace = "; ".join(violations) if violations else f"Analyzed {abstract_states} abstract states"
        
        return SafetyCheckResult(
            property_id=safety_property.property_id,
            status=status,
            witness_trace=trace if status == "satisfied" else None,
            counter_example_trace=trace if status == "violated" else None
        )
    
    async def _pattern_based_check(
        self,
        safety_property: SafetyProperty,
        policy_rules: List[PolicyRule]
    ) -> SafetyCheckResult:
        """
        Pattern-based safety property checking (fallback method).
        """
        violations = []
        
        # Define safety patterns
        safety_patterns = {
            "no_unauthorized_access": ["unauthorized", "bypass", "escalate"],
            "data_protection": ["unencrypted", "plaintext", "exposed"],
            "resource_safety": ["deadlock", "race_condition", "resource_leak"],
            "input_validation": ["unsanitized", "injection", "malformed"]
        }
        
        for rule in policy_rules:
            rule_content = rule.rule_content.lower()
            
            for pattern_name, keywords in safety_patterns.items():
                if pattern_name in safety_property.formal_specification.lower():
                    for keyword in keywords:
                        if keyword in rule_content:
                            violations.append(f"Rule {rule.id} violates {pattern_name}: contains '{keyword}'")
        
        status = "violated" if violations else "satisfied"
        trace = "; ".join(violations) if violations else "All pattern checks passed"
        
        return SafetyCheckResult(
            property_id=safety_property.property_id,
            status=status,
            witness_trace=trace if status == "satisfied" else None,
            counter_example_trace=trace if status == "violated" else None
        )
    
    def _determine_safety_status(self, results: List[SafetyCheckResult]) -> str:
        """
        Determine overall safety status from individual results.
        """
        if not results:
            return "unknown"
        
        violated_count = sum(1 for r in results if r.status == "violated")
        satisfied_count = sum(1 for r in results if r.status == "satisfied")
        unknown_count = sum(1 for r in results if r.status == "unknown")
        
        if violated_count > 0:
            return "unsafe"
        elif satisfied_count == len(results):
            return "safe"
        elif unknown_count > 0:
            return "unknown"
        else:
            return "inconclusive"
    
    def _generate_safety_summary(self, results: List[SafetyCheckResult], critical_violations: List[str]) -> str:
        """
        Generate summary of safety check results.
        """
        total = len(results)
        satisfied = sum(1 for r in results if r.status == "satisfied")
        violated = sum(1 for r in results if r.status == "violated")
        unknown = sum(1 for r in results if r.status == "unknown")
        
        summary = f"Safety check: {satisfied}/{total} satisfied, {violated}/{total} violated, {unknown}/{total} unknown"
        
        if critical_violations:
            summary += f" | {len(critical_violations)} critical violations detected"
        
        return summary


class ConflictDetector:
    """
    Implements conflict detection between policy rules.
    """
    
    def __init__(self):
        self.conflict_cache = {}
        
    async def detect_conflicts(
        self,
        request: ConflictCheckRequest,
        all_policy_rules: Dict[str, List[PolicyRule]]
    ) -> ConflictCheckResponse:
        """
        Detect conflicts between rule sets.
        """
        start_time = time.time()
        
        logger.info(f"Starting conflict detection for {len(request.rule_sets)} rule sets")
        
        conflicts = []
        
        # Check conflicts between different rule sets
        for i, rule_set_1 in enumerate(request.rule_sets):
            for j, rule_set_2 in enumerate(request.rule_sets[i+1:], i+1):
                set_conflicts = await self._detect_conflicts_between_sets(
                    rule_set_1, rule_set_2,
                    all_policy_rules.get(rule_set_1, []),
                    all_policy_rules.get(rule_set_2, []),
                    request.conflict_types
                )
                conflicts.extend(set_conflicts)
        
        # Check internal conflicts within each rule set
        for rule_set_name in request.rule_sets:
            rules = all_policy_rules.get(rule_set_name, [])
            internal_conflicts = await self._detect_internal_conflicts(
                rule_set_name, rules, request.conflict_types
            )
            conflicts.extend(internal_conflicts)
        
        # Calculate metrics
        total_conflicts = len(conflicts)
        critical_conflicts = sum(1 for c in conflicts if c.severity == "critical")
        resolution_required = critical_conflicts > 0 or total_conflicts > 5
        
        summary = self._generate_conflict_summary(conflicts, request.rule_sets)
        
        total_time = int((time.time() - start_time) * 1000)
        logger.info(f"Conflict detection completed in {total_time}ms")
        
        return ConflictCheckResponse(
            conflicts=conflicts,
            total_conflicts=total_conflicts,
            critical_conflicts=critical_conflicts,
            resolution_required=resolution_required,
            summary=summary
        )
    
    async def _detect_conflicts_between_sets(
        self,
        set_name_1: str,
        set_name_2: str,
        rules_1: List[PolicyRule],
        rules_2: List[PolicyRule],
        conflict_types: List[ConflictType]
    ) -> List[ConflictDetectionResult]:
        """
        Detect conflicts between two rule sets.
        """
        conflicts = []
        
        for rule_1 in rules_1:
            for rule_2 in rules_2:
                for conflict_type in conflict_types:
                    conflict = await self._check_rule_pair_conflict(
                        rule_1, rule_2, conflict_type, f"{set_name_1}_vs_{set_name_2}"
                    )
                    if conflict:
                        conflicts.append(conflict)
        
        return conflicts
    
    async def _detect_internal_conflicts(
        self,
        rule_set_name: str,
        rules: List[PolicyRule],
        conflict_types: List[ConflictType]
    ) -> List[ConflictDetectionResult]:
        """
        Detect conflicts within a single rule set.
        """
        conflicts = []
        
        for i, rule_1 in enumerate(rules):
            for j, rule_2 in enumerate(rules[i+1:], i+1):
                for conflict_type in conflict_types:
                    conflict = await self._check_rule_pair_conflict(
                        rule_1, rule_2, conflict_type, f"{rule_set_name}_internal"
                    )
                    if conflict:
                        conflicts.append(conflict)
        
        return conflicts
    
    async def _check_rule_pair_conflict(
        self,
        rule_1: PolicyRule,
        rule_2: PolicyRule,
        conflict_type: ConflictType,
        context: str
    ) -> Optional[ConflictDetectionResult]:
        """
        Check for a specific type of conflict between two rules.
        """
        # Generate cache key
        cache_key = f"{rule_1.id}_{rule_2.id}_{conflict_type.value}"
        if cache_key in self.conflict_cache:
            return self.conflict_cache[cache_key]
        
        conflict = None
        
        if conflict_type == ConflictType.LOGICAL_CONTRADICTION:
            conflict = await self._check_logical_contradiction(rule_1, rule_2, context)
        elif conflict_type == ConflictType.PRACTICAL_INCOMPATIBILITY:
            conflict = await self._check_practical_incompatibility(rule_1, rule_2, context)
        elif conflict_type == ConflictType.PRIORITY_CONFLICT:
            conflict = await self._check_priority_conflict(rule_1, rule_2, context)
        elif conflict_type == ConflictType.RESOURCE_CONFLICT:
            conflict = await self._check_resource_conflict(rule_1, rule_2, context)
        
        # Cache result
        self.conflict_cache[cache_key] = conflict
        
        return conflict
    
    async def _check_logical_contradiction(
        self,
        rule_1: PolicyRule,
        rule_2: PolicyRule,
        context: str
    ) -> Optional[ConflictDetectionResult]:
        """
        Check for logical contradictions between rules.
        """
        content_1 = rule_1.rule_content.lower()
        content_2 = rule_2.rule_content.lower()
        
        # Simple contradiction patterns
        contradictions = [
            ("allow", "deny"),
            ("permit", "forbid"),
            ("grant", "revoke"),
            ("enable", "disable"),
            ("true", "false")
        ]
        
        for pos, neg in contradictions:
            if pos in content_1 and neg in content_2:
                return ConflictDetectionResult(
                    conflict_id=f"logical_{rule_1.id}_{rule_2.id}",
                    conflict_type=ConflictType.LOGICAL_CONTRADICTION,
                    conflicting_rules=[rule_1.id, rule_2.id],
                    conflict_description=f"Logical contradiction: Rule {rule_1.id} contains '{pos}' while Rule {rule_2.id} contains '{neg}'",
                    severity="high",
                    resolution_suggestion="Review rule logic and resolve contradiction through priority ordering or condition refinement"
                )
            elif neg in content_1 and pos in content_2:
                return ConflictDetectionResult(
                    conflict_id=f"logical_{rule_1.id}_{rule_2.id}",
                    conflict_type=ConflictType.LOGICAL_CONTRADICTION,
                    conflicting_rules=[rule_1.id, rule_2.id],
                    conflict_description=f"Logical contradiction: Rule {rule_1.id} contains '{neg}' while Rule {rule_2.id} contains '{pos}'",
                    severity="high",
                    resolution_suggestion="Review rule logic and resolve contradiction through priority ordering or condition refinement"
                )
        
        return None
    
    async def _check_practical_incompatibility(
        self,
        rule_1: PolicyRule,
        rule_2: PolicyRule,
        context: str
    ) -> Optional[ConflictDetectionResult]:
        """
        Check for practical incompatibilities between rules.
        """
        content_1 = rule_1.rule_content.lower()
        content_2 = rule_2.rule_content.lower()
        
        # Check for incompatible requirements
        incompatibilities = [
            ("encryption", "plaintext"),
            ("synchronous", "asynchronous"),
            ("cached", "real_time"),
            ("public", "private")
        ]
        
        for req_1, req_2 in incompatibilities:
            if req_1 in content_1 and req_2 in content_2:
                return ConflictDetectionResult(
                    conflict_id=f"practical_{rule_1.id}_{rule_2.id}",
                    conflict_type=ConflictType.PRACTICAL_INCOMPATIBILITY,
                    conflicting_rules=[rule_1.id, rule_2.id],
                    conflict_description=f"Practical incompatibility: Rule {rule_1.id} requires '{req_1}' while Rule {rule_2.id} requires '{req_2}'",
                    severity="medium",
                    resolution_suggestion="Consider conditional application or rule prioritization to resolve incompatibility"
                )
        
        return None
    
    async def _check_priority_conflict(
        self,
        rule_1: PolicyRule,
        rule_2: PolicyRule,
        context: str
    ) -> Optional[ConflictDetectionResult]:
        """
        Check for priority conflicts between rules.
        """
        # Simulate priority conflict detection
        # In a real implementation, this would analyze rule priorities and overlapping conditions
        
        content_1 = rule_1.rule_content.lower()
        content_2 = rule_2.rule_content.lower()
        
        # Check for overlapping conditions with different actions
        if ("admin" in content_1 and "admin" in content_2 and 
            "access" in content_1 and "access" in content_2):
            
            return ConflictDetectionResult(
                conflict_id=f"priority_{rule_1.id}_{rule_2.id}",
                conflict_type=ConflictType.PRIORITY_CONFLICT,
                conflicting_rules=[rule_1.id, rule_2.id],
                conflict_description=f"Priority conflict: Rules {rule_1.id} and {rule_2.id} have overlapping conditions for admin access",
                severity="medium",
                resolution_suggestion="Establish clear priority ordering or refine rule conditions to eliminate overlap"
            )
        
        return None
    
    async def _check_resource_conflict(
        self,
        rule_1: PolicyRule,
        rule_2: PolicyRule,
        context: str
    ) -> Optional[ConflictDetectionResult]:
        """
        Check for resource conflicts between rules.
        """
        content_1 = rule_1.rule_content.lower()
        content_2 = rule_2.rule_content.lower()
        
        # Check for resource contention
        resources = ["database", "memory", "cpu", "network", "storage"]
        
        for resource in resources:
            if resource in content_1 and resource in content_2:
                if "exclusive" in content_1 or "exclusive" in content_2:
                    return ConflictDetectionResult(
                        conflict_id=f"resource_{rule_1.id}_{rule_2.id}",
                        conflict_type=ConflictType.RESOURCE_CONFLICT,
                        conflicting_rules=[rule_1.id, rule_2.id],
                        conflict_description=f"Resource conflict: Rules {rule_1.id} and {rule_2.id} both require exclusive access to {resource}",
                        severity="high",
                        resolution_suggestion="Implement resource scheduling or modify rules to allow shared access"
                    )
        
        return None
    
    def _generate_conflict_summary(self, conflicts: List[ConflictDetectionResult], rule_sets: List[str]) -> str:
        """
        Generate summary of conflict detection results.
        """
        total = len(conflicts)
        critical = sum(1 for c in conflicts if c.severity == "critical")
        high = sum(1 for c in conflicts if c.severity == "high")
        medium = sum(1 for c in conflicts if c.severity == "medium")
        
        summary = f"Conflict analysis for {len(rule_sets)} rule sets: {total} conflicts detected"
        
        if total > 0:
            summary += f" (Critical: {critical}, High: {high}, Medium: {medium})"
        
        return summary


# Global instances
safety_property_checker = SafetyPropertyChecker()
conflict_detector = ConflictDetector()
