from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# --- Schemas for FV Service's own API ---

class PolicyRuleRef(BaseModel):
    id: int # ID of the policy rule in Integrity Service
    # content: Optional[str] = None # Optionally pass content if already fetched

class ACPrincipleRef(BaseModel):
    id: int # ID of the AC principle
    # content: Optional[str] = None # Optionally pass content if already fetched for context

class VerificationRequest(BaseModel):
    policy_rule_refs: List[PolicyRuleRef] = Field(..., description="References to policy rules to be verified.")
    # Optionally, principles can be referenced directly if verification is triggered per principle
    ac_principle_refs: Optional[List[ACPrincipleRef]] = Field(None, description="References to AC principles to derive proof obligations from. If not provided, obligations might be derived from principles linked to the policy rules.")

class VerificationResult(BaseModel):
    policy_rule_id: int
    status: str # e.g., "verified", "failed", "error"
    message: Optional[str] = None
    counter_example: Optional[str] = None # If applicable and found by SMT solver

class VerificationResponse(BaseModel):
    results: List[VerificationResult]
    overall_status: str # e.g., "all_verified", "some_failed", "error"
    summary_message: Optional[str] = None

# --- Schemas for internal logic and SMT interaction ---

class ProofObligation(BaseModel):
    principle_id: int
    obligation_content: str # e.g., a formal representation of the principle's intent
    description: Optional[str] = None

class SMTSolverInput(BaseModel):
    datalog_rules: List[str] # List of Datalog rule strings
    proof_obligations: List[str] # List of proof obligation strings (formalized)

class SMTSolverOutput(BaseModel):
    is_satisfiable: bool # True if rules + NOT(obligation) is satisfiable (meaning obligation NOT entailed)
    is_unsatisfiable: bool # True if rules + NOT(obligation) is unsatisfiable (meaning obligation IS entailed)
    # In a real SMT solver, satisfiability refers to whether a model exists for the given assertions.
    # For verifying if Rules => Obligation, we check if Rules AND (NOT Obligation) is UNSATISFIABLE.
    # If UNSAT, then Obligation is entailed by Rules.
    counter_example: Optional[str] = None # If satisfiable, a model might be a counter-example to the obligation
    error_message: Optional[str] = None

# --- Schemas for interacting with external services ---

# For AC Service (ac_service)
class ACPrinciple(BaseModel): # Simplified version of AC's Principle schema
    id: int
    name: str
    content: str
    description: Optional[str] = None

# For Integrity Service (integrity_service)
class PolicyRule(BaseModel): # Matches Integrity Service's PolicyRule response
    id: int
    rule_content: str
    source_principle_ids: Optional[List[int]] = []
    version: int
    verification_status: str

class PolicyRuleStatusUpdate(BaseModel): # For updating status in Integrity Service
    verification_status: str # "verified", "failed", "pending"
    # verified_at: Optional[datetime] # Integrity service might set this automatically

# Placeholder for User (if FV Service needs to be auth-aware for its own endpoints)
class User(BaseModel):
    id: str
    roles: List[str] = []
