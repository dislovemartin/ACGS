from typing import List
from ..schemas import ACPrinciple, ProofObligation

# This is a very simplified mock. A real system would use NLP or structured data from principles.
def generate_proof_obligations_from_principle(principle: ACPrinciple) -> List[ProofObligation]:
    """
    Generates proof obligations from a single AC principle.
    Mock implementation: Creates a generic obligation based on principle content.
    """
    obligations = []
    content_lower = principle.content.lower()
    obligation_description = f"Obligation derived from Principle ID {principle.id}: {principle.name}"

    # Example 1: If principle mentions "access control" and "role"
    if "access" in content_lower and "role" in content_lower:
        # This is a very simplified representation of a formal obligation.
        # It might translate to something like:
        # "FORALL User, Resource, Action: IF attempts_access(User, Resource, Action) AND requires_role(Resource, Action, Role) THEN has_role(User, Role)"
        formal_obligation = f"ensure_role_based_access_for_principle_{principle.id}."
        obligations.append(
            ProofObligation(
                principle_id=principle.id,
                obligation_content=formal_obligation,
                description=f"{obligation_description} - Ensures actions are role-based."
            )
        )

    # Example 2: If principle mentions "data privacy" or "sensitive data"
    elif "privacy" in content_lower or "sensitive data" in content_lower:
        formal_obligation = f"protect_sensitive_data_for_principle_{principle.id}."
        obligations.append(
            ProofObligation(
                principle_id=principle.id,
                obligation_content=formal_obligation,
                description=f"{obligation_description} - Ensures sensitive data is protected."
            )
        )
    
    # Default/Fallback obligation if no specific keywords match
    if not obligations:
        formal_obligation = f"generic_obligation_for_principle_{principle.id}."
        obligations.append(
            ProofObligation(
                principle_id=principle.id,
                obligation_content=formal_obligation,
                description=f"{obligation_description} - Generic compliance."
            )
        )
        
    return obligations

async def generate_proof_obligations_from_principles(
    principles: List[ACPrinciple]
) -> List[ProofObligation]:
    """
    Generates proof obligations from a list of AC principles.
    This would involve fetching principle details from AC Service if not already provided.
    """
    all_obligations: List[ProofObligation] = []
    for p in principles:
        all_obligations.extend(generate_proof_obligations_from_principle(p))
    return all_obligations


# Example Usage (can be run directly for testing this file)
if __name__ == "__main__":
    import asyncio

    async def test_proof_obligation_generation():
        sample_principles_data = [
            {"id": 1, "name": "Role-Based Access", "content": "Access to resources must be based on user roles."},
            {"id": 2, "name": "Data Privacy", "content": "Sensitive data must be protected from unauthorized access."},
            {"id": 3, "name": "Audit Logging", "content": "All system modifications should be logged."},
        ]
        
        sample_principles = [ACPrinciple(**data) for data in sample_principles_data]

        all_generated_obligations = await generate_proof_obligations_from_principles(sample_principles)
        
        print("Generated Proof Obligations:")
        for ob in all_generated_obligations:
            print(f"  Principle ID: {ob.principle_id}")
            print(f"  Description: {ob.description}")
            print(f"  Obligation Content: {ob.obligation_content}\n")

    asyncio.run(test_proof_obligation_generation())
