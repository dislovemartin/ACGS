"""
AlphaEvolve Governance System Engine
====================================

This package provides the core functionalities for the AlphaEvolve Governance System,
including data structures for constitutional principles, operational rules, amendments,
and various services for policy synthesis, validation, and cryptographic operations.

Modules:
    core: Defines the fundamental data structures of the governance system.
    services: Provides services for LLM interaction, cryptography, policy synthesis, and validation.
    utils: Contains utility functions, such as logging.

Key Classes:
    - ConstitutionalPrinciple: Represents a high-level governance principle.
    - OperationalRule: Represents a specific, enforceable rule.
    - Amendment: Represents a proposed change to a principle or rule.
    - PolicySynthesizer: Service for generating and refining policies.
    - Various Validators (Syntactic, Semantic, Safety, Bias, Conflict): Services for policy validation.
    - LLMService: Interface for interacting with large language models.
    - CryptoService: Provides cryptographic utilities.

Example:
    >>> from alphaevolve_gs_engine.core import ConstitutionalPrinciple
    >>> principle = ConstitutionalPrinciple("CP001", "Harm Prevention", "...", "Safety", "...")
    >>> print(principle)
"""

# Expose key classes and functions at the package level for easier access.

# From 'core' module
from .core.constitutional_principle import ConstitutionalPrinciple
from .core.operational_rule import OperationalRule
from .core.amendment import Amendment

# From 'services' module
from .services.llm_service import LLMService, OpenAILLMService, MockLLMService, get_llm_service
from .services.crypto_service import CryptoService, hash_data
from .services.policy_synthesizer import PolicySynthesizer, LLMPolicyGenerator, PolicySynthesisInput, PolicySuggestion

# From 'services.validation' sub-package (expose main validator classes)
from .services.validation.syntactic_validator import SyntacticValidator
from .services.validation.semantic_validator import SemanticValidator, ScenarioBasedSemanticValidator, SemanticTestCase
from .services.validation.formal_verifier import FormalVerifier, MockFormalVerifier, FormalVerificationProperty
from .services.validation.safety_validator import SafetyValidator, PatternBasedSafetyValidator, SimulationBasedSafetyValidator, SafetyAssertion
from .services.validation.bias_validator import BiasValidator, FairnessMetricValidator, LLMBiasReviewer, BiasMetric
from .services.validation.conflict_validator import ConflictValidator, OPAConflictDetector, ConflictDefinition

# From 'utils' module
from .utils.logging_utils import setup_logger

__version__ = "0.1.0" # Placeholder for versioning

__all__ = [
    # Core
    "ConstitutionalPrinciple",
    "OperationalRule",
    "Amendment",
    # Services
    "LLMService", "OpenAILLMService", "MockLLMService", "get_llm_service",
    "CryptoService", "hash_data",
    "PolicySynthesizer", "LLMPolicyGenerator", "PolicySynthesisInput", "PolicySuggestion",
    # Validation Services & Data Structures
    "SyntacticValidator",
    "SemanticValidator", "ScenarioBasedSemanticValidator", "SemanticTestCase",
    "FormalVerifier", "MockFormalVerifier", "FormalVerificationProperty",
    "SafetyValidator", "PatternBasedSafetyValidator", "SimulationBasedSafetyValidator", "SafetyAssertion",
    "BiasValidator", "FairnessMetricValidator", "LLMBiasReviewer", "BiasMetric",
    "ConflictValidator", "OPAConflictDetector", "ConflictDefinition",
    # Utils
    "setup_logger",
    # Version
    "__version__"
]

logger = setup_logger(__name__)
logger.info(f"AlphaEvolve Governance System Engine version {__version__} loaded.")
