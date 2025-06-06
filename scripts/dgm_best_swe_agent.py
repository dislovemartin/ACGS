"""
Darwin Gödel Machine - Best Software Engineering Agent

This implementation combines the theoretical foundation of the Darwin Gödel Machine
with the practical improvements discovered through iterative self-improvement.

Key Features:
- Multi-attempt problem solving with iterative improvement
- Detailed test result analysis and error tracking
- Enhanced editing capabilities (str_replace, insert, undo)
- Language-specific test output parsing
- Progress tracking between attempts
- Integration with Requesty API system
- Polyglot programming support
- Comprehensive logging and debugging

Based on research: arXiv:2505.22954v1 - "Darwin Gödel Machine"
"""

import argparse
import subprocess
import logging
from logging.handlers import RotatingFileHandler
import os
import threading
import json
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple, Any
from pathlib import Path

# Import Requesty API integration
try:
    from requesty_api_integration import RequestyAPI
    REQUESTY_AVAILABLE = True
except ImportError:
    REQUESTY_AVAILABLE = False
    print("Warning: Requesty API not available. Running in standalone mode.")

# TEST COMMANDS for different languages
# IMPORTANT: TEST COMMAND SHOULD BE RUN UNDER git_tempdir!!
NPM_TEST_COMMANDS = [
    ["sh", "-c", "set -e"],
    ["sh", "-c", "[ ! -e node_modules ] && ln -s /npm-install/node_modules ."],
    ["sh", "-c", "[ ! -e package-lock.json ] && ln -s /npm-install/package-lock.json ."],
    ["sed", "-i", "s/\\bxtest(/test(/g", "*.spec.js"],
    ["npm", "run", "test"]
]

CPP_TEST_COMMANDS = [
    ["sh", "-c", "set -e"],
    ["sh", "-c", "[ ! -d \"build\" ] && mkdir build"],
    ["sh", "-c", "cd build"],
    ["cmake", "-DEXERCISM_RUN_ALL_TESTS=1", "-G", "Unix Makefiles", ".."],
    ["make"],
    ["sh", "-c", "cd ../"]
]

TEST_COMMANDS = {
    "python": [["pytest", "-rA", "--tb=long"]],
    "rust": [["cargo", "test", "--", "--include-ignored"]],
    "go": [["go", "test", "./..."]],
    "javascript": NPM_TEST_COMMANDS,
    "cpp": CPP_TEST_COMMANDS,
    "java": [["./gradlew", "test"]],
}

# Global edit history for undo functionality
edit_history: Dict[str, List[str]] = {}

# Thread-local storage for logger instances
thread_local = threading.local()


@dataclass
class SolutionAttempt:
    """Class to store information about a solution attempt."""
    patch: str  # The patch content
    test_output: str  # Raw test output
    test_success: bool  # Whether tests passed
    test_stats: dict  # Test statistics (e.g., number of passed/failed tests)
    error_messages: List[str] = field(default_factory=list)  # List of specific error messages
    test_details: dict = field(default_factory=dict)  # Detailed test information like specific test names and their status
    execution_time: float = None  # Test execution time in seconds
    attempt_number: int = None  # The attempt number in the sequence
    improvement_strategy: str = ""  # Strategy used for this attempt
    

@dataclass
class DGMConfig:
    """Configuration for Darwin Gödel Machine."""
    max_attempts: int = 3
    max_tokens: int = 4000
    temperature: float = 0.7
    enable_self_improvement: bool = True
    enable_requesty_integration: bool = True
    archive_solutions: bool = True
    use_novelty_selection: bool = True
    performance_threshold: float = 0.8  # 80% test pass rate threshold
    

