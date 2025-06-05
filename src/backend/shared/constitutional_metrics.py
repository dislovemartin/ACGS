"""
Constitutional AI Governance Metrics for ACGS-PGP
Provides specialized metrics for constitutional AI governance operations.
"""

from typing import Dict, Any, Optional, List
from prometheus_client import Counter, Histogram, Gauge, Info
import logging

logger = logging.getLogger(__name__)

class ConstitutionalMetrics:
    """Specialized metrics for constitutional AI governance operations."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        
        # Constitutional principle metrics
        self.constitutional_principle_operations = Counter(
            'acgs_constitutional_principle_operations_total',
            'Total constitutional principle operations',
            ['service', 'operation_type', 'principle_category', 'status']
        )
        
        self.constitutional_compliance_score = Gauge(
            'acgs_constitutional_compliance_score',
            'Constitutional compliance score (0-1)',
            ['service', 'principle_id', 'policy_type']
        )
        
        # Policy synthesis metrics
        self.policy_synthesis_operations = Counter(
            'acgs_policy_synthesis_operations_total',
            'Total policy synthesis operations',
            ['service', 'synthesis_type', 'constitutional_context', 'status']
        )
        
        self.policy_synthesis_duration = Histogram(
            'acgs_policy_synthesis_duration_seconds',
            'Policy synthesis operation duration',
            ['service', 'synthesis_type', 'constitutional_context'],
            buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0)
        )
        
        # LLM reliability metrics
        self.llm_constitutional_reliability = Gauge(
            'acgs_llm_constitutional_reliability_score',
            'LLM constitutional reliability score (0-1)',
            ['service', 'model_name', 'constitutional_domain']
        )
        
        self.llm_bias_detection_score = Gauge(
            'acgs_llm_bias_detection_score',
            'LLM bias detection score (0-1)',
            ['service', 'bias_type', 'demographic_group']
        )
        
        # Constitutional Council metrics
        self.constitutional_council_operations = Counter(
            'acgs_constitutional_council_operations_total',
            'Constitutional Council operations',
            ['service', 'operation_type', 'council_member_role', 'status']
        )
        
        self.constitutional_amendment_votes = Counter(
            'acgs_constitutional_amendment_votes_total',
            'Constitutional amendment votes',
            ['service', 'amendment_id', 'vote_type', 'council_member_role']
        )
        
        # Formal verification metrics
        self.formal_verification_operations = Counter(
            'acgs_formal_verification_operations_total',
            'Formal verification operations',
            ['service', 'verification_type', 'solver_type', 'result']
        )
        
        self.formal_verification_duration = Histogram(
            'acgs_formal_verification_duration_seconds',
            'Formal verification duration',
            ['service', 'verification_type', 'solver_type'],
            buckets=(0.01, 0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0)
        )
        
        # Cryptographic integrity metrics
        self.cryptographic_operations = Counter(
            'acgs_cryptographic_operations_total',
            'Cryptographic operations',
            ['service', 'operation_type', 'key_type', 'status']
        )
        
        self.pgp_signature_verifications = Counter(
            'acgs_pgp_signature_verifications_total',
            'PGP signature verifications',
            ['service', 'artifact_type', 'verification_result']
        )
        
        # Conflict resolution metrics
        self.conflict_resolution_operations = Counter(
            'acgs_conflict_resolution_operations_total',
            'Conflict resolution operations',
            ['service', 'conflict_type', 'resolution_method', 'status']
        )
        
        self.conflict_resolution_duration = Histogram(
            'acgs_conflict_resolution_duration_seconds',
            'Conflict resolution duration',
            ['service', 'conflict_type', 'resolution_method'],
            buckets=(0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0)
        )
        
        # Human-in-the-loop metrics
        self.human_escalation_operations = Counter(
            'acgs_human_escalation_operations_total',
            'Human escalation operations',
            ['service', 'escalation_reason', 'escalation_type', 'resolution_status']
        )
        
        self.human_oversight_accuracy = Gauge(
            'acgs_human_oversight_accuracy_score',
            'Human oversight accuracy score (0-1)',
            ['service', 'oversight_type', 'decision_category']
        )
        
        # Performance and efficiency metrics
        self.constitutional_fidelity_score = Gauge(
            'acgs_constitutional_fidelity_score',
            'Overall constitutional fidelity score (0-1)',
            ['service', 'measurement_type']
        )
        
        self.governance_efficiency_score = Gauge(
            'acgs_governance_efficiency_score',
            'Governance efficiency score (0-1)',
            ['service', 'efficiency_type']
        )
    
    def record_constitutional_principle_operation(self, operation_type: str, 
                                                principle_category: str, status: str):
        """Record constitutional principle operation."""
        self.constitutional_principle_operations.labels(
            service=self.service_name,
            operation_type=operation_type,
            principle_category=principle_category,
            status=status
        ).inc()
    
    def update_constitutional_compliance_score(self, principle_id: str, 
                                             policy_type: str, score: float):
        """Update constitutional compliance score."""
        self.constitutional_compliance_score.labels(
            service=self.service_name,
            principle_id=principle_id,
            policy_type=policy_type
        ).set(score)
    
    def record_policy_synthesis_operation(self, synthesis_type: str, 
                                        constitutional_context: str, 
                                        status: str, duration: float):
        """Record policy synthesis operation."""
        self.policy_synthesis_operations.labels(
            service=self.service_name,
            synthesis_type=synthesis_type,
            constitutional_context=constitutional_context,
            status=status
        ).inc()
        
        self.policy_synthesis_duration.labels(
            service=self.service_name,
            synthesis_type=synthesis_type,
            constitutional_context=constitutional_context
        ).observe(duration)
    
    def update_llm_constitutional_reliability(self, model_name: str, 
                                            constitutional_domain: str, score: float):
        """Update LLM constitutional reliability score."""
        self.llm_constitutional_reliability.labels(
            service=self.service_name,
            model_name=model_name,
            constitutional_domain=constitutional_domain
        ).set(score)
    
    def update_constitutional_fidelity_score(self, measurement_type: str, score: float):
        """Update constitutional fidelity score."""
        self.constitutional_fidelity_score.labels(
            service=self.service_name,
            measurement_type=measurement_type
        ).set(score)
    
    def record_formal_verification_operation(self, verification_type: str, 
                                           solver_type: str, result: str, duration: float):
        """Record formal verification operation."""
        self.formal_verification_operations.labels(
            service=self.service_name,
            verification_type=verification_type,
            solver_type=solver_type,
            result=result
        ).inc()
        
        self.formal_verification_duration.labels(
            service=self.service_name,
            verification_type=verification_type,
            solver_type=solver_type
        ).observe(duration)
    
    def record_human_escalation(self, escalation_reason: str, 
                              escalation_type: str, resolution_status: str):
        """Record human escalation operation."""
        self.human_escalation_operations.labels(
            service=self.service_name,
            escalation_reason=escalation_reason,
            escalation_type=escalation_type,
            resolution_status=resolution_status
        ).inc()

# Global constitutional metrics registry
constitutional_metrics_registry: Dict[str, ConstitutionalMetrics] = {}

def get_constitutional_metrics(service_name: str) -> ConstitutionalMetrics:
    """Get or create constitutional metrics instance for a service."""
    if service_name not in constitutional_metrics_registry:
        constitutional_metrics_registry[service_name] = ConstitutionalMetrics(service_name)
    return constitutional_metrics_registry[service_name]
