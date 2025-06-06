from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List

@dataclass
class ConstitutionalPrinciple:
    """Represents a constitutional principle for policy synthesis."""
    id: str
    text: str
    version: Optional[str] = None
    source: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SynthesisContext:
    """Context information for policy synthesis."""
    domain: Optional[str] = None
    jurisdiction: Optional[str] = None
    target_audience: Optional[str] = None
    application_scenario: Optional[str] = None
    historical_data: Optional[List[Dict[str, Any]]] = field(default_factory=list)
    related_policies: Optional[List[str]] = field(default_factory=list)
    custom_instructions: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
