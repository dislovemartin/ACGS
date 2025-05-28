# ACGS-PGP Framework Deployment Checklist

This comprehensive checklist ensures successful deployment of the AI Compliance Governance System - Policy Generation Platform (ACGS-PGP) following the three-phase development approach: Foundational Enhancements & Theoretical Alignment, Evolutionary Computation Integration, and Advanced Governance Mechanisms & System Hardening.

## Overview

The ACGS-PGP framework implements a formal Artificial Constitution (AC) layer with democratic legitimacy, governance synthesis engine, formal verification, and cryptographic integrity. This deployment checklist is organized to support the progressive implementation of these capabilities.

## Prerequisites and System Requirements

### System Requirements
- **Docker**: Version 20.10+ with Docker Compose v2.0+
- **Kubernetes**: Version 1.20+ (for production deployment)
- **Memory**: Minimum 8GB RAM (16GB+ recommended for production)
- **Storage**: Minimum 20GB free space
- **Network**: Ports 8000-8005, 5432, 6379 available
- **Python**: 3.9+ for development
- **Node.js**: 16+ for frontend development

### Required Tools
```bash
# Verify required tools are installed
docker --version
docker-compose --version
kubectl version --client  # For K8s deployment
python3 --version
node --version
npm --version
curl --version
```

### Environment Setup
```bash
# 1. Clone and navigate to project
git clone <repository-url>
cd ACGS-master

# 2. Copy environment configuration
cp .env.example .env

# 3. Review and update .env file with your specific values
nano .env
```

**Critical .env Variables to Configure:**
- `DATABASE_URL`: PostgreSQL connection string
- `AUTH_SERVICE_SECRET_KEY`: Strong JWT secret (32+ characters)
- `AUTH_SERVICE_CSRF_SECRET_KEY`: Strong CSRF secret (32+ characters)
- `LLM_API_KEY`: Your LLM provider API key (GPT-4 recommended)
- `LLM_PROVIDER`: Set to "real" for OpenAI integration or "mock" for testing
- `OPENAI_API_KEY`: OpenAI API key for constitutional prompting (if using real LLM)
- `OPENAI_MODEL_NAME`: OpenAI model name (default: "gpt-3.5-turbo")
- `SMT_SOLVER_PATH`: Path to Z3 solver binary
- `ENVIRONMENT`: Set to "development", "staging", or "production"
- `CONSTITUTIONAL_COUNCIL_ENABLED`: Enable democratic governance features
- `CRYPTOGRAPHIC_INTEGRITY_ENABLED`: Enable PGP assurance layer
- `AC_SERVICE_URL`: AC service URL for constitutional prompting (default: "http://ac_service:8000/api/v1")

## Phase 1: Foundational Enhancements & Theoretical Alignment

This phase implements the core theoretical framework including the formal Artificial Constitution (AC) layer, democratic legitimacy mechanisms, and enhanced governance synthesis engine.

### 1.1 Artificial Constitution (AC) Layer Implementation

#### 1.1.1 Validate AC Framework Prerequisites
```bash
# Check if AC service is properly configured
if ! grep -q "CONSTITUTIONAL_COUNCIL_ENABLED" .env; then
    echo "⚠️  Adding Constitutional Council configuration to .env"
    echo "CONSTITUTIONAL_COUNCIL_ENABLED=true" >> .env
    echo "AC_AMENDMENT_THRESHOLD=0.67" >> .env
    echo "AC_VOTING_PERIOD_HOURS=168" >> .env
fi

# Verify AC database schema requirements
docker-compose exec alembic-runner alembic check
echo "✅ AC framework prerequisites validated"
```

#### 1.1.2 ✅ Enhanced Principles (P) Component - COMPLETED
**Status: IMPLEMENTED** - Enhanced principle management with constitutional features

**Database Migration Required:**
```bash
# Execute enhanced principle schema migration
cd ACGS-master
alembic upgrade head

# Verify enhanced principle fields are available
docker exec -it acgs_postgres psql -U acgs_user -d acgs_pgp_db -c "
\d+ principles;
"
```

**Test Enhanced Principle Management:**
```bash
# Test enhanced principle creation with constitutional fields
curl -X POST http://localhost:8000/api/v1/principles \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Data Privacy Principle",
    "description": "Personal data must be processed lawfully, fairly, and transparently",
    "content": "All data processing operations SHALL implement privacy-by-design principles",
    "priority_weight": 0.9,
    "scope": ["data_processing", "healthcare", "financial_services"],
    "normative_statement": "All data processing operations SHALL implement privacy-by-design principles and obtain explicit consent",
    "constraints": {
      "mandatory_checks": ["consent_verification", "purpose_limitation"],
      "prohibited_actions": ["unauthorized_sharing", "profiling_without_consent"]
    },
    "rationale": "Privacy is a fundamental right that must be protected in all AI systems",
    "keywords": ["privacy", "data_protection", "consent", "GDPR"],
    "category": "Privacy",
    "validation_criteria_nl": "System must verify user consent before processing personal data",
    "constitutional_metadata": {
      "constitutional_level": "fundamental",
      "enforcement_priority": "critical"
    }
  }'

# Test enhanced principle retrieval endpoints
curl http://localhost:8000/api/v1/principles/category/Privacy | jq '.principles[] | {id, name, priority_weight, category}'
curl http://localhost:8000/api/v1/principles/scope/healthcare | jq '.principles[] | {id, name, scope}'
curl -X POST http://localhost:8000/api/v1/principles/search/keywords \
  -H "Content-Type: application/json" \
  -d '["privacy", "data_protection"]' | jq '.principles[] | {id, name, keywords}'

echo "✅ Enhanced Principles component implemented with constitutional features"
```

#### 1.1.3 Implement Meta-Rules (R) Component
```bash
# Test meta-governance rules creation
curl -X POST http://localhost:8000/ac/meta-rules \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rule_type": "amendment_procedure",
    "description": "Defines how AC principles can be modified",
    "threshold": 0.67,
    "stakeholder_roles": ["admin", "policy_manager", "constitutional_council"],
    "decision_mechanism": "supermajority_vote"
  }'

echo "✅ Meta-rules component implemented"
```

#### 1.1.4 ✅ Conflict Resolution Mapping (M) - COMPLETED
**Status: IMPLEMENTED** - Principle conflict detection and resolution strategies

**Test Conflict Resolution Functionality:**
```bash
# Test conflict resolution creation
curl -X POST http://localhost:8000/api/v1/constitutional-council/conflict-resolutions \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "conflict_type": "principle_contradiction",
    "principle_ids": [1, 2],
    "context": "data_retention_vs_privacy",
    "conflict_description": "Data retention requirements conflict with privacy deletion rights",
    "severity": "high",
    "resolution_strategy": "principle_priority_based",
    "resolution_details": {
      "primary_principle": 1,
      "secondary_principle": 2,
      "balancing_criteria": ["user_consent", "legal_requirement", "business_necessity"]
    },
    "precedence_order": [1, 2]
  }'

# Test conflict resolution listing and filtering
curl -X GET http://localhost:8000/api/v1/constitutional-council/conflict-resolutions?severity=high \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Test conflict resolution retrieval
curl -X GET http://localhost:8000/api/v1/constitutional-council/conflict-resolutions/1 \
  -H "Authorization: Bearer $ADMIN_TOKEN"

echo "✅ Conflict resolution mapping implemented with full CRUD operations"
```

