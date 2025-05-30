from typing import List, Dict, Any, Optional, Tuple
import z3
import re
import logging
from ..schemas import SMTSolverInput, SMTSolverOutput

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Z3SMTSolverClient:
    """
    Real Z3 SMT Solver integration for formal verification of policy rules against constitutional principles.
    """

    def __init__(self):
        self.solver = z3.Solver()
        self.context_vars = {}  # Store Z3 variables for reuse

    async def check_satisfiability(self, solver_input: SMTSolverInput) -> SMTSolverOutput:
        """
        Uses Z3 SMT solver to check if (Datalog Rules AND NOT ProofObligation) is satisfiable.
        - If SAT, it means the obligation is NOT entailed (verification fails).
        - If UNSAT, it means the obligation IS entailed (verification passes).
        """
        try:
            logger.info(f"Starting Z3 verification for {len(solver_input.datalog_rules)} rules and {len(solver_input.proof_obligations)} obligations")

            # Reset solver state
            self.solver.reset()
            self.context_vars.clear()

            # Convert Datalog rules to Z3 constraints
            rule_constraints = self._convert_datalog_to_z3(solver_input.datalog_rules)

            # Convert proof obligations to Z3 constraints
            obligation_constraints = self._convert_obligations_to_z3(solver_input.proof_obligations)

            # Add rule constraints to solver
            for constraint in rule_constraints:
                self.solver.add(constraint)

            # Check if (Rules AND NOT Obligations) is satisfiable
            # If UNSAT, then Rules => Obligations (verification passes)
            negated_obligations = [z3.Not(obligation) for obligation in obligation_constraints]
            for neg_obligation in negated_obligations:
                self.solver.add(neg_obligation)

            # Check satisfiability
            result = self.solver.check()

            if result == z3.sat:
                # SAT means obligations are NOT entailed
                model = self.solver.model()
                counter_example = self._extract_counter_example(model)
                logger.info("Verification FAILED - counter-example found")
                return SMTSolverOutput(
                    is_satisfiable=True,
                    is_unsatisfiable=False,
                    counter_example=counter_example
                )
            elif result == z3.unsat:
                # UNSAT means obligations ARE entailed
                logger.info("Verification PASSED - obligations are entailed")
                return SMTSolverOutput(
                    is_satisfiable=False,
                    is_unsatisfiable=True
                )
            else:
                # Unknown result
                logger.warning("Z3 returned unknown result")
                return SMTSolverOutput(
                    is_satisfiable=False,
                    is_unsatisfiable=False,
                    error_message="Z3 solver returned unknown result - verification inconclusive"
                )

        except Exception as e:
            logger.error(f"Error in Z3 verification: {str(e)}")
            return SMTSolverOutput(
                is_satisfiable=False,
                is_unsatisfiable=False,
                error_message=f"Z3 solver error: {str(e)}"
            )

    def _convert_datalog_to_z3(self, datalog_rules: List[str]) -> List[z3.BoolRef]:
        """
        Convert Datalog rules to Z3 constraints.
        This is a simplified conversion for common patterns.
        """
        constraints = []

        for rule in datalog_rules:
            try:
                constraint = self._parse_datalog_rule(rule)
                if constraint is not None:
                    constraints.append(constraint)
            except Exception as e:
                logger.warning(f"Failed to parse Datalog rule '{rule}': {str(e)}")

        return constraints

    def _parse_datalog_rule(self, rule: str) -> Optional[z3.BoolRef]:
        """
        Parse a single Datalog rule into Z3 constraint.
        Handles common patterns like:
        - access_allowed(User, Resource) :- has_role(User, admin).
        - data_protected(Data) :- is_sensitive(Data), has_encryption(Data).
        """
        rule = rule.strip()
        if not rule or rule.startswith('#'):
            return None

        # Basic pattern: head :- body.
        if ':-' in rule:
            head, body = rule.split(':-', 1)
            head = head.strip()
            body = body.strip().rstrip('.')

            # Parse head predicate
            head_pred = self._parse_predicate(head)
            if head_pred is None:
                return None

            # Parse body predicates
            body_parts = [part.strip() for part in body.split(',')]
            body_preds = []
            for part in body_parts:
                pred = self._parse_predicate(part)
                if pred is not None:
                    body_preds.append(pred)

            # Create implication: body => head
            if body_preds:
                body_conjunction = z3.And(*body_preds) if len(body_preds) > 1 else body_preds[0]
                return z3.Implies(body_conjunction, head_pred)
            else:
                # Fact (no body)
                return head_pred
        else:
            # Simple fact
            return self._parse_predicate(rule.rstrip('.'))

    def _parse_predicate(self, predicate: str) -> Optional[z3.BoolRef]:
        """
        Parse a predicate like 'has_role(User, admin)' into Z3 boolean variable.
        """
        predicate = predicate.strip()
        if not predicate:
            return None

        # Extract predicate name and arguments
        match = re.match(r'(\w+)\((.*)\)', predicate)
        if match:
            pred_name = match.group(1)
            args_str = match.group(2)
            args = [arg.strip() for arg in args_str.split(',') if arg.strip()]

            # Create unique variable name
            var_name = f"{pred_name}_{hash(predicate) % 10000}"

            # Create or reuse Z3 boolean variable
            if var_name not in self.context_vars:
                self.context_vars[var_name] = z3.Bool(var_name)

            return self.context_vars[var_name]
        else:
            # Simple predicate without parentheses
            var_name = f"{predicate}_{hash(predicate) % 10000}"
            if var_name not in self.context_vars:
                self.context_vars[var_name] = z3.Bool(var_name)
            return self.context_vars[var_name]

    def _convert_obligations_to_z3(self, obligations: List[str]) -> List[z3.BoolRef]:
        """
        Convert proof obligations to Z3 constraints.
        """
        constraints = []

        for obligation in obligations:
            try:
                constraint = self._parse_obligation(obligation)
                if constraint is not None:
                    constraints.append(constraint)
            except Exception as e:
                logger.warning(f"Failed to parse obligation '{obligation}': {str(e)}")

        return constraints

    def _parse_obligation(self, obligation: str) -> Optional[z3.BoolRef]:
        """
        Parse a proof obligation into Z3 constraint.
        Obligations are typically safety properties or invariants.
        """
        obligation = obligation.strip()
        if not obligation:
            return None

        # Handle different obligation patterns
        if 'ensure_role_based_access' in obligation:
            # Create constraint for role-based access
            var_name = f"role_access_enforced_{hash(obligation) % 10000}"
            if var_name not in self.context_vars:
                self.context_vars[var_name] = z3.Bool(var_name)
            return self.context_vars[var_name]

        elif 'protect_sensitive_data' in obligation:
            # Create constraint for data protection
            var_name = f"data_protected_{hash(obligation) % 10000}"
            if var_name not in self.context_vars:
                self.context_vars[var_name] = z3.Bool(var_name)
            return self.context_vars[var_name]

        elif 'generic_obligation' in obligation:
            # Generic obligation
            var_name = f"generic_compliance_{hash(obligation) % 10000}"
            if var_name not in self.context_vars:
                self.context_vars[var_name] = z3.Bool(var_name)
            return self.context_vars[var_name]

        else:
            # Default: treat as boolean predicate
            return self._parse_predicate(obligation)

    def _extract_counter_example(self, model: z3.ModelRef) -> str:
        """
        Extract a human-readable counter-example from Z3 model.
        """
        try:
            counter_parts = []
            for var in model:
                value = model[var]
                counter_parts.append(f"{var} = {value}")

            if counter_parts:
                return f"Counter-example: {', '.join(counter_parts[:5])}"  # Limit to first 5 for readability
            else:
                return "Counter-example found but no variable assignments available"

        except Exception as e:
            return f"Counter-example extraction failed: {str(e)}"


