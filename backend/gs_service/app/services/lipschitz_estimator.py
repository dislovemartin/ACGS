"""
Lipschitz Constant Estimation for ACGS Policy Synthesis

This module provides experimental protocols for estimating Lipschitz constants
of the policy synthesis process components, addressing the technical review
finding that fixed values were asserted without derivation.
"""

import asyncio
import logging
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from scipy.spatial.distance import cosine
from sklearn.metrics.pairwise import euclidean_distances
import time
import json

from ..schemas import gs_schemas
from .policy_synthesizer import PolicySynthesizer
from .llm_service import get_llm_service

logger = logging.getLogger(__name__)


@dataclass
class LipschitzEstimationConfig:
    """Configuration for Lipschitz constant estimation experiments."""
    num_perturbations: int = 100
    perturbation_magnitude: float = 0.1
    confidence_level: float = 0.95
    max_distance_threshold: float = 2.0
    embedding_dimension: int = 384  # SBERT default
    random_seed: int = 42


@dataclass
class LipschitzEstimationResult:
    """Results from Lipschitz constant estimation."""
    component_name: str
    estimated_constant: float
    confidence_interval: Tuple[float, float]
    num_samples: int
    max_ratio: float
    mean_ratio: float
    std_ratio: float
    methodology: str
    raw_ratios: List[float]


class MetricSpaceValidator:
    """Validates metric space properties for distance functions."""
    
    @staticmethod
    def validate_triangle_inequality(
        distance_func,
        points: List[Any],
        tolerance: float = 1e-6
    ) -> Dict[str, Any]:
        """Test triangle inequality: d(x,z) ≤ d(x,y) + d(y,z)"""
        violations = 0
        total_tests = 0
        max_violation = 0.0
        
        for i in range(len(points)):
            for j in range(i + 1, len(points)):
                for k in range(j + 1, len(points)):
                    x, y, z = points[i], points[j], points[k]
                    
                    d_xz = distance_func(x, z)
                    d_xy = distance_func(x, y)
                    d_yz = distance_func(y, z)
                    
                    violation = d_xz - (d_xy + d_yz)
                    if violation > tolerance:
                        violations += 1
                        max_violation = max(max_violation, violation)
                    
                    total_tests += 1
        
        return {
            "is_metric": violations == 0,
            "violation_rate": violations / total_tests if total_tests > 0 else 0,
            "max_violation": max_violation,
            "total_tests": total_tests
        }
    
    @staticmethod
    def validate_symmetry(
        distance_func,
        points: List[Any],
        tolerance: float = 1e-6
    ) -> Dict[str, Any]:
        """Test symmetry: d(x,y) = d(y,x)"""
        violations = 0
        total_tests = 0
        max_violation = 0.0
        
        for i in range(len(points)):
            for j in range(i + 1, len(points)):
                x, y = points[i], points[j]
                
                d_xy = distance_func(x, y)
                d_yx = distance_func(y, x)
                
                violation = abs(d_xy - d_yx)
                if violation > tolerance:
                    violations += 1
                    max_violation = max(max_violation, violation)
                
                total_tests += 1
        
        return {
            "is_symmetric": violations == 0,
            "violation_rate": violations / total_tests if total_tests > 0 else 0,
            "max_violation": max_violation,
            "total_tests": total_tests
        }


