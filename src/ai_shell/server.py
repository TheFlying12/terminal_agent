"""FastAPI server for AI Shell daemon."""

import os
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uvicorn

from .config import config
from .provider import OpenAIProvider, OllamaProvider, ProviderError
from .safety import Safety
from .context import ContextCollector
from .audit import AuditLogger


class SuggestionRequest(BaseModel):
    """Request model for command suggestions."""
    goal: str = Field(..., description="Natural language goal")
    cwd: Optional[str] = Field(None, description="Current working directory")
    shell: Optional[str] = Field(None, description="Shell type (zsh, bash, etc.)")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    policy: str = Field("normal", description="Safety policy (normal, strict, permissive)")


class SuggestionResponse(BaseModel):
    """Response model for command suggestions."""
    command: str = Field(..., description="Suggested shell command")
    explanation: str = Field("", description="Brief explanation of the command")
    risk: float = Field(0.0, description="Risk score (0.0 = safe, 1.0 = dangerous)")
    alternatives: List[str] = Field(default_factory=list, description="Alternative commands")


# Initialize components
app = FastAPI(
    title="AI Shell",
    description="AI-assisted terminal command palette",
    version="0.1.0",
)

safety = Safety()
context_collector = ContextCollector()
audit_logger = AuditLogger(str(config.expanded_log_path))


def get_provider():
    """Get the configured AI provider."""
    if config.ai_provider == "openai":
        return OpenAIProvider(config.openai_api_key, config.openai_model)
    elif config.ai_provider == "ollama":
        return OllamaProvider(config.ollama_host, config.ollama_model)
    else:
        raise ValueError(f"Unknown provider: {config.ai_provider}")


@app.post("/suggest", response_model=SuggestionResponse)
async def suggest_command(request: SuggestionRequest) -> SuggestionResponse:
    """
    Generate a command suggestion based on natural language goal.
    
    Args:
        request: Suggestion request with goal and context
        
    Returns:
        Command suggestion with safety information
        
    Raises:
        HTTPException: If suggestion generation fails
    """
    # Use provided cwd or current directory
    cwd = request.cwd or os.getcwd()
    
    # Collect context if not provided
    if request.context is None:
        context = context_collector.collect(cwd)
    else:
        # Merge provided context with collected context
        collected_context = context_collector.collect(cwd)
        context = {**collected_context, **request.context}
    
    # Add shell info if provided
    if request.shell:
        context["shell"] = request.shell
    
    try:
        # Get AI provider and generate suggestion
        provider = get_provider()
        raw_command = await provider.suggest(request.goal, context)
        
        if not raw_command or not raw_command.strip():
            raise HTTPException(status_code=400, detail="No command generated")
        
        # Apply safety checks
        command = raw_command.strip()
        risk_score = safety.risk_score(command)
        
        # Apply dry-run rewriting if policy allows
        if request.policy == "normal":
            command = safety.rewrite_to_dry_run(command)
        
        # Generate explanation (simple for MVP)
        explanation = f"Command to: {request.goal}"
        
        # Log the suggestion
        audit_logger.log_suggestion(
            goal=request.goal,
            command=command,
            cwd=cwd,
            provider=config.ai_provider,
            risk_score=risk_score,
        )
        
        return SuggestionResponse(
            command=command,
            explanation=explanation,
            risk=risk_score,
            alternatives=[],
        )
        
    except ProviderError as e:
        # Log the error
        audit_logger.log_error(
            goal=request.goal,
            error=str(e),
            cwd=cwd,
            provider=config.ai_provider,
        )
        raise HTTPException(status_code=500, detail=str(e))
    
    except Exception as e:
        # Log unexpected errors
        audit_logger.log_error(
            goal=request.goal,
            error=f"Unexpected error: {str(e)}",
            cwd=cwd,
            provider=config.ai_provider,
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "provider": config.ai_provider}


@app.get("/stats")
async def get_stats():
    """Get usage statistics."""
    return audit_logger.get_stats()


def main():
    """Run the FastAPI server."""
    uvicorn.run(
        "ai_shell.server:app",
        host=config.ai_host,
        port=config.ai_port,
        reload=False,
        access_log=False,
    )


if __name__ == "__main__":
    main()
