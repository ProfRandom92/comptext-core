import os
from google import genai
from google.genai import types

class GoogleProvider:
    """Provider implementing Google Gemini API access using the new google.genai SDK."""
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY", "")
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None
        self.model_name = "gemini-2.5-pro"

    def complete(self, prompt: str) -> str:
        """Complete a prompt using gemini-2.5-pro."""
        if not self.api_key or not self.client:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt
        )
        return response.text

    def chat(self, history: list[dict]) -> str:
        """Chat with gemini-2.5-pro converting roles to Gemini format."""
        if not self.api_key or not self.client:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")
        
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

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=config
        )
        return response.text
