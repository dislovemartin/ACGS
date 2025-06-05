"""
constitutional_fidelity_monitor.py

QEC-inspired Constitutional Fidelity Monitor for system-wide health monitoring.
Provides holistic system health metric for proactive governance oversight with
real-time fidelity calculation and alert management.

Classes:
    ConstitutionalFidelityMonitor: Main monitor for system-wide health
    FidelityComponents: Data structure for fidelity calculation components
    FidelityAlert: Alert configuration and management
    FidelityThresholds: Threshold configuration for alerts
"""

import logging
import time
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from ...core.constitutional_principle import ConstitutionalPrinciple
from .constitutional_distance_calculator import ConstitutionalDistanceCalculator
from .error_prediction_model import ErrorPredictionModel

logger = logging.getLogger(__name__)


class FidelityLevel(Enum):
    """Enumeration of fidelity alert levels."""
    GREEN = "green"    # Normal operation (≥0.85)
    AMBER = "amber"    # Attention required (≥0.70)
    RED = "red"        # Critical intervention needed (≥0.55)
    CRITICAL = "critical"  # Emergency state (<0.55)


@dataclass
class FidelityComponents:
    """Data structure for fidelity calculation components."""
    principle_coverage: float      # 0.0-1.0, coverage of constitutional principles
    synthesis_success: float       # 0.0-1.0, success rate of policy synthesis
    enforcement_reliability: float # 0.0-1.0, reliability of policy enforcement
    adaptation_speed: float        # 0.0-1.0, speed of system adaptation
    stakeholder_satisfaction: float # 0.0-1.0, stakeholder satisfaction score
    appeal_frequency: float        # 0.0-1.0, inverse of appeal frequency (lower appeals = higher score)
    composite_score: float         # 0.0-1.0, weighted composite fidelity score
    calculation_metadata: Dict[str, Any]


@dataclass
class FidelityAlert:
    """Alert configuration and state."""
    level: FidelityLevel
    title: str
    description: str
    timestamp: datetime
    components_affected: List[str]
    recommended_actions: List[str]
    metadata: Dict[str, Any]


@dataclass
class FidelityThresholds:
    """Threshold configuration for fidelity alerts."""
    green: float = 0.85    # Normal operation
    amber: float = 0.70    # Attention required
    red: float = 0.55      # Critical intervention needed
    
    # Component-specific thresholds
    principle_coverage_min: float = 0.80
    synthesis_success_min: float = 0.75
    enforcement_reliability_min: float = 0.90
    adaptation_speed_min: float = 0.60
    stakeholder_satisfaction_min: float = 0.70
    appeal_frequency_max: float = 0.30  # Maximum acceptable appeal rate


