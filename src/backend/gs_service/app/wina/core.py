import math
from typing import List, Dict, Tuple
import numpy as np # Added for type hinting and example matrix

from .models import (
    NeuronActivationInput,
    AnalyzedNeuronActivation,
    WINAWeightOutput
)
from .svd_utils import apply_svd_transformation # Added SVD import

async def analyze_neuron_activations(
    activation_input: NeuronActivationInput
) -> List[AnalyzedNeuronActivation]:
    """
    Analyzes raw neuron activations to compute summary statistics.

    Args:
        activation_input: Raw neuron activation data.

    Returns:
        A list of analyzed neuron activation objects, each containing
        statistics like mean and variance for a neuron.
    """
    analyzed_activations: List[AnalyzedNeuronActivation] = []

    for neuron_id, activations in activation_input.activations.items():
        if not activations:
            # Handle cases with no activations for a neuron, if necessary
            # For now, we might skip or assign default values
            mean_activation = 0.0
            variance_activation = 0.0
        else:
            n = len(activations)
            mean_activation = sum(activations) / n if n > 0 else 0.0
            
            # Calculate variance
            if n > 1:
                variance_activation = sum((x - mean_activation) ** 2 for x in activations) / (n - 1)
            else:
                variance_activation = 0.0 # Variance is undefined for a single data point or no data

        analyzed_activations.append(
            AnalyzedNeuronActivation(
                neuron_id=neuron_id,
                mean_activation=mean_activation,
                variance_activation=variance_activation,
                raw_activations_sample=activations[:10] # Store a small sample
            )
        )
    return analyzed_activations

async def calculate_wina_weights(
    analyzed_activations: List[AnalyzedNeuronActivation],
    # Alternatively, could take NeuronActivationInput directly
    # activation_input: NeuronActivationInput 
) -> WINAWeightOutput:
    """
    Calculates WINA (Weight Informed Neuron Activation) weights based on
    analyzed neuron activations.

    Args:
        analyzed_activations: A list of analyzed neuron activation objects.
        
    Returns:
        A WINAWeightOutput object containing the calculated weights for each neuron.

    Note:
        The current WINA weight calculation is a placeholder.
        It assigns weights proportional to the mean activation.
        This should be replaced with the actual WINA algorithm logic.
    """
    weights: Dict[str, float] = {}

    # Placeholder WINA calculation: weight is proportional to mean activation.
    # This is a simplified assumption and should be replaced with the actual WINA formula.
    # For example, it could involve normalization or more complex relationships
    # with variance, activation frequency, etc.
    
    # Sum of all mean activations for normalization (optional, depends on WINA formula)
    # total_mean_activation = sum(ana.mean_activation for ana in analyzed_activations if ana.mean_activation > 0)

    for analysis in analyzed_activations:
        # Basic placeholder: weight = mean_activation
        # A more refined placeholder might involve normalization or scaling.
        # Example: if total_mean_activation > 0:
        #     weights[analysis.neuron_id] = analysis.mean_activation / total_mean_activation
        # else:
        #     weights[analysis.neuron_id] = 0.0
        
        # For now, a direct assignment or a simple scaling factor.
        # Let's assume WINA weights are directly related to their positive mean activation.
        # Negative or zero activations might imply less importance in some contexts.
        if analysis.mean_activation > 0:
            weights[analysis.neuron_id] = analysis.mean_activation 
        else:
            weights[analysis.neuron_id] = 0.0 # Assign zero weight if mean activation is not positive

        # Further considerations for a real WINA algorithm:
        # - How does variance play a role? Higher variance might mean less stable/reliable.
        # - Are there thresholds for activation?
        # - How are weights normalized across a layer or the network?
        # - Interaction with SVD and gating mechanisms (for later subtasks).

    return WINAWeightOutput(
        weights=weights,
        metadata={"calculation_method": "placeholder_mean_proportional"}
    )

# Example usage (for testing or integration later)
async def process_neuron_data_for_wina(
    activation_input: NeuronActivationInput
) -> WINAWeightOutput:
    """
    Orchestrates the analysis of neuron activations and calculation of WINA weights.
    """
    analyzed_data = await analyze_neuron_activations(activation_input)
    wina_weights = await calculate_wina_weights(analyzed_data)
    return wina_weights

async def transform_matrix_with_svd(
    matrix: np.ndarray,
    k: int
) -> np.ndarray:
    """
    Applies SVD-based transformation to a given matrix.

    This is a wrapper function to demonstrate calling the SVD utility
    from within the WINA core logic.

    Args:
        matrix: The input matrix (e.g., W_k, W_gate from an LLM layer).
        k: The number of singular values/vectors to retain.

    Returns:
        The transformed matrix with reduced dimensionality.
    """
    if not isinstance(matrix, np.ndarray):
        # In a real scenario, matrix loading/retrieval would happen here or be passed in.
        # For this example, we expect a NumPy array.
        raise TypeError("Input 'matrix' must be a NumPy array.")
    
    # The actual SVD transformation is not async, but we keep the function
    # async to align with FastAPI patterns if it were to involve I/O
    # for loading matrices in a real application.
    # For pure computation, it could be synchronous.
    transformed_matrix = apply_svd_transformation(matrix, k)
    return transformed_matrix

# Example of how transform_matrix_with_svd might be called (for testing/demonstration)
# async def example_svd_usage():
#     # This would typically be a weight matrix from an LLM
#     example_weight_matrix = np.random.rand(100, 50) # e.g., 100 features, 50 neurons
#     num_components_to_keep = 10
#
#     print(f"Original matrix shape: {example_weight_matrix.shape}")
#
#     reduced_matrix = await transform_matrix_with_svd(
#         example_weight_matrix,
#         num_components_to_keep
#     )
#
#     print(f"Reduced matrix shape: {reduced_matrix.shape}")
#     # The shape will be the same, but the rank is reduced.
#     # Further steps would involve using this reduced_matrix or its components
#     # in the WINA algorithm.
#
# if __name__ == '__main__':
#     import asyncio
#     asyncio.run(example_svd_usage())