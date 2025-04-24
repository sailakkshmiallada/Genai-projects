"""
Assistant module for handling API interactions with language models.

This module provides a class for managing API calls to language models
with proper error handling and response formatting.
"""

import os
import json
import logging
from typing import Optional, Literal, Dict, Type, Any, Union, cast

from openai import OpenAI
from openai.types.chat import ChatCompletion
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError

from .utils.logger import get_logger

# Configure logging
logger = get_logger(__name__)

class AssistantError(Exception):
    """Base exception for assistant errors"""
    pass

class APIError(AssistantError):
    """Raised when API calls fail"""
    pass

class ValidationError(AssistantError):
    """Raised when validation fails"""
    pass

class AssistantConfig(BaseModel):
    """Configuration model for Assistant class."""
    
    api_key: str = Field(..., description="API key for authentication")
    base_url: str = Field(..., description="Base URL for API endpoint")
    model: str = Field(..., description="Default model to use")

class AssistantResponse(BaseModel):
    """Standardized response model for assistant outputs."""
    
    content: str = Field(..., description="Generated content")
    model: str = Field(..., description="Model used for generation")
    usage: Dict[str, int] = Field(..., description="Token usage statistics")

class Assistant:
    """
    A class to handle interactions with language model APIs.
    
    Attributes:
        client (OpenAI): OpenAI client instance
        model (str): Default model identifier
    """

    def __init__(self) -> None:
        """Initialize the Assistant with configuration from environment variables."""
        logger.info("Initializing Assistant")
        try:
            load_dotenv()
            logger.debug("Environment variables loaded")
            
            # Check for required environment variables
            api_key = os.getenv("API_KEY", "")
            base_url = os.getenv("BASE_URL", "")
            model = os.getenv("MODEL", "gemini-2.0-flash")
            
            if not api_key:
                logger.warning("API_KEY environment variable not set")
                
            if not base_url:
                logger.warning("BASE_URL environment variable not set")
                
            logger.debug(f"Using model: {model}")
            
            config = AssistantConfig(
                api_key=api_key,
                base_url=base_url,
                model=model
            )
            
            self.client = OpenAI(
                api_key=config.api_key,
                base_url=config.base_url
            )
            self.model = config.model
            
            logger.info("Assistant initialized successfully")
            
        except ValidationError as e:
            logger.error("Configuration validation failed: %s", e)
            raise
        except Exception as e:
            logger.error("Failed to initialize Assistant: %s", e)
            raise

    def _validate_temperature(self, temperature: float) -> None:
        """
        Validate temperature parameter.
        
        Args:
            temperature (float): Temperature value to validate
            
        Raises:
            ValueError: If temperature is not between 0 and 1
        """
        logger.debug(f"Validating temperature: {temperature}")
        if not 0 <= temperature <= 1:
            logger.error("Invalid temperature value: %f", temperature)
            raise ValueError("Temperature must be between 0 and 1")

    def _prepare_messages(
        self,
        prompt: str,
        system_message: Optional[str],
        output_json: Optional[Literal["json"]]
    ) -> list[Dict[str, str]]:
        """
        Prepare message list for API call.
        
        Args:
            prompt (str): User prompt
            system_message (Optional[str]): System message
            output_json (Optional[Literal["json"]]): JSON output flag
            
        Returns:
            list[Dict[str, str]]: Prepared messages
        """
        logger.debug("Preparing messages for API call")
        messages = []
        
        if system_message:
            logger.debug(f"Using custom system message: {system_message[:50]}...")
            messages.append({"role": "system", "content": system_message})
        elif output_json == "json":
            logger.debug("Using JSON output system message")
            messages.append({
                "role": "system",
                "content": "You are a helpful assistant designed to output JSON."
            })
        
        messages.append({"role": "user", "content": prompt})
        logger.debug(f"Prepared {len(messages)} messages for API call")
        return messages

    def _prepare_api_parameters(
        self,
        messages: list[Dict[str, str]],
        model: str,
        temperature: float,
        output_format: Optional[Union[Literal["json"], Type[BaseModel]]],
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Prepare parameters for API call.
        
        Args:
            messages (list[Dict[str, str]]): Prepared messages
            model (str): Model identifier
            temperature (float): Temperature value
            output_format (Optional[Union[Literal["json"], Type[BaseModel]]]): Output format
            
        Returns:
            Dict[str, Any]: API parameters
        """
        logger.debug(f"Preparing API parameters: model={model or self.model}, temperature={temperature}")
        params = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
        }

        if max_tokens is not None:
            params["max_tokens"] = max_tokens

        if output_format:
            logger.debug(f"Setting output format: {output_format.__name__ if hasattr(output_format, '__name__') else output_format}")
            params["response_format"] = (
                {"type": "json_object"}
                if output_format == "json"
                else output_format
            )
        
        return params

    def generate_response(
        self,
        prompt: str,
        model: Optional[str] = None,
        output_json: Optional[Literal["json"]] = None,
        output_pydantic: Optional[Type[BaseModel]] = None,
        temperature: float = 0,
        max_tokens: Optional[int] = None,
        system_message: Optional[str] = None
    ) -> AssistantResponse:
        """
        Generate a response using the language model API.

        Args:
            prompt (str): The user prompt/question
            model (Optional[str]): Model to use. Defaults to None.
            output_json (Optional[Literal["json"]]): JSON output flag. Defaults to None.
            output_pydantic (Optional[Type[BaseModel]]): Pydantic model. Defaults to None.
            temperature (float): Temperature for randomness. Defaults to 0.
            system_message (Optional[str]): System message. Defaults to None.

        Returns:
            AssistantResponse: Standardized response object

        Raises:
            ValueError: If temperature is invalid
            Exception: For API-related errors
        """
        try:
            logger.debug(f"Prompt length: {len(prompt)} characters")
            logger.debug(f"Output format: json={output_json}, pydantic={output_pydantic.__name__ if output_pydantic else None}")
            
            self._validate_temperature(temperature)
            
            messages = self._prepare_messages(prompt, system_message, output_json)
            output_format = output_json or output_pydantic
            
            params = self._prepare_api_parameters(
                messages, model, temperature, output_format, max_tokens
            )
            
            logger.debug("Sending request to LLM API")
            try:
                response = self.client.beta.chat.completions.parse(**params)
                response = cast(ChatCompletion, response)
                logger.debug("Received response from LLM API")
                
            except Exception as e:
                logger.error("Failed to create mock response")
                raise APIError(f"Failed to generate response: {str(e)}")
            
            # Create the standardized response
            result = AssistantResponse(
                content=response.choices[0].message.content,
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            )
            
            logger.debug("Successfully generated response")
            return result
            
        except ValueError as e:
            logger.error("Validation error: %s", e)
            raise ValidationError(str(e))
        except Exception as e:
            logger.error("API call failed: %s", e)
            raise APIError(f"Failed to generate response: {str(e)}")
