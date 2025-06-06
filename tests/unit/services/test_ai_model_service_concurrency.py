import asyncio
import pytest

# Import AIModelService utilities
try:
    from shared.ai_model_service import (
        get_ai_model_service,
        reset_ai_model_service,
    )
except ImportError:  # fallback if path not set
    from src.backend.shared.ai_model_service import (
        get_ai_model_service,
        reset_ai_model_service,
    )


@pytest.mark.asyncio
async def test_concurrent_generate_text_does_not_mutate_config():
    await reset_ai_model_service()
    service = await get_ai_model_service()

    original_max_tokens = service.models["primary"].max_tokens
    original_temperature = service.models["primary"].temperature

    async def call_one():
        return await service.generate_text(
            "one", max_tokens=50, temperature=0.9
        )

    async def call_two():
        return await service.generate_text(
            "two", max_tokens=60, temperature=0.1
        )

    await asyncio.gather(call_one(), call_two())

    assert service.models["primary"].max_tokens == original_max_tokens
    assert service.models["primary"].temperature == original_temperature

@pytest.mark.asyncio
async def test_concurrent_generation_federated_does_not_mutate_config():
    from src.backend.federated_service.shared.ai_model_service import (
        get_ai_model_service as get_fed_service,
        reset_ai_model_service as reset_fed_service,
    )

    await reset_fed_service()
    service = await get_fed_service()

    original_max_tokens = service.models["primary"].max_tokens
    original_temperature = service.models["primary"].temperature

    async def call_one():
        return await service.generate_text(
            "f-one", max_tokens=40, temperature=0.8
        )

    async def call_two():
        return await service.generate_text(
            "f-two", max_tokens=70, temperature=0.2
        )

    await asyncio.gather(call_one(), call_two())

    assert service.models["primary"].max_tokens == original_max_tokens
    assert service.models["primary"].temperature == original_temperature