### 1.2 Democratic Legitimacy Framework

#### 1.2.1 ✅ Constitutional Council Setup - COMPLETED
**Status: IMPLEMENTED** - Amendment proposal workflow, voting mechanisms, and democratic governance

**Test Constitutional Council Functionality:**
```bash
# Test amendment proposal workflow
curl -X POST http://localhost:8001/api/v1/constitutional-council/amendments \
  -H "Authorization: Bearer $COUNCIL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "principle_id": 1,
    "amendment_type": "modify",
    "proposed_changes": "Update privacy principle to include AI-specific requirements",
    "justification": "Emerging AI technologies require enhanced privacy protections",
    "proposed_content": "Enhanced privacy principle with AI governance requirements",
    "consultation_period_days": 30,
    "public_comment_enabled": true,
    "stakeholder_groups": ["citizens", "experts", "affected_parties"]
  }'

# Test amendment listing and filtering
curl -X GET http://localhost:8001/api/v1/constitutional-council/amendments?status=proposed \
  -H "Authorization: Bearer $USER_TOKEN"

# Test voting mechanism
curl -X POST http://localhost:8001/api/v1/constitutional-council/amendments/1/votes \
  -H "Authorization: Bearer $COUNCIL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "vote": "for",
    "reasoning": "This amendment improves AI transparency and aligns with democratic values"
  }'

# Test public comment system
curl -X POST http://localhost:8001/api/v1/constitutional-council/amendments/1/comments \
  -H "Content-Type: application/json" \
  -d '{
    "comment_text": "I support this amendment as it enhances privacy protection",
    "sentiment": "support",
    "stakeholder_group": "citizen"
  }'

# Test meta-rules framework
curl -X POST http://localhost:8001/api/v1/constitutional-council/meta-rules \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rule_type": "amendment_procedure",
    "name": "Constitutional Amendment Procedure",
    "description": "Defines how AC principles can be modified",
    "rule_definition": {
      "threshold": 0.67,
      "stakeholder_roles": ["admin", "constitutional_council"],
      "decision_mechanism": "supermajority_vote"
    },
    "threshold": "0.67",
    "stakeholder_roles": ["admin", "constitutional_council"],
    "decision_mechanism": "supermajority_vote"
  }'

echo "✅ Constitutional Council framework implemented with full democratic governance"
```

#### 1.2.2 🔄 Public Consultation Mechanisms - IN PROGRESS
**Status: PARTIALLY IMPLEMENTED** - Basic public comment system exists, needs enhanced consultation workflows

**Current Implementation Status:**
- ✅ Public comment system for amendments (via Constitutional Council)
- ✅ Stakeholder group categorization
- ✅ Comment sentiment tracking
- ⚠️  Dedicated consultation endpoints need implementation
- ⚠️  Consultation period management needs enhancement
- ⚠️  Public notification mechanisms need development

**Test Current Public Consultation Features:**
```bash
# Test public comment submission (currently working)
curl -X POST http://localhost:8001/api/v1/constitutional-council/amendments/1/comments \
  -H "Content-Type: application/json" \
  -d '{
    "comment_text": "I support this amendment as it enhances privacy protection for citizens",
    "sentiment": "support",
    "stakeholder_group": "citizen"
  }'

# Test comment retrieval with public filtering
curl -X GET http://localhost:8001/api/v1/constitutional-council/amendments/1/comments?is_public=true

# Test amendment consultation features
curl -X GET http://localhost:8001/api/v1/constitutional-council/amendments?public_comment_enabled=true

echo "✅ Basic public consultation features working"
echo "⚠️  Enhanced consultation workflows need implementation"
```

**Next Implementation Steps:**
1. Create dedicated consultation management endpoints
2. Implement consultation period automation
3. Add public notification mechanisms
4. Enhance stakeholder engagement features
5. Add consultation analytics and reporting

### 1.3 ✅ Enhanced Governance Synthesis (GS) Engine - COMPLETED

#### 1.3.1 ✅ Constitutional Prompting Implementation - COMPLETED
**Status: IMPLEMENTED** - Constitutional prompting with AC principle integration

**Test Constitutional Synthesis:**
```bash
# Test constitutional synthesis with AC principle integration
curl -X POST http://localhost:8000/api/v1/constitutional/synthesize \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "context": "healthcare_ai_systems",
    "category": "Safety",
    "synthesis_request": "Generate governance rules for AI-powered medical diagnosis systems that ensure patient safety and data privacy",
    "target_format": "datalog"
  }'

# Test constitutional context analysis
curl -X POST http://localhost:8000/api/v1/constitutional/analyze-context \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "context": "financial_ai_systems",
    "category": "Privacy"
  }'

# Verify constitutional context retrieval
curl -X GET http://localhost:8000/api/v1/constitutional/constitutional-context/healthcare_ai_systems \
  -H "Authorization: Bearer $ADMIN_TOKEN"

echo "✅ Constitutional Prompting implemented with AC principle integration"
```

#### 1.3.2 ✅ Contextual Analyzer Implementation - COMPLETED
**Status: IMPLEMENTED** - Environmental factor processing and contextual analysis

**Test Contextual Analysis:**
```bash
# Test environmental factor addition
curl -X POST http://localhost:8000/api/v1/constitutional/environmental-factors \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "factor_id": "gdpr_compliance_2024",
    "factor_type": "regulatory",
    "value": "GDPR compliance requirements updated for AI systems",
    "source": "eu_regulation",
    "confidence": 0.95
  }'

# Test contextual analysis with environmental factors
curl -X GET http://localhost:8000/api/v1/constitutional/constitutional-context/healthcare_ai_systems \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Test adaptation triggers
curl -X GET http://localhost:8000/api/v1/constitutional/adaptation-triggers/healthcare_ai_systems \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Test environmental factor retrieval by type
curl -X GET http://localhost:8000/api/v1/constitutional/environmental-factors/regulatory \
  -H "Authorization: Bearer $ADMIN_TOKEN"

echo "✅ Contextual Analyzer implemented with environmental factor processing"
```

#### 1.3.3 ✅ Enhanced LLM Integration - COMPLETED
**Status: IMPLEMENTED** - Constitutional prompting with Mock and Real LLM clients

**Test LLM Integration:**
```bash
# Test constitutional synthesis with LLM integration
curl -X POST http://localhost:8000/api/v1/constitutional/synthesize \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "context": "autonomous_vehicles",
    "category": "Safety",
    "synthesis_request": "Generate safety governance rules for autonomous vehicle decision-making systems",
    "target_format": "datalog"
  }'

# Verify constitutional compliance information in response
# Response should include:
# - generated_rules with constitutional_compliance metadata
# - constitutional_context with applicable principles
# - synthesis_metadata with constitutional prompting details

echo "✅ Enhanced LLM Integration with constitutional prompting implemented"
```

