# ACGS-PGP Development Workflow Documentation

## 🎯 Overview

This document outlines the development workflow, coding standards, testing procedures, and deployment processes for the **ACGS-PGP (AI Compliance Governance System - Policy Generation Platform)**.

## 🏗️ Development Environment Setup

### **Prerequisites**
```bash
# Required Software
- Python 3.11+
- Node.js 18+
- Docker 24.0+
- Docker Compose 2.0+
- Git 2.30+
- PostgreSQL 15+ (for local development)
- Redis 7.0+ (for caching)

# Development Tools
- VS Code / PyCharm
- Postman / Insomnia (API testing)
- pgAdmin / DBeaver (database management)
- Git GUI client (optional)
```

### **Local Environment Setup**
```bash
# Clone repository
git clone https://github.com/dislovemartin/ACGS.git
cd ACGS-master

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Copy environment configuration
cp config/env/.env.example config/env/.env

# Start development services
cd config/docker
docker-compose -f docker-compose.dev.yml up -d

# Run database migrations
./scripts/run_migrations.sh

# Seed test data
./scripts/seed_test_data.sh

# Verify setup
./scripts/health_check_all_services.sh
```

### **TaskMaster AI Integration**
```bash
# Initialize TaskMaster AI for project management
cd /path/to/ACGS-master
python -m taskmaster_ai.cli initialize_project --project-root $(pwd) --yes

# Configure AI models
python -m taskmaster_ai.cli models --set-main gpt-4 --set-research perplexity --set-fallback gpt-3.5-turbo

# Check current tasks
python -m taskmaster_ai.cli get_tasks --with-subtasks

# Get next task to work on
python -m taskmaster_ai.cli next_task
```

## 📋 Development Standards

### **Code Style Guidelines**

#### **Python Standards**
```python
# Follow PEP 8 with these specific requirements:

# 1. Line length: 88 characters (Black formatter)
# 2. Import organization (isort)
from __future__ import annotations

import os
import sys
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.models import BaseEntity
from src.shared.utils import logger

# 3. Type hints required for all functions
async def create_policy(
    db: AsyncSession,
    policy_data: PolicyCreate,
    user_id: str
) -> PolicyResponse:
    """Create a new policy with constitutional validation.
    
    Args:
        db: Database session
        policy_data: Policy creation data
        user_id: ID of the user creating the policy
        
    Returns:
        Created policy response
        
    Raises:
        HTTPException: If validation fails
    """
    pass

# 4. Docstring format (Google style)
class PolicyService:
    """Service for managing AI governance policies.
    
    This service handles policy creation, validation, and enforcement
    with constitutional compliance checking.
    
    Attributes:
        db: Database session
        constitutional_validator: Constitutional compliance validator
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.constitutional_validator = ConstitutionalValidator()

# 5. Error handling patterns
try:
    result = await policy_service.create_policy(policy_data)
except ValidationError as e:
    logger.error(f"Policy validation failed: {e}")
    raise HTTPException(status_code=422, detail=str(e))
except DatabaseError as e:
    logger.error(f"Database error: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

#### **JavaScript/TypeScript Standards**
```typescript
// Follow Airbnb style guide with these additions:

// 1. Use TypeScript for all new code
interface PolicyData {
  id: string;
  name: string;
  description: string;
  constitutionalPrinciples: string[];
  createdAt: Date;
  updatedAt: Date;
}

// 2. Functional components with hooks
import React, { useState, useEffect, useCallback } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';

const PolicyManager: React.FC = () => {
  const [selectedPolicy, setSelectedPolicy] = useState<PolicyData | null>(null);
  
  const { data: policies, isLoading } = useQuery({
    queryKey: ['policies'],
    queryFn: fetchPolicies,
  });
  
  const createPolicyMutation = useMutation({
    mutationFn: createPolicy,
    onSuccess: () => {
      // Handle success
    },
  });
  
  return (
    <div className="policy-manager">
      {/* Component JSX */}
    </div>
  );
};

// 3. Error boundaries for robust error handling
class PolicyErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }
  
  static getDerivedStateFromError(error: Error): State {
    return { hasError: true };
  }
  
  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Policy component error:', error, errorInfo);
  }
  
  render() {
    if (this.state.hasError) {
      return <ErrorFallback />;
    }
    
    return this.props.children;
  }
}
```

### **Database Standards**
```sql
-- 1. Naming conventions
-- Tables: snake_case, plural
-- Columns: snake_case
-- Indexes: idx_table_column
-- Foreign keys: fk_table_referenced_table

