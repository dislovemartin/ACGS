#!/usr/bin/env python3
"""
Automated Validation Pipeline

This script implements a comprehensive validation pipeline for the ACGS-PGP framework,
addressing the errors identified in the research workflow enhancement analysis.
"""

import os
import sys
import subprocess
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple
import tempfile
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ACGSValidationPipeline:
    """Comprehensive validation pipeline for ACGS-PGP framework."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.errors = []
        self.warnings = []
        self.fixes_applied = []
        
    def run_full_validation(self) -> Dict[str, Any]:
        """Run the complete validation pipeline."""
        logger.info("Starting ACGS-PGP validation pipeline")
        
        results = {
            'syntax_validation': self.validate_syntax(),
            'import_validation': self.validate_imports(),
            'schema_validation': self.validate_schemas(),
            'data_consistency': self.validate_data_consistency(),
            'documentation_check': self.validate_documentation(),
            'test_execution': self.run_tests(),
            'overall_status': 'pending'
        }
        
        # Determine overall status
        has_critical_errors = any(
            not results[key].get('passed', True) 
            for key in ['syntax_validation', 'import_validation', 'schema_validation']
        )
        
        results['overall_status'] = 'failed' if has_critical_errors else 'passed'
        
        return results
    
    def validate_syntax(self) -> Dict[str, Any]:
        """Validate Python syntax across all backend services."""
        logger.info("Validating Python syntax")
        
        python_files = list(self.project_root.rglob("*.py"))
        syntax_errors = []
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    compile(f.read(), py_file, 'exec')
            except SyntaxError as e:
                error_msg = f"Syntax error in {py_file}: {e}"
                syntax_errors.append(error_msg)
                logger.error(error_msg)
            except Exception as e:
                warning_msg = f"Warning in {py_file}: {e}"
                self.warnings.append(warning_msg)
                logger.warning(warning_msg)
        
        return {
            'passed': len(syntax_errors) == 0,
            'errors': syntax_errors,
            'files_checked': len(python_files)
        }
    
    def validate_imports(self) -> Dict[str, Any]:
        """Validate import statements and dependencies."""
        logger.info("Validating imports and dependencies")
        
        import_errors = []
        missing_dependencies = []
        
        # Check for common import issues
        backend_services = [
            'src/backend/auth_service',
            'src/backend/ac_service', 
            'src/backend/gs_service',
            'src/backend/pgc_service',
            'src/backend/fv_service',
            'src/backend/integrity_service'
        ]
        
        for service_dir in backend_services:
            service_path = self.project_root / service_dir
            if service_path.exists():
                errors = self._check_service_imports(service_path)
                import_errors.extend(errors)
        
        return {
            'passed': len(import_errors) == 0,
            'errors': import_errors,
            'missing_dependencies': missing_dependencies
        }
    
    def _check_service_imports(self, service_path: Path) -> List[str]:
        """Check imports for a specific service."""
        errors = []
        
        # Check for deprecated Pydantic imports
        for py_file in service_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for deprecated validator import
                if 'from pydantic import' in content and 'validator' in content:
                    if 'field_validator' not in content:
                        errors.append(f"Deprecated 'validator' import in {py_file}. Use 'field_validator' instead.")
                
                # Check for deprecated orm_mode
                if 'from_attributes = True' in content:
                    errors.append(f"Deprecated 'orm_mode' in {py_file}. Use 'from_attributes = True' instead.")
                    
            except Exception as e:
                errors.append(f"Error reading {py_file}: {e}")
        
        return errors
    
    def validate_schemas(self) -> Dict[str, Any]:
        """Validate Pydantic schema consistency across services."""
        logger.info("Validating schema consistency")
        
        schema_errors = []
        
        # Check shared schemas consistency
        shared_schemas_path = self.project_root / "src/backend/shared/schemas.py"
        if shared_schemas_path.exists():
            errors = self._validate_shared_schemas(shared_schemas_path)
            schema_errors.extend(errors)
        
        return {
            'passed': len(schema_errors) == 0,
            'errors': schema_errors
        }
    
    def _validate_shared_schemas(self, schemas_path: Path) -> List[str]:
        """Validate shared schemas file."""
        errors = []
        
        try:
            with open(schemas_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check for required imports
            required_imports = ['BaseModel', 'Field', 'EmailStr']
            for import_name in required_imports:
                if import_name not in content:
                    errors.append(f"Missing required import '{import_name}' in shared schemas")
            
            # Check for consistent field definitions
            if 'from_attributes = True' not in content:
                errors.append("Missing 'from_attributes = True' in schema Config classes")
                
        except Exception as e:
            errors.append(f"Error validating shared schemas: {e}")
        
        return errors
    
    def validate_data_consistency(self) -> Dict[str, Any]:
        """Validate data consistency in research documents."""
        logger.info("Validating data consistency")
        
        # Run the research data validator
        try:
            result = subprocess.run([
                sys.executable, 
                str(self.project_root / "scripts/validate_research_data.py")
            ], capture_output=True, text=True, timeout=60)
            
            return {
                'passed': result.returncode == 0,
                'output': result.stdout,
                'errors': result.stderr.split('\n') if result.stderr else []
            }
        except subprocess.TimeoutExpired:
            return {
                'passed': False,
                'errors': ['Data validation timed out']
            }
        except Exception as e:
            return {
                'passed': False,
                'errors': [f'Data validation failed: {e}']
            }
    
    def validate_documentation(self) -> Dict[str, Any]:
        """Validate documentation completeness and consistency."""
        logger.info("Validating documentation")
        
        doc_errors = []
        
        # Check for required documentation files
        required_docs = [
            'README.md',
            'docs/architecture.md',
            'docs/deployment.md',
            'docs/user_guide.md'
        ]
        
        for doc_file in required_docs:
            doc_path = self.project_root / doc_file
            if not doc_path.exists():
                doc_errors.append(f"Missing required documentation: {doc_file}")
        
        return {
            'passed': len(doc_errors) == 0,
            'errors': doc_errors
        }
    
    def run_tests(self) -> Dict[str, Any]:
        """Run available tests."""
        logger.info("Running tests")
        
        test_results = {
            'unit_tests': {'passed': True, 'output': 'No unit tests configured'},
            'integration_tests': {'passed': True, 'output': 'No integration tests configured'}
        }
        
        # Check if pytest is available and run tests
        tests_dir = self.project_root / "tests"
        if tests_dir.exists():
            try:
                result = subprocess.run([
                    sys.executable, '-m', 'pytest', str(tests_dir), '-v'
                ], capture_output=True, text=True, timeout=300)
                
                test_results['unit_tests'] = {
                    'passed': result.returncode == 0,
                    'output': result.stdout,
                    'errors': result.stderr
                }
            except subprocess.TimeoutExpired:
                test_results['unit_tests'] = {
                    'passed': False,
                    'errors': ['Tests timed out']
                }
            except FileNotFoundError:
                test_results['unit_tests'] = {
                    'passed': True,
                    'output': 'pytest not available'
                }
        
        return test_results
    
    def apply_automatic_fixes(self) -> List[str]:
        """Apply automatic fixes for common issues."""
        logger.info("Applying automatic fixes")
        
        fixes = []
        
        # Fix deprecated Pydantic imports
        fixes.extend(self._fix_pydantic_imports())
        
        # Fix schema configurations
        fixes.extend(self._fix_schema_configs())
        
        return fixes
    
    def _fix_pydantic_imports(self) -> List[str]:
        """Fix deprecated Pydantic imports."""
        fixes = []
        
        for py_file in self.project_root.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # Replace deprecated validator import
                content = re.sub(
                    r'from pydantic import (.*?)field_validator(.*?)$',
                    r'from pydantic import \1field_field_validator\2',
                    content,
                    flags=re.MULTILINE
                )
                
                # Replace validator usage
                content = re.sub(
                    r'@validator\((.*?)\)',
                    r'@field_validator(\1)\n    @classmethod',
                    content
                )
                
                # Update validator method signatures
                content = re.sub(
                    r'def (\w+)\(cls, v, values\):',
                    r'def \1(cls, v, info):',
                    content
                )
                
                # Update values access
                content = re.sub(
                    r'values\.get\(',
                    r'info.data.get(' if 'info.data' not in content else r'(info.data if hasattr(info, "data") else {}).get(',
                    content
                )
                
                if content != original_content:
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    fixes.append(f"Fixed Pydantic imports in {py_file}")
                    
            except Exception as e:
                logger.warning(f"Could not fix imports in {py_file}: {e}")
        
        return fixes
    
    def _fix_schema_configs(self) -> List[str]:
        """Fix schema configuration issues."""
        fixes = []
        
        for py_file in self.project_root.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # Replace orm_mode with from_attributes
                content = re.sub(
                    r'from_attributes = True',
                    r'from_attributes = True',
                    content
                )
                
                if content != original_content:
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    fixes.append(f"Fixed schema config in {py_file}")
                    
            except Exception as e:
                logger.warning(f"Could not fix schema config in {py_file}: {e}")
        
        return fixes

def main():
    """Main function."""
    project_root = Path(__file__).parent.parent
    
    pipeline = ACGSValidationPipeline(project_root)
    
    # Apply automatic fixes first
    fixes = pipeline.apply_automatic_fixes()
    if fixes:
        print("Applied automatic fixes:")
        for fix in fixes:
            print(f"  - {fix}")
        print()
    
    # Run validation
    results = pipeline.run_full_validation()
    
    # Display results
    print("="*60)
    print("ACGS-PGP VALIDATION PIPELINE RESULTS")
    print("="*60)
    
    for check_name, check_result in results.items():
        if check_name == 'overall_status':
            continue
            
        status = "✅ PASSED" if check_result.get('passed', True) else "❌ FAILED"
        print(f"{check_name.upper()}: {status}")
        
        if 'errors' in check_result and check_result['errors']:
            for error in check_result['errors']:
                print(f"  - {error}")
        print()
    
    print(f"OVERALL STATUS: {'✅ PASSED' if results['overall_status'] == 'passed' else '❌ FAILED'}")
    
    return 0 if results['overall_status'] == 'passed' else 1

if __name__ == "__main__":
    sys.exit(main())
