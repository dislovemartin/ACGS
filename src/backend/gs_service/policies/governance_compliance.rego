# Governance Compliance Checking Policy
# Package: acgs.compliance
#
# This policy provides comprehensive compliance checking against established
# governance rules and regulatory requirements.
#
# Phase 2: Governance Synthesis Hardening with Rego/OPA Integration

package acgs.compliance

import rego.v1

# Default compliance decisions
default compliant := false
default compliance_score := 0.0
default requires_review := false

# Compliance categories
compliance_categories := {
    "constitutional",
    "regulatory", 
    "operational",
    "ethical",
    "security",
    "privacy"
}

# Compliance requirements by category
compliance_requirements := {
    "constitutional": {
        "human_rights_protection": {"weight": 1.0, "mandatory": true},
        "democratic_principles": {"weight": 0.9, "mandatory": true},
        "rule_of_law": {"weight": 1.0, "mandatory": true},
        "separation_of_powers": {"weight": 0.8, "mandatory": false}
    },
    "regulatory": {
        "data_protection": {"weight": 0.9, "mandatory": true},
        "algorithmic_transparency": {"weight": 0.8, "mandatory": false},
        "audit_requirements": {"weight": 0.7, "mandatory": false},
        "reporting_obligations": {"weight": 0.6, "mandatory": false}
    },
    "operational": {
        "performance_standards": {"weight": 0.7, "mandatory": false},
        "resource_constraints": {"weight": 0.6, "mandatory": false},
        "scalability_requirements": {"weight": 0.5, "mandatory": false},
        "maintenance_procedures": {"weight": 0.5, "mandatory": false}
    },
    "ethical": {
        "fairness_principles": {"weight": 0.9, "mandatory": true},
        "bias_prevention": {"weight": 0.9, "mandatory": true},
        "transparency_requirements": {"weight": 0.8, "mandatory": false},
        "accountability_mechanisms": {"weight": 0.8, "mandatory": false}
    },
    "security": {
        "access_controls": {"weight": 0.9, "mandatory": true},
        "data_encryption": {"weight": 0.8, "mandatory": true},
        "vulnerability_management": {"weight": 0.7, "mandatory": false},
        "incident_response": {"weight": 0.7, "mandatory": false}
    },
    "privacy": {
        "data_minimization": {"weight": 0.9, "mandatory": true},
        "consent_management": {"weight": 0.9, "mandatory": true},
        "purpose_limitation": {"weight": 0.8, "mandatory": true},
        "retention_policies": {"weight": 0.7, "mandatory": false}
    }
}

# Main compliance check
compliant if {
    valid_compliance_input
    meets_mandatory_requirements
    achieves_minimum_compliance_score
    no_critical_violations
}

# Validate compliance input
valid_compliance_input if {
    # Required fields
    input.policy_content != ""
    input.compliance_context.category in compliance_categories
    input.compliance_context.jurisdiction != ""
    
    # Governance context
    input.governance_context.system_type != ""
    input.governance_context.risk_level in {"low", "medium", "high", "critical"}
}

# Check mandatory requirements
meets_mandatory_requirements if {
    category := input.compliance_context.category
    requirements := compliance_requirements[category]
    
    every requirement_id, requirement in requirements {
        requirement.mandatory == false
    }
}

meets_mandatory_requirements if {
    category := input.compliance_context.category
    requirements := compliance_requirements[category]
    
    every requirement_id, requirement in requirements {
        requirement.mandatory == true
        requirement_satisfied(requirement_id, requirement)
    }
}

# Check if specific requirement is satisfied
requirement_satisfied(requirement_id, requirement) if {
    # Check policy content for requirement keywords
    requirement_keywords := get_requirement_keywords(requirement_id)
    some keyword
    requirement_keywords[_] == keyword
    contains(lower(input.policy_content), keyword)
}

requirement_satisfied(requirement_id, requirement) if {
    # Check explicit compliance declarations
    some declaration
    input.compliance_declarations[_] == declaration
    declaration.requirement_id == requirement_id
    declaration.status == "satisfied"
}

