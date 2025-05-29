#!/usr/bin/env python3
"""
File Name Validation Script for ACGS-PGP

This script validates that all files and directories in the repository
follow cross-platform naming conventions to prevent CI/CD failures
on Windows systems.

Usage:
    python scripts/validate_file_names.py
    python scripts/validate_file_names.py --fix-dry-run
"""

import os
import re
import sys
import argparse
from pathlib import Path
from typing import List, Tuple


# Characters that are invalid on Windows
INVALID_CHARS = r'[:<>"|?*]'

# Directories to exclude from validation
EXCLUDE_DIRS = {
    '.git', '__pycache__', 'node_modules', 'venv', '.venv',
    'build', 'dist', '.pytest_cache', '.mypy_cache'
}

# File extensions to exclude
EXCLUDE_EXTENSIONS = {
    '.pyc', '.pyo', '.pyd', '.so', '.dll', '.dylib'
}


def find_invalid_files(root_dir: str = '.') -> List[Tuple[str, str]]:
    """
    Find files and directories with invalid characters.
    
    Returns:
        List of tuples (file_path, reason)
    """
    invalid_files = []
    root_path = Path(root_dir)
    
    for item in root_path.rglob('*'):
        # Skip excluded directories
        if any(excluded in item.parts for excluded in EXCLUDE_DIRS):
            continue
            
        # Skip excluded file extensions
        if item.suffix in EXCLUDE_EXTENSIONS:
            continue
            
        # Check for invalid characters
        if re.search(INVALID_CHARS, item.name):
            invalid_chars = re.findall(INVALID_CHARS, item.name)
            reason = f"Contains invalid characters: {', '.join(set(invalid_chars))}"
            invalid_files.append((str(item), reason))
            
        # Check for trailing spaces or dots (Windows issue)
        if item.name.endswith(' ') or item.name.endswith('.'):
            reason = "Ends with space or dot (Windows incompatible)"
            invalid_files.append((str(item), reason))
            
        # Check for reserved Windows names
        reserved_names = {
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        }
        
        name_without_ext = item.stem.upper()
        if name_without_ext in reserved_names:
            reason = f"Reserved Windows name: {name_without_ext}"
            invalid_files.append((str(item), reason))
    
    return invalid_files


def suggest_fix(filename: str) -> str:
    """
    Suggest a corrected filename.
    """
    # Replace invalid characters
    fixed = re.sub(r'[:<>"|?*]', '_', filename)
    
    # Replace spaces with underscores
    fixed = fixed.replace(' ', '_')
    
    # Remove trailing spaces and dots
    fixed = fixed.rstrip(' .')
    
    # Handle multiple consecutive underscores
    fixed = re.sub(r'_+', '_', fixed)
    
    return fixed


def main():
    parser = argparse.ArgumentParser(description='Validate file names for cross-platform compatibility')
    parser.add_argument('--fix-dry-run', action='store_true',
                       help='Show what files would be renamed (dry run)')
    parser.add_argument('--root-dir', default='.',
                       help='Root directory to scan (default: current directory)')
    
    args = parser.parse_args()
    
    print("🔍 Scanning for files with invalid names...")
    invalid_files = find_invalid_files(args.root_dir)
    
    if not invalid_files:
        print("✅ All files have valid cross-platform names!")
        return 0
    
    print(f"\n❌ Found {len(invalid_files)} files with invalid names:\n")
    
    for file_path, reason in invalid_files:
        print(f"  {file_path}")
        print(f"    Reason: {reason}")
        
        if args.fix_dry_run:
            suggested = suggest_fix(os.path.basename(file_path))
            if suggested != os.path.basename(file_path):
                print(f"    Suggested: {suggested}")
        print()
    
    if args.fix_dry_run:
        print("💡 This was a dry run. No files were actually renamed.")
        print("   To implement these changes, manually rename the files or")
        print("   create a script to automate the renaming process.")
    else:
        print("💡 Run with --fix-dry-run to see suggested fixes.")
    
    print(f"\n📖 See FILE_NAMING_CONVENTIONS.md for detailed guidelines.")
    
    return 1


if __name__ == '__main__':
    sys.exit(main())
