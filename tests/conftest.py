"""Pytest fixtures and configuration for ttyt tests."""

import os
import pytest
from typing import Optional, Tuple
from ttyt_cli.providers.base import AIProvider


class _MockProvider(AIProvider):
    """Simple mock provider returning canned responses for all 5 methods."""

    def __init__(self):
        self.model_name = "mock-model"
        self.generate_command_return = "echo 'mock command'"
        self.generate_answer_return = "Mock answer"
        self.check_goal_achieved_return = (False, "Mock failure")
        self.generate_fix_command_return = "echo 'mock fix command'"
        self.suggest_exploration_command_return = None
        self.call_log = []

    def generate_command(self, user_input, cwd, history_context, os_name, project_context=""):
        self.call_log.append(('generate_command', user_input, cwd, history_context, os_name, project_context))
        return self.generate_command_return

    def generate_answer(self, user_input, cwd, history_context, os_name):
        self.call_log.append(('generate_answer', user_input, cwd, history_context, os_name))
        return self.generate_answer_return

    def check_goal_achieved(self, goal, command, output, exit_code, os_name):
        self.call_log.append(('check_goal_achieved', goal, command, output, exit_code, os_name))
        return self.check_goal_achieved_return

    def generate_fix_command(self, goal, failed_command, error_output, cwd, history_context, os_name, project_context="", exploration_output=""):
        self.call_log.append(('generate_fix_command', goal, failed_command, error_output, cwd, history_context, os_name, project_context, exploration_output))
        return self.generate_fix_command_return

    def suggest_exploration_command(self, goal, failed_command, error_output, cwd, os_name):
        self.call_log.append(('suggest_exploration', goal, failed_command, error_output, cwd, os_name))
        return self.suggest_exploration_command_return


@pytest.fixture
def mock_provider():
    """Return a MockProvider instance with canned responses."""
    return _MockProvider()


@pytest.fixture
def tmp_env(tmp_path, monkeypatch):
    """Redirect HOME to a temp path so ~/.ttyt/.env writes go to tmpdir."""
    fake_home = tmp_path / "fake_home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    return fake_home


@pytest.fixture
def clean_env_vars():
    """Save and restore os.environ around a test."""
    saved = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(saved)
