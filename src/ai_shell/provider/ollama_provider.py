"""Ollama provider implementation."""

from typing import Dict, Any

import httpx

from .base import AIProvider, ProviderError


class OllamaProvider(AIProvider):
    """Ollama local AI provider for command suggestions."""
    
    def __init__(self, host: str = "http://127.0.0.1:11434", model: str = "llama3.1:8b"):
        """
        Initialize Ollama provider.
        
        Args:
            host: Ollama server host URL
            model: Model name to use
        """
        self.host = host.rstrip("/")
        self.model = model
    
    async def suggest(self, goal: str, context: Dict[str, Any]) -> str:
        """Generate command suggestion using Ollama API."""
        # Build the full prompt (Ollama doesn't have separate system/user messages in chat API)
        full_prompt = f"{self._build_system_prompt()}\n\n{self._build_user_prompt(goal, context)}"
        
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 50,  # Limit tokens for short responses
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.host}/api/generate",
                    json=payload,
                )
                response.raise_for_status()
                
                data = await response.json()
                if not data.get("response"):
                    raise ProviderError("No response from Ollama")
                
                raw_command = data["response"]
                return self._clean_command(raw_command)
                
        except httpx.ConnectError:
            raise ProviderError(
                f"Cannot connect to Ollama at {self.host}. "
                "Make sure Ollama is running with 'ollama serve'"
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ProviderError(f"Model '{self.model}' not found in Ollama")
            else:
                raise ProviderError(f"Ollama API error: {e.response.status_code}")
        except httpx.TimeoutException:
            raise ProviderError("Ollama API request timed out")
        except Exception as e:
            raise ProviderError(f"Ollama provider error: {str(e)}")
