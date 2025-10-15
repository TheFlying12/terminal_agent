"""Tests for safety module."""

import pytest
from ai_shell.safety import Safety


class TestSafety:
    """Test safety checks and command filtering."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.safety = Safety()
    
    def test_risk_score_safe_commands(self):
        """Test risk scoring for safe commands."""
        safe_commands = [
            "ls -la",
            "pwd",
            "echo hello",
            "cat file.txt",
            "grep pattern file.txt",
        ]
        
        for cmd in safe_commands:
            risk = self.safety.risk_score(cmd)
            assert risk <= 0.2, f"Command '{cmd}' should be low risk, got {risk}"
    
    def test_risk_score_dangerous_commands(self):
        """Test risk scoring for dangerous commands."""
        dangerous_commands = [
            "rm -rf /",
            "rm -rf *",
            "dd if=/dev/zero of=/dev/sda",
            "mkfs.ext4 /dev/sda1",
            "chmod 777 /",
        ]
        
        for cmd in dangerous_commands:
            risk = self.safety.risk_score(cmd)
            assert risk >= 0.6, f"Command '{cmd}' should be high risk, got {risk}"
    
    def test_risk_score_sudo_commands(self):
        """Test risk scoring for sudo commands."""
        sudo_commands = [
            "sudo apt install package",
            "sudo systemctl restart service",
            "sudo rm file.txt",
        ]
        
        for cmd in sudo_commands:
            risk = self.safety.risk_score(cmd)
            assert risk >= 0.3, f"Sudo command '{cmd}' should have elevated risk, got {risk}"
    
    def test_requires_confirmation(self):
        """Test confirmation requirement logic."""
        # High risk commands should require confirmation
        assert self.safety.requires_confirmation("rm -rf /")
        assert self.safety.requires_confirmation("sudo rm -rf important_dir")
        
        # Low risk commands should not require confirmation
        assert not self.safety.requires_confirmation("ls -la")
        assert not self.safety.requires_confirmation("echo hello")
    
    def test_rewrite_to_dry_run(self):
        """Test dry-run rewriting."""
        test_cases = [
            ("rsync -av src/ dest/", "rsync --dry-run -av src/ dest/"),
            ("cp file1 file2", "cp -n file1 file2"),
            ("mv old new", "mv -n old new"),
            ("git clean -fd", "git clean --dry-run -fd"),
        ]
        
        for original, expected in test_cases:
            result = self.safety.rewrite_to_dry_run(original)
            assert expected in result or result == expected, f"Expected '{expected}', got '{result}'"
    
    def test_rewrite_to_dry_run_no_change(self):
        """Test that commands without dry-run options are unchanged."""
        commands = [
            "ls -la",
            "echo hello",
            "cat file.txt",
        ]
        
        for cmd in commands:
            result = self.safety.rewrite_to_dry_run(cmd)
            assert result == cmd, f"Command '{cmd}' should be unchanged, got '{result}'"
    
    def test_get_safety_warnings(self):
        """Test safety warning generation."""
        # Dangerous command should have warnings
        warnings = self.safety.get_safety_warnings("rm -rf /")
        assert len(warnings) > 0
        assert any("DANGER" in warning for warning in warnings)
        
        # Safe command should have no warnings
        warnings = self.safety.get_safety_warnings("ls -la")
        assert len(warnings) == 0
    
    def test_is_safe_for_auto_execution(self):
        """Test auto-execution safety check."""
        # Safe commands should be auto-executable
        assert self.safety.is_safe_for_auto_execution("ls -la")
        assert self.safety.is_safe_for_auto_execution("pwd")
        
        # Dangerous commands should not be auto-executable
        assert not self.safety.is_safe_for_auto_execution("rm -rf /")
        assert not self.safety.is_safe_for_auto_execution("sudo rm file")
    
    def test_empty_command(self):
        """Test handling of empty commands."""
        assert self.safety.risk_score("") == 0.0
        assert self.safety.risk_score("   ") == 0.0
        assert not self.safety.requires_confirmation("")
        assert self.safety.is_safe_for_auto_execution("")
