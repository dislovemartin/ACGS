# Governance Synthesis Service (GS Service) API Documentation

## Overview

The GS Service generates policies using LLM integration with constitutional prompting, contextual analysis, and AlphaEvolve integration for evolutionary computation governance.

**Base URL:** `http://localhost:8000/api/gs/`
**Interactive Docs:** `http://localhost:8000/api/gs/docs`

## Authentication

All endpoints require JWT authentication with appropriate role permissions:
- **Admin:** Full access to all operations
- **Policy Manager:** Access to policy synthesis and management
- **Auditor:** Read-only access to synthesis logs

## Core Policy Synthesis

### POST /synthesize
Generate policies from constitutional principles using LLM integration.

**Request Body:**
```json
{
  "context": "autonomous_vehicle_safety",
  "requirements": [
    "Ensure passenger safety",
    "Minimize environmental impact",
    "Comply with traffic regulations"
  ],
  "target_format": "datalog",
  "constitutional_guidance": true,
  "environmental_factors": {
    "deployment_environment": "urban",
    "risk_level": "high",
    "regulatory_framework": "EU_AI_Act"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "synthesis_id": "synth_123456",
    "policies": [
      {
        "id": "policy_001",
        "content": "safety_check(Vehicle, Context) :- speed_limit_check(Vehicle, Context), obstacle_detection(Vehicle), emergency_brake_available(Vehicle).",
        "format": "datalog",
        "confidence_score": 0.92,
        "constitutional_basis": [
          {
            "principle_id": 1,
            "relevance_score": 0.95,
            "application": "Safety override mechanism"
          }
        ]
      }
    ],
    "synthesis_metadata": {
      "llm_model": "gpt-4",
      "processing_time_ms": 1250,
      "constitutional_principles_used": 3,
      "environmental_factors_considered": 5
    }
  }
}
```

### GET /synthesis/{synthesis_id}
Retrieve details of a previous synthesis operation.

### GET /synthesis
List synthesis operations with filtering options.

**Query Parameters:**
- `context` (str): Filter by context
- `status` (str): Filter by status (pending, completed, failed)
- `date_from` (str): Filter by date range
- `date_to` (str): Filter by date range

## Constitutional Prompting

### POST /constitutional-synthesis
Perform constitutional prompting for policy generation.

**Request Body:**
```json
{
  "context": "data_privacy_protection",
  "policy_requirements": {
    "data_types": ["personal", "sensitive"],
    "processing_purposes": ["analytics", "personalization"],
    "retention_period": "2_years"
  },
  "constitutional_constraints": [
    "minimize_data_collection",
    "explicit_consent_required",
    "right_to_deletion"
  ]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "constitutional_guidance": "Based on privacy principles, implement data minimization and consent mechanisms",
    "generated_policies": [...],
    "constitutional_compliance_score": 0.88,
    "recommendations": [
      "Add explicit consent validation",
      "Implement automated data deletion"
    ]
  }
}
```

### POST /contextual-analysis
Analyze environmental factors for constitutional policy synthesis.

**Request Body:**
```json
{
  "context": "healthcare_ai_diagnosis",
  "environmental_factors": {
    "regulatory_environment": "HIPAA_compliant",
    "risk_assessment": "high",
    "stakeholder_groups": ["patients", "doctors", "hospitals"],
    "technical_constraints": ["real_time_processing", "high_accuracy"]
  }
}
```

## AlphaEvolve Integration

### POST /alphaevolve/constitutional-prompting
Perform constitutional prompting for evolutionary computation systems.