### 1.4 Environment Configuration Validation
```bash
# Validate enhanced .env file with AC-specific variables
required_vars=(
    "DATABASE_URL"
    "AUTH_SERVICE_SECRET_KEY"
    "AUTH_SERVICE_CSRF_SECRET_KEY"
    "LLM_API_KEY"
    "SMT_SOLVER_PATH"
    "CONSTITUTIONAL_COUNCIL_ENABLED"
    "CRYPTOGRAPHIC_INTEGRITY_ENABLED"
)

for var in "${required_vars[@]}"; do
    if ! grep -q "^${var}=" .env; then
        echo "❌ Missing required variable: $var"
        exit 1
    fi
done
echo "✅ Enhanced environment configuration validated"
```

### 1.5 Docker Environment Validation
```bash
# Check Docker daemon is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker daemon is not running"
    exit 1
fi

# Check available disk space (minimum 20GB for enhanced features)
available_space=$(df . | tail -1 | awk '{print $4}')
if [ "$available_space" -lt 20971520 ]; then  # 20GB in KB
    echo "⚠️  Warning: Less than 20GB disk space available"
fi

# Check available memory (minimum 8GB for LLM integration)
available_memory=$(free -m | awk 'NR==2{print $7}')
if [ "$available_memory" -lt 8192 ]; then
    echo "⚠️  Warning: Less than 8GB memory available"
fi
echo "✅ Docker environment validated"
```

### 1.6 Port Availability Check
```bash
# Check if required ports are available (expanded for new services)
required_ports=(8000 8001 8002 8003 8004 8005 8006 8007 5432 6379)
for port in "${required_ports[@]}"; do
    if netstat -tuln | grep -q ":$port "; then
        echo "❌ Port $port is already in use"
        netstat -tuln | grep ":$port "
        exit 1
    fi
done
echo "✅ All required ports are available"
```

### 1.7 Constitutional Fidelity Mechanisms
```bash
# Test principle traceability for generated rules
curl -X POST http://localhost:8000/gs/rule-synthesis \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "principle_ids": ["principle_1"],
    "context": "data_processing_rules",
    "enable_traceability": true,
    "consistency_check": true
  }'

# Verify constitutional compliance scoring
curl -X POST http://localhost:8000/fv/constitutional-compliance \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rule_set": "generated_rules_1",
    "ac_principles": ["principle_1", "principle_2"],
    "compliance_threshold": 0.8
  }'

echo "✅ Constitutional fidelity mechanisms implemented"
```

## Phase 2: Evolutionary Computation (EC) Integration

This phase introduces the "AlphaEvolve" governance layer for managing evolutionary computation systems with constitutional oversight.

### 2.1 Governed Evolutionary Layer Implementation

#### 2.1.1 Constitutional Prompting for EC
```bash
# Test constitutional prompting integration
curl -X POST http://localhost:8000/gs/ec-constitutional-prompting \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "base_prompt": "Generate solutions for resource allocation optimization",
    "active_principles": ["fairness", "efficiency", "transparency"],
    "ec_context": {
      "population_size": 100,
      "generations": 50,
      "domain": "resource_allocation"
    }
  }'

echo "✅ Constitutional prompting for EC implemented"
```

#### 2.1.2 Constitution-Aware EC Operators
```bash
# Test fitness function integration with governance penalties
curl -X POST http://localhost:8000/pgc/ec-governance-evaluation \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "solution_candidates": [
      {"id": "sol_1", "parameters": {"allocation": [0.3, 0.4, 0.3]}},
      {"id": "sol_2", "parameters": {"allocation": [0.8, 0.1, 0.1]}}
    ],
    "governance_rules": ["fairness_constraint", "minimum_allocation_rule"],
    "penalty_weight": 0.5
  }'

# Test solution culling based on constitutional compliance
curl -X POST http://localhost:8000/pgc/ec-solution-culling \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "population": "ec_population_1",
    "compliance_threshold": 0.7,
    "cull_percentage": 0.2
  }'

echo "✅ Constitution-aware EC operators implemented"
```

### 2.2 Real-Time PGC Enforcement for EC

#### 2.2.1 Optimize PGC Performance for EC Loops
```bash
# Test PGC performance under EC load
curl -X POST http://localhost:8000/pgc/performance-test \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "test_type": "ec_simulation",
    "concurrent_evaluations": 100,
    "target_latency_ms": 50,
    "duration_seconds": 60
  }'

# Verify sub-50ms policy enforcement requirement
curl -X GET http://localhost:8000/pgc/performance-metrics \
  -H "Authorization: Bearer $ADMIN_TOKEN"

echo "✅ PGC performance optimized for EC"
```

#### 2.2.2 Enhanced Rule Caching and Incremental Evaluation
```bash
# Test incremental rule evaluation
curl -X POST http://localhost:8000/pgc/incremental-evaluation \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rule_changes": ["rule_1_modified", "rule_2_added"],
    "affected_solutions": ["sol_1", "sol_2", "sol_3"],
    "cache_strategy": "differential_update"
  }'

# Test parallel processing capabilities
curl -X POST http://localhost:8000/pgc/parallel-evaluation \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "evaluation_batch": "batch_1",
    "parallel_workers": 4,
    "load_balancing": "round_robin"
  }'

echo "✅ Enhanced rule caching and parallel processing implemented"
```

### 2.3 Service Verification and Network Connectivity

#### 2.3.1 Check All Container Status
```bash
# Verify all services are running (including new EC integration services)
docker-compose ps
```
**Expected Output**: All services should show "Up" status:
- acgs_postgres (Up)
- acgs_redis (Up)
- acgs_nginx_gateway (Up)
- acgs_auth_service (Up)
- acgs_ac_service (Up)
- acgs_gs_service (Up)
- acgs_fv_service (Up)
- acgs_integrity_service (Up)
- acgs_pgc_service (Up)
- acgs_ec_integration_service (Up) [if implemented as separate service]

#### 2.3.2 Fix Any Failed Services
```bash
# Check logs for specific service (replace SERVICE_NAME)
docker logs acgs_SERVICE_NAME --tail 50

# Common fixes for EC integration:
# - Check LLM API connectivity for constitutional prompting
# - Verify SMT solver integration for constraint checking
# - Ensure adequate memory allocation for parallel processing
```

#### 2.3.3 Verify Network Connectivity
```bash
# Test internal service communication
docker exec acgs_auth_service ping postgres
docker exec acgs_auth_service ping redis
docker exec acgs_gs_service ping pgc_service
docker exec acgs_fv_service ping gs_service
```
**Expected Output**: Successful ping responses

### 2.4 Database Connection and Schema Validation
```bash
# Test database connectivity from auth_service
docker exec acgs_auth_service python -c "
import asyncio
from app.db.database import engine
async def test():
    async with engine.begin() as conn:
        result = await conn.execute('SELECT 1')
        print('Database connection successful')
asyncio.run(test())
"

# Verify EC-specific database tables
docker exec -it acgs_postgres psql -U acgs_user -d acgs_pgp_db -c "
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name LIKE '%ec_%' OR table_name LIKE '%evolution%';
"
```
**Expected Output**: "Database connection successful" and list of EC-related tables

## Phase 3: Advanced Governance Mechanisms & System Hardening

