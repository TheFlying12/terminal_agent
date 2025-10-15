"""Base AI provider interface."""

from abc import ABC, abstractmethod
from typing import Dict, Any


class ProviderError(Exception):
    """Base exception for provider errors."""
    pass


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    async def suggest(self, goal: str, context: Dict[str, Any]) -> str:
        """
        Generate a single shell command suggestion based on the goal and context.
        
        Args:
            goal: Natural language description of what the user wants to accomplish
            context: Dictionary containing contextual information like cwd, git status, etc.
            
        Returns:
            A single shell command as a string
            
        Raises:
            ProviderError: If the provider fails to generate a suggestion
        """
        pass
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for the AI model."""
        return (
            "You are a helpful assistant that converts natural language goals into "
            "safe, single-line shell commands for macOS/Unix systems. "
            "Return ONLY the command, no explanation or formatting. "
            "Prefer commands with dry-run flags when available. "
            "Never return destructive commands without confirmation flags."
        )
    
    def _build_user_prompt(self, goal: str, context: Dict[str, Any]) -> str:
        """Build the user prompt with goal and context."""
        prompt_parts = [f"Goal: {goal}"]
        
        if context.get("cwd"):
            prompt_parts.append(f"Current directory: {context['cwd']}")
        
        if context.get("shell"):
            prompt_parts.append(f"Shell: {context['shell']}")
        
        if context.get("git"):
            prompt_parts.append(f"Git status: {context['git']}")
        
        if context.get("files_sample"):
            files = context["files_sample"][:10]  # Limit to first 10 files
            prompt_parts.append(f"Files in directory: {', '.join(files)}")
        
        return "\n".join(prompt_parts)
    
    def _clean_command(self, raw_response: str) -> str:
        """Clean the raw response to extract just the command."""
        # Remove code fences
        response = raw_response.strip()
        if response.startswith("```"):
            lines = response.split("\n")
            # Find first non-fence line
            for i, line in enumerate(lines):
                if not line.startswith("```") and line.strip():
                    response = line.strip()
                    break
        
        # Remove any remaining backticks or formatting
        response = response.strip("`").strip()
        
        # Take only the first line if multiple lines
        if "\n" in response:
            response = response.split("\n")[0].strip()
        
        return response