class EnhancedEditTool:
    """Enhanced editing tool with undo, string replacement, and insertion capabilities."""
    
    @staticmethod
    def validate_path(path: str, command: str) -> Path:
        """Validate the file path for each command."""
        path_obj = Path(path)
        
        if command == "view":
            if not path_obj.exists():
                raise ValueError(f"The path {path} does not exist.")
        elif command == "create":
            if path_obj.exists():
                raise ValueError(f"Cannot create new file; {path} already exists.")
        else:
            if not path_obj.exists():
                raise ValueError(f"The file {path} does not exist.")
            if path_obj.is_dir():
                raise ValueError(f"{path} is a directory and cannot be edited as a file.")
        
        return path_obj
    
    @staticmethod
    def read_file(path: Path) -> str:
        """Read entire file contents."""
        try:
            return path.read_text(encoding='utf-8')
        except Exception as e:
            raise ValueError(f"Failed to read file: {e}")
    
    @staticmethod
    def write_file(path: Path, content: str, save_history: bool = True):
        """Write (overwrite) entire file contents."""
        try:
            if save_history and path.exists():
                if str(path) not in edit_history:
                    edit_history[str(path)] = []
                edit_history[str(path)].append(path.read_text())
            
            path.write_text(content, encoding='utf-8')
        except Exception as e:
            raise ValueError(f"Failed to write file: {e}")
    
    @staticmethod
    def str_replace(path_obj: Path, old_str: str, new_str: str) -> str:
        """Replace string in file, ensuring uniqueness."""
        content = EnhancedEditTool.read_file(path_obj)
        
        if content.count(old_str) > 1:
            return f"Error: Multiple occurrences of '{old_str}' found. Replacement requires a unique match."
        elif content.count(old_str) == 0:
            return f"Error: String '{old_str}' not found in file."
        
        new_content = content.replace(old_str, new_str)
        EnhancedEditTool.write_file(path_obj, new_content)
        return f"File at {path_obj} has been edited: replaced '{old_str}' with '{new_str}'."
    
    @staticmethod
    def insert_text(path_obj: Path, insert_line: int, new_str: str) -> str:
        """Insert text at specified line number (1-based)."""
        content = EnhancedEditTool.read_file(path_obj)
        lines = content.splitlines()
        
        if insert_line < 1:
            raise ValueError(f"Invalid insert line {insert_line} - must be greater than 0")
        if insert_line > len(lines) + 1:
            raise ValueError(f"Invalid insert line {insert_line} - file only has {len(lines)} lines")
        
        new_text = new_str.rstrip('\n')
        lines.insert(insert_line, new_text)
        new_content = '\n'.join(lines) + '\n'
        
        EnhancedEditTool.write_file(path_obj, new_content)
        return f"File at {path_obj} has been edited: inserted text at line {insert_line}."
    
    @staticmethod
    def undo_edit(path_obj: Path) -> str:
        """Undo last edit operation on the file."""
        path_str = str(path_obj)
        if path_str not in edit_history or not edit_history[path_str]:
            return "Error: No edit history available for this file."
        
        previous_content = edit_history[path_str].pop()
        EnhancedEditTool.write_file(path_obj, previous_content, save_history=False)
        return f"Last edit on {path_obj} has been undone successfully."


def get_thread_logger():
    """Get the logger instance specific to the current thread."""
    return getattr(thread_local, 'logger', None)


def set_thread_logger(logger):
    """Set the logger instance for the current thread."""
    thread_local.logger = logger


