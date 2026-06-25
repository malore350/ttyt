"""Integration tests for agent mode safety classification with configuration."""

from ttyt_cli.safety import CommandSafety, CommandRisk
from ttyt_cli.config import get_trust_level
from ttyt_cli.trust import TrustLevel


class TestAgentSafetyBehavior:
    """Verify commands are classified correctly for agent mode dispatch."""

    def test_command_classification(self):
        """Previously a false-pass (no assertions, always exited 0)."""
        test_commands = [
            ("ls -la", CommandRisk.SAFE),
            ("git status", CommandRisk.SAFE),
            ("npm install", CommandRisk.CAUTION),
            ("git commit -m 'test'", CommandRisk.CAUTION),
            ("mkdir newdir", CommandRisk.CAUTION),
            ("taskkill /PID 5173", CommandRisk.CAUTION),
            ("echo 'data' > file.txt", CommandRisk.CAUTION),
            ("npm install && npm run build", CommandRisk.CAUTION),
            ("rm -rf /", CommandRisk.DANGER),
            ("taskkill /IM notepad.exe", CommandRisk.DANGER),
            ("git reset --hard", CommandRisk.DANGER),
        ]

        for command, expected_risk in test_commands:
            actual_risk = CommandSafety.classify(command)
            assert actual_risk == expected_risk, (
                f"Mismatch for {command!r}: expected {expected_risk.value}, got {actual_risk.value}"
            )

    def test_trust_level_defaults(self, monkeypatch):
        """Verify that TRUST_LEVEL parsing works."""
        monkeypatch.delenv("TRUST_LEVEL", raising=False)
        assert get_trust_level() == TrustLevel.CAUTIOUS

        monkeypatch.setenv("TRUST_LEVEL", "balanced")
        assert get_trust_level() == TrustLevel.BALANCED

        monkeypatch.setenv("TRUST_LEVEL", "cautious")
        assert get_trust_level() == TrustLevel.CAUTIOUS
