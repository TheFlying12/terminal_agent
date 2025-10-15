"""Tests for FastAPI server."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from ai_shell.server import app


class TestServer:
    """Test FastAPI server endpoints."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
    
    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "provider" in data
    
    def test_stats_endpoint(self):
        """Test stats endpoint."""
        response = self.client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    @patch("ai_shell.server.get_provider")
    def test_suggest_endpoint_success(self, mock_get_provider):
        """Test successful command suggestion."""
        # Mock the provider
        mock_provider = AsyncMock()
        mock_provider.suggest.return_value = "ls -la"
        mock_get_provider.return_value = mock_provider
        
        payload = {
            "goal": "list files",
            "cwd": "/tmp",
            "shell": "zsh",
        }
        
        response = self.client.post("/suggest", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "command" in data
        assert "explanation" in data
        assert "risk" in data
        assert "alternatives" in data
        
        # Verify provider was called
        mock_provider.suggest.assert_called_once()
    
    @patch("ai_shell.server.get_provider")
    def test_suggest_endpoint_provider_error(self, mock_get_provider):
        """Test suggestion endpoint with provider error."""
        # Mock provider to raise error
        mock_provider = AsyncMock()
        mock_provider.suggest.side_effect = Exception("Provider error")
        mock_get_provider.return_value = mock_provider
        
        payload = {
            "goal": "list files",
        }
        
        response = self.client.post("/suggest", json=payload)
        assert response.status_code == 500
    
    def test_suggest_endpoint_missing_goal(self):
        """Test suggestion endpoint with missing goal."""
        payload = {}
        
        response = self.client.post("/suggest", json=payload)
        assert response.status_code == 422  # Validation error
    
    def test_suggest_endpoint_empty_goal(self):
        """Test suggestion endpoint with empty goal."""
        payload = {"goal": ""}
        
        response = self.client.post("/suggest", json=payload)
        # Should still process but might return error depending on provider
        assert response.status_code in [200, 400, 500]
    
    @patch("ai_shell.server.get_provider")
    def test_suggest_endpoint_with_context(self, mock_get_provider):
        """Test suggestion endpoint with custom context."""
        mock_provider = AsyncMock()
        mock_provider.suggest.return_value = "find . -name '*.py'"
        mock_get_provider.return_value = mock_provider
        
        payload = {
            "goal": "find python files",
            "context": {
                "files_sample": ["main.py", "test.py", "README.md"],
                "git": "On branch main",
            },
        }
        
        response = self.client.post("/suggest", json=payload)
        assert response.status_code == 200
        
        # Verify context was passed to provider
        call_args = mock_provider.suggest.call_args
        assert call_args is not None
        context = call_args[0][1]  # Second argument is context
        assert "files_sample" in context
        assert "git" in context
