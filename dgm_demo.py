#!/usr/bin/env python3
"""
Darwin Gödel Machine - Demonstration Script

This script demonstrates how to use the Darwin Gödel Machine for software engineering tasks.
It includes example scenarios and shows the evolution process in action.
"""

import os
import tempfile
import subprocess
import json
from pathlib import Path
from dgm_best_swe_agent import DarwinGodelMachine, DGMConfig

# Import Requesty API integration
try:
    from requesty_api_integration import RequestyAPI
    REQUESTY_AVAILABLE = True
except ImportError:
    REQUESTY_AVAILABLE = False
    print("Warning: Requesty API not available for demo.")

def create_demo_repository():
    """Create a demonstration repository with a simple Python project and failing tests."""
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="dgm_demo_")
    repo_path = Path(temp_dir)
    
    # Initialize git repository
    subprocess.run(['git', 'init'], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(['git', 'config', 'user.email', 'demo@dgm.ai'], cwd=repo_path, check=True)
    subprocess.run(['git', 'config', 'user.name', 'DGM Demo'], cwd=repo_path, check=True)
    
    # Create a simple Python project with failing tests
    
    # Main module
    main_py = repo_path / "calculator.py"
    main_py.write_text('''
class Calculator:
    """A simple calculator class with intentional bugs for DGM demonstration."""
    
    def add(self, a, b):
        # Bug: should return a + b
        return a - b
    
    def multiply(self, a, b):
        # Bug: missing implementation
        pass
    
    def divide(self, a, b):
        # Bug: no zero division check
        return a / b
    
    def fibonacci(self, n):
        # Bug: incorrect implementation
        if n <= 1:
            return n
        return self.fibonacci(n-1) + self.fibonacci(n-3)  # Should be n-2
''')
    
    # Test file
    test_py = repo_path / "test_calculator.py"
    test_py.write_text('''
import pytest
from calculator import Calculator

class TestCalculator:
    def setup_method(self):
        self.calc = Calculator()
    
    def test_add(self):
        assert self.calc.add(2, 3) == 5
        assert self.calc.add(-1, 1) == 0
        assert self.calc.add(0, 0) == 0
    
    def test_multiply(self):
        assert self.calc.multiply(2, 3) == 6
        assert self.calc.multiply(-2, 3) == -6
        assert self.calc.multiply(0, 5) == 0
    
    def test_divide(self):
        assert self.calc.divide(6, 2) == 3.0
        assert self.calc.divide(5, 2) == 2.5
        
        # Should handle zero division
        with pytest.raises(ZeroDivisionError):
            self.calc.divide(5, 0)
    
    def test_fibonacci(self):
        assert self.calc.fibonacci(0) == 0
        assert self.calc.fibonacci(1) == 1
        assert self.calc.fibonacci(5) == 5
        assert self.calc.fibonacci(8) == 21
''')
    
    # Requirements file
    requirements = repo_path / "requirements.txt"
    requirements.write_text('pytest>=7.0.0\n')
    
    # README
    readme = repo_path / "README.md"
    readme.write_text('''
# Calculator Demo Project

A simple calculator project for demonstrating the Darwin Gödel Machine.

## Running Tests

```bash
pytest test_calculator.py -v
```

## Known Issues

This project intentionally contains bugs to demonstrate DGM's self-improvement capabilities:
- Addition returns subtraction
- Multiplication is not implemented
- Division doesn't handle zero division
- Fibonacci sequence has incorrect recursion
''')
    
    # Commit initial version
    subprocess.run(['git', 'add', '.'], cwd=repo_path, check=True)
    subprocess.run(['git', 'commit', '-m', 'Initial commit with buggy calculator'], 
                  cwd=repo_path, check=True)
    
    # Get the base commit hash
    result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                          cwd=repo_path, capture_output=True, text=True, check=True)
    base_commit = result.stdout.strip()
    
    return str(repo_path), base_commit