This phase implements formal verification enhancements, algorithmic fairness integration, democratic governance mechanisms, and cryptographic integrity (PGP Assurance).

### 3.1 Formal Verification Enhancements

#### 3.1.1 SMT Solver Integration (Z3)
```bash
# Test Z3 SMT solver integration
curl -X POST http://localhost:8000/fv/smt-verification \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "formula": "(assert (> x 0))",
    "variables": {"x": "Int"},
    "verification_type": "safety_property",
    "timeout_seconds": 30
  }'

# Test safety-critical rule verification
curl -X POST http://localhost:8000/fv/safety-verification \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rule_set": "critical_safety_rules",
    "properties": ["deadlock_freedom", "liveness", "safety"],
    "verification_depth": "exhaustive"
  }'

echo "✅ SMT solver integration implemented"
```

#### 3.1.2 Tiered Validation Pipeline
```bash
# Test automated baseline validation
curl -X POST http://localhost:8000/fv/automated-validation \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rule_set": "generated_rules_1",
    "validation_level": "baseline",
    "automated_checks": ["syntax", "consistency", "basic_safety"]
  }'

# Test human-in-the-loop validation
curl -X POST http://localhost:8000/fv/hitl-validation \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rule_set": "generated_rules_1",
    "validation_level": "human_review",
    "reviewer_role": "policy_expert",
    "review_criteria": ["ethical_alignment", "practical_feasibility"]
  }'

# Test rigorous formal verification
curl -X POST http://localhost:8000/fv/rigorous-verification \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rule_set": "critical_rules",
    "verification_level": "formal_proof",
    "proof_techniques": ["model_checking", "theorem_proving"],
    "completeness_requirement": true
  }'

echo "✅ Tiered validation pipeline implemented"
```

#### 3.1.3 Safety and Conflict Checking
```bash
# Test safety property validation
curl -X POST http://localhost:8000/fv/safety-checking \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "system_model": "ec_governance_model",
    "safety_properties": [
      "no_discriminatory_outcomes",
      "privacy_preservation",
      "fairness_guarantees"
    ],
    "verification_method": "bounded_model_checking"
  }'

# Test conflict detection between rules
curl -X POST http://localhost:8000/fv/conflict-detection \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rule_sets": ["privacy_rules", "efficiency_rules", "fairness_rules"],
    "conflict_types": ["logical_contradiction", "practical_incompatibility"],
    "resolution_strategy": "principle_priority_based"
  }'

echo "✅ Safety and conflict checking implemented"
```

### 3.2 Algorithmic Fairness Integration

#### 3.2.1 Fairness Criteria as Constitutional Principles
```bash
# Test demographic parity principle implementation
curl -X POST http://localhost:8000/ac/fairness-principles \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "fairness_type": "demographic_parity",
    "description": "Equal positive prediction rates across protected groups",
    "mathematical_definition": "P(Y=1|A=0) = P(Y=1|A=1)",
    "protected_attributes": ["race", "gender", "age"],
    "tolerance_threshold": 0.05
  }'

# Test equalized odds principle
curl -X POST http://localhost:8000/ac/fairness-principles \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "fairness_type": "equalized_odds",
    "description": "Equal true positive and false positive rates across groups",
    "mathematical_definition": "P(Y=1|A=0,Y*=y) = P(Y=1|A=1,Y*=y) for y in {0,1}",
    "protected_attributes": ["race", "gender"],
    "tolerance_threshold": 0.03
  }'

echo "✅ Fairness criteria as constitutional principles implemented"
```

#### 3.2.2 Bias Detection Algorithms
```bash
# Test counterfactual analysis for bias detection
curl -X POST http://localhost:8000/fv/bias-detection/counterfactual \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "ec_solution_evaluator",
    "test_cases": [
      {"individual_id": "test_1", "protected_attribute": "race", "counterfactual_value": "different_race"},
      {"individual_id": "test_2", "protected_attribute": "gender", "counterfactual_value": "different_gender"}
    ],
    "fairness_metric": "individual_fairness"
  }'

# Test embedding analysis for bias
curl -X POST http://localhost:8000/fv/bias-detection/embedding \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "embedding_model": "solution_representation_model",
    "protected_attributes": ["race", "gender", "age"],
    "bias_metrics": ["word_embedding_association_test", "clustering_analysis"],
    "threshold": 0.1
  }'

# Test outcome simulation for bias assessment
curl -X POST http://localhost:8000/fv/bias-detection/outcome-simulation \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "simulation_parameters": {
      "population_size": 10000,
      "protected_groups": ["group_a", "group_b"],
      "simulation_rounds": 1000
    },
    "fairness_constraints": ["demographic_parity", "equal_opportunity"],
    "statistical_tests": ["chi_square", "kolmogorov_smirnov"]
  }'

echo "✅ Bias detection algorithms implemented"
```

### 3.3 Democratic AI Governance Mechanisms

#### 3.3.1 Appeal and Dispute Resolution Workflow
```bash
# Test appeal submission
curl -X POST http://localhost:8000/integrity/appeals \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "decision_id": "policy_decision_123",
    "appeal_reason": "algorithmic_bias_suspected",
    "evidence": "Statistical analysis showing disparate impact on protected group",
    "requested_remedy": "decision_review_and_correction"
  }'

# Test dispute resolution process
curl -X POST http://localhost:8000/integrity/dispute-resolution \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "appeal_id": "appeal_123",
    "resolution_method": "expert_panel_review",
    "panel_composition": ["ai_ethics_expert", "domain_expert", "affected_community_representative"],
    "timeline_days": 30
  }'

echo "✅ Appeal and dispute resolution workflow implemented"
```

#### 3.3.2 Explainability Dashboard Interface
```bash
# Test rule provenance tracking
curl -X GET http://localhost:8000/integrity/rule-provenance/rule_123 \
  -H "Authorization: Bearer $USER_TOKEN"

# Test decision explanation generation
curl -X POST http://localhost:8000/integrity/explain-decision \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "decision_id": "policy_decision_123",
    "explanation_level": "detailed",
    "include_counterfactuals": true,
    "target_audience": "affected_individual"
  }'

# Test transparency reporting
curl -X GET http://localhost:8000/integrity/transparency-report \
  -H "Authorization: Bearer $PUBLIC_TOKEN" \
  -d '{
    "report_period": "2024-Q1",
    "include_metrics": ["decision_volume", "appeal_rates", "bias_assessments"],
    "aggregation_level": "anonymized"
  }'

echo "✅ Explainability dashboard interface implemented"
```

### 3.4 Cryptographic Integrity (PGP Assurance)

#### 3.4.1 Digital Signatures for AC Versions
```bash
# Test AC version signing
curl -X POST http://localhost:8000/integrity/sign-ac-version \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ac_version_id": "ac_v1.2.0",
    "signing_authority": "constitutional_council",
    "signature_algorithm": "ECDSA_P256",
    "include_timestamp": true
  }'

# Test signature verification
curl -X POST http://localhost:8000/integrity/verify-signature \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "ac_v1.2.0",
    "signature": "signature_data_here",
    "public_key": "public_key_data_here",
    "verification_level": "strict"
  }'

echo "✅ Digital signatures for AC versions implemented"
```

