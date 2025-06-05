"""
syntactic_validator.py

This module defines the SyntacticValidator, responsible for checking
the syntactic correctness of policy code (e.g., Rego).

Classes:
    SyntacticValidator: Validates policy syntax.
"""

from typing import Tuple, Optional
import subprocess # For calling external linters/parsers like 'opa parse'

from alphaevolve_gs_engine.utils.logging_utils import setup_logger

logger = setup_logger(__name__)

class SyntacticValidator:
    """
    Validates the syntax of policy code, primarily targeting Rego policies
    by using the OPA (Open Policy Agent) parser.
    """

    def __init__(self, opa_executable_path: str = "opa"):
        """
        Initializes the SyntacticValidator.

        Args:
            opa_executable_path (str): Path to the OPA executable.
                                       Assumes 'opa' is in PATH by default.
        """
        self.opa_executable_path = opa_executable_path
        self._check_opa_availability()

    def _check_opa_availability(self):
        """Checks if the OPA executable is available and runnable."""
        try:
            result = subprocess.run([self.opa_executable_path, "version"],
                                    capture_output=True, text=True, check=False, timeout=5)
            if result.returncode == 0:
                logger.info(f"OPA executable found and working: {result.stdout.strip()}")
            else:
                logger.warning(f"OPA executable '{self.opa_executable_path}' might not be correctly configured. "
                               f"Error: {result.stderr}")
        except FileNotFoundError:
            logger.error(f"OPA executable not found at '{self.opa_executable_path}'. "
                         "Syntactic validation of Rego policies will fail. Please install OPA.")
            # This could raise an exception if OPA is strictly required for the validator to function
            # raise EnvironmentError(f"OPA executable not found at '{self.opa_executable_path}'.")
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout when trying to run '{self.opa_executable_path} version'.")


    def validate_rego_policy(self, policy_code: str, policy_id: Optional[str] = "UnknownPolicy") -> Tuple[bool, str]:
        """
        Validates a Rego policy string for syntactic correctness using `opa parse`.

        Args:
            policy_code (str): The Rego policy code as a string.
            policy_id (Optional[str]): An identifier for the policy, for logging.

        Returns:
            Tuple[bool, str]: A tuple containing:
                - bool: True if the policy is syntactically correct, False otherwise.
                - str: A message indicating success or detailing the error.
        """
        if not policy_code.strip():
            logger.warning(f"Policy '{policy_id}' is empty. Considered syntactically invalid.")
            return False, "Policy code is empty."

        try:
            # Use a temporary file or pass via stdin if OPA supports it well for `opa parse`
            # For simplicity, this example uses a temporary file if code is large,
            # but `opa parse` can take a file path.
            # However, `opa eval` or `opa check` are often used with files.
            # `opa parse` itself can check files.
            # Let's try to pass it via stdin, which is cleaner than temp files.
            
            # Command: opa parse -
            # The '-' tells opa parse to read from stdin.
            # For more complex scenarios, e.g. multiple files or bundles, file-based approaches are better.
            process = subprocess.Popen(
                [self.opa_executable_path, "parse", "-"], # Check a single policy from stdin
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(input=policy_code, timeout=10) # 10s timeout

            if process.returncode == 0:
                logger.info(f"Rego policy '{policy_id}' is syntactically valid.")
                # stdout might contain the parsed AST, not particularly useful here for just validation
                return True, "Policy is syntactically valid."
            else:
                error_message = stderr.strip()
                logger.warning(f"Rego policy '{policy_id}' is syntactically invalid. Error: {error_message}")
                return False, f"Syntactic error: {error_message}"

        except FileNotFoundError:
            logger.error(f"OPA executable not found at '{self.opa_executable_path}'. Cannot validate policy '{policy_id}'.")
            return False, "OPA executable not found. Install OPA and ensure it's in PATH or configured."
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout during syntactic validation of policy '{policy_id}'. It might be too complex or OPA is hanging.")
            return False, "Validation timed out. Policy might be too complex or OPA unresponsive."
        except Exception as e:
            logger.error(f"An unexpected error occurred during syntactic validation of policy '{policy_id}': {e}", exc_info=True)
            return False, f"An unexpected error occurred: {str(e)}"

    def validate(self, policy_code: str, language: str = "rego", policy_id: Optional[str] = None) -> Tuple[bool, str]:
        """
        Generic validation entry point. Currently only supports Rego.

        Args:
            policy_code (str): The policy code to validate.
            language (str): The language of the policy code (default: "rego").
            policy_id (Optional[str]): An identifier for the policy, for logging.

        Returns:
            Tuple[bool, str]: Validation result (isValid, message).
        
        Raises:
            NotImplementedError: If an unsupported language is specified.
        """
        _policy_id = policy_id or "UnnamedPolicy"
        if language.lower() == "rego":
            return self.validate_rego_policy(policy_code, policy_id=_policy_id)
        else:
            logger.error(f"Unsupported language for syntactic validation: {language}")
            raise NotImplementedError(f"Syntactic validation for '{language}' is not implemented.")

# Example Usage
if __name__ == "__main__":
    validator = SyntacticValidator() # Assumes 'opa' is in PATH

    # --- Example 1: Valid Rego Policy ---
    valid_rego_policy = """
    package example.auth

    default allow = false

    allow {
        input.user.role == "admin"
    }

    allow {
        input.user.role == "editor"
        input.request.method == "GET"
    }
    """
    is_valid, message = validator.validate(valid_rego_policy, language="rego", policy_id="AuthPolicy1")
    print(f"Validation for AuthPolicy1: Valid = {is_valid}, Message = {message}")
    assert is_valid

    # --- Example 2: Invalid Rego Policy (Syntax Error) ---
    invalid_rego_policy = """
    package example.broken

    default allow = false

    allow {
        input.user.role = "admin" # Common mistake: should be == or :=
    }
    """
    is_valid, message = validator.validate(invalid_rego_policy, language="rego", policy_id="BrokenPolicy1")
    print(f"Validation for BrokenPolicy1: Valid = {is_valid}, Message = {message}")
    assert not is_valid
    assert "Syntax error" in message or "parse error" in message # OPA error messages can vary slightly

    # --- Example 3: Empty Policy ---
    empty_policy = ""
    is_valid, message = validator.validate(empty_policy, language="rego", policy_id="EmptyPolicy")
    print(f"Validation for EmptyPolicy: Valid = {is_valid}, Message = {message}")
    assert not is_valid
    assert "Policy code is empty" in message
    
    # --- Example 4: Policy with only comments ---
    comment_only_policy = """
    # This is a policy with only comments
    # No actual rules defined.
    """
    # `opa parse` might consider this valid as there's no syntax error, but it's not a useful policy.
    # The definition of "valid" here is purely syntactic. Semantic validity is a different concern.
    is_valid, message = validator.validate(comment_only_policy, language="rego", policy_id="CommentOnlyPolicy")
    print(f"Validation for CommentOnlyPolicy: Valid = {is_valid}, Message = {message}")
    assert is_valid # OPA `parse` typically says this is fine.

    # --- Example 5: Test with non-existent OPA path (if possible to simulate) ---
    # This would require changing the environment or path, harder to test in a script directly
    # validator_bad_opa = SyntacticValidator(opa_executable_path="/non/existent/opa")
    # is_valid, message = validator_bad_opa.validate(valid_rego_policy)
    # print(f"Validation with bad OPA path: Valid = {is_valid}, Message = {message}")
    # assert not is_valid
    # assert "OPA executable not found" in message

    print("\nSyntactic validator tests completed.")

    # To make this truly runnable and test the OPA path, ensure OPA is installed.
    # You can download OPA from https://www.openpolicyagent.org/docs/latest/
    # and place it in your PATH or provide the path to the executable.
    
    # If OPA is not installed, the _check_opa_availability method will log an error,
    # and validate_rego_policy will return (False, "OPA executable not found...").
    # The assertions above might fail if OPA isn't installed as `is_valid` would be False.
    # For robust testing, one might mock subprocess.run or ensure OPA is in the test environment.

    print("\nNote: For these examples to pass as asserted, OPA executable must be installed and in the PATH.")
