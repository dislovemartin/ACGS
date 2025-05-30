# ACGS-PGP Framework File Organization & Cleanup Plan

## Overview
This document outlines the comprehensive file organization and cleanup plan for the ACGS-PGP framework to improve maintainability, reduce redundancy, and ensure consistent structure.

## Phase 1: Duplicate Requirements Files Cleanup

### Identified Duplicate Files to Remove:
1. **AC Service**:
   - `backend/ac_service/requirements_new.txt` (duplicate of requirements.txt)
   
2. **FV Service**:
   - `backend/fv_service/requirements_base.txt` (consolidate into requirements.txt)
   
3. **GS Service**:
   - `backend/gs_service/requirements_new.txt` (duplicate of requirements.txt)
   
4. **Auth Service**:
   - `backend/auth_service/requirements_simple.txt` (if exists, consolidate)

### Actions:
- Remove duplicate requirements files
- Ensure main requirements.txt files are comprehensive
- Update Dockerfiles to reference correct requirements files

## Phase 2: Deprecated Files Cleanup

### Files to Remove:
1. **Backup/Temporary Files**:
   - `backend/shared_backup_temp/` (entire directory - appears to be temporary backup)
   
2. **Compiled/Generated Files**:
   - `ACGS-PGP_Framework/*.aux`, `*.bbl`, `*.blg`, `*.out` files
   - `AlphaEvolve-ACGS_Integration_System/*.aux`, `*.log` files (keep main.pdf)
   
3. **Cache Files**:
   - `__pycache__` directories (should be in .gitignore)

## Phase 3: File Naming Standardization

### Current Inconsistencies:
1. **Test Files**: Mix of `test_*.py` and `*_test.py` patterns
2. **Configuration Files**: Inconsistent naming patterns
3. **Documentation Files**: Mixed case and underscore usage

### Standardization Rules:
- Test files: `test_*.py` format
- Configuration files: `snake_case.ext`
- Documentation files: `UPPER_CASE.md` for important docs, `lower_case.md` for others
- Service directories: `snake_case`

## Phase 4: Directory Structure Optimization

### Current Structure Issues:
1. **Mixed service locations**: Some services in `backend/`, others in root
2. **Inconsistent shared module usage**
3. **Test files scattered across directories

### Proposed Structure:
```
ACGS-master/
├── backend/
│   ├── shared/           # Shared modules and utilities
│   ├── ac_service/       # Audit & Compliance Service
│   ├── auth_service/     # Authentication Service  
│   ├── gs_service/       # Governance Synthesis Service
│   ├── fv_service/       # Formal Verification Service
│   ├── integrity_service/ # Integrity & Verifiability Service
│   └── pgc_service/      # Protective Governance Controls Service
├── tests/                # Centralized test directory
│   ├── unit/            # Unit tests by service
│   ├── integration/     # Integration tests
│   └── e2e/            # End-to-end tests
├── docs/                # Documentation
├── scripts/             # Utility scripts
├── k8s/                 # Kubernetes configurations
├── frontend/            # Frontend application
└── deployment/          # Deployment configurations
```

## Phase 5: Import Statement Updates

### Issues to Fix:
1. **Relative imports**: Update to absolute imports where appropriate
2. **Deprecated imports**: Remove unused imports
3. **Circular imports**: Resolve circular dependencies
4. **Missing imports**: Add missing imports for new functionality

## Phase 6: Code Quality Improvements

### Standards to Implement:
1. **Consistent formatting**: Apply black/autopep8
2. **Type hints**: Add type annotations
3. **Docstrings**: Ensure all functions have proper docstrings
4. **Error handling**: Standardize exception handling patterns

## Implementation Priority

### High Priority (Immediate):
1. Remove duplicate requirements files
2. Clean up backup/temporary directories
3. Standardize test file naming
4. Update import statements

### Medium Priority (Next Sprint):
1. Reorganize directory structure
2. Consolidate test files
3. Update documentation structure
4. Implement code formatting standards

### Low Priority (Future):
1. Advanced code quality improvements
2. Performance optimizations
3. Additional tooling integration

## Validation Steps

After each phase:
1. Run all tests to ensure no breakage
2. Verify Docker builds work correctly
3. Check that all services start properly
4. Validate API endpoints are accessible
5. Confirm documentation is up-to-date

## Rollback Plan

- Maintain git branches for each phase
- Create backup of current state before major changes
- Document all changes for easy reversal if needed
- Test rollback procedures before implementation

## Success Metrics

- Reduced file count by removing duplicates
- Improved build times
- Cleaner directory structure
- Consistent naming conventions
- All tests passing
- Documentation up-to-date
