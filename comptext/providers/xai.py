import os
import httpx

class XAIProvider:
    """Provider implementing xAI Grok API access via HTTPX."""
    BASE_URL = "https://api.x.ai/v1/chat/completions"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("XAI_API_KEY", "")
        self.model_name = "grok-3"

    def complete(self, prompt: str) -> str:
        """Complete a prompt using grok-3."""
        if not self.api_key:
            raise ValueError("XAI_API_KEY environment variable is not set")
        
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = httpx.post(self.BASE_URL, json=payload, headers=headers, timeout=60.0)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    def chat(self, history: list[dict]) -> str:
        """Chat with grok-3 using the messages history."""
        if not self.api_key:
            raise ValueError("XAI_API_KEY environment variable is not set")
            
        payload = {
            "model": self.model_name,
            "messages": history,
            "stream": False
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = httpx.post(self.BASE_URL, json=payload, headers=headers, timeout=60.0)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
