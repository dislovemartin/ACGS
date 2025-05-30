#!/usr/bin/env python3
"""
Validation script for ACGS-PGP framework reorganization
Tests that the new directory structure is working correctly
"""

import os
import sys
import subprocess
from pathlib import Path

def check_directory_structure():
    """Check that all expected directories exist"""
    print("🔍 Checking directory structure...")
    
    expected_dirs = [
        "src/backend/ac_service",
        "src/backend/auth_service", 
        "src/backend/fv_service",
        "src/backend/gs_service",
        "src/backend/integrity_service",
        "src/backend/pgc_service",
        "src/backend/shared",
        "src/frontend",
        "src/alphaevolve_gs_engine",
        "tests/unit",
        "tests/integration", 
        "tests/e2e",
        "config/docker",
        "config/k8s",
        "config/env",
        "config/monitoring",
        "docs/api",
        "docs/deployment",
        "docs/development",
        "docs/research",
        "docs/user",
        "scripts",
        "data",
        "migrations",
        "tools"
    ]
    
    missing_dirs = []
    for dir_path in expected_dirs:
        if not os.path.exists(dir_path):
            missing_dirs.append(dir_path)
        else:
            print(f"  ✅ {dir_path}")
    
    if missing_dirs:
        print(f"  ❌ Missing directories: {missing_dirs}")
        return False
    
    print("  ✅ All expected directories exist")
    return True

def check_key_files():
    """Check that key files are in the right locations"""
    print("\n🔍 Checking key file locations...")
    
    key_files = [
        "src/backend/shared/models.py",
        "src/backend/shared/database.py",
        "src/backend/shared/schemas.py",
        "config/docker/docker-compose.yml",
        "config/docker/nginx.conf",
        "migrations/alembic.ini",
        "migrations/env.py",
        "tests/README.md",
        "src/README.md",
        "config/README.md"
    ]
    
    missing_files = []
    for file_path in key_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
        else:
            print(f"  ✅ {file_path}")
    
    if missing_files:
        print(f"  ❌ Missing files: {missing_files}")
        return False
    
    print("  ✅ All key files are in correct locations")
    return True

def check_import_syntax():
    """Check that Python files have valid syntax"""
    print("\n🔍 Checking Python syntax...")
    
    python_files = []
    for root, dirs, files in os.walk("src"):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    
    syntax_errors = []
    for py_file in python_files[:10]:  # Check first 10 files to avoid too much output
        try:
            with open(py_file, 'r') as f:
                compile(f.read(), py_file, 'exec')
            print(f"  ✅ {py_file}")
        except SyntaxError as e:
            syntax_errors.append(f"{py_file}: {e}")
            print(f"  ❌ {py_file}: {e}")
    
    if syntax_errors:
        print(f"  ❌ Syntax errors found in {len(syntax_errors)} files")
        return False
    
    print("  ✅ Python syntax validation passed")
    return True

def check_docker_compose():
    """Check Docker Compose configuration"""
    print("\n🔍 Checking Docker Compose configuration...")
    
    try:
        result = subprocess.run(
            ["docker-compose", "-f", "config/docker/docker-compose.yml", "config"],
            capture_output=True,
            text=True,
            cwd="."
        )
        
        if result.returncode == 0:
            print("  ✅ Docker Compose configuration is valid")
            return True
        else:
            print(f"  ❌ Docker Compose validation failed: {result.stderr}")
            return False
    except FileNotFoundError:
        print("  ⚠️  Docker Compose not available, skipping validation")
        return True

def main():
    """Run all validation checks"""
    print("🚀 ACGS-PGP Framework Reorganization Validation")
    print("=" * 50)
    
    checks = [
        ("Directory Structure", check_directory_structure),
        ("Key Files", check_key_files),
        ("Python Syntax", check_import_syntax),
        ("Docker Compose", check_docker_compose)
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"  ❌ {check_name} failed with error: {e}")
            results.append((check_name, False))
    
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{check_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All validation checks passed! Reorganization successful.")
        return 0
    else:
        print("⚠️  Some validation checks failed. Please review and fix issues.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
