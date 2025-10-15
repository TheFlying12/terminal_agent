"""OpenAI provider implementation."""

import json
from typing import Dict, Any

import httpx

from .base import AIProvider, ProviderError


class OpenAIProvider(AIProvider):
    """OpenAI API provider for command suggestions."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """
        Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            model: Model name to use
        """
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.openai.com/v1"
    
    async def suggest(self, goal: str, context: Dict[str, Any]) -> str:
        """Generate command suggestion using OpenAI API."""
        if not self.api_key or self.api_key == "sk-REPLACE_ME":
            raise ProviderError("OpenAI API key not configured")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self._build_system_prompt()},
                {"role": "user", "content": self._build_user_prompt(goal, context)},
            ],
            "max_tokens": 100,
            "temperature": 0.1,
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                
                data = await response.json()
                if not data.get("choices"):
                    raise ProviderError("No response from OpenAI")
                
                raw_command = data["choices"][0]["message"]["content"]
                return self._clean_command(raw_command)
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise ProviderError("Invalid OpenAI API key")
            elif e.response.status_code == 429:
                raise ProviderError("OpenAI API rate limit exceeded")
            else:
                raise ProviderError(f"OpenAI API error: {e.response.status_code}")
        except httpx.TimeoutException:
            raise ProviderError("OpenAI API request timed out")
        except Exception as e:
            raise ProviderError(f"OpenAI provider error: {str(e)}")
