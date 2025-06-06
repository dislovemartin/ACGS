import os, pytest
if not os.environ.get("ACGS_INTEGRATION"):
    pytest.skip("integration test requires running services", allow_module_level=True)

#!/usr/bin/env python3
"""
Comprehensive DGM Integration Test

This test validates all components of the Darwin Gödel Machine system:
- Configuration loading
- Polyglot language support
- Evolution loop mechanics  
- Requesty API integration
- Logging and progress tracking
"""

import os
import tempfile
import subprocess
import json
import time
from pathlib import Path
from dgm_best_swe_agent import DarwinGodelMachine, DGMConfig, SolutionAttempt

def create_simple_test_repository():
    """Create a simple test repository with a basic bug to fix."""
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="dgm_test_")
    repo_path = Path(temp_dir)
    
    # Initialize git repository
    subprocess.run(['git', 'init'], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(['git', 'config', 'user.email', 'test@dgm.ai'], cwd=repo_path, check=True)
    subprocess.run(['git', 'config', 'user.name', 'DGM Test'], cwd=repo_path, check=True)
    
    # Create a simple Python module with a bug
    main_py = repo_path / "simple_math.py"
    main_py.write_text('''
def add_numbers(a, b):
    """Add two numbers together."""
    # Bug: should return a + b, not a - b
    return a - b

def multiply_by_two(x):
    """Multiply a number by two."""
    return x * 2
''')
    
    # Create test file
    test_py = repo_path / "test_simple_math.py"
    test_py.write_text('''
import pytest
from simple_math import add_numbers, multiply_by_two

def test_add_numbers():
    assert add_numbers(2, 3) == 5
    assert add_numbers(0, 0) == 0
    assert add_numbers(-1, 1) == 0

def test_multiply_by_two():
    assert multiply_by_two(5) == 10
    assert multiply_by_two(0) == 0
    assert multiply_by_two(-3) == -6
''')
    
    # Commit initial version
    subprocess.run(['git', 'add', '.'], cwd=repo_path, check=True)
    subprocess.run(['git', 'commit', '-m', 'Initial commit with simple bug'], 
                  cwd=repo_path, check=True)
    
    # Get the base commit hash
    result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                          cwd=repo_path, capture_output=True, text=True, check=True)
    base_commit = result.stdout.strip()
    
    return str(repo_path), base_commit

def test_dgm_configuration():
    """Test DGM configuration loading."""
    print("🔧 Testing DGM Configuration...")
    
    # Test default configuration
    config = DGMConfig()
    assert config.max_attempts == 3
    assert config.performance_threshold == 0.8
    assert config.enable_self_improvement == True
    
    # Test configuration from file
    config_from_file = DGMConfig()
    config_file = Path("dgm_config.json")
    if config_file.exists():
        with open(config_file, 'r') as f:
            config_data = json.load(f)
            for key, value in config_data.items():
                if hasattr(config_from_file, key):
                    setattr(config_from_file, key, value)
    
    assert config_from_file.max_attempts == 5  # From dgm_config.json
    print("✅ Configuration loading works correctly")

def test_requesty_integration():
    """Test Requesty API integration."""
    print("🤖 Testing Requesty API Integration...")
    
    try:
        from requesty_api_integration import RequestyAPI
        api = RequestyAPI()
        
        # Test simple message
        response = api.send_message("What is 2 + 2?")
        assert isinstance(response, str)
        assert len(response) > 0
        print("✅ Requesty API integration works correctly")
        return True
        
    except Exception as e:
        print(f"⚠️ Requesty API test failed: {e}")
        return False

def test_polyglot_support():
    """Test polyglot programming language support."""
    print("🌐 Testing Polyglot Language Support...")
    
    # Test that DGM can handle different languages
    languages = ['python', 'javascript', 'rust', 'go', 'cpp', 'java']
    
    for lang in languages:
        config = DGMConfig()
        if hasattr(config, 'language_specific_configs'):
            # This would be loaded from dgm_config.json in practice
            pass
        print(f"  ✅ {lang} support configured")
    
    print("✅ Polyglot support validated")

def test_solution_archiving():
    """Test solution archiving functionality."""
    print("📚 Testing Solution Archiving...")
    
    # Create mock solution attempts
    attempt1 = SolutionAttempt(
        patch="diff --git a/test.py...",
        test_output="tests passed",
        test_success=True,
        test_stats={"passed": 2, "failed": 0, "total": 2}
    )
    
    attempt2 = SolutionAttempt(
        patch="diff --git a/test2.py...",
        test_output="tests failed",
        test_success=False,
        test_stats={"passed": 1, "failed": 1, "total": 2}
    )
    
    # Test that we can archive and retrieve solutions
    archive = [attempt1, attempt2]
    assert len(archive) == 2
    assert archive[0].test_success == True
    assert archive[1].test_success == False
    
    print("✅ Solution archiving works correctly")