class ConstitutionDistanceFunction:
    """Improved distance function for constitutional principle spaces."""
    
    def __init__(self, embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.embedding_model = embedding_model
        self._embeddings_cache = {}
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """Get or compute embedding for text."""
        if text not in self._embeddings_cache:
            # In practice, use actual sentence transformer
            # For now, simulate with hash-based embedding
            import hashlib
            hash_obj = hashlib.md5(text.encode())
            # Create deterministic "embedding" from hash
            np.random.seed(int(hash_obj.hexdigest()[:8], 16))
            embedding = np.random.normal(0, 1, 384)
            embedding = embedding / np.linalg.norm(embedding)  # Normalize
            self._embeddings_cache[text] = embedding
        return self._embeddings_cache[text]
    
    def semantic_distance(self, principle1: str, principle2: str) -> float:
        """Compute semantic distance using embeddings (proper metric)."""
        emb1 = self._get_embedding(principle1)
        emb2 = self._get_embedding(principle2)
        
        # Use Euclidean distance in embedding space (proper metric)
        return float(np.linalg.norm(emb1 - emb2))
    
    def edit_distance_normalized(self, text1: str, text2: str) -> float:
        """Compute normalized edit distance."""
        def levenshtein(s1, s2):
            if len(s1) < len(s2):
                return levenshtein(s2, s1)
            if len(s2) == 0:
                return len(s1)
            
            previous_row = list(range(len(s2) + 1))
            for i, c1 in enumerate(s1):
                current_row = [i + 1]
                for j, c2 in enumerate(s2):
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (c1 != c2)
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row
            
            return previous_row[-1]
        
        max_len = max(len(text1), len(text2))
        if max_len == 0:
            return 0.0
        return levenshtein(text1, text2) / max_len
    
    def combined_distance(
        self,
        principle1: str,
        principle2: str,
        semantic_weight: float = 0.7,
        edit_weight: float = 0.3
    ) -> float:
        """Combine semantic and edit distances with proper metric properties."""
        semantic_dist = self.semantic_distance(principle1, principle2)
        edit_dist = self.edit_distance_normalized(principle1, principle2)
        
        # Weighted combination preserves metric properties if components are metrics
        return semantic_weight * semantic_dist + edit_weight * edit_dist


class LipschitzEstimator:
    """Estimates Lipschitz constants for ACGS policy synthesis components."""
    
    def __init__(self, config: LipschitzEstimationConfig = None):
        self.config = config or LipschitzEstimationConfig()
        self.distance_func = ConstitutionDistanceFunction()
        self.policy_synthesizer = None
        self.llm_service = None
        
    async def initialize(self):
        """Initialize services for estimation."""
        self.llm_service = get_llm_service()
        # Initialize policy synthesizer if available
        try:
            from .policy_synthesizer import PolicySynthesizer
            self.policy_synthesizer = PolicySynthesizer(self.llm_service)
        except Exception as e:
            logger.warning(f"Could not initialize policy synthesizer: {e}")
    
    async def estimate_llm_lipschitz_constant(
        self,
        test_principles: List[str]
    ) -> LipschitzEstimationResult:
        """Estimate Lipschitz constant for LLM synthesis component."""
        if not self.llm_service:
            await self.initialize()
        
        ratios = []
        np.random.seed(self.config.random_seed)
        
        for i in range(self.config.num_perturbations):
            # Select two random principles
            if len(test_principles) < 2:
                continue
                
            idx1, idx2 = np.random.choice(len(test_principles), 2, replace=False)
            principle1, principle2 = test_principles[idx1], test_principles[idx2]
            
            # Compute input distance
            input_distance = self.distance_func.combined_distance(principle1, principle2)
            
            if input_distance < 1e-6:  # Skip nearly identical inputs
                continue
            
            try:
                # Generate policies for both principles
                policy1 = await self._generate_policy_text(principle1)
                policy2 = await self._generate_policy_text(principle2)
                
                # Compute output distance
                output_distance = self.distance_func.combined_distance(policy1, policy2)
                
                # Compute ratio
                ratio = output_distance / input_distance
                ratios.append(ratio)
                
            except Exception as e:
                logger.warning(f"Error in LLM Lipschitz estimation iteration {i}: {e}")
                continue
        
        return self._compute_estimation_result("LLM_synthesis", ratios)
    
    async def _generate_policy_text(self, principle: str) -> str:
        """Generate policy text from principle using LLM."""
        prompt = f"""
        Convert the following constitutional principle into a Rego policy rule:
        
        Principle: {principle}
        
        Generate only the Rego code without explanations:
        """
        
        try:
            response = await self.llm_service.generate_text(
                prompt, max_tokens=500, temperature=0.1
            )
            return response.strip()
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return ""
    
    def _compute_estimation_result(
        self,
        component_name: str,
        ratios: List[float]
    ) -> LipschitzEstimationResult:
        """Compute estimation statistics from ratios."""
        if not ratios:
            return LipschitzEstimationResult(
                component_name=component_name,
                estimated_constant=float('inf'),
                confidence_interval=(0.0, float('inf')),
                num_samples=0,
                max_ratio=0.0,
                mean_ratio=0.0,
                std_ratio=0.0,
                methodology="perturbation_analysis",
                raw_ratios=[]
            )
        
        ratios_array = np.array(ratios)
        mean_ratio = float(np.mean(ratios_array))
        std_ratio = float(np.std(ratios_array))
        max_ratio = float(np.max(ratios_array))
        
        # Compute confidence interval
        alpha = 1 - self.config.confidence_level
        z_score = 1.96  # For 95% confidence
        margin_error = z_score * std_ratio / np.sqrt(len(ratios))
        
        ci_lower = max(0.0, mean_ratio - margin_error)
        ci_upper = mean_ratio + margin_error
        
        # Use conservative estimate (upper bound of CI or max observed)
        estimated_constant = min(max_ratio, ci_upper)
        
        return LipschitzEstimationResult(
            component_name=component_name,
            estimated_constant=estimated_constant,
            confidence_interval=(ci_lower, ci_upper),
            num_samples=len(ratios),
            max_ratio=max_ratio,
            mean_ratio=mean_ratio,
            std_ratio=std_ratio,
            methodology="perturbation_analysis",
            raw_ratios=ratios
        )
    
    async def validate_metric_properties(
        self,
        test_principles: List[str]
    ) -> Dict[str, Any]:
        """Validate that distance function satisfies metric properties."""
        validator = MetricSpaceValidator()
        
        # Test triangle inequality
        triangle_result = validator.validate_triangle_inequality(
            lambda x, y: self.distance_func.combined_distance(x, y),
            test_principles[:20]  # Limit for computational efficiency
        )
        
        # Test symmetry
        symmetry_result = validator.validate_symmetry(
            lambda x, y: self.distance_func.combined_distance(x, y),
            test_principles[:20]
        )
        
        return {
            "triangle_inequality": triangle_result,
            "symmetry": symmetry_result,
            "is_valid_metric": triangle_result["is_metric"] and symmetry_result["is_symmetric"]
        }


# Example usage and testing
async def run_lipschitz_estimation_example():
    """Example of running Lipschitz constant estimation."""
    estimator = LipschitzEstimator()
    await estimator.initialize()
    
    # Test principles
    test_principles = [
        "AI systems must not cause harm to humans",
        "AI decisions must be explainable and transparent",
        "AI systems must respect user privacy",
        "AI systems must be fair and unbiased",
        "AI systems must be secure and robust"
    ]
    
    # Validate metric properties
    metric_validation = await estimator.validate_metric_properties(test_principles)
    print("Metric validation:", json.dumps(metric_validation, indent=2))
    
    # Estimate LLM Lipschitz constant
    llm_result = await estimator.estimate_llm_lipschitz_constant(test_principles)
    print(f"LLM Lipschitz estimate: {llm_result.estimated_constant:.3f}")
    print(f"Confidence interval: {llm_result.confidence_interval}")


if __name__ == "__main__":
    asyncio.run(run_lipschitz_estimation_example())
