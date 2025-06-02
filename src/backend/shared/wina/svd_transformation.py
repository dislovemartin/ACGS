"""
SVD Transformation Module for WINA

Implements SVD-based orthogonality protocol for model transformation
as part of the WINA (Weight Informed Neuron Activation) optimization.
"""

import logging
import time
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import torch
from dataclasses import dataclass
from datetime import datetime, timezone

from .exceptions import WINATransformationError
from .config import WINAConfig

logger = logging.getLogger(__name__)


@dataclass
class SVDTransformationResult:
    """
    Result of SVD transformation process.
    
    Attributes:
        original_shape: Original tensor shape
        transformed_tensor: Transformed tensor
        u_matrix: U matrix from SVD
        s_values: Singular values
        vt_matrix: V^T matrix from SVD
        rank_reduction: Applied rank reduction ratio
        compression_ratio: Achieved compression ratio
        transformation_time: Time taken for transformation
        numerical_stability: Numerical stability metrics
    """
    original_shape: Tuple[int, ...]
    transformed_tensor: torch.Tensor
    u_matrix: torch.Tensor
    s_values: torch.Tensor
    vt_matrix: torch.Tensor
    rank_reduction: float
    compression_ratio: float
    transformation_time: float
    numerical_stability: Dict[str, float]


