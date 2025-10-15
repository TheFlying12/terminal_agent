"""CLI interface for AI Shell."""

import os
import sys
import subprocess
import time
from typing import Optional

import httpx
import typer

from .config import config
from .safety import Safety
from .audit import AuditLogger


app = typer.Typer(
    name="ai",
    help="AI-assisted terminal command palette",
    no_args_is_help=True,
)

safety = Safety()
audit_logger = AuditLogger(str(config.expanded_log_path))


def ensure_daemon_running() -> bool:
    """
    Ensure the AI Shell daemon is running.
    
    Returns:
        True if daemon is running or was started successfully
    """
    # Check if daemon is already running
    try:
        response = httpx.get(f"{config.server_url}/health", timeout=2.0)
        if response.status_code == 200:
            return True
    except httpx.RequestError:
        pass
    
    # Try to start the daemon
    try:
        subprocess.Popen(
            [sys.executable, "-m", "ai_shell.server"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        
        # Wait a bit for startup
        time.sleep(2)
        
        # Check if it's running now
        try:
            response = httpx.get(f"{config.server_url}/health", timeout=5.0)
            return response.status_code == 200
        except httpx.RequestError:
            return False
            
    except Exception:
        return False


def call_daemon(goal: str) -> Optional[str]:
    """
    Call the daemon to get a command suggestion.
    
    Args:
        goal: Natural language goal
        
    Returns:
        Suggested command or None if failed
    """
    if not ensure_daemon_running():
        typer.echo("Error: Could not start AI Shell daemon", err=True)
        return None
    
    try:
        payload = {
            "goal": goal,
            "cwd": os.getcwd(),
            "shell": os.environ.get("SHELL", "").split("/")[-1] if os.environ.get("SHELL") else "unknown",
        }
        
        response = httpx.post(
            f"{config.server_url}/suggest",
            json=payload,
            timeout=30.0,
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("command")
        else:
            error_detail = response.json().get("detail", "Unknown error")
            typer.echo(f"Error: {error_detail}", err=True)
            return None
            
    except httpx.TimeoutException:
        typer.echo("Error: Request timed out", err=True)
        return None
    except httpx.RequestError as e:
        typer.echo(f"Error: Could not connect to daemon: {e}", err=True)
        return None
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        return None


@app.command()
def suggest(goal: str = typer.Argument(..., help="Natural language goal")):
    """
    Get a command suggestion for the given goal.
    
    Prints the command to STDOUT and explanation to STDERR.
    """
    command = call_daemon(goal)
    if command:
        # Print command to STDOUT (for shell integration)
        print(command)
        
        # Print explanation and warnings to STDERR
        typer.echo(f"# Suggested command for: {goal}", err=True)
        
        warnings = safety.get_safety_warnings(command)
        for warning in warnings:
            typer.echo(warning, err=True)
    else:
        sys.exit(1)


@app.command()
def run(goal: str = typer.Argument(..., help="Natural language goal")):
    """
    Get a command suggestion and optionally execute it.
    
    Shows the suggestion and prompts for confirmation before execution.
    """
    command = call_daemon(goal)
    if not command:
        sys.exit(1)
    
    # Show the suggestion
    typer.echo(f"Goal: {goal}")
    typer.echo(f"Suggested command: {typer.style(command, fg=typer.colors.CYAN)}")
    
    # Show safety warnings
    warnings = safety.get_safety_warnings(command)
    for warning in warnings:
        typer.echo(warning)
    
    # Ask for confirmation
    if safety.requires_confirmation(command):
        confirm = typer.confirm("⚠️  This command requires confirmation. Execute?", default=False)
    else:
        confirm = typer.confirm("Execute this command?", default=True)
    
    if confirm:
        typer.echo(f"Executing: {command}")
        try:
            # Execute the command
            result = subprocess.run(
                command,
                shell=True,
                cwd=os.getcwd(),
            )
            
            # Log the execution
            audit_logger.log_suggestion(
                goal=goal,
                command=command,
                cwd=os.getcwd(),
                provider=config.ai_provider,
                approved=True,
                exit_code=result.returncode,
                risk_score=safety.risk_score(command),
            )
            
            sys.exit(result.returncode)
            
        except KeyboardInterrupt:
            typer.echo("\nCommand interrupted", err=True)
            sys.exit(130)
        except Exception as e:
            typer.echo(f"Error executing command: {e}", err=True)
            sys.exit(1)
    else:
        # Log the rejection
        audit_logger.log_suggestion(
            goal=goal,
            command=command,
            cwd=os.getcwd(),
            provider=config.ai_provider,
            approved=False,
            risk_score=safety.risk_score(command),
        )
        typer.echo("Command not executed")


@app.command()
def explain(
    command: Optional[str] = typer.Argument(None, help="Command to explain"),
    last: bool = typer.Option(False, "--last", help="Explain the last suggested command"),
):
    """
    Explain what a command does.
    
    Can explain a specific command or the last suggested command.
    """
    if last:
        # Get the last command from audit log
        entries = audit_logger.get_recent_entries(1)
        if not entries:
            typer.echo("No recent commands found", err=True)
            sys.exit(1)
        
        command = entries[0].get("command")
        if not command:
            typer.echo("No command found in last entry", err=True)
            sys.exit(1)
    
    if not command:
        typer.echo("Please provide a command to explain or use --last", err=True)
        sys.exit(1)
    
    # For MVP, provide basic explanation
    typer.echo(f"Command: {typer.style(command, fg=typer.colors.CYAN)}")
    
    # Show safety information
    risk_score = safety.risk_score(command)
    typer.echo(f"Risk score: {risk_score:.2f}")
    
    warnings = safety.get_safety_warnings(command)
    for warning in warnings:
        typer.echo(warning)
    
    # Basic command breakdown
    parts = command.split()
    if parts:
        typer.echo(f"Main command: {parts[0]}")
        if len(parts) > 1:
            typer.echo(f"Arguments: {' '.join(parts[1:])}")


@app.command()
def status():
    """Show AI Shell status and statistics."""
    # Check daemon status
    try:
        response = httpx.get(f"{config.server_url}/health", timeout=2.0)
        if response.status_code == 200:
            typer.echo("✅ Daemon is running")
            data = response.json()
            typer.echo(f"Provider: {data.get('provider', 'unknown')}")
        else:
            typer.echo("❌ Daemon is not responding")
    except httpx.RequestError:
        typer.echo("❌ Daemon is not running")
    
    # Show configuration
    typer.echo(f"\nConfiguration:")
    typer.echo(f"  Provider: {config.ai_provider}")
    typer.echo(f"  Server: {config.server_url}")
    typer.echo(f"  Log path: {config.expanded_log_path}")
    
    # Show statistics
    stats = audit_logger.get_stats()
    typer.echo(f"\nStatistics:")
    typer.echo(f"  Total entries: {stats['total_entries']}")
    typer.echo(f"  Approval rate: {stats['approval_rate']:.1%}")
    typer.echo(f"  Log size: {stats['file_size_bytes']} bytes")


@app.command()
def daemon():
    """Start the AI Shell daemon in foreground mode."""
    from .server import main
    main()


if __name__ == "__main__":
    app()
