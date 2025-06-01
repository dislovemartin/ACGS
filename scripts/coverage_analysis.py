#!/usr/bin/env python3
"""
ACGS-PGP Coverage Analysis Script

Analyzes test coverage, identifies gaps, and provides recommendations
for improving coverage to exceed 95%.
"""

import json
import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

@dataclass
class CoverageResult:
    """Coverage analysis result for a module."""
    module: str
    coverage_pct: float
    missing_lines: List[int]
    excluded_lines: List[int]
    total_lines: int
    covered_lines: int
    branch_coverage: float = 0.0
    missing_branches: List[str] = None

class CoverageAnalyzer:
    """Comprehensive coverage analysis for ACGS-PGP."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.coverage_data = {}
        self.results = []
        
    def run_coverage_analysis(self) -> Dict[str, Any]:
        """Run comprehensive coverage analysis."""
        print("🔍 Running ACGS-PGP Coverage Analysis")
        print("=" * 60)
        
        # Step 1: Run tests with coverage
        print("1. Running tests with coverage...")
        test_success = self._run_tests_with_coverage()
        
        if not test_success:
            print("❌ Tests failed. Coverage analysis incomplete.")
            return {"success": False, "error": "Test execution failed"}
        
        # Step 2: Parse coverage data
        print("2. Parsing coverage data...")
        self._parse_coverage_data()
        
        # Step 3: Analyze coverage gaps
        print("3. Analyzing coverage gaps...")
        gaps = self._analyze_coverage_gaps()
        
        # Step 4: Generate recommendations
        print("4. Generating recommendations...")
        recommendations = self._generate_recommendations()
        
        # Step 5: Create detailed report
        print("5. Creating detailed report...")
        report = self._create_coverage_report(gaps, recommendations)
        
        # Step 6: Save results
        self._save_coverage_results(report)
        
        return report
    
    def _run_tests_with_coverage(self) -> bool:
        """Run tests with coverage collection."""
        try:
            # Run pytest with coverage
            cmd = [
                sys.executable, "-m", "pytest",
                "tests/",
                "--cov=src",
                "--cov-report=json:coverage.json",
                "--cov-report=html:htmlcov",
                "--cov-report=xml:coverage.xml",
                "--cov-branch",
                "--tb=short",
                "-q"
            ]
            
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            if result.returncode == 0:
                print("✅ Tests passed successfully")
                return True
            else:
                print(f"⚠️  Tests completed with issues (exit code: {result.returncode})")
                print("STDOUT:", result.stdout[-500:])  # Last 500 chars
                print("STDERR:", result.stderr[-500:])
                return True  # Continue with coverage analysis even if some tests fail
                
        except subprocess.TimeoutExpired:
            print("❌ Test execution timed out")
            return False
        except Exception as e:
            print(f"❌ Test execution failed: {e}")
            return False
    
    def _parse_coverage_data(self):
        """Parse coverage data from JSON report."""
        coverage_file = self.project_root / "coverage.json"
        
        if not coverage_file.exists():
            print("❌ Coverage data file not found")
            return
        
        try:
            with open(coverage_file, 'r') as f:
                self.coverage_data = json.load(f)
            
            # Parse file coverage data
            files_data = self.coverage_data.get('files', {})
            
            for file_path, file_data in files_data.items():
                # Skip test files and non-source files
                if any(skip in file_path for skip in ['test_', '/tests/', '__pycache__']):
                    continue
                
                # Extract module name
                module = file_path.replace('src/', '').replace('/', '.').replace('.py', '')
                
                # Calculate coverage metrics
                executed_lines = file_data.get('executed_lines', [])
                missing_lines = file_data.get('missing_lines', [])
                excluded_lines = file_data.get('excluded_lines', [])
                
                total_lines = len(executed_lines) + len(missing_lines)
                covered_lines = len(executed_lines)
                coverage_pct = (covered_lines / total_lines * 100) if total_lines > 0 else 0
                
                # Branch coverage
                branch_data = file_data.get('summary', {})
                branch_coverage = branch_data.get('percent_covered_display', 0)
                
                result = CoverageResult(
                    module=module,
                    coverage_pct=coverage_pct,
                    missing_lines=missing_lines,
                    excluded_lines=excluded_lines,
                    total_lines=total_lines,
                    covered_lines=covered_lines,
                    branch_coverage=float(branch_coverage) if branch_coverage else 0.0
                )
                
                self.results.append(result)
            
            print(f"✅ Parsed coverage data for {len(self.results)} modules")
            
        except Exception as e:
            print(f"❌ Failed to parse coverage data: {e}")
    
    def _analyze_coverage_gaps(self) -> List[Dict[str, Any]]:
        """Analyze coverage gaps and identify areas needing attention."""
        gaps = []
        
        for result in self.results:
            if result.coverage_pct < 95:
                gap_info = {
                    'module': result.module,
                    'current_coverage': result.coverage_pct,
                    'target_coverage': 95.0,
                    'gap_percentage': 95.0 - result.coverage_pct,
                    'missing_lines_count': len(result.missing_lines),
                    'missing_lines': result.missing_lines[:10],  # First 10 missing lines
                    'priority': self._calculate_priority(result),
                    'recommendations': self._get_module_recommendations(result)
                }
                gaps.append(gap_info)
        
        # Sort by priority (highest first)
        gaps.sort(key=lambda x: x['priority'], reverse=True)
        
        return gaps
    
    def _calculate_priority(self, result: CoverageResult) -> int:
        """Calculate priority for addressing coverage gaps."""
        priority = 0
        
        # Higher priority for larger gaps
        if result.coverage_pct < 50:
            priority += 10
        elif result.coverage_pct < 70:
            priority += 7
        elif result.coverage_pct < 85:
            priority += 5
        elif result.coverage_pct < 95:
            priority += 3
        
        # Higher priority for core modules
        core_modules = ['auth', 'ac_service', 'gs_service', 'fv_service', 'integrity', 'pgc']
        if any(core in result.module for core in core_modules):
            priority += 5
        
        # Higher priority for modules with many missing lines
        if len(result.missing_lines) > 50:
            priority += 3
        elif len(result.missing_lines) > 20:
            priority += 2
        
        return priority
    
    def _get_module_recommendations(self, result: CoverageResult) -> List[str]:
        """Get specific recommendations for improving module coverage."""
        recommendations = []
        
        if result.coverage_pct < 50:
            recommendations.append("Create comprehensive unit tests for core functionality")
            recommendations.append("Add integration tests for main workflows")
        
        if result.coverage_pct < 70:
            recommendations.append("Add tests for error handling and edge cases")
            recommendations.append("Test exception paths and validation logic")
        
        if result.coverage_pct < 85:
            recommendations.append("Add parameterized tests for different input scenarios")
            recommendations.append("Test configuration and initialization code")
        
        if result.coverage_pct < 95:
            recommendations.append("Add tests for utility functions and helpers")
            recommendations.append("Test logging and debugging code paths")
        
        if len(result.missing_lines) > 20:
            recommendations.append("Focus on testing the most critical missing lines first")
        
        if result.branch_coverage < result.coverage_pct:
            recommendations.append("Improve branch coverage by testing conditional logic")
        
        return recommendations
    
    def _generate_recommendations(self) -> Dict[str, Any]:
        """Generate overall recommendations for improving coverage."""
        total_modules = len(self.results)
        modules_above_95 = len([r for r in self.results if r.coverage_pct >= 95])
        modules_above_90 = len([r for r in self.results if r.coverage_pct >= 90])
        modules_below_80 = len([r for r in self.results if r.coverage_pct < 80])
        
        overall_coverage = self.coverage_data.get('totals', {}).get('percent_covered', 0)
        
        recommendations = {
            'overall_status': {
                'total_modules': total_modules,
                'modules_above_95': modules_above_95,
                'modules_above_90': modules_above_90,
                'modules_below_80': modules_below_80,
                'overall_coverage': overall_coverage,
                'target_met': overall_coverage >= 95
            },
            'priority_actions': [],
            'quick_wins': [],
            'long_term_goals': []
        }
        
        # Priority actions
        if modules_below_80 > 0:
            recommendations['priority_actions'].append(
                f"Address {modules_below_80} modules with coverage below 80%"
            )
        
        if overall_coverage < 95:
            gap = 95 - overall_coverage
            recommendations['priority_actions'].append(
                f"Increase overall coverage by {gap:.1f}% to reach 95% target"
            )
        
        # Quick wins
        modules_85_to_95 = [r for r in self.results if 85 <= r.coverage_pct < 95]
        if modules_85_to_95:
            recommendations['quick_wins'].append(
                f"Focus on {len(modules_85_to_95)} modules between 85-95% coverage for quick wins"
            )
        
        # Long-term goals
        recommendations['long_term_goals'].append("Maintain 95%+ coverage for all new code")
        recommendations['long_term_goals'].append("Implement coverage gates in CI/CD pipeline")
        recommendations['long_term_goals'].append("Add mutation testing for quality assurance")
        
        return recommendations
    
    def _create_coverage_report(self, gaps: List[Dict], recommendations: Dict) -> Dict[str, Any]:
        """Create comprehensive coverage report."""
        return {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_modules': len(self.results),
                'overall_coverage': self.coverage_data.get('totals', {}).get('percent_covered', 0),
                'target_coverage': 95.0,
                'modules_meeting_target': len([r for r in self.results if r.coverage_pct >= 95]),
                'coverage_gaps': len(gaps)
            },
            'coverage_gaps': gaps,
            'recommendations': recommendations,
            'detailed_results': [
                {
                    'module': r.module,
                    'coverage_pct': r.coverage_pct,
                    'missing_lines_count': len(r.missing_lines),
                    'branch_coverage': r.branch_coverage,
                    'total_lines': r.total_lines
                }
                for r in sorted(self.results, key=lambda x: x.coverage_pct)
            ]
        }
    
    def _save_coverage_results(self, report: Dict[str, Any]):
        """Save coverage analysis results."""
        # Save JSON report
        report_file = self.project_root / "coverage_analysis_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Coverage analysis report saved: {report_file}")
        
        # Print summary
        summary = report['summary']
        print(f"\n📊 Coverage Summary:")
        print(f"  Overall Coverage: {summary['overall_coverage']:.1f}%")
        print(f"  Target Coverage: {summary['target_coverage']:.1f}%")
        print(f"  Modules Meeting Target: {summary['modules_meeting_target']}/{summary['total_modules']}")
        print(f"  Coverage Gaps: {summary['coverage_gaps']}")
        
        if summary['overall_coverage'] >= 95:
            print("🎉 Coverage target achieved!")
        else:
            gap = 95 - summary['overall_coverage']
            print(f"⚠️  Need to improve coverage by {gap:.1f}% to reach target")


def main():
    """Main execution function."""
    analyzer = CoverageAnalyzer()
    report = analyzer.run_coverage_analysis()
    
    if report.get('success', True):
        print("\n✅ Coverage analysis completed successfully")
        return 0
    else:
        print("\n❌ Coverage analysis failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
