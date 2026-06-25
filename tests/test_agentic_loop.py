"""Tests for agentic loop retry behavior."""

from unittest.mock import patch
from typing import Optional, Tuple

import pytest

from ttyt_cli.providers.base import AIProvider


class MockProvider(AIProvider):
    """Mock provider with queued responses. Accepts os_name to match AIProvider ABC."""

    def __init__(self):
        self.model_name = "mock-model"
        self.generate_command_calls = []
        self.generate_fix_command_calls = []
        self.check_goal_achieved_calls = []
        self.suggest_exploration_calls = []
        self.commands_to_return = []
        self.fix_commands_to_return = []
        self.goal_results = []
        self.exploration_commands_to_return = []

    def generate_command(self, user_input, cwd, history_context, os_name, project_context=""):
        self.generate_command_calls.append({
            'user_input': user_input,
            'cwd': cwd,
            'history_context': history_context,
            'os_name': os_name,
            'project_context': project_context
        })
        if self.commands_to_return:
            return self.commands_to_return.pop(0)
        return "echo 'mock command'"

    def generate_answer(self, user_input, cwd, history_context, os_name):
        return "Mock answer"

    def check_goal_achieved(self, goal, command, output, exit_code, os_name):
        self.check_goal_achieved_calls.append({
            'goal': goal,
            'command': command,
            'output': output,
            'exit_code': exit_code,
            'os_name': os_name
        })
        if self.goal_results:
            return self.goal_results.pop(0)
        return (False, "Mock failure")

    def generate_fix_command(self, goal, failed_command, error_output, cwd, history_context, os_name, project_context="", exploration_output=""):
        self.generate_fix_command_calls.append({
            'goal': goal,
            'failed_command': failed_command,
            'error_output': error_output,
            'cwd': cwd,
            'history_context': history_context,
            'os_name': os_name,
            'project_context': project_context,
            'exploration_output': exploration_output
        })
        if self.fix_commands_to_return:
            return self.fix_commands_to_return.pop(0)
        return "echo 'mock fix command'"

    def suggest_exploration_command(self, goal, failed_command, error_output, cwd, os_name):
        self.suggest_exploration_calls.append({
            'goal': goal,
            'failed_command': failed_command,
            'error_output': error_output,
            'cwd': cwd,
            'os_name': os_name
        })
        if self.exploration_commands_to_return:
            return self.exploration_commands_to_return.pop(0)
        return None


