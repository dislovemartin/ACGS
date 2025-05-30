#!/bin/bash
# ACGS-PGP Comprehensive Workflow Validation
# Tests end-to-end workflows with loaded test data

source auth_tokens.env

echo "🚀 ACGS-PGP Comprehensive Workflow Testing"
echo "=========================================="

echo "1. Testing Enhanced Principle Management..."
curl -H "Authorization: Bearer $ADMIN_TOKEN" http://localhost:8001/api/v1/principles/ | jq '.total'

echo -e "
2. Testing Constitutional Synthesis..."
curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json"   http://localhost:8004/api/v1/constitutional/analyze-context   -d '{"context": "healthcare_ai_systems", "category": "Safety"}' | jq .

echo -e "
3. Testing Constitutional Council..."
curl -H "Authorization: Bearer $COUNCIL_TOKEN" http://localhost:8001/api/v1/constitutional-council/meta-rules | jq .

echo -e "
4. Testing AlphaEvolve Integration..."
curl -H "Authorization: Bearer $POLICY_MANAGER_TOKEN" http://localhost:8004/api/v1/alphaevolve/constitutional-prompting | jq .

echo -e "
5. Testing Formal Verification..."
curl -H "Authorization: Bearer $ADMIN_TOKEN" http://localhost:8003/api/v1/verify/ | jq .

echo -e "
6. Testing Cryptographic Integrity..."
curl -H "Authorization: Bearer $AUDITOR_TOKEN" http://localhost:8002/api/v1/integrity/ | jq .

echo -e "
✅ Comprehensive Workflow Testing Complete"