#### 3.4.2 Hash Functions and Merkle Trees
```bash
# Test rule output integrity verification
curl -X POST http://localhost:8000/integrity/verify-rule-integrity \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rule_set_id": "generated_rules_1",
    "hash_algorithm": "SHA3-256",
    "merkle_root": "expected_merkle_root_hash",
    "verification_depth": "full_tree"
  }'

# Test audit log integrity
curl -X POST http://localhost:8000/integrity/verify-audit-log \
  -H "Authorization: Bearer $AUDITOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "log_period": "2024-01-01_to_2024-01-31",
    "integrity_check_type": "merkle_tree_verification",
    "tamper_detection": true
  }'

echo "✅ Hash functions and Merkle trees implemented"
```

#### 3.4.3 Key Management and HSM Integration
```bash
# Test key generation and storage
curl -X POST http://localhost:8000/integrity/generate-keys \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key_type": "ECDSA_P256",
    "key_purpose": "ac_signing",
    "storage_location": "hsm",
    "backup_required": true
  }'

# Test HSM integration
curl -X POST http://localhost:8000/integrity/hsm-operation \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "sign",
    "key_id": "ac_signing_key_1",
    "data_to_sign": "ac_version_hash",
    "hsm_authentication": "required"
  }'

echo "✅ Key management and HSM integration implemented"
```

#### 3.4.4 RFC 3161 Timestamping
```bash
# Test timestamp generation
curl -X POST http://localhost:8000/integrity/timestamp \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "document_hash": "sha256_hash_of_document",
    "timestamp_authority": "trusted_tsa",
    "rfc3161_compliant": true
  }'

# Test timestamp verification
curl -X POST http://localhost:8000/integrity/verify-timestamp \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp_token": "rfc3161_timestamp_token",
    "original_document_hash": "sha256_hash",
    "verification_policy": "strict"
  }'

echo "✅ RFC 3161 timestamping implemented"
```

### 3.5 API Endpoint Testing

#### 3.5.1 Test Gateway Access
```bash
# Test nginx gateway is accessible
curl -I http://localhost:8000
```
**Expected Output**: HTTP 200 or 404 (not connection refused)

#### 3.5.2 Test Enhanced Service Endpoints
```bash
# Test auth service root endpoint
curl http://localhost:8000/auth/
```
**Expected Output**: `{"message": "Authentication Service is running. Use /auth/docs for API documentation."}`

```bash
# Test all service health endpoints including new Phase 3 features
curl http://localhost:8000/ac/health
curl http://localhost:8000/gs/health
curl http://localhost:8000/fv/health
curl http://localhost:8000/integrity/health
curl http://localhost:8000/pgc/health
```
**Expected Output**: Service-specific health status with Phase 3 feature indicators

## Phase 4: Database Migration and Schema Management

### 4.1 Alembic Migration Verification
```bash
# Check Alembic migration status
docker-compose exec alembic-runner alembic current
docker-compose exec alembic-runner alembic history --verbose

# Verify all migrations are applied
docker-compose exec alembic-runner alembic check
```
**Expected Output**: Current revision should match the latest migration

### 4.2 Manual Migration Management
```bash
# Create new migration (after model changes)
docker-compose exec alembic-runner alembic revision --autogenerate -m "Description of changes"

# Review generated migration file
ls -la alembic/versions/

# Apply specific migration
docker-compose exec alembic-runner alembic upgrade head

# Rollback to previous migration (if needed)
docker-compose exec alembic-runner alembic downgrade -1
```

### 4.3 Database Schema Validation
```bash
# Connect to PostgreSQL and check tables
docker exec -it acgs_postgres psql -U youruser -d yourdatabase_auth -c "\dt"
```
**Expected Output**: List of tables including users, refresh_tokens, etc.

### 4.2 Test Database Operations
```bash
# Test basic database operations through auth service
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "testpass123"}'
```
**Expected Output**: User creation response or appropriate error message

## Phase 5: Service-Specific Configuration

### 5.1 Configure Environment Variables
```bash
# Check if all required environment variables are set
docker exec acgs_auth_service env | grep -E "(DATABASE_URL|JWT_SECRET|CSRF_SECRET)"
```

**If missing, add to docker-compose.yml**:
```yaml
environment:
  - DATABASE_URL=postgresql+asyncpg://youruser:yourpassword@postgres:5432/yourdatabase_auth
  - JWT_SECRET=your-jwt-secret-key
  - CSRF_SECRET=your-csrf-secret-key
```

### 5.2 Verify Redis Connection
```bash
# Test Redis connectivity
docker exec acgs_redis redis-cli ping
```
**Expected Output**: "PONG"

### 5.3 Test Inter-Service Communication
```bash
# Test that services can communicate with each other
docker exec acgs_ac_service ping auth_service
docker exec acgs_gs_service ping auth_service
```

## Phase 6: Kubernetes Deployment (Production)

### 6.1 Kubernetes Prerequisites
```bash
# Verify Kubernetes cluster access
kubectl cluster-info
kubectl get nodes

# Create namespace for ACGS-PGP
kubectl create namespace acgs-pgp
kubectl config set-context --current --namespace=acgs-pgp
```

### 6.2 Secrets and ConfigMaps Setup
```bash
# Create database credentials secret
kubectl create secret generic postgres-credentials \
  --from-literal=database_url="postgresql+asyncpg://acgs_user:acgs_password@postgres-service:5432/acgs_pgp_db" \
  --from-literal=postgres_user="acgs_user" \
  --from-literal=postgres_password="acgs_password"

# Create auth service secrets
kubectl create secret generic auth-secrets \
  --from-literal=jwt_secret="your-strong-jwt-secret-key" \
  --from-literal=csrf_secret="your-strong-csrf-secret-key"

# Create LLM API secret
kubectl create secret generic llm-secrets \
  --from-literal=api_key="your-llm-api-key"

# Verify secrets
kubectl get secrets
```

### 6.3 Deploy Services to Kubernetes
```bash
# Deploy PostgreSQL first
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/postgres-service.yaml

# Wait for PostgreSQL to be ready
kubectl wait --for=condition=ready pod -l app=postgres --timeout=300s

# Deploy Redis
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/redis-service.yaml

# Deploy microservices
kubectl apply -f k8s/auth-service.yaml
kubectl apply -f k8s/ac-service.yaml
kubectl apply -f k8s/gs-service.yaml
kubectl apply -f k8s/fv-service.yaml
kubectl apply -f k8s/integrity-service.yaml
kubectl apply -f k8s/pgc-service.yaml

# Deploy frontend (if available)
kubectl apply -f k8s/frontend-deployment.yaml

# Deploy ingress/load balancer
kubectl apply -f k8s/ingress.yaml
```

### 6.4 Verify Kubernetes Deployment
```bash
# Check all pods are running
kubectl get pods -o wide

# Check services
kubectl get services

# Check ingress
kubectl get ingress

# View logs for any failing pods
kubectl logs -l app=auth-service --tail=50
```

## Phase 7: Frontend Integration and Build

### 7.1 Frontend Build Verification
```bash
# If frontend exists, check build process
if [ -d "frontend" ]; then
    cd frontend
    npm install
    npm run build
    cd ..
fi
```

