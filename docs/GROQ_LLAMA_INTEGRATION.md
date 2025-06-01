# ACGS-PGP Groq Llama Models Integration

## Overview

This document describes the integration of three Groq-hosted Llama models into the ACGS-PGP (AI Compliance Governance System - Policy Generation Platform) for enhanced testing and research operations.

## Integrated Models

### 1. llama-3.3-70b-versatile
- **Purpose**: Large versatile model for comprehensive testing and complex reasoning tasks
- **Use Cases**: 
  - Complex constitutional analysis
  - Comprehensive policy synthesis
  - Multi-step governance reasoning
- **Configuration**: `GROQ_TESTING_MODEL_VERSATILE=llama-3.3-70b-versatile`

### 2. meta-llama/llama-4-maverick-17b-128e-instruct
- **Purpose**: Mid-size model with extended context for research operations
- **Use Cases**:
  - Research-backed governance analysis
  - Extended context constitutional interpretation
  - Long-form policy document analysis
- **Configuration**: `GROQ_TESTING_MODEL_MAVERICK=meta-llama/llama-4-maverick-17b-128e-instruct`

### 3. meta-llama/llama-4-scout-17b-16e-instruct
- **Purpose**: Efficient model for rapid testing and quick task generation
- **Use Cases**:
  - Rapid policy validation
  - Quick constitutional compliance checks
  - Fast iteration testing
- **Configuration**: `GROQ_TESTING_MODEL_SCOUT=meta-llama/llama-4-scout-17b-16e-instruct`

## Implementation Details

### AlphaEvolve GS Engine Integration

**File**: `src/alphaevolve_gs_engine/src/alphaevolve_gs_engine/services/llm_service.py`

- Added `GroqLLMService` class with OpenAI-compatible API integration
- Extended `get_llm_service()` factory function to support "groq" service type
- Implemented robust JSON parsing with fallback mechanisms
- Added comprehensive error handling and logging

**Key Features**:
- Uses Groq's OpenAI-compatible endpoint: `https://api.groq.com/openai/v1`
- Supports all three Llama models with dynamic model selection
- Implements structured output generation with JSON parsing
- Includes retry logic and graceful error handling

### GS Service Integration

**File**: `src/backend/gs_service/app/core/llm_integration.py`

- Added `GroqLLMClient` class for constitutional principle interpretation
- Extended `get_llm_client()` function to support "groq" provider
- Implemented structured interpretation with Pydantic validation
- Added constitutional prompting optimized for Llama models

**Key Features**:
- Specialized prompts for constitutional AI governance
- Structured output parsing for principle interpretation
- Confidence scoring and explanation generation
- Integration with existing LLM interpretation pipeline

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Groq API Configuration
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL_NAME=llama-3.3-70b-versatile

# Model-specific configurations
GROQ_TESTING_MODEL_VERSATILE=llama-3.3-70b-versatile
GROQ_TESTING_MODEL_MAVERICK=meta-llama/llama-4-maverick-17b-128e-instruct
GROQ_TESTING_MODEL_SCOUT=meta-llama/llama-4-scout-17b-16e-instruct

# Enable Groq models
ENABLE_GROQ_LLAMA_MODELS=true
```

### Usage Examples

#### AlphaEvolve GS Engine

```python
from alphaevolve_gs_engine.services.llm_service import get_llm_service

# Create Groq service instance
groq_service = get_llm_service("groq", {
    "api_key": "your_groq_api_key",
    "default_model": "llama-3.3-70b-versatile"
})

# Generate policy text
response = groq_service.generate_text(
    "Generate a data privacy policy rule",
    max_tokens=300,
    temperature=0.3
)

# Generate structured output
structured_response = groq_service.generate_structured_output(
    "Create a governance rule for AI transparency",
    output_format={"rule_name": "string", "conditions": ["list"]},
    model="meta-llama/llama-4-maverick-17b-128e-instruct"
)
```

#### GS Service

```python
import os
from gs_service.app.core.llm_integration import get_llm_client, LLMInterpretationInput

# Set Groq as LLM provider
os.environ["LLM_PROVIDER"] = "groq"
os.environ["GROQ_MODEL_NAME"] = "llama-3.3-70b-versatile"

# Get Groq client
client = get_llm_client()

# Interpret constitutional principle
input_data = LLMInterpretationInput(
    principle_id=1,
    principle_content="All automated decisions must be explainable and auditable."
)

result = await client.get_structured_interpretation(input_data)
```

## Testing

### Comprehensive Test Script

Run the comprehensive integration test:

```bash
python scripts/test_groq_acgs_integration.py
```

This script tests:
- AlphaEvolve GS Engine integration with all three models
- GS Service integration with structured interpretation
- Performance comparison across models
- Error handling and fallback mechanisms

### Integration Test Suite

Run the dedicated integration tests:

```bash
python tests/integration/test_groq_llm_integration.py
```

## API Endpoint Integration

The Groq models use the OpenAI-compatible API endpoint:
- **Base URL**: `https://api.groq.com/openai/v1`
- **Authentication**: Bearer token with GROQ_API_KEY
- **Request Format**: Standard OpenAI chat completions format

### Example API Call

```bash
curl https://api.groq.com/openai/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -d '{
    "model": "llama-3.3-70b-versatile",
    "messages": [{"role": "user", "content": "Generate a constitutional AI governance rule"}],
    "max_tokens": 300,
    "temperature": 0.3
  }'
```

## Error Handling and Fallback

The integration includes robust error handling:

1. **API Key Validation**: Checks for GROQ_API_KEY availability
2. **Model Fallback**: Falls back to MockLLMService if Groq is unavailable
3. **JSON Parsing**: Multiple attempts to extract valid JSON from responses
4. **Retry Logic**: Exponential backoff for transient failures
5. **Graceful Degradation**: Continues operation with mock responses if needed

## Performance Characteristics

Based on testing, the models show different performance profiles:

- **llama-3.3-70b-versatile**: Highest quality, slower response times
- **llama-4-maverick-17b-128e-instruct**: Balanced quality and speed
- **llama-4-scout-17b-16e-instruct**: Fastest response, good for rapid iteration

## Integration Benefits

1. **Model Diversity**: Three different model sizes for various use cases
2. **Cost Optimization**: Choose appropriate model based on task complexity
3. **Testing Flexibility**: Rapid testing with scout, comprehensive analysis with versatile
4. **Research Capabilities**: Extended context with maverick for research operations
5. **Fallback Options**: Multiple model options reduce single points of failure

## Future Enhancements

Potential future improvements:
- Dynamic model selection based on task complexity
- Load balancing across multiple models
- Performance monitoring and optimization
- Custom fine-tuning for ACGS-PGP specific tasks
- Integration with additional Groq models as they become available

## Troubleshooting

Common issues and solutions:

1. **API Key Issues**: Ensure GROQ_API_KEY is set correctly
2. **Model Availability**: Check Groq's model availability and quotas
3. **Network Connectivity**: Verify access to api.groq.com
4. **JSON Parsing**: The integration includes fallback mechanisms for malformed JSON
5. **Rate Limiting**: Implement appropriate delays between requests if needed

## Conclusion

The Groq Llama models integration provides ACGS-PGP with powerful, diverse LLM options for testing and research operations. The three models offer different trade-offs between quality, speed, and context length, enabling optimal model selection based on specific use cases within the governance framework.
