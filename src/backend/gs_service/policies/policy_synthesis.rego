# Policy Synthesis Validation and Conflict Detection
# Package: acgs.synthesis
#
# This policy validates synthesized policies for conflicts, consistency,
# and quality requirements in the governance synthesis process.
#
# Phase 2: Governance Synthesis Hardening with Rego/OPA Integration

package acgs.synthesis

import rego.v1

# Default decisions
default allow_synthesis := false
default has_conflicts := false
default synthesis_quality_score := 0.0

# Policy synthesis validation rules
allow_synthesis if {
    valid_synthesis_input
    no_policy_conflicts
    meets_quality_requirements
    passes_consistency_checks
}

# Validate synthesis input
valid_synthesis_input if {
    # Required fields present
    input.synthesis_goal != ""
    input.policy_type in {"constitutional_principle", "operational_rule", "governance_rule"}
    input.target_format in {"rego", "datalog", "json", "yaml"}
    
    # Constitutional principles provided
    count(input.constitutional_principles) > 0
    
    # Valid context data
    input.context_data.target_system != ""
    input.context_data.governance_type != ""
}

# Policy conflict detection
no_policy_conflicts if {
    not has_logical_conflicts
    not has_semantic_conflicts
    not has_priority_conflicts
    not has_scope_conflicts
}

# Logical conflict detection
has_logical_conflicts if {
    # Check for contradictory rules
    some rule1, rule2
    input.existing_policies[rule1]
    input.existing_policies[rule2]
    rule1 != rule2
    contradictory_rules(input.existing_policies[rule1], input.existing_policies[rule2])
}

has_logical_conflicts if {
    # Check new policy against existing policies
    some existing_rule
    input.existing_policies[existing_rule]
    contradictory_with_new_policy(input.existing_policies[existing_rule])
}

# Semantic conflict detection
has_semantic_conflicts if {
    # Check for semantic inconsistencies
    some principle1, principle2
    input.constitutional_principles[principle1]
    input.constitutional_principles[principle2]
    principle1 != principle2
    semantically_inconsistent(
        input.constitutional_principles[principle1],
        input.constitutional_principles[principle2]
    )
}

# Priority conflict detection
has_priority_conflicts if {
    # Check for conflicting priorities
    some policy1, policy2
    input.existing_policies[policy1]
    input.existing_policies[policy2]
    policy1 != policy2
    conflicting_priorities(input.existing_policies[policy1], input.existing_policies[policy2])
}

# Scope conflict detection
has_scope_conflicts if {
    # Check for overlapping scopes with different rules
    some policy1, policy2
    input.existing_policies[policy1]
    input.existing_policies[policy2]
    policy1 != policy2
    overlapping_scopes(input.existing_policies[policy1], input.existing_policies[policy2])
    different_decisions(input.existing_policies[policy1], input.existing_policies[policy2])
}

# Quality requirements
meets_quality_requirements if {
    synthesis_quality_score >= 0.8
    has_clear_semantics
    has_measurable_outcomes
    has_enforcement_mechanisms
}

# Consistency checks
passes_consistency_checks if {
    consistent_with_constitutional_principles
    consistent_with_governance_framework
    consistent_with_existing_policies
}

# Helper functions for conflict detection

# Check if two rules are contradictory
contradictory_rules(rule1, rule2) if {
    rule1.action == "allow"
    rule2.action == "deny"
    same_subject_and_resource(rule1, rule2)
}

contradictory_rules(rule1, rule2) if {
    rule1.effect == "permit"
    rule2.effect == "deny"
    overlapping_conditions(rule1, rule2)
}

# Check if new policy contradicts existing rule
contradictory_with_new_policy(existing_rule) if {
    contains(lower(input.policy_content), "allow")
    existing_rule.action == "deny"
    policy_applies_to_same_context(existing_rule)
}

contradictory_with_new_policy(existing_rule) if {
    contains(lower(input.policy_content), "deny")
    existing_rule.action == "allow"
    policy_applies_to_same_context(existing_rule)
}

# Check semantic inconsistency
semantically_inconsistent(principle1, principle2) if {
    principle1.category == principle2.category
    principle1.direction != principle2.direction
    principle1.scope == principle2.scope
}

# Check conflicting priorities
conflicting_priorities(policy1, policy2) if {
    policy1.priority == policy2.priority
    policy1.action != policy2.action
    overlapping_conditions(policy1, policy2)
}

# Check overlapping scopes
overlapping_scopes(policy1, policy2) if {
    policy1.scope.domain == policy2.scope.domain
    policy1.scope.context == policy2.scope.context
}

# Check different decisions
different_decisions(policy1, policy2) if {
    policy1.action != policy2.action
}

different_decisions(policy1, policy2) if {
    policy1.effect != policy2.effect
}

# Check same subject and resource
same_subject_and_resource(rule1, rule2) if {
    rule1.subject == rule2.subject
    rule1.resource == rule2.resource
}

# Check overlapping conditions
overlapping_conditions(rule1, rule2) if {
    rule1.conditions.context == rule2.conditions.context
    rule1.conditions.scope == rule2.conditions.scope
}

# Check if policy applies to same context
policy_applies_to_same_context(existing_rule) if {
    existing_rule.context.target_system == input.context_data.target_system
    existing_rule.context.governance_type == input.context_data.governance_type
}