def setup_logger(log_file='./dgm_chat_history.md', level=logging.INFO):
    """Set up a logger with both file and console handlers."""
    logger = logging.getLogger(f'DGM-{threading.get_ident()}')
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers = []
    
    # Create formatters
    file_formatter = logging.Formatter('%(message)s')
    
    # Create and set up file handler
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
    file_handler.setLevel(level)
    file_handler.setFormatter(file_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    
    # Store logger in thread-local storage
    set_thread_logger(logger)
    
    return logger


def safe_log(message, level=logging.INFO):
    """Thread-safe logging function that ensures messages go to the correct logger."""
    logger = get_thread_logger()
    if logger:
        logger.log(level, message)
    else:
        print(f"Warning: No logger found for thread {threading.get_ident()}")


class DarwinGodelMachine:
    """
    Darwin Gödel Machine - Self-improving AI system for software engineering tasks.
    
    This implementation combines theoretical DGM concepts with practical improvements
    discovered through iterative self-improvement.
    """
    
    def __init__(
        self,
        problem_statement: str,
        git_tempdir: str,
        base_commit: str,
        chat_history_file: str = './dgm_chat_history.md',
        test_description: Optional[str] = None,
        language: str = 'python',
        config: Optional[DGMConfig] = None,
        requesty_api: Optional[Any] = None
    ):
        self.problem_statement = problem_statement
        self.git_tempdir = git_tempdir
        self.base_commit = base_commit
        self.chat_history_file = chat_history_file
        self.test_description = test_description
        self.language = language
        self.config = config or DGMConfig()
        self.requesty_api = requesty_api
        
        # Initialize logger
        self.logger = setup_logger(chat_history_file)
        
        # Clear the log file
        with open(chat_history_file, 'w') as f:
            f.write('')
        
        # Initialize solution archive for DGM
        self.solution_archive: List[SolutionAttempt] = []
        self.generation_count = 0
        
        # Enhanced edit tool
        self.edit_tool = EnhancedEditTool()
        
        safe_log("🧬 Darwin Gödel Machine Initialized")
        safe_log(f"Language: {self.language}")
        safe_log(f"Git Directory: {self.git_tempdir}")
        safe_log(f"Problem: {self.problem_statement[:100]}...")
    
    def get_current_edits(self):
        """Get current git diff versus base commit."""
        try:
            result = subprocess.run(
                ['git', 'diff', self.base_commit],
                cwd=self.git_tempdir,
                capture_output=True,
                text=True,
                check=True
            )
            diff = result.stdout
            
            new_msg_history = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"# Current Repo Edits\n{diff}",
                        }
                    ],
                }
            ]
            return new_msg_history
        except subprocess.CalledProcessError as e:
            safe_log(f"Error getting git diff: {e}")
            return []
    
    def extract_test_details(self, output: str) -> Tuple[dict, List[str], dict]:
        """Extract detailed test information from the output."""
        error_messages = []
        test_details = {}
        stats = {"passed": 0, "failed": 0, "errors": 0, "total": 0, "skipped": 0}
        
        lines = output.split("\n")
        
        # Language-specific parsing
        if self.language == "python":
            for line in lines:
                if "FAILED" in line and "::" in line:
                    test_name = line.split("::")[1].split()[0]
                    test_details[test_name] = "FAILED"
                    stats["failed"] += 1
                elif "PASSED" in line and "::" in line:
                    test_name = line.split("::")[1].split()[0]
                    test_details[test_name] = "PASSED"
                    stats["passed"] += 1
                elif "ERROR" in line and "::" in line:
                    test_name = line.split("::")[1].split()[0]
                    test_details[test_name] = "ERROR"
                    stats["errors"] += 1
                    if lines.index(line) + 1 < len(lines):
                        error_messages.append(lines[lines.index(line) + 1])
        
        elif self.language in ["javascript", "node"]:
            current_test = None
            for line in lines:
                if line.startswith('✓'):
                    test_name = line.replace('✓', '').strip()
                    test_details[test_name] = "PASSED"
                    stats["passed"] += 1
                elif line.startswith('×'):
                    test_name = line.replace('×', '').strip()
                    test_details[test_name] = "FAILED"
                    stats["failed"] += 1
                    current_test = test_name
                elif current_test and ('Error:' in line or 'AssertionError:' in line):
                    error_messages.append(f"{current_test}: {line.strip()}")
        
        elif self.language == "rust":
            for line in lines:
                if "test" in line and "... ok" in line:
                    test_name = line.split("test")[1].split("...")[0].strip()
                    test_details[test_name] = "PASSED"
                    stats["passed"] += 1
                elif "test" in line and "... FAILED" in line:
                    test_name = line.split("test")[1].split("...")[0].strip()
                    test_details[test_name] = "FAILED"
                    stats["failed"] += 1
                elif "---- " in line and " stdout ----" in line:
                    test_name = line.split("----")[1].split("stdout")[0].strip()
                    if test_name in test_details and test_details[test_name] == "FAILED":
                        error_messages.append(f"{test_name}: {next((l for l in lines[lines.index(line)+1:] if l.strip()), '')}")
        
        # Generic counting for other languages or as fallback
        if not any(stats.values()):
            stats["passed"] = output.count("PASS") + output.count("ok")
            stats["failed"] = output.count("FAIL") + output.count("not ok")
            stats["errors"] = output.count("ERROR") + output.count("panic:")
        
        stats["total"] = stats["passed"] + stats["failed"] + stats["errors"]
        
        return stats, error_messages, test_details
    
    def run_tests(self) -> Tuple[bool, str, dict]:
        """Run tests and return success status, output, and test statistics."""
        start_time = time.time()
        success = False
        output = ""
        
        try:
            for command in TEST_COMMANDS.get(self.language, []):
                proc = subprocess.run(
                    command,
                    cwd=self.git_tempdir,
                    capture_output=True,
                    text=True,
                    check=False
                )
                output += f"$ {' '.join(command)}\n{proc.stdout}\n{proc.stderr}\n"
                success = proc.returncode == 0
                if not success:
                    break
            
            # Extract detailed test information
            stats, error_messages, test_details = self.extract_test_details(output)
            stats["execution_time"] = time.time() - start_time
            
            # Enhance stats with extracted information
            stats["error_messages"] = error_messages
            stats["test_details"] = test_details
            
        except Exception as e:
            output = f"Error running tests: {str(e)}"
            success = False
            stats = {
                "passed": 0, "failed": 0, "errors": 1, "total": 1,
                "execution_time": time.time() - start_time,
                "error_messages": [str(e)],
                "test_details": {}
            }
        
        return success, output, stats
    
    def analyze_test_results(self, attempts: List[SolutionAttempt]) -> str:
        """Analyze test results and create a detailed summary for the agent."""
        summary = "# 🧬 Darwin Gödel Machine - Test Results Analysis\n\n"
        
        # Overall progress tracking
        if len(attempts) > 1:
            summary += "## 📈 Progress Overview\n"
            first_attempt = attempts[0].test_stats
            last_attempt = attempts[-1].test_stats
            
            progress = {
                "passed": last_attempt["passed"] - first_attempt["passed"],
                "failed": first_attempt["failed"] - last_attempt["failed"],
                "errors": first_attempt["errors"] - last_attempt["errors"]
            }
            
            summary += "Progress since first attempt:\n"
            summary += f"- Additional passing tests: {progress['passed']}\n"
            summary += f"- Reduced failures: {progress['failed']}\n"
            summary += f"- Reduced errors: {progress['errors']}\n\n"
        
        # Detailed attempt analysis
        for i, attempt in enumerate(attempts, 1):
            summary += f"## 🔄 Attempt {i}\n"
            summary += f"Test Success: {attempt.test_success}\n"
            summary += f"Execution Time: {attempt.test_stats.get('execution_time', 'N/A'):.2f}s\n"
            summary += f"Strategy: {attempt.improvement_strategy}\n"
            
            # Test statistics
            stats = attempt.test_stats
            total = stats.get("total", 0) or 1
            pass_rate = (stats.get("passed", 0) / total) * 100
            
            summary += f"Pass Rate: {pass_rate:.1f}% ({stats.get('passed', 0)}/{total})\n"
            summary += "Test Statistics:\n"
            summary += f"- Passed: {stats.get('passed', 0)}\n"
            summary += f"- Failed: {stats.get('failed', 0)}\n"
            summary += f"- Errors: {stats.get('errors', 0)}\n"
            summary += f"- Total: {total}\n\n"
            
            # Error messages
            if stats.get("error_messages"):
                summary += "Error Messages:\n```\n"
                for error in stats["error_messages"][:5]:
                    summary += f"{error}\n"
                if len(stats["error_messages"]) > 5:
                    summary += f"... and {len(stats['error_messages']) - 5} more errors\n"
                summary += "```\n\n"
            
            # Test details
            if stats.get("test_details"):
                summary += "Individual Test Results:\n```\n"
                for test_name, result in stats["test_details"].items():
                    summary += f"{result}: {test_name}\n"
                summary += "```\n\n"
        
        # Recommendations for next attempt
        if not attempts[-1].test_success:
            summary += "## 💡 Recommendations for Next Attempt\n"
            last_stats = attempts[-1].test_stats
            
            if last_stats.get("errors", 0) > 0:
                summary += "- Focus on resolving runtime errors first\n"
            if last_stats.get("failed", 0) > 0:
                summary += "- Address failing test cases\n"
            if len(attempts) > 1 and not attempts[-1].test_success:
                prev_stats = attempts[-2].test_stats
                if last_stats.get("passed", 0) < prev_stats.get("passed", 0):
                    summary += "- Recent changes caused regressions. Consider reverting some changes\n"
        
        return summary
    
    def select_improvement_strategy(self, attempts: List[SolutionAttempt]) -> str:
        """Select improvement strategy based on DGM principles."""
        if not attempts:
            return "initial_analysis"
        
        last_attempt = attempts[-1]
        
        # If we have high error rate, focus on basic correctness
        if last_attempt.test_stats.get("errors", 0) > 0:
            return "error_resolution"
        
        # If we have test failures, focus on test-driven fixes
        if last_attempt.test_stats.get("failed", 0) > 0:
            return "test_driven_fix"
        
        # If we're close to success, do fine-tuning
        pass_rate = last_attempt.test_stats.get("passed", 0) / max(last_attempt.test_stats.get("total", 1), 1)
        if pass_rate > 0.8:
            return "fine_tuning"
        
        # If we're making progress, continue with incremental improvement
        if len(attempts) > 1:
            prev_passed = attempts[-2].test_stats.get("passed", 0)
            curr_passed = last_attempt.test_stats.get("passed", 0)
            if curr_passed > prev_passed:
                return "incremental_improvement"
        
        # Default to comprehensive refactor
        return "comprehensive_refactor"
    
    def chat_with_agent(self, instruction: str, strategy: str = "initial") -> str:
        """Chat with the AI agent using available backends."""
        enhanced_instruction = f"""
🧬 Darwin Gödel Machine - Software Engineering Agent

Strategy: {strategy}
Language: {self.language}
Working Directory: {self.git_tempdir}

{instruction}

Please use the following enhanced editing capabilities:
- str_replace(old_str, new_str): Replace specific strings
- insert_text(line_number, text): Insert text at specific lines
- undo_edit(): Undo the last edit operation
- Standard file operations: create, edit, view

Focus on producing working, tested code that follows best practices for {self.language}.
"""
        
        if REQUESTY_AVAILABLE and self.requesty_api:
            try:
                response = self.requesty_api.send_message(enhanced_instruction)
                safe_log(f"🤖 Agent Response: {response[:200]}...")
                return response
            except Exception as e:
                safe_log(f"❌ Requesty API error: {e}")
        
        # Fallback to mock response for demonstration
        safe_log("⚠️ Using mock response - implement actual LLM integration")
        return "Mock response: Analysis completed, implementing solution..."
    
    def reset_to_commit(self):
        """Reset git repository to base commit."""
        try:
            subprocess.run(
                ['git', 'reset', '--hard', self.base_commit],
                cwd=self.git_tempdir,
                check=True
            )
            safe_log(f"🔄 Reset to commit: {self.base_commit}")
        except subprocess.CalledProcessError as e:
            safe_log(f"❌ Error resetting to commit: {e}")
    
    def get_current_patch(self) -> str:
        """Get current patch versus base commit."""
        try:
            result = subprocess.run(
                ['git', 'diff', self.base_commit],
                cwd=self.git_tempdir,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            safe_log(f"❌ Error getting patch: {e}")
            return ""
    
    def apply_patch(self, patch: str):
        """Apply a patch to the repository."""
        try:
            proc = subprocess.run(
                ['git', 'apply'],
                input=patch,
                text=True,
                cwd=self.git_tempdir,
                check=True
            )
            safe_log("✅ Patch applied successfully")
        except subprocess.CalledProcessError as e:
            safe_log(f"❌ Error applying patch: {e}")
    
    def archive_solution(self, attempt: SolutionAttempt):
        """Archive a solution in the DGM solution archive."""
        if self.config.archive_solutions:
            self.solution_archive.append(attempt)
            safe_log(f"📚 Archived solution #{len(self.solution_archive)}")
    
    def select_parent_solution(self) -> Optional[SolutionAttempt]:
        """Select parent solution using DGM selection strategy."""
        if not self.solution_archive:
            return None
        
        if self.config.use_novelty_selection:
            # Simple novelty-based selection (in practice, would use more sophisticated metrics)
            return max(self.solution_archive, key=lambda x: x.test_stats.get("passed", 0))
        else:
            # Performance-based selection
            successful_solutions = [s for s in self.solution_archive if s.test_success]
            if successful_solutions:
                return max(successful_solutions, key=lambda x: x.test_stats.get("passed", 0))
            return max(self.solution_archive, key=lambda x: x.test_stats.get("passed", 0))
    
    def evolve(self) -> Optional[SolutionAttempt]:
        """
        Main DGM evolution loop - the heart of the Darwin Gödel Machine.
        """
        safe_log("🧬 Starting DGM Evolution Process")
        
        attempts: List[SolutionAttempt] = []
        best_attempt: Optional[SolutionAttempt] = None
        
        base_task = f"""I have uploaded a code repository in the directory {self.git_tempdir}. Help solve the following problem.

<problem_description>
{self.problem_statement}
</problem_description>

Your task is to make changes to the files in the {self.git_tempdir} directory to address the <problem_description>. I have already taken care of the required dependencies.
"""
        
        for attempt_num in range(self.config.max_attempts):
            safe_log(f"🔄 Evolution Attempt {attempt_num + 1}/{self.config.max_attempts}")
            
            # Reset to base commit for each attempt
            self.reset_to_commit()
            
            # Select improvement strategy
            strategy = self.select_improvement_strategy(attempts)
            
            # Prepare instruction based on previous attempts and DGM principles
            instruction = base_task
            if attempts:
                instruction += "\n\nPrevious solution attempts have been made. Here are the results:\n\n"
                instruction += self.analyze_test_results(attempts)
                instruction += f"\nPlease analyze these results and provide an improved solution using the '{strategy}' strategy that addresses the issues found."
            else:
                instruction += "\n\nPlease analyze the problem description carefully. Then make edits to the code files to complete the instruction."
            
            # Get solution attempt from agent
            response = self.chat_with_agent(instruction, strategy)
            
            # Capture current patch
            current_patch = self.get_current_patch()
            
            # Run tests and collect results
            test_success, test_output, test_stats = self.run_tests()
            
            # Create and store attempt with enhanced information
            attempt = SolutionAttempt(
                patch=current_patch,
                test_output=test_output,
                test_success=test_success,
                test_stats=test_stats,
                error_messages=test_stats.get('error_messages', []),
                test_details=test_stats.get('test_details', {}),
                execution_time=test_stats.get('execution_time', None),
                attempt_number=attempt_num + 1,
                improvement_strategy=strategy
            )
            attempts.append(attempt)
            
            # Archive solution for future DGM generations
            self.archive_solution(attempt)
            
            # Update best attempt based on multiple criteria
            if test_success and (
                best_attempt is None or
                (attempt.test_stats["passed"] > best_attempt.test_stats["passed"]) or
                (attempt.test_stats["passed"] == best_attempt.test_stats["passed"] and
                 len(attempt.error_messages or []) < len(best_attempt.error_messages or []))
            ):
                best_attempt = attempt
            
            # Log detailed attempt information
            safe_log(f"\n=== 🧬 DGM Attempt {attempt_num + 1} Summary ===")
            safe_log(f"Strategy: {strategy}")
            safe_log(f"Test Success: {test_success}")
            safe_log(f"Tests Passed: {test_stats.get('passed', 0)}")
            safe_log(f"Tests Failed: {test_stats.get('failed', 0)}")
            safe_log(f"Errors: {test_stats.get('errors', 0)}")
            safe_log(f"Execution Time: {test_stats.get('execution_time', 'N/A'):.2f}s")
            safe_log(f"Archive Size: {len(self.solution_archive)}")
            
            # Check if we've achieved the performance threshold
            pass_rate = test_stats.get('passed', 0) / max(test_stats.get('total', 1), 1)
            if test_success and pass_rate >= self.config.performance_threshold:
                safe_log(f"🎯 Performance threshold reached: {pass_rate:.1%}")
                break
        
        # Apply the best solution
        final_attempt = best_attempt or attempts[-1] if attempts else None
        if final_attempt:
            self.reset_to_commit()
            self.apply_patch(final_attempt.patch)
            safe_log(f"✅ Applied final solution from attempt #{final_attempt.attempt_number}")
        
        self.generation_count += 1
        safe_log(f"🧬 DGM Evolution Generation {self.generation_count} Complete")
        
        return final_attempt


def main():
    parser = argparse.ArgumentParser(description='Darwin Gödel Machine - Best Software Engineering Agent')
    parser.add_argument('--problem_statement', required=True, help='The problem statement to process')
    parser.add_argument('--git_dir', required=True, help='Path to git repository directory')
    parser.add_argument('--base_commit', required=True, help='Base commit hash to compare against')
    parser.add_argument('--chat_history_file', required=True, help='Path to chat history file')
    parser.add_argument('--outdir', required=False, default="/dgm/", help='Output directory')
    parser.add_argument('--test_description', default=None, required=False, help='Description of how to test the repository')
    parser.add_argument('--language', required=False, default="python", 
                       choices=['cpp', 'java', 'python', 'go', 'rust', 'javascript'], 
                       help='Task\'s programming language')
    parser.add_argument('--max_attempts', type=int, default=3, help='Maximum number of solution attempts')
    parser.add_argument('--enable_requesty', action='store_true', help='Enable Requesty API integration')
    parser.add_argument('--config_file', help='Path to DGM configuration file')
    
    args = parser.parse_args()
    
    # Load configuration
    config = DGMConfig(max_attempts=args.max_attempts)
    if args.config_file and os.path.exists(args.config_file):
        with open(args.config_file, 'r') as f:
            config_data = json.load(f)
            for key, value in config_data.items():
                if hasattr(config, key):
                    setattr(config, key, value)
    
    # Initialize Requesty API if available and enabled
    requesty_api = None
    if REQUESTY_AVAILABLE and args.enable_requesty:
        try:
            requesty_api = RequestyAPI()
            print("✅ Requesty API integration enabled")
        except Exception as e:
            print(f"⚠️ Requesty API initialization failed: {e}")
    
    # Initialize Darwin Gödel Machine
    dgm = DarwinGodelMachine(
        problem_statement=args.problem_statement,
        git_tempdir=args.git_dir,
        base_commit=args.base_commit,
        chat_history_file=args.chat_history_file,
        test_description=args.test_description,
        language=args.language,
        config=config,
        requesty_api=requesty_api
    )
    
    # Run the DGM evolution process
    final_solution = dgm.evolve()
    
    # Save results
    if final_solution:
        model_patch_outfile = os.path.join(args.outdir, 'dgm_model_patch.diff') if args.outdir else 'dgm_model_patch.diff'
        os.makedirs(os.path.dirname(model_patch_outfile), exist_ok=True)
        with open(model_patch_outfile, 'w') as f:
            f.write(final_solution.patch)
        
        # Save solution metadata
        solution_metadata = {
            "attempt_number": final_solution.attempt_number,
            "test_success": final_solution.test_success,
            "test_stats": final_solution.test_stats,
            "improvement_strategy": final_solution.improvement_strategy,
            "execution_time": final_solution.execution_time,
            "generation": dgm.generation_count,
            "archive_size": len(dgm.solution_archive)
        }
        
        metadata_file = os.path.join(args.outdir, 'dgm_solution_metadata.json') if args.outdir else 'dgm_solution_metadata.json'
        with open(metadata_file, 'w') as f:
            json.dump(solution_metadata, f, indent=2)
        
        print(f"🧬 Darwin Gödel Machine completed successfully!")
        print(f"📊 Final solution: Attempt #{final_solution.attempt_number}")
        print(f"✅ Test success: {final_solution.test_success}")
        print(f"📈 Pass rate: {final_solution.test_stats.get('passed', 0)}/{final_solution.test_stats.get('total', 0)}")
        print(f"🏛️ Archive size: {len(dgm.solution_archive)} solutions")
    else:
        print("❌ Darwin Gödel Machine failed to generate a solution")


if __name__ == "__main__":
    main()