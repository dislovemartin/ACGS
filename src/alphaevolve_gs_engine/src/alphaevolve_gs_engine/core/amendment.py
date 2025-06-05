"""
amendment.py

This module defines the data structures for representing proposed amendments 
to the existing constitutional principles or operational rules. 
Amendments are central to the evolution of the governing system.

Classes:
    Amendment: Represents a proposed change to a rule or principle.
"""

from typing import Dict, Any, Optional
from datetime import datetime

class Amendment:
    """
    Represents a proposed amendment to an existing constitutional principle or 
    operational rule.

    Attributes:
        amendment_id (str): Unique identifier for the amendment.
        target_rule_id (str): Identifier of the rule or principle to be amended.
        proposed_change (Dict[str, Any]): The proposed modification.
        justification (str): Reason for the proposed amendment.
        status (str): Current status (e.g., 'proposed', 'approved', 'rejected').
        timestamp (datetime): Timestamp of the proposal.
        proposer_id (Optional[str]): Identifier of the entity proposing the amendment.
    """
    def __init__(self,
                 amendment_id: str,
                 target_rule_id: str,
                 proposed_change: Dict[str, Any],
                 justification: str,
                 proposer_id: Optional[str] = None,
                 timestamp: Optional[datetime] = None):
        """
        Initializes an Amendment instance.
        """
        self.amendment_id = amendment_id
        self.target_rule_id = target_rule_id
        self.proposed_change = proposed_change
        self.justification = justification
        self.status = 'proposed'  # Initial status
        self.timestamp = timestamp or datetime.now()
        self.proposer_id = proposer_id

    def __repr__(self) -> str:
        """
        Returns a string representation of the Amendment.
        """
        return (f"Amendment(id={self.amendment_id}, target='{self.target_rule_id}', "
                f"status='{self.status}')")

    def approve(self):
        """
        Marks the amendment as approved.
        """
        self.status = 'approved'
        # Potentially, trigger further actions upon approval

    def reject(self):
        """
        Marks the amendment as rejected.
        """
        self.status = 'rejected'
        # Potentially, log reasons or notify proposer

    def get_details(self) -> Dict[str, Any]:
        """
        Returns a dictionary with the details of the amendment.
        """
        return {
            "amendment_id": self.amendment_id,
            "target_rule_id": self.target_rule_id,
            "proposed_change": self.proposed_change,
            "justification": self.justification,
            "status": self.status,
            "timestamp": self.timestamp.isoformat(),
            "proposer_id": self.proposer_id
        }

if __name__ == '__main__':
    # Example Usage (Illustrative)
    amendment_proposal = Amendment(
        amendment_id="AM001",
        target_rule_id="CP001",
        proposed_change={"text": "New constitutional principle text."},
        justification="To adapt to new ethical considerations.",
        proposer_id="HumanOverseer_01"
    )
    print(f"Created Amendment: {amendment_proposal}")
    print(f"Details: {amendment_proposal.get_details()}")

    amendment_proposal.approve()
    print(f"Status after approval: {amendment_proposal.status}")

    amendment_proposal.reject() # Example of status change
    print(f"Status after rejection: {amendment_proposal.status}")
