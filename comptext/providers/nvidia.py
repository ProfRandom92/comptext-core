import os
import time
from openai import OpenAI, OpenAIError, RateLimitError, AuthenticationError, APIConnectionError, APIStatusError, APIError
from .exceptions import (
    ProviderError,
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderConnectionError,
    ProviderAPIError
)

class NVIDIAProvider:
    """Provider implementing NVIDIA NIM API access using the openai SDK."""
    def __init__(self, api_key: str = None, model: str = "deepseek-ai/deepseek-v4-flash"):
        self.api_key = api_key or os.environ.get("NVIDIA_API_KEY", "")
        if self.api_key:
            if not self.api_key.startswith("nvapi-"):
                raise ProviderAuthError("NVIDIA API key must start with 'nvapi-'")
            self.client = OpenAI(
                base_url="https://integrate.api.nvidia.com/v1",
                api_key=self.api_key
            )
        else:
            self.client = None
            
        self.model_name = model

    def _execute_with_retry(self, fn, *args, **kwargs):
        """Execute client completion call with exponential backoff on rate limits."""
        if not self.api_key or not self.client:
            raise ProviderAuthError("NVIDIA_API_KEY environment variable is not set")
            
        retries = 3
        delay = 1.0
        for attempt in range(retries + 1):
            try:
                return fn(*args, **kwargs)
            except RateLimitError as e:
                if attempt == retries:
                    raise ProviderRateLimitError(f"NVIDIA API rate limits exceeded after {retries} retries: {str(e)}") from e
                time.sleep(delay)
                delay *= 2.0
            except AuthenticationError as e:
                raise ProviderAuthError(f"NVIDIA API authentication failed: {str(e)}") from e
            except APIConnectionError as e:
                raise ProviderConnectionError(f"NVIDIA API connection failed: {str(e)}") from e
            except (APIStatusError, APIError) as e:
                raise ProviderAPIError(f"NVIDIA API status error: {str(e)}") from e
            except Exception as e:
                raise ProviderError(f"NVIDIA provider error: {str(e)}") from e

    def complete(self, prompt: str) -> str:
        """Complete a prompt using NVIDIA NIM."""
        def call():
            resp = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                stream=False
            )
            return resp.choices[0].message.content
            
        return self._execute_with_retry(call)

    def chat(self, history: list[dict]) -> str:
        """Chat using NVIDIA NIM messages history."""
        def call():
            resp = self.client.chat.completions.create(
                model=self.model_name,
                messages=history,
                stream=False
            )
            return resp.choices[0].message.content
            
        return self._execute_with_retry(call)