# Quality assessment functions

# Calculate synthesis quality score
synthesis_quality_score := score if {
    quality_factors := [
        clarity_score,
        completeness_score,
        consistency_score,
        enforceability_score
    ]
    score := sum(quality_factors) / count(quality_factors)
}

# Clarity score
clarity_score := 1.0 if {
    has_clear_semantics
}

clarity_score := 0.5 if {
    not has_clear_semantics
    input.policy_content != ""
}

clarity_score := 0.0 if {
    input.policy_content == ""
}

# Completeness score
completeness_score := 1.0 if {
    has_all_required_components
}

completeness_score := 0.7 if {
    has_most_required_components
}

completeness_score := 0.3 if {
    has_some_required_components
}

completeness_score := 0.0 if {
    not has_some_required_components
}

# Consistency score
consistency_score := 1.0 if {
    passes_consistency_checks
}

consistency_score := 0.0 if {
    not passes_consistency_checks
}

# Enforceability score
enforceability_score := 1.0 if {
    has_enforcement_mechanisms
}

enforceability_score := 0.5 if {
    has_partial_enforcement_mechanisms
}

enforceability_score := 0.0 if {
    not has_partial_enforcement_mechanisms
}

# Quality check functions
has_clear_semantics if {
    input.policy_content != ""
    not contains(lower(input.policy_content), "unclear")
    not contains(lower(input.policy_content), "ambiguous")
}

has_measurable_outcomes if {
    contains(lower(input.policy_content), "measur")
    contains(lower(input.policy_content), "metric")
}

has_measurable_outcomes if {
    contains(lower(input.policy_content), "quantif")
}

has_enforcement_mechanisms if {
    contains(lower(input.policy_content), "enforce")
    contains(lower(input.policy_content), "penalty")
}

has_enforcement_mechanisms if {
    contains(lower(input.policy_content), "sanction")
}

has_partial_enforcement_mechanisms if {
    contains(lower(input.policy_content), "monitor")
}

has_partial_enforcement_mechanisms if {
    contains(lower(input.policy_content), "audit")
}

# Component completeness checks
has_all_required_components if {
    has_policy_statement
    has_scope_definition
    has_enforcement_clause
    has_exception_handling
}

has_most_required_components if {
    has_policy_statement
    has_scope_definition
    has_enforcement_clause
}

has_some_required_components if {
    has_policy_statement
    has_scope_definition
}

has_policy_statement if {
    contains(lower(input.policy_content), "policy")
    contains(lower(input.policy_content), "rule")
}

has_scope_definition if {
    contains(lower(input.policy_content), "scope")
    contains(lower(input.policy_content), "applies to")
}

has_enforcement_clause if {
    contains(lower(input.policy_content), "enforce")
    contains(lower(input.policy_content), "violation")
}

has_exception_handling if {
    contains(lower(input.policy_content), "except")
    contains(lower(input.policy_content), "unless")
}

# Consistency check functions
consistent_with_constitutional_principles if {
    every principle in input.constitutional_principles {
        not violates_principle(principle)
    }
}

consistent_with_governance_framework if {
    input.context_data.governance_type in {"constitutional", "operational", "procedural"}
    not contradicts_framework_principles
}

consistent_with_existing_policies if {
    every policy in input.existing_policies {
        not contradictory_with_policy(policy)
    }
}

# Violation checks
violates_principle(principle) if {
    principle.type == "prohibition"
    contains(lower(input.policy_content), lower(principle.prohibited_action))
}

contradicts_framework_principles if {
    input.context_data.governance_type == "constitutional"
    contains(lower(input.policy_content), "violate constitution")
}

contradictory_with_policy(existing_policy) if {
    existing_policy.action == "allow"
    contains(lower(input.policy_content), "deny")
    policy_applies_to_same_context(existing_policy)
}

# Synthesis result summary
synthesis_result := {
    "allowed": allow_synthesis,
    "quality_score": synthesis_quality_score,
    "has_conflicts": has_conflicts,
    "conflict_details": conflict_details,
    "quality_assessment": quality_assessment,
    "recommendations": synthesis_recommendations
}

# Conflict details
conflict_details := {
    "logical_conflicts": has_logical_conflicts,
    "semantic_conflicts": has_semantic_conflicts,
    "priority_conflicts": has_priority_conflicts,
    "scope_conflicts": has_scope_conflicts
}

# Quality assessment details
quality_assessment := {
    "clarity_score": clarity_score,
    "completeness_score": completeness_score,
    "consistency_score": consistency_score,
    "enforceability_score": enforceability_score
}

# Synthesis recommendations
synthesis_recommendations := recommendations if {
    recommendations := [recommendation |
        improvement_areas := [
            {"condition": not has_clear_semantics, "message": "Improve policy clarity and semantic precision"},
            {"condition": not has_measurable_outcomes, "message": "Add measurable outcomes and success metrics"},
            {"condition": not has_enforcement_mechanisms, "message": "Define enforcement mechanisms and penalties"},
            {"condition": has_conflicts, "message": "Resolve policy conflicts before implementation"},
            {"condition": synthesis_quality_score < 0.8, "message": "Improve overall policy quality"}
        ]
        some area
        improvement_areas[_] == area
        area.condition == true
        recommendation := area.message
    ]
}
