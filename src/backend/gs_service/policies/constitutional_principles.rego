# Constitutional Principles Validation Policy
# Package: acgs.constitutional
#
# This policy validates governance rules against constitutional principles
# and ensures constitutional compliance in policy synthesis.
#
# Phase 2: Governance Synthesis Hardening with Rego/OPA Integration

package acgs.constitutional

import rego.v1

# Default deny for constitutional compliance
default allow_policy := false

# Default constitutional compliance score
default compliance_score := 0.0

# Constitutional principle categories
principle_categories := {
    "fairness",
    "transparency", 
    "accountability",
    "privacy",
    "safety",
    "non_discrimination",
    "human_dignity",
    "democratic_governance"
}

# Core constitutional principles that must be satisfied
core_principles := {
    "human_dignity": {
        "description": "Respect for human dignity and fundamental rights",
        "weight": 1.0,
        "mandatory": true
    },
    "fairness": {
        "description": "Fair treatment and equal opportunity",
        "weight": 0.9,
        "mandatory": true
    },
    "transparency": {
        "description": "Transparent decision-making processes",
        "weight": 0.8,
        "mandatory": false
    },
    "accountability": {
        "description": "Clear accountability mechanisms",
        "weight": 0.8,
        "mandatory": false
    },
    "privacy": {
        "description": "Protection of personal privacy",
        "weight": 0.9,
        "mandatory": true
    }
}

# Allow policy if it meets constitutional requirements
allow_policy if {
    input.policy_type in {"governance_rule", "operational_rule", "constitutional_principle"}
    constitutional_compliance_check
    no_constitutional_violations
    meets_minimum_compliance_score
}

# Check constitutional compliance
constitutional_compliance_check if {
    # Policy must reference constitutional principles
    count(input.constitutional_principles) > 0
    
    # Policy must not contradict core principles
    not contradicts_core_principles
    
    # Policy must have valid governance context
    valid_governance_context
}

# Check for constitutional violations
no_constitutional_violations if {
    not violates_human_dignity
    not violates_fairness
    not violates_privacy
    not enables_discrimination
}

# Check if policy contradicts core principles
contradicts_core_principles if {
    some principle_id
    core_principles[principle_id]
    principle := core_principles[principle_id]
    principle.mandatory == true
    not principle_satisfied(principle_id)
}

# Check if a specific principle is satisfied
principle_satisfied(principle_id) if {
    some ref_principle
    input.constitutional_principles[_] == ref_principle
    contains(lower(ref_principle.description), principle_id)
}

principle_satisfied(principle_id) if {
    some policy_text
    policy_text := input.policy_content
    contains(lower(policy_text), principle_id)
}

# Validate governance context
valid_governance_context if {
    input.context.governance_type in {"constitutional", "operational", "procedural"}
    input.context.target_system != ""
    input.context.scope in {"global", "local", "domain_specific"}
}

# Human dignity violation checks
violates_human_dignity if {
    contains(lower(input.policy_content), "dehumaniz")
}

violates_human_dignity if {
    contains(lower(input.policy_content), "discriminat")
    not contains(lower(input.policy_content), "anti-discriminat")
    not contains(lower(input.policy_content), "prevent discriminat")
}

# Fairness violation checks
violates_fairness if {
    contains(lower(input.policy_content), "unfair")
}

violates_fairness if {
    contains(lower(input.policy_content), "bias")
    not contains(lower(input.policy_content), "anti-bias")
    not contains(lower(input.policy_content), "prevent bias")
}

# Privacy violation checks
violates_privacy if {
    contains(lower(input.policy_content), "collect all data")
}

violates_privacy if {
    contains(lower(input.policy_content), "no privacy")
}

# Discrimination enablement checks
enables_discrimination if {
    contains(lower(input.policy_content), "discriminate against")
}

enables_discrimination if {
    contains(lower(input.policy_content), "exclude based on")
    not contains(lower(input.policy_content), "exclude based on merit")
    not contains(lower(input.policy_content), "exclude based on qualification")
}

# Calculate compliance score
compliance_score := score if {
    scores := [principle_score |
        some principle_id
        core_principles[principle_id]
        principle := core_principles[principle_id]
        principle_score := calculate_principle_score(principle_id, principle)
    ]
    score := sum(scores) / count(scores)
}

# Calculate score for individual principle
calculate_principle_score(principle_id, principle) := score if {
    principle_satisfied(principle_id)
    score := principle.weight
}

calculate_principle_score(principle_id, principle) := score if {
    not principle_satisfied(principle_id)
    principle.mandatory == true
    score := 0.0
}

calculate_principle_score(principle_id, principle) := score if {
    not principle_satisfied(principle_id)
    principle.mandatory == false
    score := principle.weight * 0.5  # Partial credit for non-mandatory principles
}

# Minimum compliance score requirement
meets_minimum_compliance_score if {
    compliance_score >= 0.7
}

# Policy recommendations for improvement
policy_recommendations := recommendations if {
    recommendations := [recommendation |
        some principle_id
        core_principles[principle_id]
        principle := core_principles[principle_id]
        not principle_satisfied(principle_id)
        recommendation := sprintf("Consider addressing %s: %s", [principle_id, principle.description])
    ]
}

# Constitutional compliance report
compliance_report := {
    "allowed": allow_policy,
    "compliance_score": compliance_score,
    "constitutional_violations": constitutional_violations,
    "recommendations": policy_recommendations,
    "principle_scores": principle_scores
}

# Detailed constitutional violations
constitutional_violations := violations if {
    violations := [violation |
        violation_checks := [
            {"type": "human_dignity", "violated": violates_human_dignity},
            {"type": "fairness", "violated": violates_fairness},
            {"type": "privacy", "violated": violates_privacy},
            {"type": "discrimination", "violated": enables_discrimination}
        ]
        some check
        violation_checks[_] == check
        check.violated == true
        violation := check.type
    ]
}

# Individual principle scores
principle_scores := scores if {
    scores := {principle_id: calculate_principle_score(principle_id, principle) |
        some principle_id
        core_principles[principle_id]
        principle := core_principles[principle_id]
    }
}
