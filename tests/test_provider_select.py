"""Tests for provider selection and interfaces."""

import pytest
from unittest.mock import AsyncMock, patch
from ai_shell.provider import OpenAIProvider, OllamaProvider, ProviderError


class TestProviderSelection:
    """Test AI provider selection and interface."""
    
    def test_openai_provider_init(self):
        """Test OpenAI provider initialization."""
        provider = OpenAIProvider("test-key", "gpt-4")
        assert provider.api_key == "test-key"
        assert provider.model == "gpt-4"
    
    def test_ollama_provider_init(self):
        """Test Ollama provider initialization."""
        provider = OllamaProvider("http://localhost:11434", "llama2")
        assert provider.host == "http://localhost:11434"
        assert provider.model == "llama2"
    
    def test_openai_provider_no_api_key(self):
        """Test OpenAI provider with missing API key."""
        provider = OpenAIProvider("", "gpt-4")
        
        with pytest.raises(ProviderError, match="API key not configured"):
            # Use asyncio.run in the actual test
            import asyncio
            asyncio.run(provider.suggest("test goal", {}))
    
    def test_openai_provider_placeholder_key(self):
        """Test OpenAI provider with placeholder API key."""
        provider = OpenAIProvider("sk-REPLACE_ME", "gpt-4")
        
        with pytest.raises(ProviderError, match="API key not configured"):
            import asyncio
            asyncio.run(provider.suggest("test goal", {}))
    
    @pytest.mark.asyncio
    async def test_openai_provider_mock_success(self):
        """Test OpenAI provider with mocked successful response."""
        provider = OpenAIProvider("test-key", "gpt-4")
        
        mock_response = {
            "choices": [
                {"message": {"content": "ls -la"}}
            ]
        }
        
        with patch("httpx.AsyncClient") as mock_client:
            # Create a mock response object
            mock_response_obj = AsyncMock()
            mock_response_obj.json = AsyncMock(return_value=mock_response)
            mock_response_obj.raise_for_status = AsyncMock(return_value=None)
            
            # Set up the mock client
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response_obj)
            
            result = await provider.suggest("list files", {"cwd": "/tmp"})
            assert result == "ls -la"
    
    @pytest.mark.asyncio
    async def test_ollama_provider_mock_success(self):
        """Test Ollama provider with mocked successful response."""
        provider = OllamaProvider("http://localhost:11434", "llama2")
        
        mock_response = {
            "response": "find . -name '*.log' -size +10M"
        }
        
        with patch("httpx.AsyncClient") as mock_client:
            # Create a mock response object
            mock_response_obj = AsyncMock()
            mock_response_obj.json = AsyncMock(return_value=mock_response)
            mock_response_obj.raise_for_status = AsyncMock(return_value=None)
            
            # Set up the mock client
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response_obj)
            
            result = await provider.suggest("find large log files", {"cwd": "/tmp"})
            assert result == "find . -name '*.log' -size +10M"
    
    def test_clean_command_with_code_fences(self):
        """Test command cleaning with code fences."""
        provider = OpenAIProvider("test-key", "gpt-4")
        
        # Test with backticks
        assert provider._clean_command("```ls -la```") == "ls -la"
        assert provider._clean_command("`ls -la`") == "ls -la"
        
        # Test with code block
        code_block = "```bash\nls -la\necho done\n```"
        assert provider._clean_command(code_block) == "ls -la"
        
        # Test plain command
        assert provider._clean_command("ls -la") == "ls -la"
    
    def test_build_user_prompt(self):
        """Test user prompt building."""
        provider = OpenAIProvider("test-key", "gpt-4")
        
        context = {
            "cwd": "/home/user",
            "shell": "zsh",
            "git": "On branch main",
            "files_sample": ["file1.txt", "file2.py"],
        }
        
        prompt = provider._build_user_prompt("list files", context)
        
        assert "Goal: list files" in prompt
        assert "Current directory: /home/user" in prompt
        assert "Shell: zsh" in prompt
        assert "Git status: On branch main" in prompt
        assert "Files in directory: file1.txt, file2.py" in prompt
    
    def test_build_system_prompt(self):
        """Test system prompt building."""
        provider = OpenAIProvider("test-key", "gpt-4")
        prompt = provider._build_system_prompt()
        
        assert "shell commands" in prompt.lower()
        assert "safe" in prompt.lower()
        assert "single-line" in prompt.lower() or "single" in prompt.lower()