class ConstitutionalFidelityMonitor:
    """
    QEC-inspired Constitutional Fidelity Monitor.
    
    Provides holistic system health metric for proactive governance oversight
    through real-time fidelity calculation combining multiple system components.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the constitutional fidelity monitor.
        
        Args:
            config: Configuration dictionary for monitor settings
        """
        self.config = config or self._get_default_config()
        self.thresholds = FidelityThresholds(**self.config.get("thresholds", {}))
        
        # Component weights for composite score calculation
        self.weights = self.config.get("weights", {
            'principle_coverage': 0.25,
            'synthesis_success': 0.20,
            'enforcement_reliability': 0.20,
            'adaptation_speed': 0.15,
            'stakeholder_satisfaction': 0.10,
            'appeal_frequency': 0.10
        })
        
        # Historical data storage
        self.fidelity_history: List[FidelityComponents] = []
        self.active_alerts: Dict[str, FidelityAlert] = {}
        self.alert_handlers: List[callable] = []
        
        # Monitoring state
        self.last_calculation_time: Optional[datetime] = None
        self.monitoring_active = False
        self.calculation_interval = self.config.get("calculation_interval_seconds", 300)  # 5 minutes
        
        # Integration components
        self.distance_calculator = ConstitutionalDistanceCalculator()
        self.error_predictor = ErrorPredictionModel()
        
        logger.info("Constitutional Fidelity Monitor initialized")
    
    async def start_monitoring(self):
        """Start continuous fidelity monitoring."""
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return
        
        self.monitoring_active = True
        logger.info("Starting constitutional fidelity monitoring")
        
        # Start monitoring loop
        asyncio.create_task(self._monitoring_loop())
    
    async def stop_monitoring(self):
        """Stop continuous fidelity monitoring."""
        self.monitoring_active = False
        logger.info("Stopped constitutional fidelity monitoring")
    
    async def calculate_fidelity(
        self, 
        principles: List[ConstitutionalPrinciple],
        system_metrics: Optional[Dict[str, Any]] = None
    ) -> FidelityComponents:
        """
        Calculate constitutional fidelity score.
        
        Args:
            principles: List of constitutional principles to evaluate
            system_metrics: Optional system metrics for calculation
            
        Returns:
            FidelityComponents with detailed fidelity breakdown
        """
        start_time = time.time()
        
        try:
            # Calculate individual components
            principle_coverage = await self._calc_principle_coverage(principles)
            synthesis_success = await self._calc_synthesis_success(system_metrics)
            enforcement_reliability = await self._calc_enforcement_reliability(system_metrics)
            adaptation_speed = await self._calc_adaptation_speed(system_metrics)
            stakeholder_satisfaction = await self._calc_stakeholder_satisfaction(system_metrics)
            appeal_frequency = await self._calc_appeal_frequency(system_metrics)
            
            # Calculate weighted composite score
            composite_score = sum(
                self.weights[component] * value
                for component, value in {
                    'principle_coverage': principle_coverage,
                    'synthesis_success': synthesis_success,
                    'enforcement_reliability': enforcement_reliability,
                    'adaptation_speed': adaptation_speed,
                    'stakeholder_satisfaction': stakeholder_satisfaction,
                    'appeal_frequency': appeal_frequency
                }.items()
            )
            
            # Apply penalties for high-severity issues
            if await self._has_high_severity_appeals(system_metrics):
                composite_score *= 0.85  # 15% penalty
            
            # Prepare calculation metadata
            calculation_time = time.time() - start_time
            metadata = {
                "calculation_timestamp": datetime.now().isoformat(),
                "calculation_time_ms": round(calculation_time * 1000, 2),
                "principles_evaluated": len(principles),
                "weights_used": self.weights,
                "penalties_applied": await self._has_high_severity_appeals(system_metrics),
                "monitor_version": "1.0.0"
            }
            
            # Create fidelity components
            fidelity = FidelityComponents(
                principle_coverage=principle_coverage,
                synthesis_success=synthesis_success,
                enforcement_reliability=enforcement_reliability,
                adaptation_speed=adaptation_speed,
                stakeholder_satisfaction=stakeholder_satisfaction,
                appeal_frequency=appeal_frequency,
                composite_score=composite_score,
                calculation_metadata=metadata
            )
            
            # Store in history
            self.fidelity_history.append(fidelity)
            if len(self.fidelity_history) > self.config.get("max_history_size", 1000):
                self.fidelity_history.pop(0)
            
            # Update last calculation time
            self.last_calculation_time = datetime.now()
            
            # Check for alerts
            await self._check_and_trigger_alerts(fidelity)
            
            logger.debug(f"Constitutional fidelity calculated: {composite_score:.3f}")
            return fidelity
            
        except Exception as e:
            logger.error(f"Error calculating constitutional fidelity: {e}")
            # Return fallback fidelity
            return await self._create_fallback_fidelity()
    
    def get_current_fidelity(self) -> Optional[FidelityComponents]:
        """Get the most recent fidelity calculation."""
        return self.fidelity_history[-1] if self.fidelity_history else None
    
    def get_fidelity_history(self, days: int = 30) -> List[FidelityComponents]:
        """
        Get fidelity history for the specified number of days.
        
        Args:
            days: Number of days of history to retrieve
            
        Returns:
            List of FidelityComponents within the time range
        """
        cutoff_time = datetime.now() - timedelta(days=days)
        
        return [
            fidelity for fidelity in self.fidelity_history
            if datetime.fromisoformat(fidelity.calculation_metadata["calculation_timestamp"]) >= cutoff_time
        ]
    
    def get_fidelity_trend(self, history: Optional[List[FidelityComponents]] = None) -> str:
        """
        Calculate fidelity trend from historical data.
        
        Args:
            history: Optional history list, uses recent history if not provided
            
        Returns:
            Trend description: 'stable', 'improving', 'degrading'
        """
        if not history:
            history = self.get_fidelity_history(days=7)  # Last week
        
        if len(history) < 2:
            return 'stable'
        
        # Calculate trend using linear regression on composite scores
        scores = [f.composite_score for f in history]
        n = len(scores)
        
        # Simple trend calculation
        recent_avg = sum(scores[-n//2:]) / (n//2) if n >= 4 else scores[-1]
        earlier_avg = sum(scores[:n//2]) / (n//2) if n >= 4 else scores[0]
        
        trend_threshold = 0.02  # 2% change threshold
        
        if recent_avg > earlier_avg + trend_threshold:
            return 'improving'
        elif recent_avg < earlier_avg - trend_threshold:
            return 'degrading'
        else:
            return 'stable'
    
    def register_alert_handler(self, handler: callable):
        """
        Register an alert handler function.
        
        Args:
            handler: Callable that takes (FidelityAlert) -> None
        """
        self.alert_handlers.append(handler)
        logger.info(f"Registered alert handler: {handler.__name__}")
    
    def get_active_alerts(self) -> List[FidelityAlert]:
        """Get list of currently active alerts."""
        return list(self.active_alerts.values())
    
    async def _monitoring_loop(self):
        """Main monitoring loop for continuous fidelity calculation."""
        while self.monitoring_active:
            try:
                # This would integrate with actual system data sources
                # For now, we'll use mock data
                principles = []  # Would fetch from AC service
                system_metrics = {}  # Would fetch from monitoring systems
                
                await self.calculate_fidelity(principles, system_metrics)
                
                # Wait for next calculation interval
                await asyncio.sleep(self.calculation_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def _calc_principle_coverage(self, principles: List[ConstitutionalPrinciple]) -> float:
        """Calculate principle coverage score."""
        if not principles:
            return 0.0
        
        # Calculate coverage based on principle quality and completeness
        total_score = 0.0
        for principle in principles:
            # Use constitutional distance as quality indicator
            distance_score = self.distance_calculator.calculate_score(principle)
            total_score += distance_score
        
        return min(total_score / len(principles), 1.0)
    
    async def _calc_synthesis_success(self, system_metrics: Optional[Dict[str, Any]]) -> float:
        """Calculate synthesis success rate."""
        if not system_metrics:
            return 0.75  # Default assumption
        
        # Would integrate with actual GS service metrics
        return system_metrics.get("synthesis_success_rate", 0.75)
    
    async def _calc_enforcement_reliability(self, system_metrics: Optional[Dict[str, Any]]) -> float:
        """Calculate enforcement reliability score."""
        if not system_metrics:
            return 0.90  # Default assumption
        
        # Would integrate with actual PGC service metrics
        return system_metrics.get("enforcement_reliability", 0.90)
    
    async def _calc_adaptation_speed(self, system_metrics: Optional[Dict[str, Any]]) -> float:
        """Calculate system adaptation speed score."""
        if not system_metrics:
            return 0.70  # Default assumption
        
        # Would measure how quickly system adapts to new requirements
        return system_metrics.get("adaptation_speed", 0.70)
    
    async def _calc_stakeholder_satisfaction(self, system_metrics: Optional[Dict[str, Any]]) -> float:
        """Calculate stakeholder satisfaction score."""
        if not system_metrics:
            return 0.75  # Default assumption
        
        # Would integrate with stakeholder feedback systems
        return system_metrics.get("stakeholder_satisfaction", 0.75)
    
    async def _calc_appeal_frequency(self, system_metrics: Optional[Dict[str, Any]]) -> float:
        """Calculate appeal frequency score (inverse of appeal rate)."""
        if not system_metrics:
            return 0.80  # Default assumption (low appeal rate)
        
        # Convert appeal frequency to score (lower appeals = higher score)
        appeal_rate = system_metrics.get("appeal_frequency", 0.20)
        return max(0.0, 1.0 - appeal_rate)
    
    async def _has_high_severity_appeals(self, system_metrics: Optional[Dict[str, Any]]) -> bool:
        """Check if there are high-severity appeals that warrant penalties."""
        if not system_metrics:
            return False
        
        return system_metrics.get("high_severity_appeals", 0) > 0
    
    async def _check_and_trigger_alerts(self, fidelity: FidelityComponents):
        """Check fidelity levels and trigger alerts as needed."""
        current_level = self._determine_fidelity_level(fidelity.composite_score)
        
        # Check if alert level has changed
        alert_key = "fidelity_level"
        existing_alert = self.active_alerts.get(alert_key)
        
        if current_level == FidelityLevel.GREEN:
            # Clear any existing alerts
            if existing_alert:
                del self.active_alerts[alert_key]
                logger.info("Fidelity returned to normal levels")
        else:
            # Create or update alert
            if not existing_alert or existing_alert.level != current_level:
                alert = FidelityAlert(
                    level=current_level,
                    title=f"Constitutional Fidelity {current_level.value.upper()}",
                    description=self._get_alert_description(current_level, fidelity),
                    timestamp=datetime.now(),
                    components_affected=self._get_affected_components(fidelity),
                    recommended_actions=self._get_recommended_actions(current_level, fidelity),
                    metadata={"fidelity_score": fidelity.composite_score}
                )
                
                self.active_alerts[alert_key] = alert
                
                # Notify alert handlers
                for handler in self.alert_handlers:
                    try:
                        await handler(alert) if asyncio.iscoroutinefunction(handler) else handler(alert)
                    except Exception as e:
                        logger.error(f"Error in alert handler {handler.__name__}: {e}")
    
    def _determine_fidelity_level(self, score: float) -> FidelityLevel:
        """Determine fidelity alert level based on score."""
        if score >= self.thresholds.green:
            return FidelityLevel.GREEN
        elif score >= self.thresholds.amber:
            return FidelityLevel.AMBER
        elif score >= self.thresholds.red:
            return FidelityLevel.RED
        else:
            return FidelityLevel.CRITICAL
    
    def _get_alert_description(self, level: FidelityLevel, fidelity: FidelityComponents) -> str:
        """Generate alert description based on fidelity level and components."""
        descriptions = {
            FidelityLevel.AMBER: f"Constitutional fidelity requires attention (score: {fidelity.composite_score:.3f})",
            FidelityLevel.RED: f"Constitutional fidelity critical intervention needed (score: {fidelity.composite_score:.3f})",
            FidelityLevel.CRITICAL: f"Constitutional fidelity emergency state (score: {fidelity.composite_score:.3f})"
        }
        return descriptions.get(level, f"Constitutional fidelity alert (score: {fidelity.composite_score:.3f})")
    
    def _get_affected_components(self, fidelity: FidelityComponents) -> List[str]:
        """Identify components that are below acceptable thresholds."""
        affected = []
        
        if fidelity.principle_coverage < self.thresholds.principle_coverage_min:
            affected.append("principle_coverage")
        if fidelity.synthesis_success < self.thresholds.synthesis_success_min:
            affected.append("synthesis_success")
        if fidelity.enforcement_reliability < self.thresholds.enforcement_reliability_min:
            affected.append("enforcement_reliability")
        if fidelity.adaptation_speed < self.thresholds.adaptation_speed_min:
            affected.append("adaptation_speed")
        if fidelity.stakeholder_satisfaction < self.thresholds.stakeholder_satisfaction_min:
            affected.append("stakeholder_satisfaction")
        if (1.0 - fidelity.appeal_frequency) > self.thresholds.appeal_frequency_max:
            affected.append("appeal_frequency")
        
        return affected
    
    def _get_recommended_actions(self, level: FidelityLevel, fidelity: FidelityComponents) -> List[str]:
        """Generate recommended actions based on fidelity level and affected components."""
        actions = []
        affected = self._get_affected_components(fidelity)
        
        if "principle_coverage" in affected:
            actions.append("Review and enhance constitutional principle coverage")
        if "synthesis_success" in affected:
            actions.append("Investigate and improve policy synthesis reliability")
        if "enforcement_reliability" in affected:
            actions.append("Audit and optimize policy enforcement mechanisms")
        if "adaptation_speed" in affected:
            actions.append("Accelerate system adaptation processes")
        if "stakeholder_satisfaction" in affected:
            actions.append("Engage stakeholders and address satisfaction concerns")
        if "appeal_frequency" in affected:
            actions.append("Investigate and resolve high appeal frequency causes")
        
        if level == FidelityLevel.CRITICAL:
            actions.insert(0, "Initiate emergency constitutional review process")
        elif level == FidelityLevel.RED:
            actions.insert(0, "Convene Constitutional Council for urgent review")
        
        return actions
    
    async def _create_fallback_fidelity(self) -> FidelityComponents:
        """Create fallback fidelity components for error cases."""
        return FidelityComponents(
            principle_coverage=0.5,
            synthesis_success=0.5,
            enforcement_reliability=0.5,
            adaptation_speed=0.5,
            stakeholder_satisfaction=0.5,
            appeal_frequency=0.5,
            composite_score=0.5,
            calculation_metadata={
                "fallback": True,
                "timestamp": datetime.now().isoformat(),
                "error": "Fallback fidelity calculation"
            }
        )
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for the fidelity monitor."""
        return {
            "calculation_interval_seconds": 300,  # 5 minutes
            "max_history_size": 1000,
            "weights": {
                'principle_coverage': 0.25,
                'synthesis_success': 0.20,
                'enforcement_reliability': 0.20,
                'adaptation_speed': 0.15,
                'stakeholder_satisfaction': 0.10,
                'appeal_frequency': 0.10
            },
            "thresholds": {
                "green": 0.85,
                "amber": 0.70,
                "red": 0.55,
                "principle_coverage_min": 0.80,
                "synthesis_success_min": 0.75,
                "enforcement_reliability_min": 0.90,
                "adaptation_speed_min": 0.60,
                "stakeholder_satisfaction_min": 0.70,
                "appeal_frequency_max": 0.30
            }
        }
