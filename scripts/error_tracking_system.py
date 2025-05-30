#!/usr/bin/env python3
"""
Error Tracking and Resolution System

This system tracks, categorizes, and manages the resolution of errors identified
in the ACGS-PGP framework research workflow enhancement analysis.
"""

import json
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class ErrorStatus(Enum):
    IDENTIFIED = "identified"
    IN_PROGRESS = "in_progress"
    FIXED = "fixed"
    VERIFIED = "verified"
    CLOSED = "closed"

class ErrorCategory(Enum):
    SYNTAX = "syntax"
    IMPORT = "import"
    SCHEMA = "schema"
    DATA_CORRUPTION = "data_corruption"
    NUMERICAL_MISMATCH = "numerical_mismatch"
    DOCUMENTATION = "documentation"
    FORMATTING = "formatting"
    LOGIC = "logic"

@dataclass
class ErrorRecord:
    """Represents a single error in the system."""
    id: str
    title: str
    description: str
    category: ErrorCategory
    severity: ErrorSeverity
    status: ErrorStatus
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    identified_date: str = ""
    fixed_date: Optional[str] = None
    fix_description: Optional[str] = None
    verification_notes: Optional[str] = None
    
    def __post_init__(self):
        if not self.identified_date:
            self.identified_date = datetime.datetime.now().isoformat()

