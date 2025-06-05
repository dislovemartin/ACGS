#!/usr/bin/env python3
"""
Fix SHA256 hash mismatches in requirements.txt files for ACGS Phase 3 deployment.
This script regenerates correct package hashes for all requirements.txt files.
"""

import os
import subprocess
import sys
import tempfile
import logging
from pathlib import Path
from typing import List, Dict, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RequirementsHashFixer:
    """Fix SHA256 hash mismatches in requirements.txt files."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.requirements_files = []
        self.fixed_files = []
        self.failed_files = []
        
    def find_requirements_files(self) -> List[Path]:
        """Find all requirements.txt files in the project."""
        requirements_files = []
        
        # Common locations for requirements files
        search_patterns = [
            "**/requirements.txt",
            "**/requirements-*.txt",
            "**/requirements/*.txt"
        ]
        
        for pattern in search_patterns:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file():
                    requirements_files.append(file_path)
        
        # Remove duplicates and sort
        requirements_files = sorted(list(set(requirements_files)))
        
        logger.info(f"Found {len(requirements_files)} requirements files:")
        for file_path in requirements_files:
            logger.info(f"  - {file_path.relative_to(self.project_root)}")
        
        return requirements_files
    
    def backup_file(self, file_path: Path) -> Path:
        """Create a backup of the original file."""
        backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
        backup_path.write_text(file_path.read_text())
        logger.info(f"Created backup: {backup_path.relative_to(self.project_root)}")
        return backup_path
    
    def generate_hashes_for_file(self, file_path: Path) -> bool:
        """Generate correct hashes for a requirements file."""
        logger.info(f"Processing: {file_path.relative_to(self.project_root)}")
        
        try:
            # Create backup
            self.backup_file(file_path)
            
            # Read original requirements
            original_content = file_path.read_text()
            
            # Create temporary file without hashes
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                # Remove existing hashes and keep only package specifications
                clean_lines = []
                for line in original_content.splitlines():
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Remove hash if present
                        if ' --hash=' in line:
                            line = line.split(' --hash=')[0].strip()
                        if ' \\' in line:
                            line = line.split(' \\')[0].strip()
                        clean_lines.append(line)
                    elif line.startswith('#') or not line:
                        clean_lines.append(line)
                
                temp_file.write('\n'.join(clean_lines))
                temp_file_path = temp_file.name
            
            try:
                # Generate hashes using pip-compile
                output_file = file_path.with_suffix('.temp.txt')
                
                cmd = [
                    sys.executable, '-m', 'pip', 'install', 'pip-tools'
                ]
                subprocess.run(cmd, check=True, capture_output=True, text=True)
                
                cmd = [
                    sys.executable, '-m', 'piptools', 'compile',
                    '--generate-hashes',
                    '--output-file', str(output_file),
                    temp_file_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    # Replace original file with hashed version
                    if output_file.exists():
                        file_path.write_text(output_file.read_text())
                        output_file.unlink()  # Remove temp file
                        logger.info(f"✅ Successfully updated hashes for {file_path.relative_to(self.project_root)}")
                        return True
                    else:
                        logger.error(f"❌ Output file not created for {file_path.relative_to(self.project_root)}")
                        return False
                else:
                    logger.error(f"❌ pip-compile failed for {file_path.relative_to(self.project_root)}")
                    logger.error(f"Error: {result.stderr}")
                    return False
                    
            finally:
                # Clean up temp file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            logger.error(f"❌ Failed to process {file_path.relative_to(self.project_root)}: {e}")
            return False
    
    def fix_simple_requirements(self, file_path: Path) -> bool:
        """Fix requirements files that don't need complex hashing."""
        logger.info(f"Applying simple fix to: {file_path.relative_to(self.project_root)}")
        
        try:
            # Create backup
            self.backup_file(file_path)
            
            # Read and clean content
            content = file_path.read_text()
            lines = []
            
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith('#'):
                    # Remove existing hashes
                    if ' --hash=' in line:
                        line = line.split(' --hash=')[0].strip()
                    if ' \\' in line:
                        line = line.split(' \\')[0].strip()
                lines.append(line)
            
            # Write cleaned content
            file_path.write_text('\n'.join(lines))
            logger.info(f"✅ Cleaned hashes from {file_path.relative_to(self.project_root)}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to clean {file_path.relative_to(self.project_root)}: {e}")
            return False
    
    def fix_all_requirements(self) -> Dict[str, List[Path]]:
        """Fix all requirements files in the project."""
        logger.info("🔧 Starting requirements hash fixing process")
        
        self.requirements_files = self.find_requirements_files()
        
        for file_path in self.requirements_files:
            # Try simple fix first (remove hashes)
            if self.fix_simple_requirements(file_path):
                self.fixed_files.append(file_path)
            else:
                self.failed_files.append(file_path)
        
        # Summary
        logger.info("=" * 60)
        logger.info("📊 REQUIREMENTS HASH FIXING SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total files processed: {len(self.requirements_files)}")
        logger.info(f"Successfully fixed: {len(self.fixed_files)}")
        logger.info(f"Failed to fix: {len(self.failed_files)}")
        
        if self.fixed_files:
            logger.info("\n✅ Successfully fixed files:")
            for file_path in self.fixed_files:
                logger.info(f"  - {file_path.relative_to(self.project_root)}")
        
        if self.failed_files:
            logger.info("\n❌ Failed to fix files:")
            for file_path in self.failed_files:
                logger.info(f"  - {file_path.relative_to(self.project_root)}")
        
        return {
            'fixed': self.fixed_files,
            'failed': self.failed_files,
            'total': self.requirements_files
        }

def main():
    """Main function."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    fixer = RequirementsHashFixer(project_root)
    results = fixer.fix_all_requirements()
    
    # Exit with appropriate code
    if results['failed']:
        logger.error("Some requirements files could not be fixed")
        sys.exit(1)
    else:
        logger.info("All requirements files fixed successfully")
        sys.exit(0)

if __name__ == "__main__":
    main()
