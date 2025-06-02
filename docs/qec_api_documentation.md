# QEC-Enhanced AlphaEvolve-ACGS API Documentation

## Overview

The QEC (Quality, Error, and Correction) enhancement system provides intelligent conflict resolution, constitutional fidelity monitoring, and automated patch generation for the AlphaEvolve-ACGS framework. This document describes the API endpoints, data structures, and integration patterns.

## Core Components

### 1. Constitutional Distance Calculator
Measures the robustness of constitutional principles using language ambiguity analysis, criteria formality assessment, and historical success rate tracking.

### 2. Error Prediction Model
Predicts potential synthesis challenges using historical patterns and principle characteristics, enabling proactive mitigation and faster recovery.

### 3. Recovery Strategy Dispatcher
Provides intelligent recovery strategy selection with 8 configurable strategies for different failure types, including performance tracking and strategy optimization.

### 4. Constitutional Fidelity Monitor
Implements system-wide health monitoring with composite scoring across 6 components and real-time alert management.

### 5. Validation DSL Parser
Transforms natural language validation criteria into machine-actionable test specifications with support for multiple output formats.

## API Endpoints

### Conflict Resolution Endpoints

#### Create Conflict Resolution with QEC Enhancement
```http
POST /api/v1/conflict-resolution/
Content-Type: application/json
Authorization: Bearer <token>

{
  "conflict_type": "principle_contradiction",
  "principle_ids": [1, 2],
  "context": "privacy_vs_security_testing",
  "conflict_description": "Privacy protection conflicts with security monitoring requirements",
  "severity": "high",
  "resolution_strategy": "weighted_priority",
  "resolution_details": {
    "weights": {"privacy": 0.6, "security": 0.4}
  },
  "precedence_order": [1, 2]
}
```

**Response:**
```json
{
  "id": 1,
  "conflict_type": "principle_contradiction",
  "principle_ids": [1, 2],
  "status": "analyzed",
  "qec_analysis": {
    "constitutional_distances": [0.75, 0.82],
    "average_distance": 0.785,
    "error_predictions": [
      {
        "principle_id": "1",
        "overall_risk": 0.4,
        "failure_predictions": {
          "semantic_conflict": 0.3,
          "ambiguous_principle": 0.2
        },
        "recommended_strategy": "enhanced_validation",
        "confidence": 0.8
      }
    ],
    "recommended_strategy": "weighted_priority",
    "validation_scenarios": [
      {
        "principle_id": "1",
        "scenario_type": "privacy_check",
        "test_cases": 3
      }
    ],
    "priority_score": 0.7,
    "qec_metadata": {
      "analysis_timestamp": "2024-01-15T14:30:00Z",
      "processing_time_ms": 250
    }
  }
}
```

#### Generate Automated Patch
```http
POST /api/v1/conflict-resolution/{conflict_id}/generate-patch
Authorization: Bearer <token>
```

**Response:**
```json
{
  "conflict_id": 1,
  "patch_generated": true,
  "strategy_used": "weighted_priority",
  "confidence_score": 0.85,
  "patch_content": {
    "resolution_approach": "contextual_balancing",
    "modified_principles": [
      {
        "principle_id": 1,
        "modifications": ["scope_refinement", "exception_clause"]
      }
    ],
    "validation_tests": [
      "privacy_compliance_check",
      "security_effectiveness_test"
    ]
  },
  "metadata": {
    "generation_time_ms": 180,
    "qec_insights_used": true,
    "recovery_strategy": "enhanced_validation"
  }
}
```

#### Get QEC Insights
```http
GET /api/v1/conflict-resolution/{conflict_id}/qec-insights
Authorization: Bearer <token>
```

**Response:**
```json
{
  "conflict_id": 1,
  "qec_enhanced": true,
  "constitutional_distances": [0.75, 0.82],
  "average_distance": 0.785,
  "priority_score": 0.7,
  "error_predictions": [
    {
      "principle_id": "1",
      "overall_risk": 0.4,
      "failure_predictions": {
        "semantic_conflict": 0.3,
        "ambiguous_principle": 0.2,
        "complexity_high": 0.1
      },
      "recommended_strategy": "enhanced_validation",
      "confidence": 0.8
    }
  ],
  "validation_scenarios": [
    {
      "principle_id": "1",
      "scenario_type": "privacy_check",
      "test_cases": 3,
      "expected_outcomes": ["data_encrypted", "consent_verified"]
    }
  ],
  "recovery_recommendations": [
    {
      "strategy": "enhanced_validation",
      "confidence": 0.8,
      "estimated_success_rate": 0.85
    }
  ]
}
```