class ErrorTrackingSystem:
    """Manages error tracking and resolution for ACGS-PGP framework."""
    
    def __init__(self, tracking_file: Path = None):
        self.tracking_file = tracking_file or Path("error_tracking.json")
        self.errors: Dict[str, ErrorRecord] = {}
        self.load_errors()
        
    def load_errors(self):
        """Load errors from tracking file."""
        if self.tracking_file.exists():
            try:
                with open(self.tracking_file, 'r') as f:
                    data = json.load(f)
                    for error_id, error_data in data.items():
                        # Convert string enums back to enum objects
                        error_data['category'] = ErrorCategory(error_data['category'])
                        error_data['severity'] = ErrorSeverity(error_data['severity'])
                        error_data['status'] = ErrorStatus(error_data['status'])
                        self.errors[error_id] = ErrorRecord(**error_data)
            except Exception as e:
                logger.error(f"Error loading tracking file: {e}")
    
    def save_errors(self):
        """Save errors to tracking file."""
        try:
            data = {}
            for error_id, error in self.errors.items():
                error_dict = asdict(error)
                # Convert enums to strings for JSON serialization
                error_dict['category'] = error.category.value
                error_dict['severity'] = error.severity.value
                error_dict['status'] = error.status.value
                data[error_id] = error_dict
                
            with open(self.tracking_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving tracking file: {e}")
    
    def add_error(self, error: ErrorRecord) -> str:
        """Add a new error to the tracking system."""
        self.errors[error.id] = error
        self.save_errors()
        logger.info(f"Added error {error.id}: {error.title}")
        return error.id
    
    def update_error_status(self, error_id: str, status: ErrorStatus, 
                           fix_description: str = None, verification_notes: str = None):
        """Update the status of an error."""
        if error_id in self.errors:
            error = self.errors[error_id]
            error.status = status
            
            if status == ErrorStatus.FIXED and fix_description:
                error.fix_description = fix_description
                error.fixed_date = datetime.datetime.now().isoformat()
            
            if verification_notes:
                error.verification_notes = verification_notes
                
            self.save_errors()
            logger.info(f"Updated error {error_id} status to {status.value}")
        else:
            logger.error(f"Error {error_id} not found")
    
    def get_errors_by_category(self, category: ErrorCategory) -> List[ErrorRecord]:
        """Get all errors in a specific category."""
        return [error for error in self.errors.values() if error.category == category]
    
    def get_errors_by_status(self, status: ErrorStatus) -> List[ErrorRecord]:
        """Get all errors with a specific status."""
        return [error for error in self.errors.values() if error.status == status]
    
    def get_critical_errors(self) -> List[ErrorRecord]:
        """Get all critical errors."""
        return [error for error in self.errors.values() if error.severity == ErrorSeverity.CRITICAL]
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive error report."""
        total_errors = len(self.errors)
        
        status_counts = {}
        for status in ErrorStatus:
            status_counts[status.value] = len(self.get_errors_by_status(status))
        
        category_counts = {}
        for category in ErrorCategory:
            category_counts[category.value] = len(self.get_errors_by_category(category))
        
        severity_counts = {}
        for severity in ErrorSeverity:
            severity_counts[severity.value] = len([
                error for error in self.errors.values() 
                if error.severity == severity
            ])
        
        return {
            'total_errors': total_errors,
            'status_breakdown': status_counts,
            'category_breakdown': category_counts,
            'severity_breakdown': severity_counts,
            'critical_errors': [asdict(error) for error in self.get_critical_errors()],
            'report_generated': datetime.datetime.now().isoformat()
        }

def initialize_acgs_errors():
    """Initialize the error tracking system with known ACGS-PGP errors."""
    tracker = ErrorTrackingSystem(Path("docs/acgs_error_tracking.json"))
    
    # Define the errors identified in the research workflow analysis
    errors = [
        ErrorRecord(
            id="ERR-001",
            title="Corrupted Table Data in Research Document",
            description="Table 11 contains corrupted data '47 A+8 0' in Compliance (%) column",
            category=ErrorCategory.DATA_CORRUPTION,
            severity=ErrorSeverity.HIGH,
            status=ErrorStatus.FIXED,
            file_path="docs/research/AlphaEvolve-ACGS_Integration_System/Research Workflow Enhancement Analysis_.md",
            line_number=21,
            fix_description="Corrected corrupted value to '47.8%' based on pattern analysis"
        ),
        ErrorRecord(
            id="ERR-002",
            title="Deprecated Pydantic Validator Import",
            description="Using deprecated 'validator' import instead of 'field_validator'",
            category=ErrorCategory.IMPORT,
            severity=ErrorSeverity.MEDIUM,
            status=ErrorStatus.FIXED,
            file_path="src/backend/gs_service/app/schemas.py",
            line_number=3,
            fix_description="Updated import to use 'field_validator' and updated method signatures"
        ),
        ErrorRecord(
            id="ERR-003",
            title="Numerical Mismatch: Adaptation Time",
            description="Text claims 15.2±12.3 generations but Table 9 shows 45.2",
            category=ErrorCategory.NUMERICAL_MISMATCH,
            severity=ErrorSeverity.HIGH,
            status=ErrorStatus.IDENTIFIED,
            file_path="docs/research/AlphaEvolve-ACGS_Integration_System/Research Workflow Enhancement Analysis_.md"
        ),
        ErrorRecord(
            id="ERR-004",
            title="Extraneous Footnote Markers",
            description="Tables contain footnote markers (1.1, 1.0) without corresponding footnotes",
            category=ErrorCategory.FORMATTING,
            severity=ErrorSeverity.LOW,
            status=ErrorStatus.IDENTIFIED,
            file_path="docs/research/AlphaEvolve-ACGS_Integration_System/Research Workflow Enhancement Analysis_.md"
        ),
        ErrorRecord(
            id="ERR-005",
            title="Deprecated orm_mode Configuration",
            description="Using deprecated 'orm_mode = True' instead of 'from_attributes = True'",
            category=ErrorCategory.SCHEMA,
            severity=ErrorSeverity.MEDIUM,
            status=ErrorStatus.FIXED,
            file_path="src/backend/gs_service/app/schemas.py",
            line_number=216,
            fix_description="Updated to use 'from_attributes = True' for Pydantic v2 compatibility"
        ),
        ErrorRecord(
            id="ERR-006",
            title="Undefined Lipschitz Constant Epsilon",
            description="Theorem 3.1 needs explicit ε definition for mathematical rigor",
            category=ErrorCategory.LOGIC,
            severity=ErrorSeverity.MEDIUM,
            status=ErrorStatus.IDENTIFIED,
            file_path="docs/research/AlphaEvolve-ACGS_Integration_System/Research Workflow Enhancement Analysis_.md"
        ),
        ErrorRecord(
            id="ERR-007",
            title="Missing Technical Terms in Dictionary",
            description="Spell-checker flags legitimate technical terms as unknown words",
            category=ErrorCategory.DOCUMENTATION,
            severity=ErrorSeverity.LOW,
            status=ErrorStatus.FIXED,
            file_path="docs/technical_dictionary.txt",
            fix_description="Created comprehensive technical dictionary with ACGS-PGP specific terms"
        )
    ]
    
    # Add all errors to the tracker
    for error in errors:
        tracker.add_error(error)
    
    return tracker

def main():
    """Main function to demonstrate the error tracking system."""
    tracker = initialize_acgs_errors()
    
    # Generate and display report
    report = tracker.generate_report()
    
    print("="*60)
    print("ACGS-PGP ERROR TRACKING REPORT")
    print("="*60)
    print(f"Total Errors: {report['total_errors']}")
    print()
    
    print("Status Breakdown:")
    for status, count in report['status_breakdown'].items():
        print(f"  {status.replace('_', ' ').title()}: {count}")
    print()
    
    print("Category Breakdown:")
    for category, count in report['category_breakdown'].items():
        print(f"  {category.replace('_', ' ').title()}: {count}")
    print()
    
    print("Severity Breakdown:")
    for severity, count in report['severity_breakdown'].items():
        print(f"  {severity.title()}: {count}")
    print()
    
    # Show critical errors
    critical_errors = tracker.get_critical_errors()
    if critical_errors:
        print("Critical Errors:")
        for error in critical_errors:
            print(f"  - {error.id}: {error.title}")
        print()
    
    # Show fixed errors
    fixed_errors = tracker.get_errors_by_status(ErrorStatus.FIXED)
    if fixed_errors:
        print("Recently Fixed Errors:")
        for error in fixed_errors:
            print(f"  ✅ {error.id}: {error.title}")
            if error.fix_description:
                print(f"     Fix: {error.fix_description}")
        print()
    
    print(f"Report generated: {report['report_generated']}")

if __name__ == "__main__":
    main()