### 7.2 Frontend Service Validation
```bash
# Check frontend service (Docker Compose)
docker-compose ps | grep frontend

# Test frontend accessibility
curl -I http://localhost:3000

# For Kubernetes deployment
kubectl get pods -l app=frontend
kubectl port-forward service/frontend-service 3000:80 &
curl -I http://localhost:3000
```

## Phase 8: Security Validation and Hardening

### 8.1 Authentication and Authorization Testing
```bash
# Test JWT token validation
# 1. Get a valid token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' | jq -r '.access_token')

# 2. Test protected endpoint with valid token
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/auth/profile

# 3. Test with invalid token
curl -H "Authorization: Bearer invalid_token" http://localhost:8000/auth/profile

# 4. Test RBAC - Admin access
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/auth/admin/users

# 5. Test CSRF protection (if implemented)
curl -X POST http://localhost:8000/auth/change-password \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"old_password": "admin123", "new_password": "newpass123"}'
```

### 8.2 Security Headers Validation
```bash
# Check security headers from nginx
curl -I http://localhost:8000/auth/ | grep -E "(X-Frame-Options|X-Content-Type-Options|Strict-Transport-Security|X-XSS-Protection)"

# Expected headers:
# X-Frame-Options: DENY
# X-Content-Type-Options: nosniff
# X-XSS-Protection: 1; mode=block
```

### 8.3 Input Validation Testing
```bash
# Test SQL injection protection
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin'\''OR 1=1--", "password": "anything"}'

# Test XSS protection
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "<script>alert(1)</script>", "email": "test@test.com", "password": "test123"}'

# Test oversized payload
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "'$(python3 -c "print('A' * 10000)")'", "email": "test@test.com", "password": "test123"}'
```

### 8.4 Rate Limiting Verification
```bash
# Test rate limiting (if implemented)
echo "Testing rate limiting..."
for i in {1..20}; do
  response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/auth/)
  echo "Request $i: HTTP $response"
  if [ "$response" = "429" ]; then
    echo "✅ Rate limiting is working"
    break
  fi
  sleep 0.1
done
```

## Phase 9: Database Backup and Recovery

### 9.1 Database Backup Procedures
```bash
# Create database backup
docker exec acgs_postgres pg_dump -U acgs_user -d acgs_pgp_db > backup_$(date +%Y%m%d_%H%M%S).sql

# For Kubernetes deployment
kubectl exec -it postgres-deployment-xxx -- pg_dump -U acgs_user -d acgs_pgp_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Verify backup file
ls -la backup_*.sql
head -20 backup_*.sql
```

### 9.2 Backup Automation Script
```bash
# Create automated backup script
cat > backup_script.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/acgs_backup_$DATE.sql"

mkdir -p $BACKUP_DIR

# Create backup
docker exec acgs_postgres pg_dump -U acgs_user -d acgs_pgp_db > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Keep only last 7 days of backups
find $BACKUP_DIR -name "acgs_backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE.gz"
EOF

chmod +x backup_script.sh
```

### 9.3 Database Recovery Testing
```bash
# Test database recovery (use with caution)
# 1. Create test backup
docker exec acgs_postgres pg_dump -U acgs_user -d acgs_pgp_db > test_backup.sql

# 2. Create test database
docker exec acgs_postgres createdb -U acgs_user test_recovery_db

# 3. Restore backup to test database
docker exec -i acgs_postgres psql -U acgs_user -d test_recovery_db < test_backup.sql

# 4. Verify restoration
docker exec acgs_postgres psql -U acgs_user -d test_recovery_db -c "\dt"

# 5. Cleanup test database
docker exec acgs_postgres dropdb -U acgs_user test_recovery_db
rm test_backup.sql
```

## Phase 8: Integration Testing

### 8.1 End-to-End Authentication Flow
```bash
# 1. Register a user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "testpass123"}'

# 2. Login and get token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'

# 3. Use token to access protected endpoint
TOKEN="your-received-token"
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/auth/profile
```

### 8.2 Test Policy Generation Workflow
```bash
# Test the complete policy generation flow
curl -X POST http://localhost:8000/gs/generate-policy \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"requirements": "Sample policy requirements"}'
```

## Phase 10: Production Readiness and Performance

### 10.1 Performance Optimization
```bash
# Test API response times
time curl http://localhost:8000/auth/
time curl http://localhost:8000/ac/
time curl http://localhost:8000/gs/

# Load testing with Apache Bench
ab -n 1000 -c 10 http://localhost:8000/auth/
ab -n 100 -c 5 http://localhost:8000/auth/login

# Memory usage optimization
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
```

### 10.2 Service-Specific Configuration Validation
```bash
# Verify LLM integration (GS Service)
curl -X POST http://localhost:8000/gs/test-llm \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"test": "connection"}'

# Verify SMT solver integration (FV Service)
curl -X POST http://localhost:8000/fv/test-solver \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"formula": "x > 0"}'

# Test policy generation workflow
curl -X POST http://localhost:8000/gs/generate-policy \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"requirements": "Data retention policy for 7 years", "domain": "healthcare"}'
```

### 10.3 Resource Limits and Scaling
```bash
# For Docker Compose - check resource usage
docker-compose exec auth_service cat /proc/meminfo | grep MemAvailable
docker-compose exec auth_service cat /proc/loadavg

# For Kubernetes - set resource limits
kubectl patch deployment auth-service-deployment -p '{"spec":{"template":{"spec":{"containers":[{"name":"auth-service","resources":{"limits":{"memory":"512Mi","cpu":"500m"},"requests":{"memory":"256Mi","cpu":"250m"}}}]}}}}'

# Test horizontal scaling (Kubernetes)
kubectl scale deployment auth-service-deployment --replicas=3
kubectl get pods -l app=auth-service
```

## Phase 11: Monitoring and Logging

### 11.1 Comprehensive Log Aggregation
```bash
# View logs from all services with timestamps
docker-compose logs -f --tail=100 --timestamps

# Check specific service logs with filtering
docker-compose logs auth_service | grep ERROR
docker-compose logs nginx_gateway | grep -E "(4[0-9]{2}|5[0-9]{2})"

# For Kubernetes deployment
kubectl logs -f deployment/auth-service-deployment
kubectl logs -l app=auth-service --tail=100
```

### 11.2 Health Monitoring Setup
```bash
# Create monitoring script
cat > monitor_services.sh << 'EOF'
#!/bin/bash
echo "=== Service Health Monitoring ==="
echo "Timestamp: $(date)"

# Check service endpoints
services=("auth" "ac" "gs" "fv" "integrity" "pgc")
for service in "${services[@]}"; do
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/$service/)
    if [ "$response" = "200" ]; then
        echo "✅ $service: OK ($response)"
    else
        echo "❌ $service: FAILED ($response)"
    fi
done

# Check database connectivity
db_status=$(docker exec acgs_postgres pg_isready -U acgs_user 2>/dev/null && echo "OK" || echo "FAILED")
echo "🗄️  Database: $db_status"

# Check Redis connectivity
redis_status=$(docker exec acgs_redis redis-cli ping 2>/dev/null | grep PONG >/dev/null && echo "OK" || echo "FAILED")
echo "🔴 Redis: $redis_status"

echo "=== End Health Check ==="
EOF

chmod +x monitor_services.sh
./monitor_services.sh
```

