"""
violation_detection_service.py

Constitutional Violation Detection Service for real-time monitoring and alerting.
Implements violation detection algorithms, classification, and real-time scanning
with integration to QEC enhancement services and Constitutional Council workflows.

Classes:
    ViolationDetectionService: Main service for violation detection
    ViolationType: Enumeration of violation types
    ViolationSeverity: Enumeration of violation severity levels
    ViolationDetectionResult: Result structure for detection operations
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload

from shared.models import (
    ConstitutionalViolation, ViolationAlert, ViolationThreshold,
    ConstitutionalPrinciple, Policy, User
)
from shared.database import get_async_db

# Import QEC enhancement services
from alphaevolve_gs_engine.services.qec_enhancement.constitutional_fidelity_monitor import (
    ConstitutionalFidelityMonitor, FidelityComponents
)
from alphaevolve_gs_engine.services.qec_enhancement.constitutional_distance_calculator import (
    ConstitutionalDistanceCalculator
)
from alphaevolve_gs_engine.services.qec_enhancement.error_prediction_model import (
    ErrorPredictionModel, FailureType
)

logger = logging.getLogger(__name__)


class ViolationType(Enum):
    """Types of constitutional violations."""
    PRINCIPLE_VIOLATION = "principle_violation"
    SYNTHESIS_FAILURE = "synthesis_failure"
    ENFORCEMENT_BREACH = "enforcement_breach"
    STAKEHOLDER_CONFLICT = "stakeholder_conflict"
    THRESHOLD_BREACH = "threshold_breach"
    POLICY_INCONSISTENCY = "policy_inconsistency"


class ViolationSeverity(Enum):
    """Severity levels for violations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ViolationDetectionResult:
    """Result of violation detection operation."""
    violation_detected: bool
    violation_type: Optional[ViolationType]
    severity: Optional[ViolationSeverity]
    fidelity_score: Optional[float]
    distance_score: Optional[float]
    description: str
    context_data: Dict[str, Any]
    recommended_actions: List[str]
    detection_metadata: Dict[str, Any]


@dataclass
class BatchViolationResult:
    """Result of batch violation analysis."""
    total_analyzed: int
    violations_detected: int
    violations_by_type: Dict[ViolationType, int]
    violations_by_severity: Dict[ViolationSeverity, int]
    detection_results: List[ViolationDetectionResult]
    analysis_time_seconds: float


