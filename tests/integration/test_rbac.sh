#!/bin/bash
# ACGS-PGP RBAC Testing Script
# Tests Role-Based Access Control with generated tokens

source auth_tokens.env

echo "🔐 Testing RBAC with Generated Tokens"
echo "======================================"

echo "1. Testing Admin Access..."
curl -H "Authorization: Bearer $ADMIN_TOKEN" http://localhost:8001/api/v1/principles/ | jq .

echo -e "
2. Testing Policy Manager Access..."
curl -H "Authorization: Bearer $POLICY_MANAGER_TOKEN" http://localhost:8004/api/v1/synthesize/ | jq .

echo -e "
3. Testing Auditor Access..."
curl -H "Authorization: Bearer $AUDITOR_TOKEN" http://localhost:8002/api/v1/audit/ | jq .

echo -e "
4. Testing Constitutional Council Access..."
curl -H "Authorization: Bearer $COUNCIL_TOKEN" http://localhost:8001/api/v1/constitutional-council/amendments | jq .

echo -e "
✅ RBAC Testing Complete"
