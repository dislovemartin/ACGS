"""
constitutional_principle.py

This module defines the data structure for representing constitutional principles 
within the AlphaEvolve Governance System. These principles are high-level rules 
that govern the behavior of the AI system and its operational rules.

Classes:
    ConstitutionalPrinciple: Represents a single constitutional principle.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

class ConstitutionalPrinciple:
    """
    Represents a constitutional principle within the AI governance system.

    These principles are foundational and guide the creation and modification 
    of more specific operational rules. They are typically expressed in a formal 
    language like Rego or a structured natural language.

    Attributes:
        principle_id (str): Unique identifier for the principle.
        name (str): A human-readable name for the principle.
        description (str): A detailed description of the principle's intent and scope.
        category (str): Category of the principle (e.g., 'Safety', 'Fairness', 'Transparency').
        policy_code (str): The formal representation of the principle (e.g., Rego code).
        version (int): Version number of the principle.
        creation_date (datetime): Date and time when the principle was created.
        last_modified (datetime): Date and time of the last modification.
        metadata (Dict[str, Any]): Additional metadata (e.g., author, source).
        dependencies (Optional[List[str]]): List of other principle IDs this principle depends on.
    """
    def __init__(self,
                 principle_id: str,
                 name: str,
                 description: str,
                 category: str,
                 policy_code: str, # Could be Rego, structured text, etc.
                 version: int = 1,
                 metadata: Optional[Dict[str, Any]] = None,
                 dependencies: Optional[List[str]] = None):
        """
        Initializes a ConstitutionalPrinciple instance.
        """
        if not all([principle_id, name, description, category, policy_code]):
            raise ValueError("Core attributes (id, name, description, category, policy_code) cannot be empty.")

        self.principle_id = principle_id
        self.name = name
        self.description = description
        self.category = category
        self.policy_code = policy_code # This could be Rego code or other formal language
        self.version = version
        self.creation_date = datetime.now()
        self.last_modified = datetime.now()
        self.metadata = metadata if metadata else {}
        self.dependencies = dependencies if dependencies else []

    def __repr__(self) -> str:
        """
        Returns a string representation of the ConstitutionalPrinciple.
        """
        return (f"ConstitutionalPrinciple(id='{self.principle_id}', name='{self.name}', "
                f"version={self.version}, category='{self.category}')")

    def update(self,
               name: Optional[str] = None,
               description: Optional[str] = None,
               category: Optional[str] = None,
               policy_code: Optional[str] = None,
               metadata: Optional[Dict[str, Any]] = None,
               dependencies: Optional[List[str]] = None) -> None:
        """
        Updates the attributes of the principle and increments its version.
        """
        if name:
            self.name = name
        if description:
            self.description = description
        if category:
            self.category = category
        if policy_code:
            self.policy_code = policy_code
        if metadata:
            self.metadata.update(metadata)
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if category is not None:
            self.category = category
        if policy_code is not None:
            self.policy_code = policy_code
        if metadata:
            self.metadata.update(metadata)
        if dependencies is not None:  # Allow clearing dependencies with []
            self.dependencies = dependencies
        
        self.version += 1
        self.last_modified = datetime.now()
        print(f"Principle '{self.principle_id}' updated to version {self.version}.")

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes the principle object to a dictionary.
        """
        return {
            "principle_id": self.principle_id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "policy_code": self.policy_code,
            "version": self.version,
            "creation_date": self.creation_date.isoformat(),
            "last_modified": self.last_modified.isoformat(),
            "metadata": self.metadata,
            "dependencies": self.dependencies
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConstitutionalPrinciple':
        """
        Creates a ConstitutionalPrinciple instance from a dictionary.
        """
        principle = cls(
            principle_id=data["principle_id"],
            name=data["name"],
            description=data["description"],
            category=data["category"],
            policy_code=data["policy_code"],
            version=data.get("version", 1), # Default version if not present
            metadata=data.get("metadata"),
            dependencies=data.get("dependencies")
        )
        # Preserve original timestamps if available
        if "creation_date" in data:
            principle.creation_date = datetime.fromisoformat(data["creation_date"])
        if "last_modified" in data:
            principle.last_modified = datetime.fromisoformat(data["last_modified"])
        return principle

# Example Usage (Illustrative)
if __name__ == '__main__':
    # Create a new constitutional principle
    cp1_policy_code = """
    package system.constitutional_principles

    # Principle: Ensure AI actions do not result in harm to humans.
    default allow_action = false
    
    allow_action {
        input.action.potential_harm_score < 0.1 # Example metric
        input.action.is_reviewed_by_human == true
    }
    """
    cp1 = ConstitutionalPrinciple(
        principle_id="CP001",
        name="Harm Prevention Principle",
        description="Ensures that AI actions minimize the risk of harm to humans.",
        category="Safety",
        policy_code=cp1_policy_code,
        metadata={"author": "EthicsCommittee", "review_date": "2023-01-15"}
    )
    print(f"Created Principle: {cp1}")
    print(f"Details: {cp1.to_dict()}")

    # Update the principle
    cp1.update(
        description="Ensures that AI actions minimize the risk of physical and psychological harm to humans, with specific oversight.",
        policy_code=cp1_policy_code.replace("0.1", "0.05"), # Make it stricter
        metadata={"updated_by": "SafetyBoard"}
    )
    print(f"Updated Principle Details: {cp1.to_dict()}")

    # Serialization and Deserialization
    cp1_dict = cp1.to_dict()
    cp1_reloaded = ConstitutionalPrinciple.from_dict(cp1_dict)
    print(f"Reloaded Principle: {cp1_reloaded}")
    assert cp1.principle_id == cp1_reloaded.principle_id
    assert cp1.version == cp1_reloaded.version
    assert cp1.policy_code == cp1_reloaded.policy_code
    print("Serialization/Deserialization test passed.")