# Get keywords for requirement checking
get_requirement_keywords(requirement_id) := keywords if {
    keyword_map := {
        "human_rights_protection": ["human rights", "fundamental rights", "dignity"],
        "democratic_principles": ["democratic", "participation", "representation"],
        "rule_of_law": ["legal", "lawful", "constitutional"],
        "data_protection": ["data protection", "privacy", "personal data"],
        "algorithmic_transparency": ["transparent", "explainable", "interpretable"],
        "fairness_principles": ["fair", "equitable", "unbiased"],
        "bias_prevention": ["bias", "discrimination", "prejudice"],
        "access_controls": ["access control", "authorization", "authentication"],
        "data_encryption": ["encrypt", "secure", "protection"],
        "data_minimization": ["minimal", "necessary", "proportionate"],
        "consent_management": ["consent", "permission", "authorization"]
    }
    keywords := keyword_map[requirement_id]
}

get_requirement_keywords(requirement_id) := [] if {
    # Default empty keywords for unmapped requirements
    not requirement_id in {
        "human_rights_protection", "democratic_principles", "rule_of_law",
        "data_protection", "algorithmic_transparency", "fairness_principles",
        "bias_prevention", "access_controls", "data_encryption",
        "data_minimization", "consent_management"
    }
}

# Calculate compliance score
compliance_score := score if {
    category := input.compliance_context.category
    requirements := compliance_requirements[category]
    
    scores := [weighted_score |
        some requirement_id, requirement
        requirements[requirement_id] == requirement
        satisfied := requirement_satisfied(requirement_id, requirement)
        base_score := 1.0 if satisfied else 0.0
        weighted_score := base_score * requirement.weight
    ]
    
    total_weight := sum([requirement.weight |
        some requirement_id, requirement
        requirements[requirement_id] == requirement
    ])
    
    score := sum(scores) / total_weight if total_weight > 0 else 0.0
}

# Minimum compliance score threshold
achieves_minimum_compliance_score if {
    risk_level := input.governance_context.risk_level
    min_score := get_minimum_score(risk_level)
    compliance_score >= min_score
}

# Get minimum score based on risk level
get_minimum_score(risk_level) := 0.95 if risk_level == "critical"
get_minimum_score(risk_level) := 0.85 if risk_level == "high"
get_minimum_score(risk_level) := 0.75 if risk_level == "medium"
get_minimum_score(risk_level) := 0.65 if risk_level == "low"

# Critical violation checks
no_critical_violations if {
    not has_constitutional_violations
    not has_regulatory_violations
    not has_security_violations
    not has_privacy_violations
}

# Constitutional violation detection
has_constitutional_violations if {
    violates_human_rights
}

has_constitutional_violations if {
    violates_democratic_principles
}

has_constitutional_violations if {
    violates_rule_of_law
}

# Regulatory violation detection
has_regulatory_violations if {
    violates_data_protection_laws
}

has_regulatory_violations if {
    violates_transparency_requirements
}

# Security violation detection
has_security_violations if {
    inadequate_access_controls
}

has_security_violations if {
    insufficient_data_protection
}

# Privacy violation detection
has_privacy_violations if {
    violates_data_minimization
}

has_privacy_violations if {
    inadequate_consent_mechanisms
}

# Specific violation checks
violates_human_rights if {
    contains(lower(input.policy_content), "violate human rights")
}

violates_human_rights if {
    contains(lower(input.policy_content), "ignore fundamental rights")
}

violates_democratic_principles if {
    contains(lower(input.policy_content), "bypass democratic process")
}

violates_rule_of_law if {
    contains(lower(input.policy_content), "ignore legal requirements")
}

violates_data_protection_laws if {
    contains(lower(input.policy_content), "collect all personal data")
    not contains(lower(input.policy_content), "with consent")
}

