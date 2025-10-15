"""Audit logging for AI Shell commands."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class AuditLogger:
    """Handles audit logging of AI Shell commands and interactions."""
    
    def __init__(self, log_path: str, max_size_mb: int = 5):
        """
        Initialize audit logger.
        
        Args:
            log_path: Path to the audit log file
            max_size_mb: Maximum log file size in MB before rotation
        """
        self.log_path = Path(log_path).expanduser()
        self.max_size_bytes = max_size_mb * 1024 * 1024
        
        # Ensure log directory exists
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def log_suggestion(
        self,
        goal: str,
        command: str,
        cwd: str,
        provider: str,
        approved: Optional[bool] = None,
        exit_code: Optional[int] = None,
        risk_score: Optional[float] = None,
    ) -> None:
        """
        Log a command suggestion and its outcome.
        
        Args:
            goal: The natural language goal
            command: The suggested command
            cwd: Current working directory
            provider: AI provider used
            approved: Whether user approved the command (None if not executed)
            exit_code: Exit code if command was executed
            risk_score: Safety risk score
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "goal": goal,
            "command": command,
            "cwd": cwd,
            "provider": provider,
            "approved": approved,
            "exit_code": exit_code,
            "risk_score": risk_score,
        }
        
        self._append_entry(entry)
        self._rotate_if_needed()
    
    def log_error(
        self,
        goal: str,
        error: str,
        cwd: str,
        provider: Optional[str] = None,
    ) -> None:
        """
        Log an error that occurred during command generation.
        
        Args:
            goal: The natural language goal
            error: Error message
            cwd: Current working directory
            provider: AI provider used (if any)
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "goal": goal,
            "error": error,
            "cwd": cwd,
            "provider": provider,
        }
        
        self._append_entry(entry)
        self._rotate_if_needed()
    
    def _append_entry(self, entry: Dict[str, Any]) -> None:
        """Append an entry to the audit log."""
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                json.dump(entry, f, separators=(",", ":"))
                f.write("\n")
        except (OSError, IOError) as e:
            # If we can't write to the log, print to stderr but don't fail
            print(f"Warning: Could not write to audit log: {e}", file=__import__("sys").stderr)
    
    def _rotate_if_needed(self) -> None:
        """Rotate log file if it exceeds maximum size."""
        try:
            if self.log_path.exists() and self.log_path.stat().st_size > self.max_size_bytes:
                backup_path = self.log_path.with_suffix(self.log_path.suffix + ".1")
                
                # Remove old backup if it exists
                if backup_path.exists():
                    backup_path.unlink()
                
                # Move current log to backup
                self.log_path.rename(backup_path)
                
        except (OSError, IOError):
            # If rotation fails, continue without failing
            pass
    
    def get_recent_entries(self, limit: int = 10) -> list:
        """
        Get recent audit log entries.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of recent log entries
        """
        entries = []
        
        try:
            if not self.log_path.exists():
                return entries
            
            with open(self.log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                
            # Get last N lines
            for line in lines[-limit:]:
                try:
                    entry = json.loads(line.strip())
                    entries.append(entry)
                except json.JSONDecodeError:
                    continue
                    
        except (OSError, IOError):
            pass
        
        return entries
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about audit log usage.
        
        Returns:
            Dictionary with statistics
        """
        stats = {
            "total_entries": 0,
            "file_size_bytes": 0,
            "providers_used": set(),
            "approval_rate": 0.0,
        }
        
        try:
            if not self.log_path.exists():
                return stats
            
            stats["file_size_bytes"] = self.log_path.stat().st_size
            
            approved_count = 0
            total_suggestions = 0
            
            with open(self.log_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        stats["total_entries"] += 1
                        
                        if "provider" in entry and entry["provider"]:
                            stats["providers_used"].add(entry["provider"])
                        
                        if "approved" in entry and entry["approved"] is not None:
                            total_suggestions += 1
                            if entry["approved"]:
                                approved_count += 1
                                
                    except json.JSONDecodeError:
                        continue
            
            if total_suggestions > 0:
                stats["approval_rate"] = approved_count / total_suggestions
            
            stats["providers_used"] = list(stats["providers_used"])
            
        except (OSError, IOError):
            pass
        
        return stats
