import pytest
from typing import Dict

from src.backend.gs_service.app.wina.models import WINAWeightOutput, GatingThresholdConfig, GatingDecision
from src.backend.gs_service.app.wina.gating import determine_gating_decision

@pytest.mark.asyncio
async def test_determine_gating_decision_basic_scenario():
    """
    Test basic gating decision based on a simple threshold.
    """
    wina_weights_data = {
        "weights": {
            "neuron_1": 0.8,
            "neuron_2": 0.3,
            "neuron_3": 0.9,
            "neuron_4": 0.1,
        },
        "metadata": {"calculation_method": "test_method"}
    }
    wina_weights = WINAWeightOutput(**wina_weights_data)

    gating_config_data = {
        "threshold": 0.5,
        "default_gating_state": False
    }
    gating_config = GatingThresholdConfig(**gating_config_data)

    expected_gating_mask = {
        "neuron_1": True,   # 0.8 > 0.5
        "neuron_2": False,  # 0.3 < 0.5
        "neuron_3": True,   # 0.9 > 0.5
        "neuron_4": False,  # 0.1 < 0.5
    }

    gating_decision = await determine_gating_decision(wina_weights, gating_config)

    assert isinstance(gating_decision, GatingDecision)
    assert gating_decision.gating_mask == expected_gating_mask
    assert gating_decision.metadata["gating_threshold_used"] == 0.5
    assert gating_decision.metadata["num_components_activated"] == 2
    assert gating_decision.metadata["num_components_processed"] == 4
    assert gating_decision.metadata["wina_calculation_method"] == "test_method"

@pytest.mark.asyncio
async def test_determine_gating_decision_all_active():
    """
    Test scenario where all neurons/components are activated.
    """
    wina_weights_data = {
        "weights": {
            "comp_A": 0.9,
            "comp_B": 0.7,
        },
        "metadata": {}
    }
    wina_weights = WINAWeightOutput(**wina_weights_data)

    gating_config_data = {
        "threshold": 0.6,
        "default_gating_state": False
    }
    gating_config = GatingThresholdConfig(**gating_config_data)

    expected_gating_mask = {
        "comp_A": True,
        "comp_B": True,
    }

    gating_decision = await determine_gating_decision(wina_weights, gating_config)

    assert gating_decision.gating_mask == expected_gating_mask
    assert gating_decision.metadata["num_components_activated"] == 2

@pytest.mark.asyncio
async def test_determine_gating_decision_all_inactive():
    """
    Test scenario where all neurons/components are inactive.
    """
    wina_weights_data = {
        "weights": {
            "neuron_x": 0.1,
            "neuron_y": 0.05,
        }
    }
    wina_weights = WINAWeightOutput(**wina_weights_data)

    gating_config_data = {
        "threshold": 0.2,
        "default_gating_state": True # Note: default state won't apply here as weights exist
    }
    gating_config = GatingThresholdConfig(**gating_config_data)

    expected_gating_mask = {
        "neuron_x": False,
        "neuron_y": False,
    }

    gating_decision = await determine_gating_decision(wina_weights, gating_config)

    assert gating_decision.gating_mask == expected_gating_mask
    assert gating_decision.metadata["num_components_activated"] == 0

@pytest.mark.asyncio
async def test_determine_gating_decision_empty_weights():
    """
    Test scenario with empty WINA weights.
    """
    wina_weights_data: Dict[str, Dict] = {
        "weights": {},
        "metadata": {"info": "no_weights_calculated"}
    }
    wina_weights = WINAWeightOutput(**wina_weights_data)

    gating_config_data = {
        "threshold": 0.5,
        "default_gating_state": False
    }
    gating_config = GatingThresholdConfig(**gating_config_data)

    expected_gating_mask = {}

    gating_decision = await determine_gating_decision(wina_weights, gating_config)

    assert gating_decision.gating_mask == expected_gating_mask
    assert gating_decision.metadata["num_components_activated"] == 0
    assert gating_decision.metadata["num_components_processed"] == 0
    assert gating_decision.metadata["wina_calculation_method"] == "unknown" # Default from function

# Placeholder for future tests involving default_gating_state if logic changes
# @pytest.mark.asyncio
# async def test_determine_gating_decision_with_default_state_logic():
#     """
#     Test scenario where default_gating_state might be applied.
#     This test is a placeholder as current logic in determine_gating_decision
#     primarily relies on wina_weights.weights keys. If logic is expanded to
#     use metadata for a full list of neurons, this test would be relevant.
#     """
#     wina_weights_data = {
#         "weights": {
#             "neuron_1": 0.6, # Active
#         },
#         "metadata": {
#             "all_neuron_ids": ["neuron_1", "neuron_2_missing_weight"],
#             "calculation_method": "default_test"
#         }
#     }
#     wina_weights = WINAWeightOutput(**wina_weights_data)

#     gating_config_data = {
#         "threshold": 0.5,
#         "default_gating_state": True # neuron_2_missing_weight should become True
#     }
#     gating_config = GatingThresholdConfig(**gating_config_data)

#     # Assuming determine_gating_decision is updated to use all_neuron_ids from metadata
#     # expected_gating_mask = {
#     #     "neuron_1": True,
#     #     "neuron_2_missing_weight": True,
#     # }
#     # gating_decision = await determine_gating_decision(wina_weights, gating_config)
#     # assert gating_decision.gating_mask == expected_gating_mask
#     # assert gating_decision.metadata["num_components_activated"] == 2
#     pass # Keep as placeholder until logic in gating.py is expanded