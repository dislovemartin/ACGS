# ACGS-PGP Test Suite

This directory contains all tests for the AI Compliance Governance System - Policy Generation Platform (ACGS-PGP).

## Directory Structure

### `unit/`
Unit tests for individual components and services:
- Service-specific test files
- Component isolation testing
- Mock-based testing for external dependencies
- Fast execution for development feedback

### `integration/`
Integration tests for cross-service functionality:
- **Phase 1 Tests**: Enhanced Principle Management, Constitutional Prompting, Contextual Analysis
- **Phase 2 Tests**: AlphaEvolve integration, Evolutionary Computation governance
- **Phase 3 Tests**: Z3 formal verification, Algorithmic fairness, PGP Assurance, Appeals/Dispute resolution
- Service communication testing
- Database integration testing
- API endpoint testing

### `e2e/`
End-to-end workflow tests:
- Complete governance pipeline testing
- User workflow validation
- System-wide integration testing
- Performance and load testing

## Test Categories

### Core Framework Tests
- `test_phase1_implementation.py` - Phase 1 foundational features
- `test_phase2_alphaevolve_integration.py` - AlphaEvolve integration
- `test_phase3_z3_integration.py` - Z3 formal verification
- `test_phase3_pgp_assurance.py` - Cryptographic integrity
- `test_phase3_algorithmic_fairness.py` - Fairness evaluation
- `test_phase3_appeals_dispute_resolution.py` - Appeals workflow

### Component-Specific Tests
- `test_constitutional_council_implementation.py` - Constitutional Council
- `test_conflict_resolution_implementation.py` - Conflict resolution
- `test_meta_rules_implementation.py` - Meta-rules management
- `test_audit_compliance_implementation.py` - Audit compliance
- `test_cryptographic_integrity_phase3.py` - Cryptographic features

### Utility Tests
- `test_crypto_standalone.py` - Standalone cryptographic functions
- `test_comprehensive_workflow.sh` - Complete workflow validation
- `test_disaster_recovery.sh` - Disaster recovery procedures
- `test_rbac.sh` - Role-based access control

## Running Tests

### All Tests
```bash
# Run complete test suite
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html
```

### By Category
```bash
# Unit tests only
python -m pytest tests/unit/ -v

# Integration tests only
python -m pytest tests/integration/ -v

# End-to-end tests only
python -m pytest tests/e2e/ -v
```

### Specific Test Files
```bash
# Phase 1 tests
python tests/integration/test_phase1_implementation.py

# Phase 2 tests
python tests/integration/test_phase2_alphaevolve_integration.py

# Phase 3 tests
python tests/integration/test_phase3_z3_integration.py
```

## Test Data

Test data files are located in the `data/` directory:
- `test_scenarios.json` - Test scenarios and configurations
- `test_environmental_factors.json` - Environmental context data
- `phase2_test_results.json` - Phase 2 test results
- `testplan.md` - Comprehensive test plan documentation

## Test Requirements

- All services must be running (use Docker Compose)
- Database must be initialized with test data
- Environment variables must be configured
- External dependencies (LLM APIs, Z3 solver) must be available

## Continuous Integration

Tests are automatically run on:
- Pull requests
- Main branch commits
- Release candidates

See `.github/workflows/` for CI configuration details.