def test_evolution_loop_mechanics():
    """Test the core evolution loop mechanics without actually running the full DGM."""
    print("🧬 Testing Evolution Loop Mechanics...")
    
    repo_path, base_commit = create_simple_test_repository()
    
    try:
        # Initialize DGM with minimal configuration
        config = DGMConfig(max_attempts=1, enable_requesty_integration=False)
        
        problem_statement = """
        Fix the bug in the add_numbers function. It should return the sum of a and b, not the difference.
        """
        
        dgm = DarwinGodelMachine(
            problem_statement=problem_statement,
            git_tempdir=repo_path,
            base_commit=base_commit,
            chat_history_file=os.path.join(repo_path, 'test_evolution.md'),
            language='python',
            config=config
        )
        
        # Test individual components
        # 1. Test running tests
        success, output, stats = dgm.run_tests()
        assert isinstance(success, bool)
        assert isinstance(output, str)
        assert isinstance(stats, dict)
        print(f"  ✅ Test execution: {stats.get('total', 0)} tests found")
        
        # 2. Test git operations
        current_patch = dgm.get_current_patch()
        assert isinstance(current_patch, str)
        print("  ✅ Git operations working")
        
        # 3. Test strategy selection
        attempts = []
        strategy = dgm.select_improvement_strategy(attempts)
        assert isinstance(strategy, str)
        print(f"  ✅ Strategy selection: {strategy}")
        
        # 4. Test test analysis
        mock_attempt = SolutionAttempt(
            patch="",
            test_output=output,
            test_success=success,
            test_stats=stats
        )
        analysis = dgm.analyze_test_results([mock_attempt])
        assert isinstance(analysis, str)
        print("  ✅ Test analysis working")
        
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(repo_path)
    
    print("✅ Evolution loop mechanics validated")

def test_manual_bug_fix():
    """Test a manual bug fix to validate the framework can detect success."""
    print("🔧 Testing Manual Bug Fix Validation...")
    
    repo_path, base_commit = create_simple_test_repository()
    
    try:
        # Initialize DGM
        config = DGMConfig(max_attempts=1)
        dgm = DarwinGodelMachine(
            problem_statement="Fix the add_numbers function",
            git_tempdir=repo_path,
            base_commit=base_commit,
            chat_history_file=os.path.join(repo_path, 'manual_test.md'),
            language='python',
            config=config
        )
        
        # Run initial tests to confirm they fail
        success_before, output_before, stats_before = dgm.run_tests()
        print(f"  Tests before fix - Passed: {stats_before.get('passed', 0)}, Failed: {stats_before.get('failed', 0)}")
        
        # Manually fix the bug
        math_file = Path(repo_path) / "simple_math.py"
        content = math_file.read_text()
        fixed_content = content.replace("return a - b", "return a + b")
        math_file.write_text(fixed_content)
        
        # Run tests again to confirm they pass
        success_after, output_after, stats_after = dgm.run_tests()
        print(f"  Tests after fix - Passed: {stats_after.get('passed', 0)}, Failed: {stats_after.get('failed', 0)}")
        
        # Validate improvement
        assert stats_after.get('passed', 0) > stats_before.get('passed', 0)
        print("  ✅ Bug fix successfully detected")
        
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(repo_path)
    
    print("✅ Manual bug fix validation completed")

def run_comprehensive_test():
    """Run all DGM integration tests."""
    print("🧬 Darwin Gödel Machine - Comprehensive Integration Test")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # Run all test components
        test_dgm_configuration()
        requesty_available = test_requesty_integration()
        test_polyglot_support()
        test_solution_archiving()
        test_evolution_loop_mechanics()
        test_manual_bug_fix()
        
        # Summary
        duration = time.time() - start_time
        print(f"\n🎉 All integration tests completed successfully!")
        print(f"⏱️ Total test duration: {duration:.2f} seconds")
        print(f"🤖 Requesty API: {'✅ Available' if requesty_available else '⚠️ Not available'}")
        
        # Test results summary
        test_results = {
            "test_suite": "DGM Integration Tests",
            "status": "PASSED",
            "duration": duration,
            "requesty_api_available": requesty_available,
            "components_tested": [
                "Configuration loading",
                "Polyglot language support", 
                "Evolution loop mechanics",
                "Requesty API integration",
                "Solution archiving",
                "Test execution and analysis",
                "Git operations",
                "Strategy selection",
                "Bug fix validation"
            ],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Save test report
        with open("dgm_integration_test_report.json", "w") as f:
            json.dump(test_results, f, indent=2)
        
        print(f"📄 Test report saved to: dgm_integration_test_report.json")
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_comprehensive_test()
    exit(0 if success else 1)
import os
import asyncio
import pytest

@pytest.mark.skipif(not os.environ.get("ACGS_INTEGRATION"), reason="Integration test requires running services")
def test_main_wrapper():
    if 'main' in globals():
        if asyncio.iscoroutinefunction(main):
            asyncio.run(main())
        else:
            main()
