"""
llm_service.py

This module provides an interface to interact with Large Language Models (LLMs)
for tasks such as generating policy suggestions, summarizing text, or offering
explanations. It's designed to be a pluggable component, allowing different
LLM backends (e.g., OpenAI, Anthropic, local models) to be used.

Classes:
    LLMService: Base class for LLM interactions.
    OpenAILLMService: An implementation using OpenAI's API.
    MockLLMService: A mock implementation for testing and development.

Functions:
    get_llm_service: Factory function to get an appropriate LLM service instance.
"""

import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Literal

# Placeholder for actual LLM client libraries like 'openai'
# Ensure these are added to requirements.txt if you implement a specific service
try:
    import openai
except ImportError:
    openai = None # Allows the module to be imported even if openai is not installed

from dotenv import load_dotenv

from alphaevolve_gs_engine.utils.logging_utils import setup_logger

# Load environment variables from .env file
load_dotenv()

logger = setup_logger(__name__)

class LLMService(ABC):
    """
    Abstract base class for Large Language Model services.
    Defines the interface for interacting with LLMs.
    """

    @abstractmethod
    def generate_text(self, 
                      prompt: str, 
                      max_tokens: int = 1024, 
                      temperature: float = 0.7,
                      model: Optional[str] = None) -> str:
        """
        Generates text based on a given prompt.

        Args:
            prompt (str): The input prompt for the LLM.
            max_tokens (int): Maximum number of tokens to generate.
            temperature (float): Sampling temperature (creativity).
            model (Optional[str]): Specific model identifier to use.

        Returns:
            str: The LLM-generated text.
        
        Raises:
            NotImplementedError: If the method is not implemented by a subclass.
            Exception: For LLM API errors or other issues.
        """
        pass

    @abstractmethod
    def generate_structured_output(self, 
                                   prompt: str, 
                                   output_format: Dict[str, Any],
                                   max_tokens: int = 2048,
                                   temperature: float = 0.5,
                                   model: Optional[str] = None) -> Dict[str, Any]:
        """
        Generates structured output (e.g., JSON) based on a prompt and a desired format.

        Args:
            prompt (str): The input prompt.
            output_format (Dict[str, Any]): A dictionary describing the desired output structure.
                                            Example: {"name": "string", "value": "integer"}
            max_tokens (int): Maximum number of tokens for the generation.
            temperature (float): Sampling temperature.
            model (Optional[str]): Specific model identifier.
            
        Returns:
            Dict[str, Any]: The LLM-generated structured data.

        Raises:
            NotImplementedError: If the method is not implemented by a subclass.
            Exception: For LLM API errors or parsing issues.
        """
        pass