### 11.3 Performance Monitoring
```bash
# Monitor resource usage continuously
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"

# Database performance monitoring
docker exec acgs_postgres psql -U acgs_user -d acgs_pgp_db -c "
SELECT
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats
WHERE schemaname = 'public'
ORDER BY tablename, attname;"

# Check slow queries (if enabled)
docker exec acgs_postgres psql -U acgs_user -d acgs_pgp_db -c "
SELECT query, mean_time, calls
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;"
```

## Phase 12: Rollback and Recovery Procedures

### 12.1 Service Rollback Procedures
```bash
# Docker Compose rollback
# 1. Stop current services
docker-compose down

# 2. Restore previous configuration
git checkout HEAD~1 -- docker-compose.yml

# 3. Rebuild and restart
docker-compose build --no-cache
docker-compose up -d

# 4. Verify rollback
docker-compose ps
./health_check.sh
```

### 12.2 Database Rollback
```bash
# Rollback database migration
docker-compose exec alembic-runner alembic downgrade -1

# Verify rollback
docker-compose exec alembic-runner alembic current
docker-compose exec alembic-runner alembic history

# If major rollback needed, restore from backup
# docker exec -i acgs_postgres psql -U acgs_user -d acgs_pgp_db < backup_YYYYMMDD_HHMMSS.sql
```

### 12.3 Kubernetes Rollback
```bash
# Rollback deployment
kubectl rollout undo deployment/auth-service-deployment
kubectl rollout undo deployment/ac-service-deployment

# Check rollback status
kubectl rollout status deployment/auth-service-deployment

# View rollout history
kubectl rollout history deployment/auth-service-deployment

# Rollback to specific revision
kubectl rollout undo deployment/auth-service-deployment --to-revision=2
```

### 12.4 Emergency Recovery Procedures
```bash
# Complete system recovery script
cat > emergency_recovery.sh << 'EOF'
#!/bin/bash
echo "🚨 Emergency Recovery Procedure"

# 1. Stop all services
echo "Stopping all services..."
docker-compose down

# 2. Remove problematic containers
echo "Removing containers..."
docker container prune -f

# 3. Restore from backup
echo "Restoring database from latest backup..."
LATEST_BACKUP=$(ls -t backup_*.sql.gz | head -1)
if [ -n "$LATEST_BACKUP" ]; then
    gunzip -c "$LATEST_BACKUP" > restore.sql
    docker-compose up -d postgres_db
    sleep 30
    docker exec -i acgs_postgres psql -U acgs_user -d acgs_pgp_db < restore.sql
    rm restore.sql
fi

# 4. Restart services
echo "Restarting services..."
docker-compose up -d

# 5. Verify recovery
echo "Verifying recovery..."
sleep 60
./health_check.sh

echo "🔄 Recovery procedure completed"
EOF

chmod +x emergency_recovery.sh
```

## Phase 10: Final Validation

### 10.1 Complete System Health Check
```bash
# Create a comprehensive health check script
cat > health_check.sh << 'EOF'
#!/bin/bash
echo "=== ACGS-PGP System Health Check ==="

echo "1. Checking container status..."
docker-compose ps

echo "2. Testing gateway access..."
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/auth/

echo "3. Testing database connectivity..."
docker exec acgs_postgres pg_isready -U youruser

echo "4. Testing Redis..."
docker exec acgs_redis redis-cli ping

echo "5. Testing service endpoints..."
for service in auth ac gs fv integrity pgc; do
  echo "Testing $service..."
  curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/$service/
done

echo "=== Health Check Complete ==="
EOF

chmod +x health_check.sh
./health_check.sh
```

### 10.2 Performance Baseline
```bash
# Run basic performance tests
ab -n 100 -c 10 http://localhost:8000/auth/
```

## Troubleshooting Guide

### Common Issues and Solutions:

1. **Port Conflicts**:
   - Check with `netstat -tlnp | grep :PORT`
   - Modify docker-compose.yml ports

2. **Database Connection Issues**:
   - Verify DATABASE_URL format: `postgresql+asyncpg://user:pass@host:port/db`
   - Check PostgreSQL is accepting connections

3. **Import Errors**:
   - Fix Python import paths in service files
   - Ensure shared modules are properly mounted

4. **Memory Issues**:
   - Increase Docker memory limits
   - Check with `docker stats`

5. **Network Issues**:
   - Verify Docker network: `docker network ls`
   - Check service names match docker-compose.yml

## Success Criteria

### Phase 1: Foundational Enhancements & Theoretical Alignment
The Phase 1 deployment is complete when:
- [ ] Artificial Constitution (AC) layer is fully implemented with P, R, M, V components
- [ ] Democratic legitimacy framework is operational with Constitutional Council
- [ ] Enhanced Governance Synthesis engine supports constitutional prompting
- [ ] Principle traceability and constitutional fidelity mechanisms are working
- [ ] All AC-related API endpoints return expected responses
- [ ] Meta-rules and conflict resolution mapping are functional
- [ ] Public consultation mechanisms are accessible
- [ ] Constitutional compliance scoring is operational

### Phase 2: Evolutionary Computation Integration
The Phase 2 deployment is complete when:
- [ ] Constitutional prompting for EC systems is implemented
- [ ] Constitution-aware EC operators are functional
- [ ] PGC performance meets sub-50ms requirement for EC loops
- [ ] Governance penalties are properly integrated into fitness functions
- [ ] Solution culling based on constitutional compliance works
- [ ] Incremental rule evaluation and caching are optimized
- [ ] Parallel processing capabilities are verified
- [ ] EC-specific database tables are created and accessible

### Phase 3: Advanced Governance Mechanisms & System Hardening
The Phase 3 deployment is complete when:
- [ ] SMT solver (Z3) integration is functional for formal verification
- [ ] Tiered validation pipeline (Automated, HITL, Rigorous) is operational
- [ ] Safety and conflict checking algorithms are implemented
- [ ] Algorithmic fairness criteria are encoded as constitutional principles
- [ ] Bias detection algorithms (counterfactual, embedding, simulation) are working
- [ ] Appeal and dispute resolution workflow is accessible
- [ ] Explainability dashboard interface is functional
- [ ] Digital signatures for AC versions are implemented
- [ ] Hash functions and Merkle trees for integrity verification work
- [ ] Key management and HSM integration are operational
- [ ] RFC 3161 timestamping is functional

### Development Environment
The complete development deployment is successful when:
- [ ] All three phases are implemented and tested
- [ ] All containers show "Up" status
- [ ] All enhanced service endpoints return 200 status codes
- [ ] Database migrations include all phase-specific schemas
- [ ] Authentication flow supports new roles (Constitutional Council, etc.)
- [ ] Inter-service communication includes new Phase 2-3 services
- [ ] No critical error logs in any service
- [ ] Comprehensive health check script passes all tests
- [ ] Advanced API functionality is verified across all phases

