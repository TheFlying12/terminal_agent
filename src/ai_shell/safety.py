"""Safety checks and command filtering."""

import re
from typing import List, Tuple


class Safety:
    """Safety checker for shell commands."""
    
    # Dangerous patterns that should be blocked or require confirmation
    DANGEROUS_PATTERNS = [
        # Destructive file operations
        r"rm\s+-rf\s+/",
        r"rm\s+-rf\s+\*",
        r"rm\s+-rf\s+~",
        r"rm\s+-rf\s+\$HOME",
        
        # Filesystem operations
        r"mkfs",
        r"fdisk",
        r"parted",
        
        # Device operations
        r"dd\s+.*of=/dev/",
        
        # Permission changes on system directories
        r"chmod\s+.*\s+/",
        r"chown\s+.*\s+/",
        
        # Network/firewall
        r"iptables\s+-F",
        r"ufw\s+--force",
        
        # System modifications
        r"systemctl\s+disable",
        r"launchctl\s+unload",
        
        # Package management (potentially dangerous)
        r"brew\s+uninstall\s+--force",
        r"npm\s+uninstall\s+-g",
        
        # Kernel/system
        r"kextunload",
        r"dtrace",
    ]
    
    # Commands that should have dry-run flags added when possible
    DRY_RUN_COMMANDS = {
        "rsync": "--dry-run",
        "cp": "-n",  # no-clobber
        "mv": "-n",  # no-clobber
        "git clean": "--dry-run",
        "git reset": "--dry-run", 
        "brew cleanup": "--dry-run",
    }
    
    def risk_score(self, command: str) -> float:
        """
        Calculate risk score for a command (0.0 = safe, 1.0 = very dangerous).
        
        Args:
            command: Shell command to analyze
            
        Returns:
            Risk score between 0.0 and 1.0
        """
        if not command or not command.strip():
            return 0.0
        
        command = command.strip().lower()
        risk = 0.0
        
        # Check dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                risk = max(risk, 0.9)
        
        # Check for sudo usage
        if command.startswith("sudo "):
            risk = max(risk, 0.3)
        
        # Check for file deletion
        if re.search(r"\brm\b", command):
            if "-r" in command or "-f" in command:
                risk = max(risk, 0.6)
            else:
                risk = max(risk, 0.2)
        
        # Check for network operations
        if any(net_cmd in command for net_cmd in ["curl", "wget", "ssh", "scp"]):
            risk = max(risk, 0.1)
        
        # Check for system modifications
        if any(sys_cmd in command for sys_cmd in ["install", "uninstall", "remove"]):
            risk = max(risk, 0.3)
        
        return min(risk, 1.0)
    
    def requires_confirmation(self, command: str) -> bool:
        """
        Check if command requires user confirmation before execution.
        
        Args:
            command: Shell command to check
            
        Returns:
            True if confirmation is required
        """
        return self.risk_score(command) >= 0.5
    
    def rewrite_to_dry_run(self, command: str) -> str:
        """
        Attempt to rewrite command to use dry-run flags where possible.
        
        Args:
            command: Original command
            
        Returns:
            Command with dry-run flags added if applicable
        """
        command = command.strip()
        
        for cmd_prefix, dry_run_flag in self.DRY_RUN_COMMANDS.items():
            if command.startswith(cmd_prefix + " "):
                # Check if dry-run flag is already present
                if dry_run_flag not in command:
                    # For multi-word commands like "git clean", handle specially
                    if " " in cmd_prefix:
                        # Replace the multi-word command with command + dry-run flag
                        rest = command[len(cmd_prefix):].strip()
                        return f"{cmd_prefix} {dry_run_flag} {rest}".strip()
                    else:
                        # Single word command - insert dry-run flag after command name
                        parts = command.split(" ", 1)
                        if len(parts) == 2:
                            return f"{parts[0]} {dry_run_flag} {parts[1]}"
                        else:
                            return f"{parts[0]} {dry_run_flag}"
        
        return command
    
    def get_safety_warnings(self, command: str) -> List[str]:
        """
        Get list of safety warnings for a command.
        
        Args:
            command: Command to analyze
            
        Returns:
            List of warning messages
        """
        warnings = []
        risk = self.risk_score(command)
        
        if risk >= 0.9:
            warnings.append("⚠️  DANGER: This command could cause irreversible damage")
        elif risk >= 0.6:
            warnings.append("⚠️  HIGH RISK: This command could delete or modify important files")
        elif risk >= 0.3:
            warnings.append("⚠️  MODERATE RISK: This command requires elevated privileges or makes system changes")
        
        if self.requires_confirmation(command):
            warnings.append("🔒 Confirmation required before execution")
        
        return warnings
    
    def is_safe_for_auto_execution(self, command: str) -> bool:
        """
        Check if command is safe for automatic execution without confirmation.
        
        Args:
            command: Command to check
            
        Returns:
            True if safe for auto-execution
        """
        return self.risk_score(command) < 0.3