class OpenAILLMService(LLMService):
    """
    LLM Service implementation using the OpenAI API.
    """
    def __init__(self, api_key: Optional[str] = None, default_model: str = "gpt-3.5-turbo"):
        if openai is None:
            raise ImportError("OpenAI Python client is not installed. Please install it with 'pip install openai'.")
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable or pass it directly.")
        
        openai.api_key = self.api_key
        self.default_model = default_model
        logger.info(f"OpenAILLMService initialized with model: {self.default_model}")

    def generate_text(self, 
                      prompt: str, 
                      max_tokens: int = 1024, 
                      temperature: float = 0.7,
                      model: Optional[str] = None) -> str:
        """
        Generates text using the OpenAI API.
        """
        selected_model = model or self.default_model
        try:
            logger.debug(f"Sending prompt to OpenAI model {selected_model}: {prompt[:100]}...") # Log snippet
            # Using the new OpenAI client syntax (v1.0.0+)
            response = openai.chat.completions.create(
                model=selected_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                n=1,
                stop=None
            )
            # The response structure for chat completions:
            # response.choices[0].message.content
            generated_text = response.choices[0].message.content.strip()
            logger.info(f"Successfully received response from OpenAI model {selected_model}.")
            return generated_text
        except Exception as e:
            logger.error(f"OpenAI API error during text generation: {e}", exc_info=True)
            raise

    def generate_structured_output(self, 
                                   prompt: str, 
                                   output_format: Dict[str, Any], # This is a conceptual guide for the prompt
                                   max_tokens: int = 2048,
                                   temperature: float = 0.5,
                                   model: Optional[str] = None) -> Dict[str, Any]:
        """
        Generates structured JSON output using OpenAI's function calling or newer JSON mode.
        Note: For reliable JSON, use models that explicitly support JSON mode (e.g., gpt-3.5-turbo-1106+).
        """
        selected_model = model or self.default_model
        
        # Construct a prompt that strongly asks for JSON output matching the format
        # This is a simplified example. More complex prompting might be needed.
        json_prompt = (
            f"{prompt}\n\n"
            f"Please provide the output in JSON format. The JSON object should strictly adhere to the following structure:\n"
            f"{output_format}\n"
            f"Ensure all string values are properly escaped."
        )
        
        try:
            logger.debug(f"Sending structured output prompt to OpenAI model {selected_model}: {json_prompt[:200]}...")
            
            # For newer models that support JSON mode (e.g., gpt-3.5-turbo-1106, gpt-4-1106-preview)
            # Models known to support JSON mode - update this list as new models are released
            json_mode_models = {"gpt-3.5-turbo-1106", "gpt-4-1106-preview", "gpt-4-turbo-preview"}
            supports_json_mode = any(model in selected_model for model in json_mode_models)
            
            if supports_json_mode:
                response = openai.chat.completions.create(
                    model=selected_model,
                    messages=[{"role": "user", "content": json_prompt}],
                    response_format={"type": "json_object"}, # Enable JSON mode
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                generated_content = response.choices[0].message.content
            else: # Fallback for older models - less reliable for JSON
                response = openai.chat.completions.create(
                    model=selected_model,
                    messages=[{"role": "user", "content": json_prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                generated_content = response.choices[0].message.content

            # Attempt to parse the JSON string
            import json
            try:
                structured_data = json.loads(generated_content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response from LLM: {e}. Response was: {generated_content[:500]}", exc_info=True)
                raise ValueError(f"LLM did not return valid JSON. Content: {generated_content[:500]}") from e

            logger.info(f"Successfully received and parsed structured response from OpenAI model {selected_model}.")
            return structured_data
        except Exception as e:
            logger.error(f"OpenAI API error during structured output generation: {e}", exc_info=True)
            raise


class MockLLMService(LLMService):
    """
    Mock LLM service for testing and development purposes.
    Returns predefined responses without actual LLM calls.
    """
    def __init__(self, delay: float = 0.1):
        self.delay = delay # Simulate network latency
        logger.info("MockLLMService initialized.")

    def generate_text(self, 
                      prompt: str, 
                      max_tokens: int = 1024, 
                      temperature: float = 0.7,
                      model: Optional[str] = None) -> str:
        import time
        time.sleep(self.delay)
        logger.debug(f"MockLLMService received prompt (model: {model}): {prompt[:100]}...")
        response = f"Mock response to: '{prompt[:50]}...'. Max tokens: {max_tokens}, Temp: {temperature}."
        if "Rego code" in prompt:
            response = """
            package mock.policy
            default allow = false
            allow { input.user.role == "admin" }
            # This is a mock Rego policy.
            """
        logger.info("MockLLMService generated text response.")
        return response

    def generate_structured_output(self, 
                                   prompt: str, 
                                   output_format: Dict[str, Any],
                                   max_tokens: int = 2048,
                                   temperature: float = 0.5,
                                   model: Optional[str] = None) -> Dict[str, Any]:
        import time
        time.sleep(self.delay)
        logger.debug(f"MockLLMService received structured prompt (model: {model}): {prompt[:100]}...")
        
        # Generate a mock response based on the output_format keys
        mock_data: Dict[str, Any] = {}
        for key, value_type in output_format.items():
            if value_type == "string":
                mock_data[key] = f"mock_{key}_value"
            elif value_type == "integer":
                mock_data[key] = 123
            elif value_type == "boolean":
                mock_data[key] = True
            elif isinstance(value_type, list) and len(value_type) > 0: # list of strings
                 mock_data[key] = [f"mock_list_item_{i}" for i in range(2)]
            else:
                mock_data[key] = f"unsupported_mock_type_for_{key}"

        if "policy_suggestion" in prompt.lower(): # Specific mock for policy suggestions
            mock_data = {
                "suggested_policy_code": "package mock.suggestion\ndefault allow = true",
                "explanation": "This mock policy allows all actions for testing.",
                "confidence_score": 0.95
            }
        
        logger.info("MockLLMService generated structured response.")
        return mock_data


class GroqLLMService(LLMService):
    """
    LLM Service implementation using the Groq API (OpenAI-compatible endpoint).
    """
    def __init__(self, api_key: Optional[str] = None, default_model: str = "llama-3.3-70b-versatile"):
        if openai is None:
            raise ImportError("OpenAI Python client is not installed. Please install it with 'pip install openai'.")

        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Groq API key not found. Set GROQ_API_KEY environment variable or pass it directly.")

        # Use OpenAI client with Groq's OpenAI-compatible endpoint
        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        self.default_model = default_model
        logger.info(f"GroqLLMService initialized with model: {self.default_model}")

    def generate_text(self,
                      prompt: str,
                      max_tokens: int = 1024,
                      temperature: float = 0.7,
                      model: Optional[str] = None) -> str:
        """
        Generates text using the Groq API.
        """
        selected_model = model or self.default_model
        try:
            logger.debug(f"Sending prompt to Groq model {selected_model}: {prompt[:100]}...")
            response = self.client.chat.completions.create(
                model=selected_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                n=1,
                stop=None
            )
            generated_text = response.choices[0].message.content
            logger.info(f"GroqLLMService generated text response for model {selected_model}.")
            return generated_text
        except Exception as e:
            logger.error(f"GroqLLMService error for model {selected_model}: {e}")
            raise

    def generate_structured_output(self,
                                   prompt: str,
                                   output_format: Dict[str, Any],
                                   max_tokens: int = 2048,
                                   temperature: float = 0.5,
                                   model: Optional[str] = None) -> Dict[str, Any]:
        """
        Generates structured JSON output using Groq API.
        Note: Groq models may not support JSON mode, so we rely on prompt engineering.
        """
        selected_model = model or self.default_model

        # Create a JSON-focused prompt
        json_prompt = f"""
{prompt}

Please respond with valid JSON only, following this format:
{json.dumps(output_format, indent=2)}

Ensure your response is valid JSON that can be parsed.
"""

        try:
            logger.debug(f"Sending structured output prompt to Groq model {selected_model}: {json_prompt[:200]}...")

            response = self.client.chat.completions.create(
                model=selected_model,
                messages=[{"role": "user", "content": json_prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            generated_content = response.choices[0].message.content

            # Parse the JSON response
            try:
                parsed_json = json.loads(generated_content)
                logger.info(f"GroqLLMService generated structured response for model {selected_model}.")
                return parsed_json
            except json.JSONDecodeError as json_err:
                logger.warning(f"GroqLLMService: Failed to parse JSON from model {selected_model}. Attempting to extract JSON...")
                # Try to extract JSON from the response if it's wrapped in text
                import re
                json_match = re.search(r'\{.*\}', generated_content, re.DOTALL)
                if json_match:
                    try:
                        parsed_json = json.loads(json_match.group())
                        return parsed_json
                    except json.JSONDecodeError:
                        pass

                # If all else fails, return a structured error
                logger.error(f"GroqLLMService: Could not extract valid JSON from response: {generated_content}")
                return {"error": "Failed to generate valid JSON", "raw_response": generated_content}

        except Exception as e:
            logger.error(f"GroqLLMService structured output error for model {selected_model}: {e}")
            raise


def get_llm_service(service_type: Literal["openai", "groq", "mock"] = "mock",
                    config: Optional[Dict[str, Any]] = None) -> LLMService:
    """
    Factory function to get an instance of an LLM service.

    Args:
        service_type (str): Type of LLM service ('openai', 'groq', 'mock').
                            Defaults to 'mock' if not specified or if API keys are missing.
        config (Dict[str, Any], optional): Configuration for the service.
            For 'openai': {"api_key": "your_key", "default_model": "gpt-4"}
            For 'groq': {"api_key": "your_key", "default_model": "llama-3.3-70b-versatile"}
            For 'mock': {"delay": 0.05}

    Returns:
        LLMService: An instance of the requested LLM service.

    Raises:
        ValueError: If an unsupported service type is requested.
    """
    config = config or {}

    # Default to mock if API keys are not available
    effective_service_type = service_type
    if service_type == "openai" and not (os.getenv("OPENAI_API_KEY") or config.get("api_key")):
        logger.warning("OpenAI service requested, but no API key found. Falling back to MockLLMService.")
        effective_service_type = "mock"
    elif service_type == "groq" and not (os.getenv("GROQ_API_KEY") or config.get("api_key")):
        logger.warning("Groq service requested, but no API key found. Falling back to MockLLMService.")
        effective_service_type = "mock"

    if effective_service_type == "openai":
        if openai is None:
            logger.error("OpenAI client library not installed. Falling back to MockLLMService.")
            return MockLLMService(**config.get("mock_config", {}))
        return OpenAILLMService(api_key=config.get("api_key"),
                                default_model=config.get("default_model", "gpt-3.5-turbo"))
    elif effective_service_type == "groq":
        if openai is None:
            logger.error("OpenAI client library not installed (required for Groq). Falling back to MockLLMService.")
            return MockLLMService(**config.get("mock_config", {}))
        return GroqLLMService(api_key=config.get("api_key"),
                              default_model=config.get("default_model", "llama-3.3-70b-versatile"))
    elif effective_service_type == "mock":
        return MockLLMService(**config.get("mock_config", {})) # e.g. config={"mock_config": {"delay": 0.2}}
    else:
        raise ValueError(f"Unsupported LLM service type: {service_type}")

# Example Usage
if __name__ == "__main__":
    # Load .env file if it exists, useful for local development
    # For this example, assume OPENAI_API_KEY is set in .env or environment
    
    # --- Mock Service Example ---
    print("--- Using Mock LLM Service ---")
    mock_service = get_llm_service("mock")
    
    mock_text_prompt = "Explain the concept of zero-trust security in simple terms."
    mock_text_response = mock_service.generate_text(mock_text_prompt)
    print(f"Mock Text Prompt: {mock_text_prompt}")
    print(f"Mock Text Response: {mock_text_response}\n")

    mock_structured_prompt = "Generate a user profile for 'John Doe'."
    mock_format = {"name": "string", "age": "integer", "is_active": "boolean", "roles": ["string"]}
    mock_structured_response = mock_service.generate_structured_output(mock_structured_prompt, mock_format)
    print(f"Mock Structured Prompt: {mock_structured_prompt}")
    print(f"Mock Structured Response: {mock_structured_response}\n")

    # --- OpenAI Service Example (requires OPENAI_API_KEY) ---
    print("--- Using OpenAI LLM Service ---")
    # This will try to use OpenAI, but fall back to Mock if key is not found or library not installed
    # To force OpenAI and see an error if not configured: get_llm_service("openai", {"api_key": "sk-..."})
    openai_service_instance = get_llm_service("openai") # Will be Mock if key is missing

    # --- Groq Service Example (requires GROQ_API_KEY) ---
    print("\n--- Using Groq LLM Service ---")
    # This will try to use Groq, but fall back to Mock if key is not found
    groq_service_instance = get_llm_service("groq") # Will be Mock if key is missing

    if isinstance(openai_service_instance, OpenAILLMService):
        print("OpenAI Service is configured.")
        try:
            # Simple text generation
            text_prompt = "What is the capital of France?"
            text_response = openai_service_instance.generate_text(text_prompt, max_tokens=50)
            print(f"OpenAI Text Prompt: {text_prompt}")
            print(f"OpenAI Text Response: {text_response}\n")

            # Structured output (JSON)
            # Use a model that supports JSON mode for best results, e.g., "gpt-3.5-turbo-1106"
            # Ensure your account has access to the model you specify.
            # If using an older model, the JSON parsing might be less reliable.
            structured_prompt = "Generate a JSON object representing a book with title, author, and publication_year."
            # Define the desired JSON structure for the LLM.
            # This is more of a guide for the prompt, actual validation is separate.
            json_format_guide = {"title": "string", "author": "string", "publication_year": "integer"}
            
            # Test with a model known for JSON mode if available
            # Otherwise, it uses the default_model which might be less reliable for JSON
            json_model = "gpt-3.5-turbo-1106" # or "gpt-4-1106-preview"
            try:
                structured_response = openai_service_instance.generate_structured_output(
                    structured_prompt, 
                    output_format=json_format_guide,
                    model=json_model 
                )
                print(f"OpenAI Structured Prompt: {structured_prompt}")
                print(f"OpenAI Structured Response (model: {json_model}): {structured_response}")
            except Exception as e:
                print(f"Error during OpenAI structured output with {json_model}: {e}")
                print("Attempting with default model for structured output...")
                try:
                    structured_response_default = openai_service_instance.generate_structured_output(
                        structured_prompt,
                        output_format=json_format_guide
                        # model=openai_service_instance.default_model # Implicitly uses default
                    )
                    print(f"OpenAI Structured Response (model: {openai_service_instance.default_model}): {structured_response_default}")
                except Exception as e_default:
                     print(f"Error during OpenAI structured output with default model: {e_default}")

        except Exception as e:
            print(f"An error occurred while using OpenAI service: {e}")
            print("Please ensure your OPENAI_API_KEY is correctly set and valid,")
            print("and that the 'openai' library is installed ('pip install openai').")
    elif isinstance(openai_service_instance, MockLLMService):
         print("OpenAI Service not configured (API key likely missing or 'openai' library not installed).")
         print("The example proceeded with the MockLLMService.")
    else:
        print("Could not determine LLM service type for the OpenAI example part.")

    # Test Groq service if configured
    if isinstance(groq_service_instance, GroqLLMService):
        print("\nGroq Service is configured.")
        try:
            # Simple text generation with Groq
            groq_text_prompt = "What are the key principles of AI governance?"
            groq_text_response = groq_service_instance.generate_text(groq_text_prompt, max_tokens=100)
            print(f"Groq Text Prompt: {groq_text_prompt}")
            print(f"Groq Text Response: {groq_text_response}\n")

            # Structured output with Groq
            groq_structured_prompt = "Generate a policy rule for data privacy compliance."
            groq_format_guide = {
                "rule_name": "string",
                "description": "string",
                "conditions": ["list of conditions"],
                "actions": ["list of actions"]
            }

            # Test with different Groq models
            groq_models = [
                "llama-3.3-70b-versatile",
                "meta-llama/llama-4-maverick-17b-128e-instruct",
                "meta-llama/llama-4-scout-17b-16e-instruct"
            ]

            for model in groq_models:
                try:
                    print(f"Testing Groq model: {model}")
                    groq_structured_response = groq_service_instance.generate_structured_output(
                        groq_structured_prompt,
                        output_format=groq_format_guide,
                        model=model
                    )
                    print(f"Groq Structured Response ({model}): {groq_structured_response}\n")
                except Exception as model_error:
                    print(f"Error with Groq model {model}: {model_error}")

        except Exception as e:
            print(f"An error occurred while using Groq service: {e}")
            print("Please ensure your GROQ_API_KEY is correctly set and valid.")
    elif isinstance(groq_service_instance, MockLLMService):
        print("\nGroq Service not configured (API key likely missing).")
        print("The example proceeded with the MockLLMService.")
    else:
        print("\nCould not determine LLM service type for the Groq example part.")