### Constitutional Fidelity Monitor Endpoints

#### Get Current Fidelity Score
```http
GET /api/v1/fidelity/current
Authorization: Bearer <token>
```

**Response:**
```json
{
  "composite_score": 0.87,
  "level": "green",
  "components": {
    "principle_coverage": 0.92,
    "synthesis_success": 0.88,
    "enforcement_reliability": 0.90,
    "adaptation_speed": 0.85,
    "stakeholder_satisfaction": 0.82,
    "appeal_frequency": 0.15
  },
  "calculation_metadata": {
    "calculation_timestamp": "2024-01-15T14:30:00Z",
    "calculation_time_ms": 150,
    "principles_evaluated": 25,
    "weights_used": {
      "principle_coverage": 0.25,
      "synthesis_success": 0.20,
      "enforcement_reliability": 0.20,
      "adaptation_speed": 0.15,
      "stakeholder_satisfaction": 0.10,
      "appeal_frequency": 0.10
    }
  },
  "alerts": [
    {
      "level": "green",
      "message": "System operating within optimal parameters",
      "threshold": 0.85
    }
  ]
}
```

#### Get Fidelity History
```http
GET /api/v1/fidelity/history?hours=24&limit=100
Authorization: Bearer <token>
```

**Response:**
```json
{
  "fidelity_history": [
    {
      "timestamp": "2024-01-15T14:30:00Z",
      "composite_score": 0.87,
      "level": "green",
      "components": {
        "principle_coverage": 0.92,
        "synthesis_success": 0.88,
        "enforcement_reliability": 0.90,
        "adaptation_speed": 0.85,
        "stakeholder_satisfaction": 0.82,
        "appeal_frequency": 0.15
      }
    }
  ],
  "summary": {
    "average_score": 0.86,
    "trend": "stable",
    "alert_count": 0,
    "time_range": "24h"
  }
}
```

### QEC Component Endpoints

#### Calculate Constitutional Distance
```http
POST /api/v1/qec/constitutional-distance
Content-Type: application/json
Authorization: Bearer <token>

{
  "principle_id": "privacy_protection",
  "principle_data": {
    "name": "Privacy Protection",
    "description": "Protect user privacy and personal data",
    "category": "privacy",
    "policy_code": "package privacy_protection...",
    "validation_criteria_structured": [
      {
        "type": "privacy_check",
        "criteria": ["encryption", "access_control"]
      }
    ]
  }
}
```

**Response:**
```json
{
  "principle_id": "privacy_protection",
  "distance_score": 0.75,
  "detailed_metrics": {
    "language_ambiguity": 0.2,
    "criteria_formality": 0.8,
    "historical_success_rate": 0.85,
    "complexity_score": 0.6
  },
  "calculation_metadata": {
    "timestamp": "2024-01-15T14:30:00Z",
    "calculation_time_ms": 45,
    "version": "1.0.0"
  }
}
```

#### Predict Synthesis Challenges
```http
POST /api/v1/qec/error-prediction
Content-Type: application/json
Authorization: Bearer <token>

{
  "principle_id": "security_enforcement",
  "principle_data": {
    "name": "Security Enforcement",
    "description": "Ensure comprehensive system security",
    "category": "security",
    "policy_code": "package security_enforcement...",
    "distance_score": 0.82,
    "error_prediction_metadata": {
      "historical_failures": 1,
      "success_rate": 0.92
    }
  }
}
```

**Response:**
```json
{
  "principle_id": "security_enforcement",
  "predicted_failures": {
    "syntax_error": 0.1,
    "semantic_conflict": 0.2,
    "ambiguous_principle": 0.15,
    "complexity_high": 0.25,
    "timeout": 0.05,
    "confidence_low": 0.1,
    "validation_failed": 0.1,
    "bias_detected": 0.05
  },
  "overall_risk_score": 0.3,
  "recommended_strategy": "enhanced_validation",
  "confidence": 0.85,
  "prediction_metadata": {
    "prediction_timestamp": "2024-01-15T14:30:00Z",
    "prediction_time_ms": 75,
    "features_used": ["description_length", "description_complexity", "distance_score"],
    "model_accuracy": 0.78,
    "model_version": "1.0.0"
  }
}
```