-- 2. Migration structure
-- migrations/versions/001_create_constitutional_principles.py
"""Create constitutional principles table

Revision ID: 001
Revises: 
Create Date: 2024-01-15 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.create_table(
        'constitutional_principles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('priority_weight', sa.Numeric(3, 2), default=1.0),
        sa.Column('scope', sa.String(100), default='general'),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Create indexes
    op.create_index('idx_constitutional_principles_name', 'constitutional_principles', ['name'])
    op.create_index('idx_constitutional_principles_scope', 'constitutional_principles', ['scope'])

def downgrade():
    op.drop_table('constitutional_principles')

-- 3. Query optimization
-- Always use appropriate indexes
-- Use EXPLAIN ANALYZE for complex queries
-- Implement connection pooling
-- Use prepared statements for repeated queries
```

## 🧪 Testing Standards

### **Test Structure**
```
tests/
├── unit/                    # Unit tests for individual components
│   ├── auth_service/
│   ├── ac_service/
│   ├── integrity_service/
│   ├── fv_service/
│   ├── gs_service/
│   ├── pgc_service/
│   └── ec_service/
├── integration/             # Integration tests between services
│   ├── test_policy_pipeline.py
│   ├── test_constitutional_council.py
│   └── test_auth_flow.py
├── e2e/                     # End-to-end tests
│   ├── test_complete_workflows.py
│   └── test_user_journeys.py
├── performance/             # Performance and load tests
│   ├── test_load_scenarios.py
│   └── test_stress_testing.py
└── fixtures/                # Test data and fixtures
    ├── test_users.json
    ├── test_policies.json
    └── test_principles.json
```

### **Testing Patterns**
```python
# Unit Test Example
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from src.auth_service.main import app
from src.auth_service.services.auth_service import AuthService
from tests.fixtures.auth_fixtures import mock_user, mock_jwt_token

class TestAuthService:
    """Test suite for authentication service."""
    
    @pytest.fixture
    def auth_service(self):
        return AuthService(db=AsyncMock())
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, auth_service, mock_user):
        """Test successful user authentication."""
        # Arrange
        auth_service.db.get_user_by_email = AsyncMock(return_value=mock_user)
        auth_service.verify_password = AsyncMock(return_value=True)
        
        # Act
        result = await auth_service.authenticate_user("test@example.com", "password")
        
        # Assert
        assert result is not None
        assert result.email == "test@example.com"
        auth_service.db.get_user_by_email.assert_called_once_with("test@example.com")
    
    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_password(self, auth_service, mock_user):
        """Test authentication with invalid password."""
        # Arrange
        auth_service.db.get_user_by_email = AsyncMock(return_value=mock_user)
        auth_service.verify_password = AsyncMock(return_value=False)
        
        # Act
        result = await auth_service.authenticate_user("test@example.com", "wrong_password")
        
        # Assert
        assert result is None

# Integration Test Example
class TestPolicyPipeline:
    """Test complete policy creation and enforcement pipeline."""
    
    @pytest.mark.asyncio
    async def test_complete_policy_workflow(self, test_client, auth_headers):
        """Test complete policy workflow from creation to enforcement."""
        # 1. Create constitutional principle
        principle_data = {
            "name": "Test Principle",
            "description": "Test constitutional principle",
            "priority_weight": 1.0
        }
        principle_response = test_client.post(
            "/api/v1/principles/",
            json=principle_data,
            headers=auth_headers
        )
        assert principle_response.status_code == 201
        
        # 2. Synthesize policy using GS service
        synthesis_data = {
            "prompt": "Create a policy for data privacy",
            "constitutional_principles": [principle_response.json()["id"]]
        }
        synthesis_response = test_client.post(
            "/api/v1/synthesize/policy",
            json=synthesis_data,
            headers=auth_headers
        )
        assert synthesis_response.status_code == 200
        
        # 3. Verify policy using FV service
        policy_content = synthesis_response.json()["policy_content"]
        verification_response = test_client.post(
            "/api/v1/verify/policy",
            json={"policy_content": policy_content},
            headers=auth_headers
        )
        assert verification_response.status_code == 200
        assert verification_response.json()["result"] == "valid"
        
        # 4. Store policy with integrity service
        policy_data = {
            "name": "Test Policy",
            "content": policy_content
        }
        policy_response = test_client.post(
            "/api/v1/policies/",
            json=policy_data,
            headers=auth_headers
        )
        assert policy_response.status_code == 201
        
        # 5. Deploy policy to PGC service
        deployment_response = test_client.post(
            f"/api/v1/enforcement/rules",
            json={"policy_id": policy_response.json()["id"]},
            headers=auth_headers
        )
        assert deployment_response.status_code == 201

# Performance Test Example
class TestPerformance:
    """Performance and load testing."""
    
    @pytest.mark.performance
    def test_authentication_performance(self, test_client):
        """Test authentication endpoint performance."""
        import time
        
        login_data = {"username": "test@example.com", "password": "password"}
        
        # Measure response time for 100 requests
        start_time = time.time()
        for _ in range(100):
            response = test_client.post("/auth/login", json=login_data)
            assert response.status_code == 200
        
        end_time = time.time()
        avg_response_time = (end_time - start_time) / 100
        
        # Assert average response time is under 50ms
        assert avg_response_time < 0.05, f"Average response time {avg_response_time}s exceeds 50ms"
```

### **Test Coverage Requirements**
```yaml
coverage_targets:
  overall: 95%
  unit_tests: 98%
  integration_tests: 90%
  critical_paths: 100%

coverage_exclusions:
  - "*/migrations/*"
  - "*/tests/*"
  - "*/venv/*"
  - "*/node_modules/*"
  - "*/__pycache__/*"

critical_paths:
  - "Authentication flow"
  - "Policy synthesis pipeline"
  - "Constitutional Council workflows"
  - "Cryptographic integrity operations"
  - "Formal verification processes"
```

## 🔄 Git Workflow

### **Branch Strategy**
```
main                    # Production-ready code
├── develop            # Integration branch for features
├── feature/           # Feature development branches
│   ├── feature/constitutional-council
│   ├── feature/wina-optimization
│   └── feature/qec-enhancements
├── hotfix/            # Critical production fixes
│   └── hotfix/security-patch-001
└── release/           # Release preparation branches
    └── release/v1.1.0
```

### **Commit Message Standards**
```bash
# Format: <type>(<scope>): <description>
# 
# <body>
# 
# <footer>

# Types:
feat: new feature
fix: bug fix
docs: documentation changes
style: formatting, missing semicolons, etc.
refactor: code change that neither fixes a bug nor adds a feature
test: adding missing tests
chore: maintain

# Examples:
feat(ac-service): add Constitutional Council amendment voting

Implement democratic voting mechanism for constitutional amendments
with cryptographic proof of votes and automatic threshold calculation.

- Add amendment voting endpoints
- Implement vote validation and storage
- Add cryptographic signature for vote integrity
- Update Constitutional Council dashboard

Closes #123

fix(auth-service): resolve JWT token expiration edge case

Fix issue where JWT tokens were not properly validated when
system clock was slightly out of sync.

- Add clock skew tolerance of 30 seconds
- Improve error messages for token validation
- Add comprehensive tests for edge cases

Fixes #456

docs(deployment): update Docker Compose configuration

Update deployment documentation to reflect new service ports
and environment variable requirements for WINA optimization.

- Update service port mappings
- Add WINA configuration variables
- Include performance tuning guidelines
```

### **Pull Request Process**
```yaml
pr_requirements:
  title: "Clear, descriptive title following commit message format"
  description:
    - "Problem description"
    - "Solution approach"
    - "Testing performed"
    - "Breaking changes (if any)"
  
  checklist:
    - "[ ] Code follows style guidelines"
    - "[ ] Self-review completed"
    - "[ ] Tests added/updated"
    - "[ ] Documentation updated"
    - "[ ] No breaking changes (or documented)"
    - "[ ] Security implications considered"
    - "[ ] Performance impact assessed"
  
  reviews:
    required: 2
    required_from_codeowners: true
    dismiss_stale_reviews: true
  
  checks:
    - "All tests pass"
    - "Code coverage >= 95%"
    - "Security scan passes"
    - "Performance benchmarks pass"
    - "Documentation builds successfully"

merge_strategy:
  default: "squash"
  exceptions:
    - "feature branches with multiple logical commits"
    - "release branches"
```

## 🚀 Deployment Process

### **Continuous Integration**
```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.11, 3.12]
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-dev.txt
    
    - name: Run linting
      run: |
        black --check src/
        isort --check-only src/
        flake8 src/
        mypy src/
    
    - name: Run security scan
      run: |
        bandit -r src/
        safety check
    
    - name: Run tests
      run: |
        pytest tests/ --cov=src --cov-report=xml --cov-fail-under=95
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  build:
    needs: test
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Build Docker images
      run: |
        docker-compose -f config/docker/docker-compose.yml build
    
    - name: Run integration tests
      run: |
        docker-compose -f config/docker/docker-compose.test.yml up --abort-on-container-exit
    
    - name: Security scan images
      run: |
        docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
          aquasec/trivy image --severity HIGH,CRITICAL acgs-pgp:latest

  deploy:
    needs: [test, build]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Deploy to staging
      run: |
        # Deployment script
        ./scripts/deploy_staging.sh
    
    - name: Run smoke tests
      run: |
        ./scripts/smoke_tests.sh
    
    - name: Deploy to production
      if: success()
      run: |
        ./scripts/deploy_production.sh
```

### **Deployment Environments**

#### **Development Environment**
```bash
# Local development with hot reload
cd config/docker
docker-compose -f docker-compose.dev.yml up -d

# Features:
# - Hot reload for code changes
# - Debug logging enabled
# - Test data seeded
# - All services exposed on localhost
# - Development-specific environment variables
```

#### **Staging Environment**
```bash
# Staging deployment (production-like)
./scripts/deploy_staging.sh

# Features:
# - Production Docker images
# - Production-like data volumes
# - SSL certificates (staging)
# - Monitoring stack enabled
# - Load testing performed
```

#### **Production Environment**
```bash
# Production deployment
./scripts/deploy_production.sh

# Features:
# - High availability configuration
# - SSL certificates (production)
# - Backup and disaster recovery
# - Full monitoring and alerting
# - Security hardening applied
```

## 📊 Quality Assurance

### **Code Quality Metrics**
```yaml
quality_gates:
  code_coverage: ">= 95%"
  test_success_rate: "100%"
  security_vulnerabilities: "0 high/critical"
  performance_regression: "< 5%"
  documentation_coverage: ">= 90%"

automated_checks:
  pre_commit:
    - "black"
    - "isort"
    - "flake8"
    - "mypy"
    - "pytest-quick"
  
  ci_pipeline:
    - "full test suite"
    - "security scanning"
    - "performance benchmarks"
    - "integration tests"
    - "documentation build"
  
  deployment:
    - "smoke tests"
    - "health checks"
    - "monitoring validation"
    - "rollback verification"
```

### **Performance Monitoring**
```python
# Performance monitoring integration
from prometheus_client import Counter, Histogram, Gauge

# Metrics collection
REQUEST_COUNT = Counter('acgs_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('acgs_request_duration_seconds', 'Request duration')
ACTIVE_CONNECTIONS = Gauge('acgs_active_connections', 'Active database connections')

# Usage in FastAPI
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    REQUEST_DURATION.observe(duration)
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    return response
```

## 🔧 Development Tools

### **Recommended VS Code Extensions**
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.black-formatter",
    "ms-python.isort",
    "ms-python.flake8",
    "ms-python.mypy-type-checker",
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "ms-vscode.vscode-typescript-next",
    "ms-vscode-remote.remote-containers",
    "ms-azuretools.vscode-docker",
    "redhat.vscode-yaml",
    "ms-vscode.test-adapter-converter"
  ]
}
```

### **Development Scripts**
```bash
# Available development scripts in scripts/
./scripts/setup_dev_environment.sh    # Initial development setup
./scripts/run_tests.sh                # Run all tests
./scripts/run_linting.sh              # Run code quality checks
./scripts/run_migrations.sh           # Apply database migrations
./scripts/seed_test_data.sh           # Seed development test data
./scripts/health_check_all_services.sh # Check all service health
./scripts/load_test_monitoring.sh     # Run load tests
./scripts/backup_database.sh          # Backup development database
./scripts/reset_dev_environment.sh    # Reset development environment
```

---

**Last Updated**: January 2024  
**Version**: 1.0.0  
**Maintainer**: ACGS-PGP Development Team
