"""
QEC-Inspired Enhancement Services for AlphaEvolve-ACGS

This package implements Quantum Error Correction (QEC) inspired resilience mechanisms
for the AlphaEvolve-ACGS constitutional governance framework. The enhancements map
QEC principles of encoding, syndrome measurement, and error correction to constitutional
AI governance, improving system reliability and robustness.

Components:
    - Constitutional Distance Calculator: Measures principle robustness
    - Validation DSL Parser: Structured validation criteria processing
    - Error Prediction Model: Proactive failure detection
    - Recovery Strategy Dispatcher: Intelligent error recovery
    - Constitutional Fidelity Monitor: System-wide health monitoring

Based on the QEC-Inspired Enhancement Blueprint for AlphaEvolve-ACGS.
"""

from .constitutional_distance_calculator import (
    ConstitutionalDistanceCalculator,
    DistanceMetrics
)

from .validation_dsl_parser import (
    ValidationDSLParser,
    ValidationScenario,
    ValidationLinter
)

from .error_prediction_model import (
    ErrorPredictionModel,
    FailureType,
    SynthesisAttemptLog,
    PredictionResult
)

from .recovery_strategy_dispatcher import (
    RecoveryStrategyDispatcher,
    RecoveryStrategy,
    RecoveryConfig,
    RecoveryResult
)

__all__ = [
    # Constitutional Distance Calculator
    "ConstitutionalDistanceCalculator",
    "DistanceMetrics",

    # Validation DSL Parser
    "ValidationDSLParser",
    "ValidationScenario",
    "ValidationLinter",

    # Error Prediction Model
    "ErrorPredictionModel",
    "FailureType",
    "SynthesisAttemptLog",
    "PredictionResult",

    # Recovery Strategy Dispatcher
    "RecoveryStrategyDispatcher",
    "RecoveryStrategy",
    "RecoveryConfig",
    "RecoveryResult"
]

__version__ = "1.0.0"
