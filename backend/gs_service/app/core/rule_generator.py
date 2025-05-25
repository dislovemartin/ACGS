# backend/gs_service/app/core/rule_generator.py
from typing import List, Optional, Dict # Ensure Dict is imported
from ..schemas import (
    ACPrinciple, 
    GeneratedRuleInfo, 
    LLMInterpretationInput, 
    LLMStructuredOutput,
    LLMSuggestedRule, # Added from issue
    LLMSuggestedAtom  # Added from issue
)
from .llm_integration import query_llm_for_structured_output 
# Datalog templates are no longer used in this new approach based on issue description

def _format_atom_to_datalog(atom: LLMSuggestedAtom) -> str:
    args_str = ", ".join(atom.arguments)
    negation_prefix = "NOT " if atom.is_negated else ""
    return f"{negation_prefix}{atom.predicate_name}({args_str})"

def _assemble_datalog_rule(suggested_rule: LLMSuggestedRule, source_principle_id: int) -> str:
    head_str = _format_atom_to_datalog(suggested_rule.head)
    
    body_atoms_str: List[str] = []
    if suggested_rule.body: # Ensure body is not None and is iterable
        body_atoms_str = [_format_atom_to_datalog(atom) for atom in suggested_rule.body]
    
    # Add traceability: include a fact indicating the source principle in the rule body
    # This assumes source_principle_id is a predicate name.
    # If it's a variable or needs quotes, adjust accordingly.
    # For simplicity, using it as a predicate name with the ID as an argument.
    traceability_atom = f"source_principle_id({source_principle_id})"
    body_atoms_str.append(traceability_atom)
    
    if not body_atoms_str: # Should not happen if traceability atom is always added
        # This case implies a fact if traceability_atom wasn't added,
        # but with traceability_atom, it will always have at least one body atom.
        # If head_str was meant to be a fact if suggested_rule.body is empty:
        # if not suggested_rule.body: return f"{head_str}."
        # However, the logic below assumes body_str will be populated by traceability_atom
        pass # Fall through to body_str join and format

    body_str = ", ".join(body_atoms_str)
    return f"{head_str} :- {body_str}."

async def generate_rules_from_principles(
    principles: List[ACPrinciple], 
    target_context: Optional[str] = None,
    datalog_predicate_schema: Optional[Dict[str, str]] = None, # Added from issue
    few_shot_examples: Optional[List[Dict[str, str]]] = None  # Added from issue
) -> List[GeneratedRuleInfo]:
    
    all_generated_rules: List[GeneratedRuleInfo] = []

    for principle in principles:
        llm_input = LLMInterpretationInput(
            principle_id=principle.id,
            principle_content=principle.content,
            target_context=target_context,
            datalog_predicate_schema=datalog_predicate_schema, # Pass through
            few_shot_examples=few_shot_examples # Pass through
        )
        
        llm_output: LLMStructuredOutput = await query_llm_for_structured_output(llm_input)
        
        # TODO: Log LLM interaction details (input, raw_output, structured_output) for auditability
        # This would typically involve calling another service (e.g., integrity_service) or a logging utility.
        # print(f"LLM Input for P{principle.id}: {llm_input.model_dump_json(indent=2)}")
        # print(f"LLM Output for P{principle.id}: {llm_output.model_dump_json(indent=2)}")


        for suggested_rule_structure in llm_output.interpretations:
            # Deterministic assembly from structured suggestion
            datalog_rule_content = _assemble_datalog_rule(suggested_rule_structure, principle.id)
            
            all_generated_rules.append(
                GeneratedRuleInfo(
                    rule_content=datalog_rule_content,
                    source_principle_ids=[principle.id] 
                    # Optionally, add confidence/explanation from suggested_rule_structure if GeneratedRuleInfo supports it
                )
            )
            
    return all_generated_rules

# Example Usage (can be run directly for testing this file)
if __name__ == "__main__":
    import asyncio

    async def test_rule_generation_structured():
        # Sample principles using the ACPrinciple schema from gs_service.app.schemas
        sample_principles = [
            ACPrinciple(id=1, name="P1", content="Users must have appropriate roles for access control.", category="Access Control"),
            ACPrinciple(id=2, name="P2", content="Access to sensitive data is strictly controlled and logged.", category="Data Security"),
            ACPrinciple(id=3, name="P3", content="All system events must be logged with details.", category="Audit"),
            ACPrinciple(id=4, name="P4", content="A very generic principle about operational integrity.", category="Operational")
        ]
        
        # Example of datalog_predicate_schema (optional, for more advanced LLM guidance)
        predicate_schema_example = {
            "allow_action": "allow_action(User, Action, Resource)",
            "user_has_role": "user_has_role(User, Role)",
            "role_has_permission_for_action": "role_has_permission_for_action(Role, Action, Resource)",
            "event_logged": "event_logged(EventID, Timestamp, Actor, Action, Details)",
            "event_occurred": "event_occurred(EventID, Timestamp, Actor, Action, Details)",
            "source_principle_id": "source_principle_id(PrincipleID)" # Include if LLM needs to know about it
        }

        print("Testing Structured Rule Generation:")
        rules = await generate_rules_from_principles(
            sample_principles, 
            target_context="document_management_system",
            datalog_predicate_schema=predicate_schema_example,
            few_shot_examples=[ # Example few-shot
                {"principle": "Old principle about admin full access", "rule": "allow_action(User, Action, Resource) :- user_is_admin(User), source_principle_id(0)."}
            ]
        )
        
        print("\nGenerated Datalog Rules (Structured Approach):")
        for rule_info in rules:
            print(f"  Source Principle IDs: {rule_info.source_principle_ids}")
            print(f"  Rule Content:\n{rule_info.rule_content}\n")

    asyncio.run(test_rule_generation_structured())
