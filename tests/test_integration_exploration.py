"""Integration tests for exploration feature with misspelled directory scenario."""

import os
import tempfile
import shutil

from unittest.mock import patch
from typing import Optional, Tuple

import pytest

from ttyt_cli.providers.base import AIProvider


class SmartMockProvider(AIProvider):
    """A mock provider that simulates intelligent exploration behavior.
    Accepts os_name to match AIProvider ABC."""

    def __init__(self):
        self.model_name = "smart-mock"
        self.call_log = []

    def generate_command(self, user_input, cwd, history_context, os_name, project_context=""):
        self.call_log.append(('generate_command', user_input))
        if "document" in user_input.lower():
            return "cd documetns"
        return f"echo '{user_input}'"

    def generate_answer(self, user_input, cwd, history_context, os_name):
        return "Mock answer"

    def check_goal_achieved(self, goal, command, output, exit_code, os_name):
        self.call_log.append(('check_goal', command, exit_code))
        if exit_code == 0 and "cd" in command:
            return (True, "Changed to directory successfully")
        if exit_code != 0:
            return (False, f"Command failed: {output[:100]}")
        return (True, "Success")

    def generate_fix_command(self, goal, failed_command, error_output, cwd,
                             history_context, os_name, project_context="", exploration_output=""):
        self.call_log.append(('generate_fix_command', failed_command, exploration_output))
        if exploration_output and "documents" in exploration_output:
            return "cd documents"
        return "cd docs"

    def suggest_exploration_command(self, goal, failed_command, error_output, cwd, os_name):
        self.call_log.append(('suggest_exploration', failed_command, error_output[:50]))
        if "no such file or directory" in error_output.lower() or "cannot find" in error_output.lower():
            return "ls"
        return None


class TestIntegrationExploration:
    """Verify exploration behavior with real filesystem directories."""

    def test_real_directory_exploration(self):
        from ttyt_cli.agentic import run_agentic_loop
        test_dir = tempfile.mkdtemp(prefix="ttyt_test_")
        os.makedirs(os.path.join(test_dir, "documents"))
        os.makedirs(os.path.join(test_dir, "downloads"))
        os.makedirs(os.path.join(test_dir, "pictures"))
        original_cwd = os.getcwd()

        try:
            os.chdir(test_dir)

            provider = SmartMockProvider()

            with patch('ttyt_cli.core.is_cancel_pressed', return_value=False):
                result = run_agentic_loop(provider, "go to documents folder", test_dir)

            exploration_calls = [c for c in provider.call_log if c[0] == 'suggest_exploration']
            fix_calls = [c for c in provider.call_log if c[0] == 'generate_fix_command']

            assert len(exploration_calls) > 0, "Expected at least one exploration call"
            assert len(fix_calls) > 0, "Expected at least one fix command call"

            if fix_calls:
                last_fix = fix_calls[-1]
                exploration_output = last_fix[2]
                assert "documents" in exploration_output, \
                    f"Expected 'documents' in exploration output, got: '{exploration_output}'"
                assert "downloads" in exploration_output

        finally:
            os.chdir(original_cwd)
            shutil.rmtree(test_dir, ignore_errors=True)

    def test_exploration_not_triggered_on_success(self):
        from ttyt_cli.agentic import run_agentic_loop
        test_dir = tempfile.mkdtemp(prefix="ttyt_test_")
        original_cwd = os.getcwd()

        try:
            os.chdir(test_dir)

            provider = SmartMockProvider()
            provider.generate_command = lambda *args, **kwargs: "echo hello"

            with patch('ttyt_cli.core.is_cancel_pressed', return_value=False):
                run_agentic_loop(provider, "print hello", test_dir)

            exploration_calls = [c for c in provider.call_log if c[0] == 'suggest_exploration']
            assert len(exploration_calls) == 0, \
                f"Exploration was called {len(exploration_calls)} times but shouldn't have been"

        finally:
            os.chdir(original_cwd)
            shutil.rmtree(test_dir, ignore_errors=True)
