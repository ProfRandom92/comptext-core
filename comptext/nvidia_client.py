"""NVIDIA NIM client for API interactions with logprobs support."""

import json
from typing import Any, Dict, List, Optional, AsyncGenerator

import httpx


class NVIDIAClient:
    """Client for interacting with NVIDIA NIM API."""

    BASE_URL = "https://integrate.api.nvidia.com/v1"

    def __init__(
        self,
        api_key: str,
        model: str = "zai-org/glm-5.1",
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: int = 4096,
        logprobs: bool = True,
    ):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.logprobs_enabled = logprobs

        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        stream: bool = True,
    ) -> Any:
        """Send a chat completion request."""
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
        }

        if system_prompt:
            payload["messages"].insert(0, {"role": "system", "content": system_prompt})

        if self.logprobs_enabled:
            payload["logprobs"] = True
            payload["top_logprobs"] = 5

        if not stream:
            payload["stream"] = False
            response = await self._client.post("/chat/completions", json=payload)
            response.raise_for_status()
            yield response.json()
            return

        # Streaming response
        payload["stream"] = True
        async with self._client.stream(
            "POST", "/chat/completions", json=payload
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        yield json.loads(data)
                    except json.JSONDecodeError:
                        continue

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    def compute_entropy(self, logprobs: List[Dict]) -> float:
        """Compute token-level entropy from logprobs."""
        import math

        entropy = 0.0
        count = 0

        for lp in logprobs:
            if "top_logprobs" in lp:
                probs = [
                    math.exp(tp["logprob"]) for tp in lp["top_logprobs"]
                ]
                total_prob = sum(probs)
                if total_prob > 0:
                    normalized = [p / total_prob for p in probs]
                    for p in normalized:
                        if p > 0:
                            entropy -= p * math.log(p)
                    count += 1

        return entropy / count if count > 0 else 0.0