## Data Structures

### ConstitutionalPrinciple (Enhanced)
```json
{
  "principle_id": "string",
  "name": "string",
  "description": "string",
  "category": "string",
  "policy_code": "string",
  "version": "integer",
  "validation_criteria_structured": [
    {
      "type": "string",
      "criteria": ["string"]
    }
  ],
  "distance_score": "float (0.0-1.0)",
  "score_updated_at": "datetime",
  "error_prediction_metadata": {
    "historical_failures": "integer",
    "success_rate": "float",
    "last_prediction": {
      "timestamp": "datetime",
      "overall_risk": "float",
      "top_risks": [
        {
          "failure_type": "string",
          "probability": "float"
        }
      ]
    }
  },
  "recovery_strategies": ["string"]
}
```

### QEC Analysis Result
```json
{
  "conflict_id": "integer",
  "constitutional_distances": ["float"],
  "average_distance": "float",
  "error_predictions": [
    {
      "principle_id": "string",
      "overall_risk": "float",
      "failure_predictions": {
        "failure_type": "float"
      },
      "recommended_strategy": "string",
      "confidence": "float"
    }
  ],
  "recommended_strategy": "string",
  "validation_scenarios": [
    {
      "principle_id": "string",
      "scenario_type": "string",
      "test_cases": "integer"
    }
  ],
  "priority_score": "float",
  "qec_metadata": {
    "analysis_timestamp": "datetime",
    "processing_time_ms": "float"
  }
}
```

## Performance Targets

- **First-pass synthesis success**: ≥88%
- **Failure resolution time**: ≤8.5 minutes
- **Constitutional fidelity threshold**: ≥0.85 (green level)
- **API response time**: ≤200ms
- **Concurrent user support**: ≥50 users
- **System uptime**: ≥99.5%

## Performance Optimization Features

### Caching Mechanisms
- **Constitutional Distance Caching**: Results cached for 1 hour with Redis
- **Error Prediction Caching**: Model predictions cached to reduce computation
- **Fidelity Calculation Caching**: System-wide metrics cached for 5 minutes
- **Cache Hit Rate Target**: ≥80% for optimal performance

### Database Optimizations
- **Indexed Queries**: All QEC tables have optimized indexes for frequent queries
- **Composite Indexes**: Multi-column indexes for complex query patterns
- **Partitioning**: Large tables partitioned by timestamp for better performance
- **Query Optimization**: Materialized views for complex aggregations

### Concurrent Processing
- **Parallel Conflict Resolution**: Multiple conflicts processed simultaneously
- **Async Operations**: All QEC components use async/await patterns
- **Connection Pooling**: Optimized database connection management
- **Resource Limits**: Configurable limits to prevent resource exhaustion

## Backward Compatibility

### Legacy API Support
- **Optional QEC Fields**: All QEC-related fields in API requests are optional
- **Graceful Degradation**: System functions normally when QEC components are disabled
- **Fallback Behavior**: Automatic fallback to non-QEC conflict resolution when needed
- **Migration Support**: Existing data automatically migrated with sensible defaults

### Configuration Compatibility
- **QEC Toggle**: QEC features can be enabled/disabled via `QEC_ENABLED` environment variable
- **Default Values**: All QEC configurations have sensible defaults for backward compatibility
- **Legacy Config**: Existing configuration files work without QEC-specific settings

### Database Compatibility
- **Nullable Columns**: All QEC database columns are nullable for existing data
- **Schema Migration**: Alembic migrations handle backward-compatible schema updates
- **Query Compatibility**: Existing database queries continue to work unchanged

## Error Handling

All endpoints return standard HTTP status codes:
- `200 OK`: Successful operation
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error
- `501 Not Implemented`: QEC components not available

Error responses include detailed error information:
```json
{
  "error": "string",
  "message": "string",
  "details": {
    "field": "validation error details"
  },
  "timestamp": "datetime",
  "request_id": "string"
}
```
