from typing import List, Tuple
from ..schemas import (
    ACPrinciple, PolicyRule, ProofObligation, VerificationResult, SMTSolverOutput
)
from .proof_obligations import generate_proof_obligations_from_principles
from .smt_solver_integration import verify_rules_against_obligations

async def verify_policy_rules(
    policy_rules: List[PolicyRule],
    ac_principles: List[ACPrinciple] # Principles to derive obligations from
) -> List[VerificationResult]:
    """
    Verifies a list of Datalog policy rules against proof obligations derived from AC principles.
    """
    verification_results: List[VerificationResult] = []

    # 1. Generate Proof Obligations from AC Principles
    # This assumes principles relevant to the rules are provided or fetched.
    all_proof_obligations: List[ProofObligation] = await generate_proof_obligations_from_principles(ac_principles)

    if not all_proof_obligations:
        # If no obligations, all rules are trivially verified (or this is an error condition)
        for rule in policy_rules:
            verification_results.append(
                VerificationResult(
                    policy_rule_id=rule.id,
                    status="error", # Or "verified_no_obligations"
                    message="No proof obligations generated for the provided principles."
                )
            )
        return verification_results

    # 2. For each policy rule (or group of related rules), verify against relevant obligations
    # This mock will verify ALL rules against ALL obligations derived from the input principles.
    # A more sophisticated system might map rules to specific principles/obligations.
    
    datalog_rule_strings = [rule.rule_content for rule in policy_rules]
    obligation_strings = [ob.obligation_content for ob in all_proof_obligations]

    # Call the SMT solver mock
    # This mock checks if (Rules AND NOT All_Obligations_Combined) is SAT/UNSAT
    # A real solver might check each obligation individually:
    # For ob in obligations: check(Rules AND NOT ob)
    smt_output: SMTSolverOutput = await verify_rules_against_obligations(
        datalog_rules=datalog_rule_strings,
        proof_obligations=obligation_strings 
    )

    # 3. Interpret SMT solver output to create VerificationResult for each rule
    # This mock applies the single SMT output to all rules.
    # A real system would have per-obligation results, then aggregate for each rule.
    
    current_status = "error" # Default status
    message = smt_output.error_message
    counter_example = smt_output.counter_example

    if smt_output.is_unsatisfiable:
        # (Rules AND NOT Obligations) is UNSAT => Obligations ARE Entailed => Verified
        current_status = "verified"
        message = "All obligations appear to be entailed by the rules."
    elif smt_output.is_satisfiable:
        # (Rules AND NOT Obligations) is SAT => Obligations ARE NOT Entailed => Failed
        current_status = "failed"
        message = "One or more obligations are not entailed by the rules."
        # counter_example is already set from smt_output
    
    for rule in policy_rules:
        verification_results.append(
            VerificationResult(
                policy_rule_id=rule.id,
                status=current_status,
                message=message,
                counter_example=counter_example if current_status == "failed" else None
            )
        )
        
    return verification_results

# Example Usage
if __name__ == "__main__":
    import asyncio

    async def test_verification_logic():
        sample_ac_principles = [
            ACPrinciple(id=1, name="P1", content="Ensure role-based access.", description=""),
            # ACPrinciple(id=2, name="P2", content="Data must be private.", description=""),
            ACPrinciple(id=3, name="P3", content="This principle will fail: fail_verification_obl.", description=""),
        ]
        
        sample_policy_rules = [
            PolicyRule(id=101, rule_content="user_role(user, admin).", version=1, verification_status="pending", source_principle_ids=[1]),
            PolicyRule(id=102, rule_content="can_access(user, resource) :- user_role(user, admin).", version=1, verification_status="pending", source_principle_ids=[1]),
        ]

        print("--- Test Case 1: Expect Verification Success ---")
        # Remove the failing principle for this test
        successful_principles = [p for p in sample_ac_principles if "fail_verification" not in p.content]
        results_success = await verify_policy_rules(sample_policy_rules, successful_principles)
        for res in results_success:
            print(res.model_dump_json(indent=2))
            assert res.status == "verified"

        print("\n--- Test Case 2: Expect Verification Failure ---")
        # Include the failing principle
        results_failure = await verify_policy_rules(sample_policy_rules, sample_ac_principles)
        for res in results_failure:
            print(res.model_dump_json(indent=2))
            assert res.status == "failed"
            assert res.counter_example is not None
            
    asyncio.run(test_verification_logic())
