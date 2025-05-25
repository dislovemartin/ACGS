from typing import List
from ..schemas import SMTSolverInput, SMTSolverOutput

class MockSMTSolverClient:
    async def check_satisfiability(self, solver_input: SMTSolverInput) -> SMTSolverOutput:
        """
        Mocks an SMT solver checking if (Datalog Rules AND NOT ProofObligation) is satisfiable.
        - If SAT, it means the obligation is NOT entailed (verification fails for that obligation).
        - If UNSAT, it means the obligation IS entailed (verification passes for that obligation).
        This mock will simply look for keywords in the obligations and rules.
        """
        # Default to obligation being entailed (UNSAT)
        is_satisfiable = False 
        counter_example = None
        error_message = None

        # Very simplistic mock logic:
        # If any obligation contains "fail_verification", simulate failure (SAT).
        # If any rule implies an obvious contradiction with an obligation, simulate failure.
        
        for obligation_content in solver_input.proof_obligations:
            if "fail_verification" in obligation_content.lower():
                is_satisfiable = True # Means (Rules AND NOT Obligation) is SAT -> Obligation NOT Entailed
                counter_example = f"Mock counter-example: Obligation '{obligation_content[:30]}...' was made to fail."
                break # One failure is enough to make the whole check SAT for this mock

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

# Global instance for use
mock_smt_solver_client = MockSMTSolverClient()

async def verify_rules_against_obligations(
    datalog_rules: List[str], 
    proof_obligations: List[str]
) -> SMTSolverOutput:
    """
    Helper function to prepare input and call the SMT solver mock.
    In a real system, this would involve complex translation to SMT-LIB format or similar.
    """
    solver_input = SMTSolverInput(
        datalog_rules=datalog_rules,
        proof_obligations=proof_obligations # Each obligation is checked individually or combined
    )
    # This mock assumes checking all obligations together. 
    # A real system might check each obligation against all rules.
    # If so, the logic in MockSMTSolverClient would need to iterate through obligations one by one.
    # For now, the mock SMT client's check_satisfiability handles the list of obligations.
    return await mock_smt_solver_client.check_satisfiability(solver_input)

# Example Usage
if __name__ == "__main__":
    import asyncio

    async def test_smt_solver_mock():
        rules1 = ["user_role_is(User, 'admin') :- has_attribute(User, 'role', 'admin')."]
        obligations1 = ["ensure_role_based_access_for_principle_1."] # Should pass (UNSAT)
        
        output1 = await verify_rules_against_obligations(rules1, obligations1)
        print(f"Test 1 (Expect Pass/UNSAT): Output: {output1.model_dump_json(indent=2)}\n")
        assert output1.is_unsatisfiable

        rules2 = ["user_role_is(User, 'viewer') :- has_attribute(User, 'role', 'viewer')."]
        obligations2 = ["ensure_role_based_access_for_principle_1.", "fail_verification_for_obligation_2."] # Should fail (SAT)
        
        output2 = await verify_rules_against_obligations(rules2, obligations2)
        print(f"Test 2 (Expect Fail/SAT): Output: {output2.model_dump_json(indent=2)}\n")
        assert output2.is_satisfiable
        assert output2.counter_example

        rules3 = ["no_roles_defined(system)."] # Contradicts the obligation implicitly
        obligations3 = ["ensure_role_based_access_for_principle_admin."]
        output3 = await verify_rules_against_obligations(rules3, obligations3)
        print(f"Test 3 (Expect Fail/SAT due to contradiction): Output: {output3.model_dump_json(indent=2)}\n")
        assert output3.is_satisfiable
        assert output3.counter_example


    asyncio.run(test_smt_solver_mock())