def run_dgm_demo():
    """Run a complete DGM demonstration."""
    
    print("🧬 Darwin Gödel Machine - Demonstration")
    print("=" * 50)
    
    # Create demo repository
    print("\n📁 Creating demonstration repository...")
    repo_path, base_commit = create_demo_repository()
    print(f"✅ Repository created at: {repo_path}")
    print(f"📝 Base commit: {base_commit[:8]}")
    
    # Show initial test results
    print("\n🧪 Running initial tests to show failures...")
    try:
        result = subprocess.run(['pytest', 'test_calculator.py', '-v'], 
                              cwd=repo_path, capture_output=True, text=True)
        print("Initial test output:")
        print(result.stdout)
        print(result.stderr)
    except Exception as e:
        print(f"Test execution error: {e}")
    
    # Configure DGM
    config = DGMConfig(
        max_attempts=3,
        performance_threshold=0.9,
        enable_self_improvement=True,
        archive_solutions=True
    )
    
    # Initialize Requesty API
    requesty_api = None
    if REQUESTY_AVAILABLE:
        try:
            requesty_api = RequestyAPI()
            print("✅ Requesty API integration enabled for demo")
        except Exception as e:
            print(f"⚠️ Requesty API initialization failed: {e}")
    else:
        print("⚠️ Requesty API not available - demo will use mock responses")
    
    # Initialize DGM
    print("\n🧬 Initializing Darwin Gödel Machine...")
    problem_statement = """
Fix the bugs in the Calculator class to make all tests pass:

1. The add() method should return the sum of two numbers, not the difference
2. The multiply() method needs to be implemented to return the product
3. The divide() method should handle zero division by raising ZeroDivisionError
4. The fibonacci() method has incorrect recursion - fix the recursive call

All tests in test_calculator.py should pass after the fixes.
"""
    
    dgm = DarwinGodelMachine(
        problem_statement=problem_statement,
        git_tempdir=repo_path,
        base_commit=base_commit,
        chat_history_file=os.path.join(repo_path, 'dgm_demo_evolution.md'),
        language='python',
        config=config,
        requesty_api=requesty_api
    )
    
    # Run DGM evolution
    print("\n🔄 Starting DGM evolution process...")
    print("This may take a few minutes as DGM iteratively improves the solution...")
    
    try:
        final_solution = dgm.evolve()
        
        if final_solution:
            print(f"\n✅ DGM Evolution Complete!")
            print(f"📊 Final Solution Summary:")
            print(f"   • Attempt: #{final_solution.attempt_number}")
            print(f"   • Success: {final_solution.test_success}")
            print(f"   • Strategy: {final_solution.improvement_strategy}")
            print(f"   • Pass Rate: {final_solution.test_stats.get('passed', 0)}/{final_solution.test_stats.get('total', 0)}")
            print(f"   • Execution Time: {final_solution.execution_time:.2f}s")
            print(f"   • Archive Size: {len(dgm.solution_archive)} solutions")
            
            # Show final test results
            print("\n🧪 Final test results:")
            try:
                result = subprocess.run(['pytest', 'test_calculator.py', '-v'], 
                                      cwd=repo_path, capture_output=True, text=True)
                print(result.stdout)
                if result.stderr:
                    print("Stderr:", result.stderr)
            except Exception as e:
                print(f"Final test execution error: {e}")
            
            # Save demonstration results
            demo_results = {
                "repository_path": repo_path,
                "base_commit": base_commit,
                "final_solution": {
                    "attempt_number": final_solution.attempt_number,
                    "test_success": final_solution.test_success,
                    "test_stats": final_solution.test_stats,
                    "improvement_strategy": final_solution.improvement_strategy,
                    "execution_time": final_solution.execution_time
                },
                "evolution_summary": {
                    "total_attempts": len(dgm.solution_archive),
                    "generation": dgm.generation_count,
                    "archive_size": len(dgm.solution_archive)
                }
            }
            
            results_file = os.path.join(repo_path, 'dgm_demo_results.json')
            with open(results_file, 'w') as f:
                json.dump(demo_results, f, indent=2)
            
            print(f"\n📄 Demonstration results saved to: {results_file}")
            print(f"📝 Evolution log available at: {os.path.join(repo_path, 'dgm_demo_evolution.md')}")
            
        else:
            print("❌ DGM evolution failed to produce a solution")
            
    except Exception as e:
        print(f"❌ Error during DGM evolution: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n🏁 Demonstration complete!")
    print(f"📁 Repository available at: {repo_path}")
    print("\nTo explore the results:")
    print(f"  cd {repo_path}")
    print("  git log --oneline")
    print("  cat dgm_demo_evolution.md")
    print("  pytest test_calculator.py -v")

def run_interactive_demo():
    """Run an interactive demonstration with user choices."""
    
    print("🧬 Darwin Gödel Machine - Interactive Demo")
    print("=" * 45)
    
    scenarios = {
        "1": {
            "name": "Simple Calculator Bug Fixes",
            "description": "Fix arithmetic bugs in a calculator class",
            "complexity": "Beginner"
        },
        "2": {
            "name": "Custom Problem",
            "description": "Specify your own problem statement",
            "complexity": "Advanced"
        }
    }
    
    print("\nAvailable demonstration scenarios:")
    for key, scenario in scenarios.items():
        print(f"  {key}. {scenario['name']}")
        print(f"     {scenario['description']} ({scenario['complexity']})")
    
    choice = input("\nSelect a scenario (1-2): ").strip()
    
    if choice == "1":
        run_dgm_demo()
    elif choice == "2":
        print("\n📝 Custom Problem Setup")
        repo_path = input("Enter repository path: ").strip()
        base_commit = input("Enter base commit hash: ").strip()
        problem_statement = input("Enter problem statement: ").strip()
        language = input("Enter programming language (python/javascript/rust/go/cpp/java): ").strip()
        
        if all([repo_path, base_commit, problem_statement]):
            # Initialize Requesty API for interactive demo
            requesty_api = None
            if REQUESTY_AVAILABLE:
                try:
                    requesty_api = RequestyAPI()
                    print("✅ Requesty API enabled for interactive demo")
                except Exception as e:
                    print(f"⚠️ Requesty API initialization failed: {e}")
            
            config = DGMConfig()
            dgm = DarwinGodelMachine(
                problem_statement=problem_statement,
                git_tempdir=repo_path,
                base_commit=base_commit,
                language=language or 'python',
                config=config,
                requesty_api=requesty_api
            )
            
            print("\n🔄 Starting custom DGM evolution...")
            final_solution = dgm.evolve()
            
            if final_solution:
                print(f"\n✅ Custom evolution complete!")
                print(f"Success: {final_solution.test_success}")
            else:
                print("❌ Evolution failed")
        else:
            print("❌ Missing required parameters")
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        run_interactive_demo()
    else:
        run_dgm_demo()