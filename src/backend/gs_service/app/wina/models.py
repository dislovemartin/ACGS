from typing import List, Dict, Any
from pydantic import BaseModel, Field

class NeuronActivationInput(BaseModel):
    """
    Represents the raw activation data for a set of neurons.
    Activations are expected to be a dictionary where keys are neuron identifiers
    (e.g., layer_index_neuron_index) and values are lists of their activation values
    observed over a period or a set of inputs.
    """
    activations: Dict[str, List[float]] = Field(
        ...,
        description="Dictionary of neuron activations. Keys are neuron IDs, values are lists of activation strengths."
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional metadata, e.g., layer name, timestamp."
    )

class AnalyzedNeuronActivation(BaseModel):
    """
    Represents the analyzed neuron activations, typically containing summary statistics.
    """
    neuron_id: str = Field(..., description="Identifier for the neuron.")
    mean_activation: float = Field(..., description="Mean activation value for the neuron.")
    variance_activation: float = Field(..., description="Variance of activation values for the neuron.")
    # Add other relevant metrics as needed, e.g., max, min, activation frequency
    raw_activations_sample: List[float] = Field(
        default_factory=list,
        description="A sample of raw activation values, for reference."
    )

class WINAWeightOutput(BaseModel):
    """
    Represents the calculated WINA weights for a set of neurons.
    """
    weights: Dict[str, float] = Field(
        ...,
        description="Dictionary of WINA weights. Keys are neuron IDs, values are the calculated weights."
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional metadata, e.g., calculation method, timestamp."
    )

class BatchWINAWeightOutput(BaseModel):
    """
    Represents WINA weights for multiple sets of neurons, possibly from different layers or contexts.
    """
    batch_weights: List[WINAWeightOutput] = Field(
        ...,
        description="A list of WINAWeightOutput objects, each corresponding to a set of neurons."
    )
    overall_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional metadata for the entire batch."
    )
class GatingThresholdConfig(BaseModel):
    """
    Configuration for the gating mechanism based on a simple threshold.
    """
    threshold: float = Field(
        ...,
        description="Activation threshold. Neurons/components with WINA weights above this threshold will be considered active."
    )
    default_gating_state: bool = Field(
        default=False,
        description="Default state for neurons if not explicitly decided (e.g. if weights are missing). False means inactive."
    )

class GatingDecision(BaseModel):
    """
    Represents the outcome of the gating mechanism.
    Indicates which neurons/components are active or inactive.
    """
    gating_mask: Dict[str, bool] = Field(
        ...,
        description="A dictionary where keys are neuron/component IDs and values are booleans (True for active, False for inactive)."
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional metadata, e.g., gating configuration used, timestamp."
    )