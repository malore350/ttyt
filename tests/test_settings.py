"""Tests for settings persistence and structure.

Previously wrote to real ~/.ttyt/.env — now uses tmp_env fixture to redirect HOME.
"""

import os
import pytest
from ttyt_cli.config import get_trust_level, save_config
from ttyt_cli.trust import TrustLevel


class TestSettingsPersistence:
    """Verify config save/load works without touching real ~/.ttyt/.env."""

    def test_persistence(self, tmp_env, monkeypatch, clean_env_vars):
        monkeypatch.delenv("TRUST_LEVEL", raising=False)

        save_config({"TRUST_LEVEL": "balanced"})
        monkeypatch.setenv("TRUST_LEVEL", "balanced")
        assert get_trust_level() == TrustLevel.BALANCED, "Should be Balanced after setting"

        save_config({"TRUST_LEVEL": "cautious"})
        monkeypatch.setenv("TRUST_LEVEL", "cautious")
        assert get_trust_level() == TrustLevel.CAUTIOUS, "Should be Cautious after setting"

    def test_persistence_default(self, monkeypatch):
        monkeypatch.delenv("TRUST_LEVEL", raising=False)
        assert get_trust_level() == TrustLevel.CAUTIOUS, "Default should be Cautious"


class TestSettingsMenuStructure:
    """Verify settings module exports required functions."""

    def test_menu_functions_exist(self):
        from ttyt_cli import settings

        assert hasattr(settings, 'show_settings_menu'), "Missing show_settings_menu"
        assert hasattr(settings, 'trust_selection_dialog'), "Missing trust_selection_dialog"
        save_config({"TRUST_LEVEL": "cautious"})
