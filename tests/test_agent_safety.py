"""Tests for agent mode trust level configuration."""

import pytest
from ttyt_cli.config import get_trust_level
from ttyt_cli.trust import TrustLevel


class TestTrustLevelParsing:
    """Verify TRUST_LEVEL env var parsing."""

    @pytest.mark.parametrize("env_value,expected", [
        (None, TrustLevel.CAUTIOUS),
        ("cautious", TrustLevel.CAUTIOUS),
        ("balanced", TrustLevel.BALANCED),
        ("expert", TrustLevel.EXPERT),
        ("CAUTIOUS", TrustLevel.CAUTIOUS),
        ("BALANCED", TrustLevel.BALANCED),
        ("EXPERT", TrustLevel.EXPERT),
        ("invalid", TrustLevel.CAUTIOUS),
        ("", TrustLevel.CAUTIOUS),
    ])
    def test_parsing(self, env_value, expected, monkeypatch, clean_env_vars):
        if env_value is None:
            monkeypatch.delenv("TRUST_LEVEL", raising=False)
        else:
            monkeypatch.setenv("TRUST_LEVEL", env_value)
        actual = get_trust_level()
        assert actual == expected, (
            f"Expected {expected} for env_value={env_value!r}, got {actual}"
        )