violates_transparency_requirements if {
    contains(lower(input.policy_content), "secret algorithm")
    input.compliance_context.requires_transparency == true
}

inadequate_access_controls if {
    contains(lower(input.policy_content), "open access")
    not contains(lower(input.policy_content), "controlled access")
    input.governance_context.risk_level in {"high", "critical"}
}

insufficient_data_protection if {
    contains(lower(input.policy_content), "unencrypted")
    input.governance_context.handles_sensitive_data == true
}

violates_data_minimization if {
    contains(lower(input.policy_content), "collect maximum data")
}

inadequate_consent_mechanisms if {
    contains(lower(input.policy_content), "implied consent")
    input.compliance_context.requires_explicit_consent == true
}

# Review requirements
requires_review if {
    compliance_score < 0.8
}

requires_review if {
    has_potential_violations
}

requires_review if {
    input.governance_context.risk_level == "critical"
    compliance_score < 0.95
}

# Potential violation detection
has_potential_violations if {
    contains(lower(input.policy_content), "may violate")
}

has_potential_violations if {
    contains(lower(input.policy_content), "potentially problematic")
}

# Compliance recommendations
compliance_recommendations := recommendations if {
    recommendations := [recommendation |
        category := input.compliance_context.category
        requirements := compliance_requirements[category]
        some requirement_id, requirement
        requirements[requirement_id] == requirement
        not requirement_satisfied(requirement_id, requirement)
        recommendation := sprintf("Address %s requirement: %s", [
            requirement_id,
            get_requirement_description(requirement_id)
        ])
    ]
}

# Get requirement descriptions
get_requirement_description(requirement_id) := description if {
    descriptions := {
        "human_rights_protection": "Ensure protection of fundamental human rights",
        "democratic_principles": "Incorporate democratic participation mechanisms",
        "rule_of_law": "Comply with legal and constitutional requirements",
        "data_protection": "Implement data protection and privacy safeguards",
        "algorithmic_transparency": "Provide algorithmic transparency and explainability",
        "fairness_principles": "Ensure fair and equitable treatment",
        "bias_prevention": "Implement bias prevention and mitigation measures",
        "access_controls": "Establish proper access control mechanisms",
        "data_encryption": "Implement data encryption and security measures",
        "data_minimization": "Apply data minimization principles",
        "consent_management": "Implement proper consent management"
    }
    description := descriptions[requirement_id]
}

get_requirement_description(requirement_id) := "Address compliance requirement" if {
    # Default description for unmapped requirements
    not requirement_id in {
        "human_rights_protection", "democratic_principles", "rule_of_law",
        "data_protection", "algorithmic_transparency", "fairness_principles",
        "bias_prevention", "access_controls", "data_encryption",
        "data_minimization", "consent_management"
    }
}

# Compliance report
compliance_report := {
    "compliant": compliant,
    "compliance_score": compliance_score,
    "requires_review": requires_review,
    "category_scores": category_scores,
    "violations": compliance_violations,
    "recommendations": compliance_recommendations,
    "risk_assessment": risk_assessment
}

# Category-specific scores
category_scores := scores if {
    category := input.compliance_context.category
    requirements := compliance_requirements[category]
    scores := {requirement_id: requirement_score |
        some requirement_id, requirement
        requirements[requirement_id] == requirement
        satisfied := requirement_satisfied(requirement_id, requirement)
        requirement_score := requirement.weight if satisfied else 0.0
    }
}

# Compliance violations summary
compliance_violations := {
    "constitutional": has_constitutional_violations,
    "regulatory": has_regulatory_violations,
    "security": has_security_violations,
    "privacy": has_privacy_violations,
    "critical_violations": not no_critical_violations
}

# Risk assessment
risk_assessment := {
    "risk_level": input.governance_context.risk_level,
    "minimum_required_score": get_minimum_score(input.governance_context.risk_level),
    "current_score": compliance_score,
    "meets_risk_threshold": achieves_minimum_compliance_score,
    "requires_additional_review": requires_review
}
