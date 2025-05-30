# Audit & Compliance Service (AC Service) API Documentation

## Overview

The AC Service manages AI governance principles, meta-rules, Constitutional Council operations, and conflict resolution mechanisms. It serves as the constitutional foundation for the ACGS-PGP framework.

**Base URL:** `http://localhost:8000/api/ac/`
**Interactive Docs:** `http://localhost:8000/api/ac/docs`

## Authentication

All endpoints require JWT authentication with appropriate role permissions:
- **Admin:** Full access to all operations
- **Policy Manager:** Read/write access to principles and guidelines
- **Auditor:** Read-only access to audit data
- **Constitutional Council:** Special access to amendment and voting operations

## Core Endpoints

### Principles Management

#### GET /principles
Retrieve constitutional principles with enhanced Phase 1 features.

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `limit` (int): Items per page (default: 20)
- `category` (str): Filter by principle category
- `scope` (str): Filter by principle scope
- `priority_min` (float): Minimum priority weight (0.0-1.0)

**Response:**
```json
{
  "success": true,
  "data": {
    "principles": [
      {
        "id": 1,
        "title": "AI Safety Principle",
        "description": "Ensure AI systems operate safely",
        "priority_weight": 0.95,
        "scope": ["safety", "autonomous_systems"],
        "normative_statement": "AI systems MUST implement fail-safe mechanisms",
        "constraints": {
          "safety_threshold": 0.99,
          "verification_required": true
        },
        "rationale": "Safety is paramount for AI deployment",
        "keywords": ["safety", "fail-safe", "verification"],
        "category": "Safety",
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z"
      }
    ],
    "total": 50,
    "page": 1,
    "pages": 3
  }
}
```

#### POST /principles
Create a new constitutional principle.

**Request Body:**
```json
{
  "title": "Privacy Protection Principle",
  "description": "Protect user privacy in AI systems",
  "priority_weight": 0.85,
  "scope": ["privacy", "data_protection"],
  "normative_statement": "AI systems MUST protect user privacy",
  "constraints": {
    "data_minimization": true,
    "consent_required": true
  },
  "rationale": "Privacy is a fundamental right",
  "keywords": ["privacy", "data_protection", "consent"],
  "category": "Privacy"
}
```

#### PUT /principles/{principle_id}
Update an existing principle.

#### DELETE /principles/{principle_id}
Delete a principle (Admin only).

### Constitutional Council Operations

#### GET /constitutional-council/meta-rules
Retrieve AC meta-rules that govern principle interactions.

**Response:**
```json
{
  "success": true,
  "data": {
    "meta_rules": [
      {
        "id": 1,
        "name": "Safety Override Rule",
        "description": "Safety principles override all other principles",
        "rule_type": "priority_override",
        "conditions": {
          "principle_category": "Safety",
          "conflict_detected": true
        },
        "actions": {
          "priority_boost": 1.0,
          "override_enabled": true
        },
        "priority": 1,
        "is_active": true,
        "created_by": 1,
        "created_at": "2024-01-15T10:30:00Z"
      }
    ]
  }
}
```

#### POST /constitutional-council/meta-rules
Create a new meta-rule (Admin only).

#### GET /constitutional-council/amendments
Retrieve constitutional amendments.

**Query Parameters:**
- `status` (str): Filter by status (proposed, voting, approved, rejected)
- `proposer_id` (int): Filter by proposer

**Response:**
```json
{
  "success": true,
  "data": {
    "amendments": [
      {
        "id": 1,
        "title": "Enhanced Privacy Protections",
        "description": "Strengthen privacy requirements for AI systems",
        "amendment_type": "principle_modification",
        "proposed_changes": {
          "principle_id": 5,
          "changes": {
            "priority_weight": 0.90,
            "constraints": {
              "encryption_required": true
            }
          }
        },
        "rationale": "Increased privacy threats require stronger protections",
        "status": "voting",
        "voting_deadline": "2024-01-30T23:59:59Z",
        "proposer_id": 2,
        "created_at": "2024-01-15T10:30:00Z"
      }
    ]
  }
}
```

#### POST /constitutional-council/amendments
Propose a new constitutional amendment (Constitutional Council role required).

#### POST /constitutional-council/amendments/{amendment_id}/votes
Vote on an amendment (Constitutional Council role required).

**Request Body:**
```json
{
  "vote": "approve",
  "comment": "This amendment strengthens our privacy protections appropriately"
}
```

#### GET /constitutional-council/amendments/{amendment_id}/votes
Get votes for an amendment.

#### POST /constitutional-council/amendments/{amendment_id}/comments
Add a comment to an amendment discussion.

### Conflict Resolution

#### GET /conflict-resolutions
Retrieve conflict resolution records.

**Response:**
```json
{
  "success": true,
  "data": {
    "conflict_resolutions": [
      {
        "id": 1,
        "conflict_type": "principle_priority_conflict",
        "conflicting_principles": [1, 3],
        "resolution_strategy": "priority_weighted_average",
        "resolution_details": {
          "weights": {"principle_1": 0.6, "principle_3": 0.4},
          "final_decision": "apply_safety_first"
        },
        "context": {
          "scenario": "autonomous_vehicle_decision",
          "environmental_factors": ["emergency_situation"]
        },
        "resolved_at": "2024-01-15T10:30:00Z",
        "resolver_id": 1
      }
    ]
  }
}
```

#### POST /conflict-resolutions
Create a new conflict resolution record.

### Guidelines Management

#### GET /guidelines
Retrieve governance guidelines.

#### POST /guidelines
Create a new guideline.

#### PUT /guidelines/{guideline_id}
Update a guideline.

#### DELETE /guidelines/{guideline_id}
Delete a guideline.

## Enhanced Features (Phase 1)

### Constitutional Context Retrieval

#### GET /principles/by-context
Retrieve principles relevant to a specific context.

**Query Parameters:**
- `context` (str): Context identifier (e.g., "autonomous_systems", "data_processing")
- `include_meta_rules` (bool): Include applicable meta-rules

**Response:**
```json
{
  "success": true,
  "data": {
    "context": "autonomous_systems",
    "principles": [...],
    "meta_rules": [...],
    "conflict_resolutions": [...]
  }
}
```

### Principle Validation

#### POST /principles/validate
Validate principle data against constitutional requirements.

**Request Body:**
```json
{
  "principle_data": {
    "title": "Test Principle",
    "priority_weight": 0.85,
    "scope": ["test_scope"],
    "normative_statement": "Test statement",
    "constraints": {}
  }
}
```

## Error Responses

### Common Error Codes
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict (e.g., duplicate principle)
- `422 Unprocessable Entity`: Validation errors

### Example Error Response
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Priority weight must be between 0.0 and 1.0",
    "details": {
      "field": "priority_weight",
      "value": 1.5,
      "constraint": "range(0.0, 1.0)"
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Rate Limiting

- **Standard endpoints:** 100 requests per minute per user
- **Constitutional Council operations:** 50 requests per minute per user
- **Admin operations:** 200 requests per minute per user

## Webhooks

The AC Service supports webhooks for real-time notifications:

### Available Events
- `principle.created`
- `principle.updated`
- `amendment.proposed`
- `amendment.voted`
- `conflict.detected`
- `conflict.resolved`

### Webhook Configuration
Configure webhooks via the admin interface or API:

```json
{
  "url": "https://your-app.com/webhooks/ac-service",
  "events": ["principle.created", "amendment.proposed"],
  "secret": "your-webhook-secret"
}
```

For complete API reference, visit the interactive documentation at `http://localhost:8000/api/ac/docs`.
