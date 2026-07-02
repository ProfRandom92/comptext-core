import os
import httpx
from google import genai
from google.genai import types
try:
    from google.genai import errors
except ImportError:
    errors = None

from .exceptions import (
    ProviderError,
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderConnectionError,
    ProviderAPIError
)

class GoogleProvider:
    """Provider implementing Google Gemini API access using the new google.genai SDK."""
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY", "")
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                raise ProviderAuthError(f"Failed to initialize Google GenAI Client: {str(e)}") from e
        else:
            self.client = None
        self.model_name = "gemini-2.5-pro"

    def _handle_exception(self, e: Exception) -> None:
        """Translate Google GenAI SDK and HTTPX exceptions into unified ProviderError."""
        if errors and isinstance(e, errors.APIError):
            code = getattr(e, "code", None)
            message = str(e)
            if code in (401, 403):
                raise ProviderAuthError(f"Google API authentication failed: {message}") from e
            elif code == 429:
                raise ProviderRateLimitError(f"Google API rate limit exceeded: {message}") from e
            else:
                raise ProviderAPIError(f"Google API status error: {message}") from e

        if isinstance(e, (httpx.ConnectError, httpx.TimeoutException, httpx.RequestError)):
            raise ProviderConnectionError(f"Google API connection failed: {str(e)}") from e

        raise ProviderError(f"Google provider error: {str(e)}") from e

    def complete(self, prompt: str) -> str:
        """Complete a prompt using gemini-2.5-pro."""
        if not self.api_key or not self.client:
            raise ProviderAuthError("GOOGLE_API_KEY environment variable is not set")
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text
        except Exception as e:
            self._handle_exception(e)

    def chat(self, history: list[dict]) -> str:
        """Chat with gemini-2.5-pro converting roles to Gemini format."""
        if not self.api_key or not self.client:
            raise ProviderAuthError("GOOGLE_API_KEY environment variable is not set")
        
        contents = []
        system_instruction = None
        for msg in history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                system_instruction = content
            elif role in ("assistant", "model"):
                contents.append(
                    types.Content(
                        role="model",
                        parts=[types.Part.from_text(text=content)]
                    )
                )
            else:
                contents.append(
                    types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=content)]
                    )
                )

        config = None
        if system_instruction:
            config = types.GenerateContentConfig(
                system_instruction=system_instruction
            )

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config
            )
            return response.text
        except Exception as e:
            self._handle_exception(e)