**Request Body:**
```json
{
  "ec_context": "neural_architecture_search",
  "current_population": [
    {
      "individual_id": "ind_001",
      "fitness_score": 0.85,
      "generation": 10,
      "code_representation": "conv2d(32) -> relu -> maxpool -> dense(10)",
      "fitness_context": "image_classification"
    }
  ],
  "optimization_objective": "maximize_accuracy_minimize_bias",
  "constitutional_constraints": [
    "fairness_across_demographics",
    "interpretability_required",
    "energy_efficiency"
  ]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "prompting_id": "ec_prompt_789",
    "constitutional_guidance": "Ensure fairness metrics are integrated into fitness evaluation",
    "fitness_modifications": {
      "fairness_penalty": 0.1,
      "interpretability_bonus": 0.05,
      "energy_efficiency_weight": 0.15
    },
    "operator_constraints": {
      "mutation_rate_limits": {"min": 0.01, "max": 0.1},
      "crossover_restrictions": ["preserve_fairness_components"]
    },
    "population_filters": {
      "bias_threshold": 0.05,
      "interpretability_minimum": 0.7
    }
  }
}
```

### POST /alphaevolve/governance-evaluation
Evaluate evolutionary computation proposals for constitutional compliance.

**Request Body:**
```json
{
  "context": "automated_trading_system",
  "proposals": [
    {
      "proposal_id": "prop_001",
      "individual_id": "ind_123",
      "fitness_score": 0.92,
      "generation": 15,
      "code_representation": "trading_strategy_code",
      "fitness_context": "risk_adjusted_returns"
    }
  ]
}
```

## LLM Integration Management

### GET /llm/models
List available LLM models and their capabilities.

**Response:**
```json
{
  "success": true,
  "data": {
    "models": [
      {
        "model_id": "gpt-4",
        "capabilities": ["constitutional_prompting", "policy_synthesis"],
        "max_tokens": 8192,
        "cost_per_token": 0.00003,
        "availability": "available"
      }
    ]
  }
}
```

### POST /llm/configure
Configure LLM integration settings (Admin only).

### GET /llm/usage-stats
Get LLM usage statistics and costs.

## Policy Templates

### GET /templates
Retrieve policy templates for different contexts.

**Query Parameters:**
- `context` (str): Filter by context
- `format` (str): Filter by format (datalog, rego, json)

### POST /templates
Create a new policy template.

### POST /templates/{template_id}/instantiate
Instantiate a policy template with specific parameters.

## Validation and Testing

### POST /validate-synthesis
Validate synthesized policies before deployment.

**Request Body:**
```json
{
  "policies": [...],
  "validation_criteria": {
    "syntax_check": true,
    "constitutional_compliance": true,
    "conflict_detection": true
  }
}
```

### POST /test-synthesis
Test policy synthesis with sample data.

## Monitoring and Analytics

### GET /metrics
Get synthesis service metrics.

**Response:**
```json
{
  "success": true,
  "data": {
    "total_syntheses": 1250,
    "success_rate": 0.94,
    "average_processing_time_ms": 1100,
    "constitutional_compliance_rate": 0.89,
    "llm_usage": {
      "total_tokens": 2500000,
      "cost_usd": 75.00
    }
  }
}
```

### GET /synthesis-logs
Retrieve synthesis operation logs.

## Error Handling

### Common Error Codes
- `400 Bad Request`: Invalid synthesis parameters
- `401 Unauthorized`: Missing authentication
- `403 Forbidden`: Insufficient permissions
- `422 Unprocessable Entity`: LLM processing errors
- `429 Too Many Requests`: Rate limit exceeded
- `503 Service Unavailable`: LLM service unavailable

### Example Error Response
```json
{
  "success": false,
  "error": {
    "code": "LLM_PROCESSING_ERROR",
    "message": "Failed to generate constitutional guidance",
    "details": {
      "llm_model": "gpt-4",
      "error_type": "token_limit_exceeded",
      "suggested_action": "Reduce input size or use chunking"
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Rate Limiting

- **Policy synthesis:** 10 requests per minute per user
- **Constitutional prompting:** 20 requests per minute per user
- **AlphaEvolve operations:** 50 requests per minute per user
- **Template operations:** 100 requests per minute per user

## Webhooks

### Available Events
- `synthesis.started`
- `synthesis.completed`
- `synthesis.failed`
- `constitutional.guidance.generated`
- `alphaevolve.evaluation.completed`

For complete API reference, visit the interactive documentation at `http://localhost:8000/api/gs/docs`.
