#!/usr/bin/env python3
"""
Research Data Validation Script

This script validates research data for consistency, identifies corrupted entries,
and checks for numerical discrepancies between text claims and table data.
"""

import re
import json
import csv
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ResearchDataValidator:
    """Validates research data for consistency and integrity."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.corrupted_entries = []
        
    def validate_table_data(self, data: List[Dict[str, Any]], table_name: str) -> bool:
        """Validate table data for corruption and consistency."""
        logger.info(f"Validating table: {table_name}")
        
        is_valid = True
        
        for row_idx, row in enumerate(data):
            for col_name, value in row.items():
                # Check for corrupted data patterns
                if self._is_corrupted_value(value):
                    error_msg = f"Table {table_name}, Row {row_idx}, Column {col_name}: Corrupted value '{value}'"
                    self.corrupted_entries.append({
                        'table': table_name,
                        'row': row_idx,
                        'column': col_name,
                        'value': value,
                        'error': error_msg
                    })
                    logger.error(error_msg)
                    is_valid = False
                    
                # Check for extraneous footnote markers
                if self._has_extraneous_footnotes(value):
                    warning_msg = f"Table {table_name}, Row {row_idx}, Column {col_name}: Extraneous footnote marker in '{value}'"
                    self.warnings.append(warning_msg)
                    logger.warning(warning_msg)
                    
        return is_valid
    
    def _is_corrupted_value(self, value: Any) -> bool:
        """Check if a value appears to be corrupted."""
        if not isinstance(value, str):
            return False
            
        # Pattern for corrupted data like "47 A+8 0"
        corrupted_patterns = [
            r'\d+\s+[A-Z]\+\d+\s+\d+',  # Pattern like "47 A+8 0"
            r'[A-Z]\+\d+',               # Pattern like "A+8"
            r'\d+\.\d+\s+[A-Z]+\d+',     # Mixed number-letter patterns
        ]
        
        for pattern in corrupted_patterns:
            if re.search(pattern, value):
                return True
                
        return False
    
    def _has_extraneous_footnotes(self, value: Any) -> bool:
        """Check for extraneous footnote markers."""
        if not isinstance(value, str):
            return False
            
        # Pattern for footnote markers like "1.1", "1.0" that don't correspond to actual footnotes
        footnote_pattern = r'\d+\.\d+'
        return bool(re.search(footnote_pattern, value))
    
    def validate_numerical_consistency(self, text_claims: Dict[str, float], table_data: Dict[str, float]) -> bool:
        """Validate consistency between text claims and table data."""
        logger.info("Validating numerical consistency between text and tables")
        
        is_consistent = True
        
        for claim_key, claim_value in text_claims.items():
            if claim_key in table_data:
                table_value = table_data[claim_key]
                
                # Allow for small rounding differences (1% tolerance)
                tolerance = 0.01
                relative_diff = abs(claim_value - table_value) / max(abs(claim_value), abs(table_value))
                
                if relative_diff > tolerance:
                    error_msg = f"Numerical mismatch for '{claim_key}': Text claims {claim_value}, Table shows {table_value}"
                    self.errors.append(error_msg)
                    logger.error(error_msg)
                    is_consistent = False
                    
        return is_consistent
    
    def fix_corrupted_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Attempt to fix corrupted data entries."""
        logger.info("Attempting to fix corrupted data")
        
        fixed_data = []
        
        for row in data:
            fixed_row = {}
            for col_name, value in row.items():
                if self._is_corrupted_value(value):
                    # Attempt to extract meaningful data
                    fixed_value = self._fix_corrupted_value(value)
                    logger.info(f"Fixed corrupted value '{value}' -> '{fixed_value}'")
                    fixed_row[col_name] = fixed_value
                else:
                    fixed_row[col_name] = value
            fixed_data.append(fixed_row)
            
        return fixed_data
    
    def _fix_corrupted_value(self, value: str) -> str:
        """Attempt to fix a corrupted value."""
        # For pattern like "47 A+8 0", extract the first number
        match = re.match(r'(\d+(?:\.\d+)?)', value)
        if match:
            return match.group(1)
            
        # If no pattern matches, return original value
        return value
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive validation report."""
        return {
            'errors': self.errors,
            'warnings': self.warnings,
            'corrupted_entries': self.corrupted_entries,
            'total_errors': len(self.errors),
            'total_warnings': len(self.warnings),
            'total_corrupted': len(self.corrupted_entries)
        }

def main():
    """Main validation function."""
    validator = ResearchDataValidator()
    
    # Example validation data (would be loaded from actual research files)
    sample_table_data = [
        {'Compliance (%)': '94.9', 'Latency (ms)': '38.3'},
        {'Compliance (%)': '47 A+8 0', 'Latency (ms)': '89.3'},  # Corrupted data
        {'Compliance (%)': '92.3', 'Latency (ms)': 'N/A^2'},    # Unexplained superscript
    ]
    
    # Validate table data
    is_valid = validator.validate_table_data(sample_table_data, "Table_11_Ablation_Study")
    
    # Example numerical consistency check
    text_claims = {
        'adaptation_time_manual': 15.2,
        'constitutional_prompting_drop': 41.1,
        'semantic_validation_drop': 28.8
    }
    
    table_data = {
        'adaptation_time_manual': 45.2,  # Mismatch
        'constitutional_prompting_drop': 66.5,  # Mismatch
        'semantic_validation_drop': 49.6   # Mismatch
    }
    
    is_consistent = validator.validate_numerical_consistency(text_claims, table_data)
    
    # Generate and display report
    report = validator.generate_report()
    
    print("\n" + "="*50)
    print("RESEARCH DATA VALIDATION REPORT")
    print("="*50)
    print(f"Total Errors: {report['total_errors']}")
    print(f"Total Warnings: {report['total_warnings']}")
    print(f"Total Corrupted Entries: {report['total_corrupted']}")
    
    if report['errors']:
        print("\nERRORS:")
        for error in report['errors']:
            print(f"  - {error}")
    
    if report['warnings']:
        print("\nWARNINGS:")
        for warning in report['warnings']:
            print(f"  - {warning}")
    
    if report['corrupted_entries']:
        print("\nCORRUPTED ENTRIES:")
        for entry in report['corrupted_entries']:
            print(f"  - {entry['error']}")
    
    # Attempt to fix corrupted data
    if report['corrupted_entries']:
        print("\nATTEMPTING TO FIX CORRUPTED DATA...")
        fixed_data = validator.fix_corrupted_data(sample_table_data)
        print("Fixed data:")
        for i, row in enumerate(fixed_data):
            print(f"  Row {i}: {row}")
    
    return 0 if is_valid and is_consistent else 1

if __name__ == "__main__":
    sys.exit(main())
