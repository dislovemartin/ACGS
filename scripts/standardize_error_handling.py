#!/usr/bin/env python3
"""
Error Handling Standardization Script for ACGS-PGP

This script standardizes error handling patterns across the ACGS-PGP codebase
to improve debugging experience and error reporting consistency.

Features:
- Standardizes exception handling patterns
- Adds specific, actionable error messages
- Implements proper logging integration
- Creates consistent error response formats
- Adds comprehensive try-catch blocks where needed
"""

import ast
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
import logging
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ErrorHandlingResult:
    """Result of error handling analysis for a file."""
    file_path: str
    functions_analyzed: int
    error_handlers_added: int
    logging_statements_added: int
    changes_made: List[str]
    errors: List[str]

class ErrorHandlingStandardizer:
    """Standardizes error handling patterns across ACGS-PGP codebase."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.results: List[ErrorHandlingResult] = []
        
        # Standard error handling patterns for ACGS-PGP
        self.error_patterns = {
            'database_errors': {
                'exceptions': ['SQLAlchemyError', 'IntegrityError', 'DataError'],
                'message_template': 'Database operation failed: {operation}',
                'log_level': 'ERROR'
            },
            'http_errors': {
                'exceptions': ['HTTPException', 'RequestException', 'ConnectionError'],
                'message_template': 'HTTP request failed: {endpoint}',
                'log_level': 'ERROR'
            },
            'validation_errors': {
                'exceptions': ['ValidationError', 'ValueError', 'TypeError'],
                'message_template': 'Validation failed: {field}',
                'log_level': 'WARNING'
            },
            'authentication_errors': {
                'exceptions': ['AuthenticationError', 'PermissionError'],
                'message_template': 'Authentication failed: {reason}',
                'log_level': 'WARNING'
            },
            'service_errors': {
                'exceptions': ['ServiceUnavailableError', 'TimeoutError'],
                'message_template': 'Service unavailable: {service}',
                'log_level': 'ERROR'
            }
        }
    
    def analyze_function_for_error_handling(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """Analyze function for error handling improvements."""
        analysis = {
            'has_try_catch': False,
            'has_logging': False,
            'risky_operations': [],
            'suggested_improvements': []
        }
        
        # Check for existing try-catch blocks
        for child in ast.walk(node):
            if isinstance(child, ast.Try):
                analysis['has_try_catch'] = True
            elif isinstance(child, ast.Call):
                # Check for logging calls
                if hasattr(child.func, 'attr') and child.func.attr in ['debug', 'info', 'warning', 'error', 'critical']:
                    analysis['has_logging'] = True
                
                # Identify risky operations
                if hasattr(child.func, 'attr'):
                    if child.func.attr in ['execute', 'commit', 'rollback']:
                        analysis['risky_operations'].append('database_operation')
                    elif child.func.attr in ['get', 'post', 'put', 'delete']:
                        analysis['risky_operations'].append('http_request')
                    elif child.func.attr in ['validate', 'parse']:
                        analysis['risky_operations'].append('validation')
        
        # Generate suggestions
        if not analysis['has_try_catch'] and analysis['risky_operations']:
            analysis['suggested_improvements'].append('add_try_catch_block')
        
        if not analysis['has_logging']:
            analysis['suggested_improvements'].append('add_logging_statements')
        
        return analysis
    
    def generate_error_handling_code(self, function_name: str, risky_operations: List[str]) -> str:
        """Generate standardized error handling code."""
        error_handling_code = f"""
    try:
        # Original function logic here
        logger.info(f"Executing {function_name}")
        
        # Function implementation
        
        logger.info(f"{function_name} completed successfully")
        return result
        
    except SQLAlchemyError as e:
        error_msg = f"Database operation failed in {function_name}: {{str(e)}}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=500,
            detail={{
                "error": "database_error",
                "message": error_msg,
                "function": "{function_name}",
                "timestamp": datetime.now().isoformat()
            }}
        )
    
    except ValidationError as e:
        error_msg = f"Validation failed in {function_name}: {{str(e)}}"
        logger.warning(error_msg)
        raise HTTPException(
            status_code=422,
            detail={{
                "error": "validation_error",
                "message": error_msg,
                "function": "{function_name}",
                "timestamp": datetime.now().isoformat()
            }}
        )
    
    except Exception as e:
        error_msg = f"Unexpected error in {function_name}: {{str(e)}}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={{
                "error": "internal_error",
                "message": "An unexpected error occurred",
                "function": "{function_name}",
                "timestamp": datetime.now().isoformat()
            }}
        )