class ViolationDetectionService:
    """
    Constitutional Violation Detection Service.
    
    Provides real-time violation detection, classification, and alerting
    with integration to QEC enhancement services and Constitutional Council workflows.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the violation detection service.
        
        Args:
            config: Configuration dictionary for detection settings
        """
        self.config = config or self._get_default_config()
        
        # Initialize QEC enhancement services
        self.fidelity_monitor = ConstitutionalFidelityMonitor()
        self.distance_calculator = ConstitutionalDistanceCalculator()
        self.error_predictor = ErrorPredictionModel()
        
        # Detection state
        self.detection_active = False
        self.last_scan_time: Optional[datetime] = None
        self.scan_interval = self.config.get("scan_interval_seconds", 30)
        
        # Thresholds cache
        self.thresholds_cache: Dict[str, ViolationThreshold] = {}
        self.cache_updated_at: Optional[datetime] = None
        
        logger.info("Violation Detection Service initialized")
    
    async def detect_violation(
        self,
        principle: Optional[ConstitutionalPrinciple] = None,
        policy: Optional[Policy] = None,
        fidelity_score: Optional[float] = None,
        context_data: Optional[Dict[str, Any]] = None
    ) -> ViolationDetectionResult:
        """
        Detect constitutional violations for a specific principle or policy.
        
        Args:
            principle: Constitutional principle to analyze
            policy: Policy to analyze
            fidelity_score: Current fidelity score
            context_data: Additional context for detection
            
        Returns:
            ViolationDetectionResult with detection details
        """
        start_time = time.time()
        context_data = context_data or {}
        
        try:
            # Initialize detection result
            result = ViolationDetectionResult(
                violation_detected=False,
                violation_type=None,
                severity=None,
                fidelity_score=fidelity_score,
                distance_score=None,
                description="No violations detected",
                context_data=context_data,
                recommended_actions=[],
                detection_metadata={}
            )
            
            # Perform different types of violation detection
            violations = []
            
            # 1. Principle-based violation detection
            if principle:
                principle_violations = await self._detect_principle_violations(principle, context_data)
                violations.extend(principle_violations)
            
            # 2. Policy-based violation detection
            if policy:
                policy_violations = await self._detect_policy_violations(policy, context_data)
                violations.extend(policy_violations)
            
            # 3. Fidelity score threshold violations
            if fidelity_score is not None:
                threshold_violations = await self._detect_threshold_violations(fidelity_score, context_data)
                violations.extend(threshold_violations)
            
            # 4. Cross-principle consistency violations
            if principle and policy:
                consistency_violations = await self._detect_consistency_violations(principle, policy, context_data)
                violations.extend(consistency_violations)
            
            # Process detected violations
            if violations:
                # Select the most severe violation
                most_severe = max(violations, key=lambda v: self._get_severity_weight(v.severity))
                
                result.violation_detected = True
                result.violation_type = most_severe.violation_type
                result.severity = most_severe.severity
                result.description = most_severe.description
                result.recommended_actions = most_severe.recommended_actions
                result.detection_metadata.update(most_severe.detection_metadata)
                
                # Calculate distance score if principle available
                if principle:
                    result.distance_score = await self.distance_calculator.calculate_distance(principle)
            
            # Add detection metadata
            detection_time = time.time() - start_time
            result.detection_metadata.update({
                "detection_timestamp": datetime.now(timezone.utc).isoformat(),
                "detection_time_ms": round(detection_time * 1000, 2),
                "violations_found": len(violations),
                "detection_methods_used": self._get_detection_methods_used(principle, policy, fidelity_score),
                "service_version": "1.0.0"
            })
            
            logger.debug(f"Violation detection completed: {result.violation_detected}")
            return result
            
        except Exception as e:
            logger.error(f"Error in violation detection: {e}")
            return ViolationDetectionResult(
                violation_detected=False,
                violation_type=None,
                severity=None,
                fidelity_score=fidelity_score,
                distance_score=None,
                description=f"Detection error: {str(e)}",
                context_data=context_data,
                recommended_actions=["Review detection service logs", "Contact system administrator"],
                detection_metadata={"error": str(e), "detection_failed": True}
            )
    
    async def scan_for_violations(self, db: AsyncSession) -> BatchViolationResult:
        """
        Perform real-time violation scanning across all active principles and policies.
        
        Args:
            db: Database session
            
        Returns:
            BatchViolationResult with scan results
        """
        start_time = time.time()
        
        try:
            # Get active principles and policies
            principles_result = await db.execute(
                select(ConstitutionalPrinciple).where(
                    ConstitutionalPrinciple.is_active == True
                )
            )
            principles = principles_result.scalars().all()
            
            policies_result = await db.execute(
                select(Policy).where(
                    Policy.is_active == True
                )
            )
            policies = policies_result.scalars().all()
            
            # Perform violation detection
            detection_results = []
            violations_by_type = {vt: 0 for vt in ViolationType}
            violations_by_severity = {vs: 0 for vs in ViolationSeverity}
            
            # Scan principles
            for principle in principles:
                result = await self.detect_violation(principle=principle)
                detection_results.append(result)
                
                if result.violation_detected:
                    violations_by_type[result.violation_type] += 1
                    violations_by_severity[result.severity] += 1
            
            # Scan policies
            for policy in policies:
                result = await self.detect_violation(policy=policy)
                detection_results.append(result)
                
                if result.violation_detected:
                    violations_by_type[result.violation_type] += 1
                    violations_by_severity[result.severity] += 1
            
            # Calculate results
            total_analyzed = len(principles) + len(policies)
            violations_detected = sum(1 for r in detection_results if r.violation_detected)
            analysis_time = time.time() - start_time
            
            # Update scan time
            self.last_scan_time = datetime.now(timezone.utc)
            
            batch_result = BatchViolationResult(
                total_analyzed=total_analyzed,
                violations_detected=violations_detected,
                violations_by_type=violations_by_type,
                violations_by_severity=violations_by_severity,
                detection_results=detection_results,
                analysis_time_seconds=analysis_time
            )
            
            logger.info(f"Violation scan completed: {violations_detected}/{total_analyzed} violations detected")
            return batch_result
            
        except Exception as e:
            logger.error(f"Error in violation scanning: {e}")
            return BatchViolationResult(
                total_analyzed=0,
                violations_detected=0,
                violations_by_type={vt: 0 for vt in ViolationType},
                violations_by_severity={vs: 0 for vs in ViolationSeverity},
                detection_results=[],
                analysis_time_seconds=time.time() - start_time
            )

    async def _detect_principle_violations(
        self,
        principle: ConstitutionalPrinciple,
        context_data: Dict[str, Any]
    ) -> List[ViolationDetectionResult]:
        """Detect violations specific to constitutional principles."""
        violations = []

        try:
            # Use error prediction model to assess principle
            prediction = self.error_predictor.predict_synthesis_challenges(principle)

            # Check for high-risk predictions
            if prediction.overall_risk_score > 0.8:
                violations.append(ViolationDetectionResult(
                    violation_detected=True,
                    violation_type=ViolationType.PRINCIPLE_VIOLATION,
                    severity=ViolationSeverity.HIGH,
                    fidelity_score=None,
                    distance_score=None,
                    description=f"High synthesis risk detected for principle {principle.name}",
                    context_data=context_data,
                    recommended_actions=["Review principle clarity", "Consider principle refinement"],
                    detection_metadata={"prediction_result": prediction.__dict__}
                ))

            # Check principle distance score
            distance_score = await self.distance_calculator.calculate_distance(principle)
            if distance_score < 0.6:  # Low distance score indicates potential issues
                violations.append(ViolationDetectionResult(
                    violation_detected=True,
                    violation_type=ViolationType.PRINCIPLE_VIOLATION,
                    severity=ViolationSeverity.MEDIUM,
                    fidelity_score=None,
                    distance_score=distance_score,
                    description=f"Low constitutional distance score for principle {principle.name}",
                    context_data=context_data,
                    recommended_actions=["Review principle formality", "Improve criteria clarity"],
                    detection_metadata={"distance_score": distance_score}
                ))

        except Exception as e:
            logger.error(f"Error detecting principle violations: {e}")

        return violations

    async def _detect_policy_violations(
        self,
        policy: Policy,
        context_data: Dict[str, Any]
    ) -> List[ViolationDetectionResult]:
        """Detect violations specific to policies."""
        violations = []

        try:
            # Check policy quality metrics
            if hasattr(policy, 'quality_score') and policy.quality_score < 0.7:
                violations.append(ViolationDetectionResult(
                    violation_detected=True,
                    violation_type=ViolationType.ENFORCEMENT_BREACH,
                    severity=ViolationSeverity.MEDIUM,
                    fidelity_score=None,
                    distance_score=None,
                    description=f"Low quality score for policy {policy.name}",
                    context_data=context_data,
                    recommended_actions=["Review policy implementation", "Improve policy clarity"],
                    detection_metadata={"quality_score": policy.quality_score}
                ))

            # Check for policy conflicts (simplified check)
            if hasattr(policy, 'conflict_indicators') and policy.conflict_indicators:
                violations.append(ViolationDetectionResult(
                    violation_detected=True,
                    violation_type=ViolationType.POLICY_INCONSISTENCY,
                    severity=ViolationSeverity.HIGH,
                    fidelity_score=None,
                    distance_score=None,
                    description=f"Policy conflicts detected for {policy.name}",
                    context_data=context_data,
                    recommended_actions=["Resolve policy conflicts", "Review policy dependencies"],
                    detection_metadata={"conflict_indicators": policy.conflict_indicators}
                ))

        except Exception as e:
            logger.error(f"Error detecting policy violations: {e}")

        return violations

    async def _detect_threshold_violations(
        self,
        fidelity_score: float,
        context_data: Dict[str, Any]
    ) -> List[ViolationDetectionResult]:
        """Detect threshold-based violations."""
        violations = []

        try:
            # Load thresholds
            await self._load_thresholds()

            # Check fidelity score thresholds
            if "fidelity_score" in self.thresholds_cache:
                threshold = self.thresholds_cache["fidelity_score"]

                if fidelity_score < threshold.red_threshold:
                    violations.append(ViolationDetectionResult(
                        violation_detected=True,
                        violation_type=ViolationType.THRESHOLD_BREACH,
                        severity=ViolationSeverity.CRITICAL,
                        fidelity_score=fidelity_score,
                        distance_score=None,
                        description=f"Critical fidelity score threshold breach: {fidelity_score:.3f} < {threshold.red_threshold}",
                        context_data=context_data,
                        recommended_actions=["Immediate system review", "Escalate to Constitutional Council"],
                        detection_metadata={"threshold_type": "red", "threshold_value": threshold.red_threshold}
                    ))
                elif fidelity_score < threshold.amber_threshold:
                    violations.append(ViolationDetectionResult(
                        violation_detected=True,
                        violation_type=ViolationType.THRESHOLD_BREACH,
                        severity=ViolationSeverity.HIGH,
                        fidelity_score=fidelity_score,
                        distance_score=None,
                        description=f"Warning fidelity score threshold breach: {fidelity_score:.3f} < {threshold.amber_threshold}",
                        context_data=context_data,
                        recommended_actions=["Monitor system closely", "Review recent changes"],
                        detection_metadata={"threshold_type": "amber", "threshold_value": threshold.amber_threshold}
                    ))

        except Exception as e:
            logger.error(f"Error detecting threshold violations: {e}")

        return violations

    async def _detect_consistency_violations(
        self,
        principle: ConstitutionalPrinciple,
        policy: Policy,
        context_data: Dict[str, Any]
    ) -> List[ViolationDetectionResult]:
        """Detect consistency violations between principles and policies."""
        violations = []

        try:
            # Check if policy is derived from principle
            if hasattr(policy, 'source_principle_ids') and principle.id not in policy.source_principle_ids:
                # This is a simplified check - in practice, would use more sophisticated analysis
                violations.append(ViolationDetectionResult(
                    violation_detected=True,
                    violation_type=ViolationType.POLICY_INCONSISTENCY,
                    severity=ViolationSeverity.MEDIUM,
                    fidelity_score=None,
                    distance_score=None,
                    description=f"Policy {policy.name} not aligned with principle {principle.name}",
                    context_data=context_data,
                    recommended_actions=["Review policy-principle alignment", "Update policy derivation"],
                    detection_metadata={"principle_id": str(principle.id), "policy_id": str(policy.id)}
                ))

        except Exception as e:
            logger.error(f"Error detecting consistency violations: {e}")

        return violations

    async def _load_thresholds(self):
        """Load violation thresholds from database."""
        try:
            # Check if cache needs refresh (refresh every 5 minutes)
            if (self.cache_updated_at is None or
                (datetime.now(timezone.utc) - self.cache_updated_at).total_seconds() > 300):

                async for db in get_async_db():
                    result = await db.execute(
                        select(ViolationThreshold).where(ViolationThreshold.enabled == True)
                    )
                    thresholds = result.scalars().all()

                    self.thresholds_cache = {t.threshold_name: t for t in thresholds}
                    self.cache_updated_at = datetime.now(timezone.utc)
                    break

        except Exception as e:
            logger.error(f"Error loading thresholds: {e}")

    def _get_severity_weight(self, severity: ViolationSeverity) -> int:
        """Get numeric weight for severity comparison."""
        weights = {
            ViolationSeverity.LOW: 1,
            ViolationSeverity.MEDIUM: 2,
            ViolationSeverity.HIGH: 3,
            ViolationSeverity.CRITICAL: 4
        }
        return weights.get(severity, 0)

    def _get_detection_methods_used(
        self,
        principle: Optional[ConstitutionalPrinciple],
        policy: Optional[Policy],
        fidelity_score: Optional[float]
    ) -> List[str]:
        """Get list of detection methods used."""
        methods = []
        if principle:
            methods.extend(["principle_analysis", "distance_calculation", "error_prediction"])
        if policy:
            methods.extend(["policy_analysis", "quality_assessment"])
        if fidelity_score is not None:
            methods.append("threshold_checking")
        if principle and policy:
            methods.append("consistency_analysis")
        return methods

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for violation detection."""
        return {
            "scan_interval_seconds": 30,
            "batch_size": 100,
            "detection_timeout_seconds": 60,
            "enable_real_time_scanning": True,
            "enable_batch_analysis": True,
            "enable_historical_analysis": True,
            "max_violations_per_scan": 1000,
            "cache_threshold_seconds": 300
        }
