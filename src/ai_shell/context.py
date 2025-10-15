"""Context collection for AI command suggestions."""

import os
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional


class ContextCollector:
    """Collects contextual information about the current environment."""
    
    def __init__(self, max_files: int = 200, max_git_output: int = 1500):
        """
        Initialize context collector.
        
        Args:
            max_files: Maximum number of files to include in context
            max_git_output: Maximum characters from git status output
        """
        self.max_files = max_files
        self.max_git_output = max_git_output
    
    def collect(self, cwd: Optional[str] = None) -> Dict[str, Any]:
        """
        Collect contextual information from the current working directory.
        
        Args:
            cwd: Working directory to collect context from (defaults to current)
            
        Returns:
            Dictionary containing contextual information
        """
        if cwd is None:
            cwd = os.getcwd()
        
        context = {
            "cwd": cwd,
            "shell": self._get_shell(),
        }
        
        # Collect git information
        git_info = self._get_git_status(cwd)
        if git_info:
            context["git"] = git_info
        
        # Collect file listing
        files = self._get_file_listing(cwd)
        if files:
            context["files_sample"] = files
        
        # Add OS information
        context["os"] = self._get_os_info()
        
        return context
    
    def _get_shell(self) -> str:
        """Get current shell name."""
        shell = os.environ.get("SHELL", "")
        if shell:
            return Path(shell).name
        return "unknown"
    
    def _get_git_status(self, cwd: str) -> Optional[str]:
        """
        Get git status information for the directory.
        
        Args:
            cwd: Directory to check git status in
            
        Returns:
            Git status string or None if not a git repository
        """
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain", "-b"],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=5,
            )
            
            if result.returncode == 0 and result.stdout:
                # Truncate output if too long
                output = result.stdout.strip()
                if len(output) > self.max_git_output:
                    output = output[:self.max_git_output] + "..."
                return output
            
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
            pass
        
        return None
    
    def _get_file_listing(self, cwd: str) -> List[str]:
        """
        Get a sample of files and directories in the current directory.
        
        Args:
            cwd: Directory to list files from
            
        Returns:
            List of file/directory names
        """
        try:
            path = Path(cwd)
            if not path.exists() or not path.is_dir():
                return []
            
            # Get all items, excluding hidden files
            items = []
            for item in path.iterdir():
                if not item.name.startswith("."):
                    items.append(item.name)
            
            # Sort and limit
            items.sort()
            return items[:self.max_files]
            
        except (OSError, PermissionError):
            return []
    
    def _get_os_info(self) -> str:
        """Get basic OS information."""
        import platform
        return f"{platform.system()} {platform.release()}"
    
    def _run_command_safe(self, command: List[str], cwd: str, timeout: int = 5) -> Optional[str]:
        """
        Safely run a command and return its output.
        
        Args:
            command: Command to run as list of strings
            cwd: Working directory
            timeout: Timeout in seconds
            
        Returns:
            Command output or None if failed
        """
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
                
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
            pass
        
        return None