class TestAgenticLoop:
    """Verify agentic loop dispatch: generate_command on first try,
    generate_fix_command on retries, exploration before fix."""

    def test_first_attempt_uses_generate_command(self):
        from ttyt_cli.agentic import run_agentic_loop
        from ttyt_cli.core import ExecutionResult
        provider = MockProvider()
        provider.commands_to_return = ["echo hello"]
        provider.goal_results = [(True, "Printed hello")]

        mock_result = ExecutionResult(exit_code=0, output="hello\n", interrupted=False)

        with patch('ttyt_cli.agentic.execute_command', return_value=mock_result), \
             patch('ttyt_cli.agentic.format_history', return_value=""), \
             patch('ttyt_cli.core.is_cancel_pressed', return_value=False):

            run_agentic_loop(provider, "print hello", "/test")

        assert len(provider.generate_command_calls) == 1, \
            f"Expected 1 generate_command call, got {len(provider.generate_command_calls)}"
        assert len(provider.generate_fix_command_calls) == 0, \
            f"Expected 0 generate_fix_command calls, got {len(provider.generate_fix_command_calls)}"

    def test_generate_fix_command_is_called_on_retry(self):
        from ttyt_cli.agentic import run_agentic_loop
        from ttyt_cli.core import ExecutionResult
        provider = MockProvider()
        provider.commands_to_return = ["ls nonexistent_dir"]
        provider.fix_commands_to_return = ["ls .", "pwd"]
        provider.goal_results = [
            (False, "Directory not found"),
            (False, "Still not right"),
            (True, "Success!"),
        ]

        mock_result_fail = ExecutionResult(exit_code=1, output="ls: cannot access 'nonexistent_dir': No such file or directory", interrupted=False)
        mock_result_success = ExecutionResult(exit_code=0, output="/home/user\n", interrupted=False)

        execution_results = [mock_result_fail, mock_result_fail, mock_result_success]

        with patch('ttyt_cli.agentic.execute_command') as mock_exec, \
             patch('ttyt_cli.agentic.format_history', return_value=""), \
             patch('ttyt_cli.core.is_cancel_pressed', return_value=False):

            mock_exec.side_effect = execution_results

            run_agentic_loop(provider, "list files", "/test/dir")

        assert len(provider.generate_command_calls) == 1, \
            f"Expected 1 generate_command call (first attempt), got {len(provider.generate_command_calls)}"
        assert len(provider.generate_fix_command_calls) == 2, \
            f"Expected 2 generate_fix_command calls (retries), got {len(provider.generate_fix_command_calls)}"

        first_fix_call = provider.generate_fix_command_calls[0]
        assert first_fix_call['failed_command'] == "ls nonexistent_dir", \
            f"Expected failed_command='ls nonexistent_dir', got '{first_fix_call['failed_command']}'"
        assert "No such file or directory" in first_fix_call['error_output'], \
            f"Expected error_output to contain actual error, got '{first_fix_call['error_output']}'"

    def test_error_output_is_passed_not_summary(self):
        from ttyt_cli.agentic import run_agentic_loop
        from ttyt_cli.core import ExecutionResult
        provider = MockProvider()
        provider.commands_to_return = ["python bad_script.py"]
        provider.fix_commands_to_return = ["python fixed_script.py"]
        provider.goal_results = [
            (False, "Script failed"),
            (True, "Success!"),
        ]

        actual_error = """Traceback (most recent call last):
  File "bad_script.py", line 10, in <module>
    result = divide(10, 0)
  File "bad_script.py", line 5, in divide
    return a / b
ZeroDivisionError: division by zero"""

        mock_result_fail = ExecutionResult(exit_code=1, output=actual_error, interrupted=False)
        mock_result_success = ExecutionResult(exit_code=0, output="Done!", interrupted=False)

        with patch('ttyt_cli.agentic.execute_command') as mock_exec, \
             patch('ttyt_cli.agentic.format_history', return_value=""), \
             patch('ttyt_cli.core.is_cancel_pressed', return_value=False):

            mock_exec.side_effect = [mock_result_fail, mock_result_success]
            run_agentic_loop(provider, "run script", "/test")

        assert len(provider.generate_fix_command_calls) == 1
        fix_call = provider.generate_fix_command_calls[0]

        assert "ZeroDivisionError" in fix_call['error_output'], \
            f"Expected actual traceback in error_output, got: '{fix_call['error_output']}'"
        assert "Script failed" not in fix_call['error_output'], \
            "AI summary should NOT be in error_output"

    def test_exploration_before_fix(self):
        from ttyt_cli.agentic import run_agentic_loop
        from ttyt_cli.core import ExecutionResult
        provider = MockProvider()
        provider.commands_to_return = ["cd documetns"]
        provider.exploration_commands_to_return = ["ls"]
        provider.fix_commands_to_return = ["cd documents"]
        provider.goal_results = [
            (False, "No such directory: documetns"),
            (True, "Changed to documents directory"),
        ]

        cd_fail = ExecutionResult(exit_code=1, output="bash: cd: documetns: No such file or directory", interrupted=False)
        ls_result = ExecutionResult(exit_code=0, output="documents\ndownloads\npictures\n", interrupted=False)
        cd_success = ExecutionResult(exit_code=0, output="", interrupted=False)

        execution_results = [cd_fail, ls_result, cd_success]
        call_index = [0]

        def mock_execute(cmd, auto_approve_caution=False, **kwargs):
            result = execution_results[call_index[0]]
            call_index[0] += 1
            return result

        with patch('ttyt_cli.agentic.execute_command', side_effect=mock_execute), \
             patch('ttyt_cli.agentic.format_history', return_value=""), \
             patch('ttyt_cli.core.is_cancel_pressed', return_value=False):

            run_agentic_loop(provider, "change to documents folder", "/home/user")

        assert len(provider.suggest_exploration_calls) == 1, \
            f"Expected 1 suggest_exploration call, got {len(provider.suggest_exploration_calls)}"
        assert len(provider.generate_fix_command_calls) == 1, \
            f"Expected 1 generate_fix_command call, got {len(provider.generate_fix_command_calls)}"

        fix_call = provider.generate_fix_command_calls[0]
        assert "documents" in fix_call['exploration_output'], \
            f"Expected 'documents' in exploration_output, got: '{fix_call['exploration_output']}'"
        assert "downloads" in fix_call['exploration_output'], \
            f"Expected 'downloads' in exploration_output"

    def test_no_exploration_when_not_needed(self):
        from ttyt_cli.agentic import run_agentic_loop
        from ttyt_cli.core import ExecutionResult
        provider = MockProvider()
        provider.commands_to_return = ["python script.py"]
        provider.exploration_commands_to_return = [None]
        provider.fix_commands_to_return = ["python3 script.py"]
        provider.goal_results = [
            (False, "python not found"),
            (True, "Script executed"),
        ]

        fail_result = ExecutionResult(exit_code=127, output="python: command not found", interrupted=False)
        success_result = ExecutionResult(exit_code=0, output="Done", interrupted=False)

        execution_results = [fail_result, success_result]
        call_index = [0]

        def mock_execute(cmd, auto_approve_caution=False, **kwargs):
            result = execution_results[call_index[0]]
            call_index[0] += 1
            return result

        with patch('ttyt_cli.agentic.execute_command', side_effect=mock_execute), \
             patch('ttyt_cli.agentic.format_history', return_value=""), \
             patch('ttyt_cli.core.is_cancel_pressed', return_value=False):

            run_agentic_loop(provider, "run script", "/test")

        assert len(provider.suggest_exploration_calls) == 1, \
            f"Expected 1 suggest_exploration call, got {len(provider.suggest_exploration_calls)}"

        fix_call = provider.generate_fix_command_calls[0]
        assert fix_call['exploration_output'] == "", \
            f"Expected empty exploration_output when exploration returns None, got: '{fix_call['exploration_output']}'"
