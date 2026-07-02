import os
import httpx
from .exceptions import (
    ProviderError,
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderConnectionError,
    ProviderAPIError
)

class XAIProvider:
    """Provider implementing xAI Grok API access via HTTPX."""
    BASE_URL = "https://api.x.ai/v1/chat/completions"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("XAI_API_KEY", "")
        self.model_name = "grok-3"

    def _execute_request(self, payload: dict, headers: dict) -> str:
        if not self.api_key:
            raise ProviderAuthError("XAI_API_KEY environment variable is not set")

        try:
            response = httpx.post(self.BASE_URL, json=payload, headers=headers, timeout=60.0)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            code = e.response.status_code
            message = str(e)
            if code in (401, 403):
                raise ProviderAuthError(f"xAI API authentication failed: {message}") from e
            elif code == 429:
                raise ProviderRateLimitError(f"xAI API rate limit exceeded: {message}") from e
            else:
                raise ProviderAPIError(f"xAI API status error: {message}") from e
        except (httpx.ConnectError, httpx.TimeoutException, httpx.RequestError) as e:
            raise ProviderConnectionError(f"xAI API connection failed: {str(e)}") from e
        except Exception as e:
            raise ProviderError(f"xAI provider error: {str(e)}") from e

    def complete(self, prompt: str) -> str:
        """Complete a prompt using grok-3."""
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        return self._execute_request(payload, headers)

    def chat(self, history: list[dict]) -> str:
        """Chat with grok-3 using the messages history."""
        payload = {
            "model": self.model_name,
            "messages": history,
            "stream": False
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        return self._execute_request(payload, headers)