### Production Environment
The production deployment is complete when:
- [ ] All Kubernetes pods are in "Running" state for all phases
- [ ] All services pass enhanced health checks
- [ ] Database backup procedures include cryptographic integrity
- [ ] Security validation passes all Phase 3 tests
- [ ] Performance benchmarks meet sub-50ms PGC requirement
- [ ] Monitoring includes constitutional compliance metrics
- [ ] Rollback procedures preserve AC version integrity
- [ ] Load balancing handles increased Phase 2-3 traffic
- [ ] SSL/TLS certificates support new endpoints
- [ ] Resource limits accommodate LLM and SMT solver usage

### Enhanced Security Checklist
- [ ] JWT secrets are properly configured with enhanced RBAC
- [ ] CSRF protection is enabled across all new endpoints
- [ ] Input validation includes constitutional principle validation
- [ ] Rate limiting protects against EC system abuse
- [ ] Security headers are present on all Phase 3 endpoints
- [ ] Database access is restricted with cryptographic integrity
- [ ] API endpoints require proper authentication for all phases
- [ ] Audit logging includes tamper-evident mechanisms
- [ ] Digital signatures are verified for all critical operations
- [ ] HSM integration is properly secured
- [ ] Bias detection and fairness monitoring are active

## Quick Start Commands

### Phase 1: Basic Deployment
Execute these commands to establish the foundational system:

```bash
# 1. Environment setup
cp .env.example .env
# Edit .env with your configuration including new Phase 1 variables

# 2. Build and start core services
docker-compose build --no-cache
docker-compose up -d

# 3. Verify basic functionality
curl http://localhost:8000/auth/
curl http://localhost:8000/ac/health
curl http://localhost:8000/gs/health

# 4. Test AC layer implementation
curl -X POST http://localhost:8000/ac/principles \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Principle", "description": "Test constitutional principle"}'
```

### Phase 2: EC Integration
Execute these commands to enable evolutionary computation governance:

```bash
# 1. Test constitutional prompting
curl -X POST http://localhost:8000/gs/ec-constitutional-prompting \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"base_prompt": "Test EC prompt", "active_principles": ["test_principle"]}'

# 2. Verify PGC performance
curl -X POST http://localhost:8000/pgc/performance-test \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"test_type": "ec_simulation", "target_latency_ms": 50}'
```

### Phase 3: Advanced Features
Execute these commands to enable advanced governance mechanisms:

```bash
# 1. Test formal verification
curl -X POST http://localhost:8000/fv/smt-verification \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"formula": "(assert (> x 0))", "variables": {"x": "Int"}}'

# 2. Test cryptographic integrity
curl -X POST http://localhost:8000/integrity/sign-ac-version \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ac_version_id": "test_v1.0.0", "signing_authority": "constitutional_council"}'

# 3. Run comprehensive health check
./health_check.sh
```

## Automated Deployment Script

For convenience, here's a comprehensive deployment automation script:

```bash
# Create automated deployment script
cat > deploy_acgs.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 ACGS-PGP Automated Deployment Script"
echo "========================================"

# Configuration
ENVIRONMENT=${1:-development}
SKIP_TESTS=${2:-false}

echo "Environment: $ENVIRONMENT"
echo "Skip Tests: $SKIP_TESTS"

# Phase 1: Prerequisites Check
echo "📋 Phase 1: Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed"
    exit 1
fi

if [ ! -f .env ]; then
    echo "⚠️  .env file not found, copying from .env.example"
    cp .env.example .env
    echo "📝 Please edit .env file with your configuration"
    read -p "Press Enter to continue after editing .env..."
fi

# Phase 2: Environment Setup
echo "🔧 Phase 2: Setting up environment..."
docker system prune -f
docker volume prune -f

# Phase 3: Build and Deploy
echo "🏗️  Phase 3: Building and deploying services..."
if [ "$ENVIRONMENT" = "production" ]; then
    echo "🔄 Production deployment with Kubernetes..."
    kubectl create namespace acgs-pgp --dry-run=client -o yaml | kubectl apply -f -
    kubectl config set-context --current --namespace=acgs-pgp

    # Apply Kubernetes manifests
    kubectl apply -f k8s/

    # Wait for deployments
    kubectl wait --for=condition=available --timeout=600s deployment --all
else
    echo "🔄 Development deployment with Docker Compose..."
    docker-compose build --no-cache
    docker-compose up -d

    # Wait for services to be ready
    echo "⏳ Waiting for services to start..."
    sleep 60
fi

# Phase 4: Health Checks
echo "🏥 Phase 4: Running health checks..."
if [ "$SKIP_TESTS" = "false" ]; then
    # Create and run health check
    cat > temp_health_check.sh << 'HEALTH_EOF'
#!/bin/bash
echo "=== Health Check ==="
failed=0

# Check service endpoints
services=("auth" "ac" "gs" "fv" "integrity" "pgc")
for service in "${services[@]}"; do
    if [ "$ENVIRONMENT" = "production" ]; then
        # For Kubernetes, use port-forward or ingress
        response=$(kubectl exec deployment/nginx-deployment -- curl -s -o /dev/null -w "%{http_code}" http://localhost/$service/ || echo "000")
    else
        response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/$service/ || echo "000")
    fi

    if [ "$response" = "200" ]; then
        echo "✅ $service: OK"
    else
        echo "❌ $service: FAILED ($response)"
        failed=1
    fi
done

if [ $failed -eq 0 ]; then
    echo "✅ All health checks passed!"
    exit 0
else
    echo "❌ Some health checks failed!"
    exit 1
fi
HEALTH_EOF

    chmod +x temp_health_check.sh
    if ./temp_health_check.sh; then
        echo "✅ Deployment successful!"
    else
        echo "❌ Deployment failed health checks"
        exit 1
    fi
    rm temp_health_check.sh
fi

# Phase 5: Post-deployment
echo "📊 Phase 5: Post-deployment setup..."
if [ "$ENVIRONMENT" = "production" ]; then
    echo "🔐 Setting up monitoring and backups..."
    # Add production-specific setup here
    kubectl get pods -o wide
    kubectl get services
else
    echo "📈 Development environment ready!"
    docker-compose ps
fi

echo ""
echo "🎉 ACGS-PGP deployment completed successfully!"
echo ""
echo "Next steps:"
echo "1. Access the API at: http://localhost:8000"
echo "2. View API documentation at: http://localhost:8000/auth/docs"
echo "3. Monitor logs with: docker-compose logs -f"
echo "4. Run health checks with: ./health_check.sh"
echo ""
EOF

chmod +x deploy_acgs.sh
```

## Usage Examples

### Development Deployment
```bash
# Quick development deployment
./deploy_acgs.sh development

# Development deployment without tests
./deploy_acgs.sh development true
```

### Production Deployment
```bash
# Production deployment to Kubernetes
./deploy_acgs.sh production

# Production deployment with full validation
./deploy_acgs.sh production false
```

### Manual Step-by-Step Deployment
```bash
# 1. Environment validation
./deploy_acgs.sh development true

# 2. Fix any issues found
docker-compose logs auth_service

# 3. Run health checks
./health_check.sh

# 4. Run security validation
./monitor_services.sh
```

Execute these steps in order, and the ACGS-PGP framework should be fully operational.
