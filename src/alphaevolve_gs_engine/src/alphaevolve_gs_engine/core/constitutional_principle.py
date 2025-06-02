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
    Represents a constitutional principle within the AI governance system with QEC-inspired enhancements.

    These principles are foundational and guide the creation and modification
    of more specific operational rules. They are typically expressed in a formal
    language like Rego or a structured natural language.

    QEC-Inspired Enhancements:
    - Structured validation criteria for automated testing
    - Constitutional distance scoring for robustness assessment
    - Error prediction metadata for proactive failure detection
    - Recovery strategies for synthesis failure mitigation

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

        # QEC-inspired enhancement fields
        validation_criteria_structured (Optional[List[Dict[str, Any]]]): Machine-actionable validation criteria
        distance_score (Optional[float]): Constitutional robustness metric (0.0-1.0)
        score_updated_at (Optional[datetime]): Timestamp of last distance score calculation
        error_prediction_metadata (Optional[Dict[str, Any]]): Historical error patterns and predictions
        recovery_strategies (Optional[List[str]]): Configured recovery mechanisms for synthesis failures
    """
    def __init__(self,
                 principle_id: str,
                 name: str,
                 description: str,
                 category: str,
                 policy_code: str, # Could be Rego, structured text, etc.
                 version: int = 1,
                 metadata: Optional[Dict[str, Any]] = None,
                 dependencies: Optional[List[str]] = None,
                 # QEC-inspired enhancement fields
                 validation_criteria_structured: Optional[List[Dict[str, Any]]] = None,
                 distance_score: Optional[float] = None,
                 score_updated_at: Optional[datetime] = None,
                 error_prediction_metadata: Optional[Dict[str, Any]] = None,
                 recovery_strategies: Optional[List[str]] = None):
        """
        Initializes a ConstitutionalPrinciple instance with QEC-inspired enhancements.

        Args:
            principle_id: Unique identifier for the principle
            name: Human-readable name for the principle
            description: Detailed description of the principle's intent and scope
            category: Category of the principle (e.g., 'Safety', 'Fairness', 'Transparency')
            policy_code: Formal representation of the principle (e.g., Rego code)
            version: Version number of the principle
            metadata: Additional metadata (e.g., author, source)
            dependencies: List of other principle IDs this principle depends on
            validation_criteria_structured: Machine-actionable validation criteria for automated testing
            distance_score: Constitutional robustness metric (0.0-1.0, higher = more robust)
            score_updated_at: Timestamp of last distance score calculation
            error_prediction_metadata: Historical error patterns and predictions for proactive failure detection
            recovery_strategies: Configured recovery mechanisms for synthesis failures
        """
        if not all([principle_id, name, description, category, policy_code]):
            raise ValueError("Core attributes (id, name, description, category, policy_code) cannot be empty.")

        # Core attributes
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

        # QEC-inspired enhancement fields
        self.validation_criteria_structured = validation_criteria_structured if validation_criteria_structured else []
        self.distance_score = distance_score
        self.score_updated_at = score_updated_at
        self.error_prediction_metadata = error_prediction_metadata if error_prediction_metadata else {}
        self.recovery_strategies = recovery_strategies if recovery_strategies else []

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
               dependencies: Optional[List[str]] = None,
               # QEC enhancement fields
               validation_criteria_structured: Optional[List[Dict[str, Any]]] = None,
               distance_score: Optional[float] = None,
               error_prediction_metadata: Optional[Dict[str, Any]] = None,
               recovery_strategies: Optional[List[str]] = None) -> None:
        """
        Updates the attributes of the principle and increments its version.
        Includes QEC-inspired enhancement fields for constitutional resilience.
        """
        # Update core attributes
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

        # Update QEC enhancement fields
        if validation_criteria_structured is not None:
            self.validation_criteria_structured = validation_criteria_structured
        if distance_score is not None:
            self.distance_score = distance_score
            self.score_updated_at = datetime.now()  # Auto-update timestamp when score changes
        if error_prediction_metadata is not None:
            self.error_prediction_metadata.update(error_prediction_metadata)
        if recovery_strategies is not None:
            self.recovery_strategies = recovery_strategies

        self.version += 1
        self.last_modified = datetime.now()
        print(f"Principle '{self.principle_id}' updated to version {self.version}.")

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes the principle object to a dictionary, including QEC enhancement fields.
        """
        result = {
            "principle_id": self.principle_id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "policy_code": self.policy_code,
            "version": self.version,
            "creation_date": self.creation_date.isoformat(),
            "last_modified": self.last_modified.isoformat(),
            "metadata": self.metadata,
            "dependencies": self.dependencies,
            # QEC enhancement fields
            "validation_criteria_structured": self.validation_criteria_structured,
            "distance_score": self.distance_score,
            "error_prediction_metadata": self.error_prediction_metadata,
            "recovery_strategies": self.recovery_strategies
        }

        # Include score_updated_at if it exists
        if self.score_updated_at:
            result["score_updated_at"] = self.score_updated_at.isoformat()

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConstitutionalPrinciple':
        """
        Creates a ConstitutionalPrinciple instance from a dictionary, including QEC enhancement fields.
        """
        principle = cls(
            principle_id=data["principle_id"],
            name=data["name"],
            description=data["description"],
            category=data["category"],
            policy_code=data["policy_code"],
            version=data.get("version", 1), # Default version if not present
            metadata=data.get("metadata"),
            dependencies=data.get("dependencies"),
            # QEC enhancement fields
            validation_criteria_structured=data.get("validation_criteria_structured"),
            distance_score=data.get("distance_score"),
            error_prediction_metadata=data.get("error_prediction_metadata"),
            recovery_strategies=data.get("recovery_strategies")
        )

        # Preserve original timestamps if available
        if "creation_date" in data:
            principle.creation_date = datetime.fromisoformat(data["creation_date"])
        if "last_modified" in data:
            principle.last_modified = datetime.fromisoformat(data["last_modified"])
        if "score_updated_at" in data:
            principle.score_updated_at = datetime.fromisoformat(data["score_updated_at"])

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