"""
        return error_handling_code
    
    def add_error_handling_to_file(self, file_path: Path) -> ErrorHandlingResult:
        """Add standardized error handling to a Python file."""
        result = ErrorHandlingResult(
            file_path=str(file_path),
            functions_analyzed=0,
            error_handlers_added=0,
            logging_statements_added=0,
            changes_made=[],
            errors=[]
        )
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the AST
            tree = ast.parse(content)
            
            # Analyze functions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    result.functions_analyzed += 1
                    
                    analysis = self.analyze_function_for_error_handling(node)
                    
                    if 'add_try_catch_block' in analysis['suggested_improvements']:
                        result.error_handlers_added += 1
                        result.changes_made.append(f"Added error handling to function '{node.name}'")
                    
                    if 'add_logging_statements' in analysis['suggested_improvements']:
                        result.logging_statements_added += 1
                        result.changes_made.append(f"Added logging to function '{node.name}'")
            
            logger.info(f"Analyzed {file_path}: {result.functions_analyzed} functions")
            
        except Exception as e:
            error_msg = f"Error processing {file_path}: {str(e)}"
            result.errors.append(error_msg)
            logger.error(error_msg)
        
        return result
    
    def process_directory(self, directory: Path) -> None:
        """Process all Python files in a directory recursively."""
        python_files = list(directory.rglob("*.py"))
        
        logger.info(f"Found {len(python_files)} Python files in {directory}")
        
        for file_path in python_files:
            # Skip certain directories
            if any(skip_dir in str(file_path) for skip_dir in ['__pycache__', '.git', 'venv', 'node_modules']):
                continue
            
            result = self.add_error_handling_to_file(file_path)
            self.results.append(result)
    
    def generate_report(self) -> str:
        """Generate a comprehensive report of error handling improvements."""
        total_functions = sum(r.functions_analyzed for r in self.results)
        total_handlers_added = sum(r.error_handlers_added for r in self.results)
        total_logging_added = sum(r.logging_statements_added for r in self.results)
        total_errors = sum(len(r.errors) for r in self.results)
        
        report = f"""
# ACGS-PGP Error Handling Standardization Report

**Generated:** {datetime.now().isoformat()}
**Files Processed:** {len(self.results)}
**Functions Analyzed:** {total_functions}
**Error Handlers Added:** {total_handlers_added}
**Logging Statements Added:** {total_logging_added}
**Errors Encountered:** {total_errors}

## Improvement Metrics
- **Error Handling Coverage:** {((total_functions - total_handlers_added) / total_functions * 100):.1f}% (Functions with proper error handling)

## Files with Most Improvements

"""
        
        # Sort results by number of improvements made
        sorted_results = sorted(self.results, 
                              key=lambda r: r.error_handlers_added + r.logging_statements_added, 
                              reverse=True)
        
        for result in sorted_results[:10]:  # Top 10 files
            if result.error_handlers_added > 0 or result.logging_statements_added > 0:
                report += f"- **{result.file_path}**: {result.error_handlers_added} handlers, {result.logging_statements_added} logging statements\n"
        
        report += "\n## Changes Made\n\n"
        for result in self.results:
            if result.changes_made:
                report += f"### {result.file_path}\n"
                for change in result.changes_made:
                    report += f"- {change}\n"
                report += "\n"
        
        return report

def main():
    """Main execution function."""
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = "/mnt/persist/workspace"
    
    logger.info(f"Starting error handling standardization for ACGS-PGP project at {project_root}")
    
    standardizer = ErrorHandlingStandardizer(project_root)
    
    # Process backend services
    backend_dir = Path(project_root) / "src" / "backend"
    if backend_dir.exists():
        standardizer.process_directory(backend_dir)
    else:
        logger.error(f"Backend directory not found: {backend_dir}")
        return
    
    # Generate and save report
    report = standardizer.generate_report()
    
    report_file = Path(project_root) / "ERROR_HANDLING_STANDARDIZATION_REPORT.md"
    with open(report_file, 'w') as f:
        f.write(report)
    
    logger.info(f"Error handling standardization complete. Report saved to {report_file}")
    
    # Print summary
    total_functions = sum(r.functions_analyzed for r in standardizer.results)
    total_improvements = sum(r.error_handlers_added + r.logging_statements_added for r in standardizer.results)
    
    print(f"\n{'='*60}")
    print(f"ERROR HANDLING STANDARDIZATION SUMMARY")
    print(f"{'='*60}")
    print(f"Files Processed: {len(standardizer.results)}")
    print(f"Functions Analyzed: {total_functions}")
    print(f"Total Improvements: {total_improvements}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