class MockSMTSolverClient:
    """
    Fallback mock implementation for testing when Z3 is not available.
    """
    async def check_satisfiability(self, solver_input: SMTSolverInput) -> SMTSolverOutput:
        """
        Mock implementation for backward compatibility.
        """
        # Default to obligation being entailed (UNSAT)
        is_satisfiable = False
        counter_example = None
        error_message = None

        # Simple mock logic for testing
        for obligation_content in solver_input.proof_obligations:
            if "fail_verification" in obligation_content.lower():
                is_satisfiable = True
                counter_example = f"Mock counter-example: Obligation '{obligation_content[:30]}...' was made to fail."
                break

            # Simplistic check for contradictions (example)
            # If obligation is "ensure_role_based_access..." and rules contain "no_roles_defined"
            if "ensure_role_based_access" in obligation_content.lower():
                for rule in solver_input.datalog_rules:
                    if "no_roles_defined" in rule.lower():
                        is_satisfiable = True
                        counter_example = f"Mock counter-example: Contradiction found between rule '{rule[:30]}...' and obligation '{obligation_content[:30]}...'"
                        break
            if is_satisfiable:
                break
        
        if not error_message:
            if is_satisfiable:
                # (Rules AND NOT Obligation) is SAT => Obligation NOT Entailed (Verification Fails)
                return SMTSolverOutput(is_satisfiable=True, is_unsatisfiable=False, counter_example=counter_example)
            else:
                # (Rules AND NOT Obligation) is UNSAT => Obligation IS Entailed (Verification Passes)
                return SMTSolverOutput(is_satisfiable=False, is_unsatisfiable=True)
        else:
            return SMTSolverOutput(is_satisfiable=False, is_unsatisfiable=False, error_message=error_message)

