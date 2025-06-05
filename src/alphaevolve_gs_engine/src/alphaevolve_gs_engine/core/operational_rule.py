"""
operational_rule.py

This module defines the data structure for representing operational rules.
These rules are more specific than constitutional principles and govern
the day-to-day behavior of the AI system.

Classes:
    OperationalRule: Represents a single operational rule.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from .constitutional_principle import ConstitutionalPrinciple # Assuming relative import

class OperationalRule:
    """
    Represents an operational rule derived from or aligned with
    constitutional principles.

    These rules are typically more concrete and directly implementable,
    often expressed in a policy language like Rego.

    Attributes:
        rule_id (str): Unique identifier for the rule.
        name (str): Human-readable name for the rule.
        description (str): Detailed description of the rule's purpose.
        policy_code (str): The formal representation of the rule (e.g., Rego code).
        derived_from_principles (List[str]): IDs of constitutional principles
                                             this rule is derived from or aligned with.
        version (int): Version number of the rule.
        creation_date (datetime): Date and time of creation.
        last_modified (datetime): Date and time of last modification.
        is_active (bool): Whether the rule is currently active and enforced.
        metadata (Dict[str, Any]): Additional metadata (e.g., author, tags).
        priority (int): Execution priority of the rule (lower numbers mean higher priority).
    """
    def __init__(self,
                 rule_id: str,
                 name: str,
                 description: str,
                 policy_code: str, # e.g., Rego code
                 derived_from_principles: List[str],
                 version: int = 1,
                 is_active: bool = True,
                 metadata: Optional[Dict[str, Any]] = None,
                 priority: int = 100): # Default priority
        """
        Initializes an OperationalRule instance.
        """
        if not all([rule_id, name, description, policy_code, derived_from_principles]):
            raise ValueError("Core attributes (id, name, description, policy_code, derived_from_principles) cannot be empty.")

        self.rule_id = rule_id
        self.name = name
        self.description = description
        self.policy_code = policy_code
        self.derived_from_principles = derived_from_principles
        self.version = version
        self.creation_date = datetime.now()
        self.last_modified = datetime.now()
        self.is_active = is_active
        self.metadata = metadata if metadata else {}
        self.priority = priority

    def __repr__(self) -> str:
        """
        Returns a string representation of the OperationalRule.
        """
        return (f"OperationalRule(id='{self.rule_id}', name='{self.name}', "
                f"version={self.version}, active={self.is_active}, priority={self.priority})")

    def update(self,
               name: Optional[str] = None,
               description: Optional[str] = None,
               policy_code: Optional[str] = None,
               derived_from_principles: Optional[List[str]] = None,
               is_active: Optional[bool] = None,
               metadata: Optional[Dict[str, Any]] = None,
               priority: Optional[int] = None) -> None:
        """
        Updates the attributes of the rule and increments its version.
        """
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if policy_code is not None:
            self.policy_code = policy_code
        if derived_from_principles is not None:
            self.derived_from_principles = derived_from_principles
        if is_active is not None:
            self.is_active = is_active
        if metadata:
            self.metadata.update(metadata)
        if priority is not None:
            self.priority = priority
        
        self.version += 1
        self.last_modified = datetime.now()
        print(f"Rule '{self.rule_id}' updated to version {self.version}.")

    def activate(self) -> None:
        """
        Activates the rule.
        """
        self.is_active = True
        self.last_modified = datetime.now()
        print(f"Rule '{self.rule_id}' activated.")

    def deactivate(self) -> None:
        """
        Deactivates the rule.
        """
        self.is_active = False
        self.last_modified = datetime.now()
        print(f"Rule '{self.rule_id}' deactivated.")

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes the rule object to a dictionary.
        """
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "description": self.description,
            "policy_code": self.policy_code,
            "derived_from_principles": self.derived_from_principles,
            "version": self.version,
            "creation_date": self.creation_date.isoformat(),
            "last_modified": self.last_modified.isoformat(),
            "is_active": self.is_active,
            "metadata": self.metadata,
            "priority": self.priority
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OperationalRule':
        """
        Creates an OperationalRule instance from a dictionary.
        """
        rule = cls(
            rule_id=data["rule_id"],
            name=data["name"],
            description=data["description"],
            policy_code=data["policy_code"],
            derived_from_principles=data["derived_from_principles"],
            version=data.get("version", 1),
            is_active=data.get("is_active", True),
            metadata=data.get("metadata"),
            priority=data.get("priority", 100)
        )
        # Preserve original timestamps if available
        if "creation_date" in data:
            rule.creation_date = datetime.fromisoformat(data["creation_date"])
        if "last_modified" in data:
            rule.last_modified = datetime.fromisoformat(data["last_modified"])
        return rule

# Example Usage (Illustrative)
if __name__ == '__main__':
    # Assume cp1 is an existing ConstitutionalPrinciple
    cp1_id = "CP001_HarmPrevention"

    # Define Rego code for an operational rule
    op_rule_rego = """
    package system.operational_rules

    default allow_specific_action = false

    # Rule: Disallow actions with high risk scores in finance.
    allow_specific_action {
        input.action.domain == "finance"
        input.action.risk_score < 0.5 # Stricter than general harm
        # This rule is derived from CP001
    }
    """

    op_rule1 = OperationalRule(
        rule_id="OPR001",
        name="Financial Risk Mitigation",
        description="Limits high-risk actions specifically within the financial domain.",
        policy_code=op_rule_rego,
        derived_from_principles=[cp1_id],
        metadata={"author": "FinanceComplianceTeam", "complexity": "medium"},
        priority=50 # Higher priority than default
    )
    print(f"Created Rule: {op_rule1}")
    print(f"Details: {op_rule1.to_dict()}")

    op_rule1.update(description="Limits high-risk actions (risk_score >= 0.5) within the financial domain, requires audit trail.")
    op_rule1.deactivate()
    print(f"Updated Rule Details: {op_rule1.to_dict()}")

    # Serialization and Deserialization
    op_rule1_dict = op_rule1.to_dict()
    op_rule1_reloaded = OperationalRule.from_dict(op_rule1_dict)
    print(f"Reloaded Rule: {op_rule1_reloaded}")
    assert op_rule1.rule_id == op_rule1_reloaded.rule_id
    assert op_rule1.version == op_rule1_reloaded.version
    assert op_rule1.is_active == op_rule1_reloaded.is_active
    print("Serialization/Deserialization test passed.")