class SVDTransformation:
    """
    SVD-based transformation for WINA optimization.
    
    This class implements the SVD-based orthogonality protocol that transforms
    model weights to enable efficient neuron activation gating while maintaining
    computational invariance.
    """
    
    def __init__(self, config: WINAConfig):
        """
        Initialize SVD transformation with configuration.
        
        Args:
            config: WINA configuration
        """
        self.config = config
        self._transformation_cache: Dict[str, SVDTransformationResult] = {}
        
        logger.info(f"Initialized SVD transformation with rank reduction: {config.svd_rank_reduction}")
    
    def transform_weight_matrix(self, weight_matrix: torch.Tensor, 
                              layer_name: str, 
                              force_recompute: bool = False) -> SVDTransformationResult:
        """
        Transform a weight matrix using SVD-based orthogonality protocol.
        
        Args:
            weight_matrix: Input weight matrix to transform
            layer_name: Name of the layer (for caching)
            force_recompute: Force recomputation even if cached
            
        Returns:
            SVDTransformationResult containing transformation details
        """
        # Check cache first
        cache_key = f"{layer_name}_{weight_matrix.shape}_{self.config.svd_rank_reduction}"
        if not force_recompute and cache_key in self._transformation_cache:
            logger.debug(f"Using cached SVD transformation for {layer_name}")
            return self._transformation_cache[cache_key]
        
        start_time = time.time()
        
        try:
            logger.info(f"Applying SVD transformation to {layer_name} with shape {weight_matrix.shape}")
            
            # Validate input
            self._validate_input_matrix(weight_matrix)
            
            # Perform SVD decomposition
            U, S, Vt = torch.svd(weight_matrix)
            
            # Calculate target rank
            original_rank = min(weight_matrix.shape)
            target_rank = int(original_rank * self.config.svd_rank_reduction)
            target_rank = max(1, target_rank)  # Ensure at least rank 1
            
            logger.debug(f"Reducing rank from {original_rank} to {target_rank}")
            
            # Apply rank reduction
            U_reduced = U[:, :target_rank]
            S_reduced = S[:target_rank]
            Vt_reduced = Vt[:target_rank, :]
            
            # Reconstruct transformed matrix
            transformed_matrix = U_reduced @ torch.diag(S_reduced) @ Vt_reduced
            
            # Calculate metrics
            transformation_time = time.time() - start_time
            compression_ratio = target_rank / original_rank
            
            # Assess numerical stability
            try:
                numerical_stability = self._assess_numerical_stability(
                    weight_matrix, transformed_matrix, U_reduced, S_reduced, Vt_reduced
                )
            except Exception as e:
                logger.warning(f"Numerical stability assessment failed for {layer_name}: {e}")
                numerical_stability = {"assessment_failed": 1.0, "error": str(e)}
            
            result = SVDTransformationResult(
                original_shape=weight_matrix.shape,
                transformed_tensor=transformed_matrix,
                u_matrix=U_reduced,
                s_values=S_reduced,
                vt_matrix=Vt_reduced,
                rank_reduction=self.config.svd_rank_reduction,
                compression_ratio=compression_ratio,
                transformation_time=transformation_time,
                numerical_stability=numerical_stability
            )
            
            # Cache result if enabled
            if self.config.cache_transformed_weights:
                self._transformation_cache[cache_key] = result
            
            logger.info(f"SVD transformation completed for {layer_name}. "
                       f"Compression ratio: {compression_ratio:.3f}, "
                       f"Time: {transformation_time:.3f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"SVD transformation failed for {layer_name}: {e}")
            raise WINATransformationError(f"SVD transformation failed: {e}")
    
    def verify_computational_invariance(self, original_matrix: torch.Tensor, 
                                      transformed_matrix: torch.Tensor,
                                      tolerance: float = 1e-6) -> Dict[str, float]:
        """
        Verify computational invariance between original and transformed matrices.
        
        Args:
            original_matrix: Original weight matrix
            transformed_matrix: Transformed weight matrix
            tolerance: Tolerance for numerical differences
            
        Returns:
            Dictionary of invariance metrics
        """
        try:
            # Ensure matrices have the same shape for comparison
            if original_matrix.shape != transformed_matrix.shape:
                logger.warning(f"Matrix shape mismatch: {original_matrix.shape} vs {transformed_matrix.shape}")
                # For SVD transformation, the shapes should match, but if not, we can't verify invariance
                return {
                    "frobenius_norm_difference": float('inf'),
                    "relative_error": float('inf'),
                    "spectral_norm_difference": float('inf'),
                    "max_element_difference": float('inf'),
                    "invariance_maintained": False,
                    "tolerance_used": tolerance,
                    "error": "Shape mismatch between original and transformed matrices"
                }

            # Calculate various distance metrics
            frobenius_norm_diff = torch.norm(original_matrix - transformed_matrix, p='fro').item()
            original_frobenius_norm = torch.norm(original_matrix, p='fro').item()
            relative_error = frobenius_norm_diff / (original_frobenius_norm + 1e-8)

            # Calculate spectral norm difference
            spectral_norm_orig = torch.norm(original_matrix, p=2).item()
            spectral_norm_trans = torch.norm(transformed_matrix, p=2).item()
            spectral_norm_diff = abs(spectral_norm_orig - spectral_norm_trans)

            # Calculate element-wise max difference
            max_element_diff = torch.max(torch.abs(original_matrix - transformed_matrix)).item()

            # Check if invariance is maintained within tolerance
            invariance_maintained = relative_error < tolerance

            metrics = {
                "frobenius_norm_difference": frobenius_norm_diff,
                "relative_error": relative_error,
                "spectral_norm_difference": spectral_norm_diff,
                "max_element_difference": max_element_diff,
                "invariance_maintained": bool(invariance_maintained),
                "tolerance_used": tolerance
            }
            
            logger.debug(f"Computational invariance check: relative_error={relative_error:.6f}, "
                        f"tolerance={tolerance}, maintained={invariance_maintained}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Computational invariance verification failed: {e}")
            raise WINATransformationError(f"Invariance verification failed: {e}")
    
    def _validate_input_matrix(self, matrix: torch.Tensor) -> None:
        """
        Validate input matrix for SVD transformation.
        
        Args:
            matrix: Input matrix to validate
        """
        if not isinstance(matrix, torch.Tensor):
            raise WINATransformationError("Input must be a torch.Tensor")
        
        if matrix.dim() != 2:
            raise WINATransformationError(f"Input must be 2D matrix, got {matrix.dim()}D")
        
        if matrix.shape[0] == 0 or matrix.shape[1] == 0:
            raise WINATransformationError("Input matrix cannot have zero dimensions")
        
        # Check for NaN or infinite values
        if torch.isnan(matrix).any():
            raise WINATransformationError("Input matrix contains NaN values")
        
        if torch.isinf(matrix).any():
            raise WINATransformationError("Input matrix contains infinite values")
        
        # Check matrix rank
        rank = torch.linalg.matrix_rank(matrix).item()
        if rank == 0:
            raise WINATransformationError("Input matrix has zero rank")
        
        logger.debug(f"Input matrix validation passed: shape={matrix.shape}, rank={rank}")
    
    def _assess_numerical_stability(self, original: torch.Tensor, transformed: torch.Tensor,
                                  U: torch.Tensor, S: torch.Tensor, Vt: torch.Tensor) -> Dict[str, float]:
        """
        Assess numerical stability of SVD transformation.
        
        Args:
            original: Original matrix
            transformed: Transformed matrix
            U: U matrix from SVD
            S: Singular values
            Vt: V^T matrix from SVD
            
        Returns:
            Dictionary of stability metrics
        """
        try:
            # Condition number analysis
            condition_number = (S[0] / S[-1]).item() if len(S) > 1 else 1.0
            
            # Orthogonality check for U and Vt
            u_orthogonality = torch.norm(U.T @ U - torch.eye(U.shape[1])).item()
            vt_orthogonality = torch.norm(Vt @ Vt.T - torch.eye(Vt.shape[0])).item()
            
            # Singular value distribution
            s_values = S.detach().cpu().numpy()
            singular_value_ratio = s_values[0] / s_values[-1] if len(s_values) > 1 else 1.0
            
            # Reconstruction error
            reconstruction_error = torch.norm(original - transformed).item()
            relative_reconstruction_error = reconstruction_error / torch.norm(original).item()
            
            stability_metrics = {
                "condition_number": condition_number,
                "u_orthogonality_error": u_orthogonality,
                "vt_orthogonality_error": vt_orthogonality,
                "singular_value_ratio": singular_value_ratio,
                "reconstruction_error": reconstruction_error,
                "relative_reconstruction_error": relative_reconstruction_error,
                "numerical_rank": len(S),
                "effective_rank": torch.sum(S > 1e-10 * S[0]).item()
            }
            
            return stability_metrics
            
        except Exception as e:
            logger.warning(f"Numerical stability assessment failed: {e}")
            return {"assessment_failed": 1.0, "error": str(e)}
    
    def get_transformation_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about performed transformations.
        
        Returns:
            Dictionary of transformation statistics
        """
        if not self._transformation_cache:
            return {"total_transformations": 0}
        
        results = list(self._transformation_cache.values())
        
        stats = {
            "total_transformations": len(results),
            "average_compression_ratio": np.mean([r.compression_ratio for r in results]),
            "average_transformation_time": np.mean([r.transformation_time for r in results]),
            "total_transformation_time": sum([r.transformation_time for r in results]),
            "rank_reductions": [r.rank_reduction for r in results],
            "numerical_stability_summary": {
                "average_condition_number": np.mean([
                    r.numerical_stability.get("condition_number", 0) for r in results
                ]),
                "average_reconstruction_error": np.mean([
                    r.numerical_stability.get("relative_reconstruction_error", 0) for r in results
                ])
            }
        }
        
        return stats
    
    def clear_cache(self) -> None:
        """Clear transformation cache."""
        self._transformation_cache.clear()
        logger.info("SVD transformation cache cleared")


class OrthogonalityProtocol:
    """
    Orthogonality protocol for WINA transformations.
    
    This class implements the orthogonality protocol that ensures
    transformed matrices maintain their essential properties while
    enabling efficient neuron gating.
    """
    
    def __init__(self, config: WINAConfig):
        """
        Initialize orthogonality protocol.
        
        Args:
            config: WINA configuration
        """
        self.config = config
        self.svd_transformer = SVDTransformation(config)
        
        logger.info("Initialized orthogonality protocol for WINA")
    
    def apply_protocol(self, weight_matrices: Dict[str, torch.Tensor]) -> Dict[str, SVDTransformationResult]:
        """
        Apply orthogonality protocol to multiple weight matrices.
        
        Args:
            weight_matrices: Dictionary of layer names to weight matrices
            
        Returns:
            Dictionary of transformation results per layer
        """
        results = {}
        
        logger.info(f"Applying orthogonality protocol to {len(weight_matrices)} layers")
        
        for layer_name, weight_matrix in weight_matrices.items():
            try:
                result = self.svd_transformer.transform_weight_matrix(weight_matrix, layer_name)
                results[layer_name] = result
                
                # Verify computational invariance
                invariance_metrics = self.svd_transformer.verify_computational_invariance(
                    weight_matrix, result.transformed_tensor
                )
                
                if not invariance_metrics["invariance_maintained"]:
                    logger.warning(f"Computational invariance not maintained for {layer_name}: "
                                 f"relative_error={invariance_metrics['relative_error']:.6f}")
                
            except Exception as e:
                logger.error(f"Orthogonality protocol failed for {layer_name}: {e}")
                raise WINATransformationError(f"Protocol application failed for {layer_name}: {e}")
        
        logger.info("Orthogonality protocol application completed successfully")
        return results
    
    def validate_protocol_compliance(self, transformation_results: Dict[str, SVDTransformationResult]) -> Dict[str, bool]:
        """
        Validate that transformation results comply with orthogonality protocol.
        
        Args:
            transformation_results: Dictionary of transformation results
            
        Returns:
            Dictionary of compliance status per layer
        """
        compliance = {}
        
        for layer_name, result in transformation_results.items():
            try:
                # Check numerical stability
                stability = result.numerical_stability
                
                # Define compliance criteria
                criteria = {
                    "condition_number": stability.get("condition_number", float('inf')) < 1e12,
                    "orthogonality_error": (
                        stability.get("u_orthogonality_error", 1.0) < 1e-6 and
                        stability.get("vt_orthogonality_error", 1.0) < 1e-6
                    ),
                    "reconstruction_error": stability.get("relative_reconstruction_error", 1.0) < 1e-3,
                    "compression_achieved": result.compression_ratio < 1.0
                }
                
                # Overall compliance
                layer_compliant = all(criteria.values())
                compliance[layer_name] = layer_compliant
                
                if not layer_compliant:
                    logger.warning(f"Layer {layer_name} does not meet orthogonality protocol compliance: {criteria}")
                
            except Exception as e:
                logger.error(f"Compliance validation failed for {layer_name}: {e}")
                compliance[layer_name] = False
        
        return compliance