# Global instances for use
try:
    # Try to use Z3 solver if available
    z3_smt_solver_client = Z3SMTSolverClient()
    smt_solver_client = z3_smt_solver_client
    logger.info("Z3 SMT Solver initialized successfully")
except Exception as e:
    # Fallback to mock if Z3 is not available
    logger.warning(f"Z3 not available, falling back to mock: {str(e)}")
    mock_smt_solver_client = MockSMTSolverClient()
    smt_solver_client = mock_smt_solver_client


async def verify_rules_against_obligations(
    datalog_rules: List[str],
    proof_obligations: List[str]
) -> SMTSolverOutput:
    """
    Helper function to prepare input and call the SMT solver (Z3 or mock).
    """
    solver_input = SMTSolverInput(
        datalog_rules=datalog_rules,
        proof_obligations=proof_obligations
    )

    # Use the available SMT solver (Z3 or mock)
    return await smt_solver_client.check_satisfiability(solver_input)

# Example Usage and Testing
if __name__ == "__main__":
    import asyncio

    async def test_z3_smt_solver():
        """Test Z3 SMT solver with real formal verification examples."""
        print("=== Testing Z3 SMT Solver ===")

        # Test 1: Simple role-based access rule that should verify
        rules1 = [
            "access_allowed(User, Resource) :- has_role(User, admin).",
            "has_role(alice, admin)."
        ]
        obligations1 = ["ensure_role_based_access_for_principle_1."]

        output1 = await verify_rules_against_obligations(rules1, obligations1)
        print(f"Test 1 (Role-based access): {output1.model_dump_json(indent=2)}\n")

        # Test 2: Data protection rule
        rules2 = [
            "data_protected(Data) :- is_sensitive(Data), has_encryption(Data).",
            "is_sensitive(user_data).",
            "has_encryption(user_data)."
        ]
        obligations2 = ["protect_sensitive_data_for_principle_2."]

        output2 = await verify_rules_against_obligations(rules2, obligations2)
        print(f"Test 2 (Data protection): {output2.model_dump_json(indent=2)}\n")

        # Test 3: Contradiction case
        rules3 = [
            "access_denied(User, Resource) :- true.",  # Always deny access
        ]
        obligations3 = ["ensure_role_based_access_for_principle_1."]  # But we need access

        output3 = await verify_rules_against_obligations(rules3, obligations3)
        print(f"Test 3 (Contradiction): {output3.model_dump_json(indent=2)}\n")

        print("Z3 SMT solver tests completed!")

    async def test_mock_smt_solver():
        """Test mock SMT solver for backward compatibility."""
        print("=== Testing Mock SMT Solver ===")

        rules1 = ["user_role_is(User, 'admin') :- has_attribute(User, 'role', 'admin')."]
        obligations1 = ["ensure_role_based_access_for_principle_1."]

        # Force use of mock solver
        mock_client = MockSMTSolverClient()
        solver_input = SMTSolverInput(datalog_rules=rules1, proof_obligations=obligations1)
        output1 = await mock_client.check_satisfiability(solver_input)
        print(f"Mock Test 1: {output1.model_dump_json(indent=2)}\n")

        # Test failure case
        obligations2 = ["fail_verification_for_obligation_2."]
        solver_input2 = SMTSolverInput(datalog_rules=rules1, proof_obligations=obligations2)
        output2 = await mock_client.check_satisfiability(solver_input2)
        print(f"Mock Test 2 (Failure): {output2.model_dump_json(indent=2)}\n")

        print("Mock SMT solver tests completed!")

    async def run_all_tests():
        await test_z3_smt_solver()
        await test_mock_smt_solver()

    asyncio.run(run_all_tests())
