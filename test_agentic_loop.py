#!/usr/bin/env python
"""Test script for agentic loop retry behavior"""

import sys
sys.path.insert(0, '.')

from unittest.mock import patch, MagicMock
from typing import Optional, Tuple
from ttyt_cli.providers.base import AIProvider


class MockProvider(AIProvider):
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
    
    def generate_command(self, user_input: str, cwd: str, history_context: str, project_context: str = "") -> str:
        self.generate_command_calls.append({
            'user_input': user_input,
            'cwd': cwd,
            'history_context': history_context,
            'project_context': project_context
        })
        if self.commands_to_return:
            return self.commands_to_return.pop(0)
        return "echo 'mock command'"
    
    def generate_answer(self, user_input: str, cwd: str, history_context: str) -> str:
        return "Mock answer"
    
    def check_goal_achieved(self, goal: str, command: str, output: str, exit_code: int) -> Tuple[bool, str]:
        self.check_goal_achieved_calls.append({
            'goal': goal,
            'command': command,
            'output': output,
            'exit_code': exit_code
        })
        if self.goal_results:
            return self.goal_results.pop(0)
        return (False, "Mock failure")
    
    def generate_fix_command(self, goal: str, failed_command: str, error_output: str, cwd: str, history_context: str, project_context: str = "", exploration_output: str = "") -> str:
        self.generate_fix_command_calls.append({
            'goal': goal,
            'failed_command': failed_command,
            'error_output': error_output,
            'cwd': cwd,
            'history_context': history_context,
            'project_context': project_context,
            'exploration_output': exploration_output
        })
        if self.fix_commands_to_return:
            return self.fix_commands_to_return.pop(0)
        return "echo 'mock fix command'"
    
    def suggest_exploration_command(self, goal: str, failed_command: str, error_output: str, cwd: str) -> Optional[str]:
        self.suggest_exploration_calls.append({
            'goal': goal,
            'failed_command': failed_command,
            'error_output': error_output,
            'cwd': cwd
        })
        if self.exploration_commands_to_return:
            return self.exploration_commands_to_return.pop(0)
        return None


def test_generate_fix_command_is_called_on_retry():
    """Verify that generate_fix_command is called on retry attempts, not generate_command"""
    from ttyt_cli.core import run_agentic_loop, ExecutionResult
    
    provider = MockProvider()
    provider.commands_to_return = ["ls nonexistent_dir"]
    provider.fix_commands_to_return = ["ls .", "pwd"]
    provider.goal_results = [
        (False, "Directory not found"),
        (False, "Still not right"),
        (True, "Success!")
    ]
    
    mock_result_fail = ExecutionResult(exit_code=1, output="ls: cannot access 'nonexistent_dir': No such file or directory", interrupted=False)
    mock_result_success = ExecutionResult(exit_code=0, output="/home/user\n", interrupted=False)
    
    execution_results = [mock_result_fail, mock_result_fail, mock_result_success]
    
    with patch('ttyt_cli.core.execute_for_agent') as mock_exec, \
         patch('ttyt_cli.core.format_history', return_value=""), \
         patch('ttyt_cli.core.is_esc_pressed', return_value=False):
        
        mock_exec.side_effect = execution_results
        
        result = run_agentic_loop(provider, "list files", "/test/dir")
    
    print("\n" + "=" * 60)
    print("TEST: generate_fix_command is called on retry")
    print("=" * 60)
    
    print(f"\ngenerate_command calls: {len(provider.generate_command_calls)}")
    for i, call in enumerate(provider.generate_command_calls):
        print(f"  Call {i+1}: user_input='{call['user_input'][:50]}...'")
    
    print(f"\ngenerate_fix_command calls: {len(provider.generate_fix_command_calls)}")
    for i, call in enumerate(provider.generate_fix_command_calls):
        print(f"  Call {i+1}:")
        print(f"    goal: '{call['goal']}'")
        print(f"    failed_command: '{call['failed_command']}'")
        print(f"    error_output: '{call['error_output'][:100]}...'")
    
    assert len(provider.generate_command_calls) == 1, \
        f"Expected 1 generate_command call (first attempt), got {len(provider.generate_command_calls)}"
    
    assert len(provider.generate_fix_command_calls) == 2, \
        f"Expected 2 generate_fix_command calls (retries), got {len(provider.generate_fix_command_calls)}"
    
    first_fix_call = provider.generate_fix_command_calls[0]
    assert first_fix_call['failed_command'] == "ls nonexistent_dir", \
        f"Expected failed_command to be 'ls nonexistent_dir', got '{first_fix_call['failed_command']}'"
    
    assert "No such file or directory" in first_fix_call['error_output'], \
        f"Expected error_output to contain actual error, got '{first_fix_call['error_output']}'"
    
    print("\n[PASS] generate_fix_command is correctly called on retries")
    print("[PASS] Full error output is passed to generate_fix_command")
    return True


def test_error_output_is_passed_not_summary():
    """Verify the actual command output is passed, not just AI summary"""
    from ttyt_cli.core import run_agentic_loop, ExecutionResult
    
    provider = MockProvider()
    provider.commands_to_return = ["python bad_script.py"]
    provider.fix_commands_to_return = ["python fixed_script.py"]
    provider.goal_results = [
        (False, "Script failed"),  # AI summary - should NOT be passed
        (True, "Success!")
    ]
    
    actual_error = """Traceback (most recent call last):
  File "bad_script.py", line 10, in <module>
    result = divide(10, 0)
  File "bad_script.py", line 5, in divide
    return a / b
ZeroDivisionError: division by zero"""
    
    mock_result_fail = ExecutionResult(exit_code=1, output=actual_error, interrupted=False)
    mock_result_success = ExecutionResult(exit_code=0, output="Done!", interrupted=False)
    
    with patch('ttyt_cli.core.execute_for_agent') as mock_exec, \
         patch('ttyt_cli.core.format_history', return_value=""), \
         patch('ttyt_cli.core.is_esc_pressed', return_value=False):
        
        mock_exec.side_effect = [mock_result_fail, mock_result_success]
        
        run_agentic_loop(provider, "run script", "/test")
    
    print("\n" + "=" * 60)
    print("TEST: Actual error output is passed, not AI summary")
    print("=" * 60)
    
    assert len(provider.generate_fix_command_calls) == 1
    
    fix_call = provider.generate_fix_command_calls[0]
    
    assert "ZeroDivisionError" in fix_call['error_output'], \
        f"Expected actual traceback in error_output, got: '{fix_call['error_output']}'"
    
    assert "Script failed" not in fix_call['error_output'], \
        "AI summary should NOT be in error_output"
    
    print(f"\nError output passed to generate_fix_command:")
    print(f"  {fix_call['error_output'][:200]}...")
    print("\n[PASS] Actual error output is passed, not AI summary")
    return True


def test_first_attempt_uses_generate_command():
    """Verify first attempt uses generate_command, not generate_fix_command"""
    from ttyt_cli.core import run_agentic_loop, ExecutionResult
    
    provider = MockProvider()
    provider.commands_to_return = ["echo hello"]
    provider.goal_results = [(True, "Printed hello")]
    
    mock_result = ExecutionResult(exit_code=0, output="hello\n", interrupted=False)
    
    with patch('ttyt_cli.core.execute_for_agent', return_value=mock_result), \
         patch('ttyt_cli.core.format_history', return_value=""), \
         patch('ttyt_cli.core.is_esc_pressed', return_value=False):
        
        run_agentic_loop(provider, "print hello", "/test")
    
    print("\n" + "=" * 60)
    print("TEST: First attempt uses generate_command")
    print("=" * 60)
    
    assert len(provider.generate_command_calls) == 1, \
        f"Expected 1 generate_command call, got {len(provider.generate_command_calls)}"
    
    assert len(provider.generate_fix_command_calls) == 0, \
        f"Expected 0 generate_fix_command calls, got {len(provider.generate_fix_command_calls)}"
    
    print("\n[PASS] First attempt correctly uses generate_command")
    return True


def test_exploration_before_fix():
    """Verify exploration command is run before fix and output is passed to generate_fix_command"""
    from ttyt_cli.core import run_agentic_loop, ExecutionResult
    
    provider = MockProvider()
    provider.commands_to_return = ["cd documetns"]
    provider.exploration_commands_to_return = ["ls"]
    provider.fix_commands_to_return = ["cd documents"]
    provider.goal_results = [
        (False, "No such directory: documetns"),
        (True, "Changed to documents directory")
    ]
    
    cd_fail = ExecutionResult(exit_code=1, output="bash: cd: documetns: No such file or directory", interrupted=False)
    ls_result = ExecutionResult(exit_code=0, output="documents\ndownloads\npictures\n", interrupted=False)
    cd_success = ExecutionResult(exit_code=0, output="", interrupted=False)
    
    execution_results = [cd_fail, ls_result, cd_success]
    call_index = [0]
    
    def mock_execute(cmd):
        result = execution_results[call_index[0]]
        call_index[0] += 1
        return result
    
    with patch('ttyt_cli.core.execute_for_agent', side_effect=mock_execute), \
         patch('ttyt_cli.core.format_history', return_value=""), \
         patch('ttyt_cli.core.is_esc_pressed', return_value=False):
        
        run_agentic_loop(provider, "change to documents folder", "/home/user")
    
    print("\n" + "=" * 60)
    print("TEST: Exploration before fix (misspelled directory)")
    print("=" * 60)
    
    assert len(provider.suggest_exploration_calls) == 1, \
        f"Expected 1 suggest_exploration call, got {len(provider.suggest_exploration_calls)}"
    
    assert len(provider.generate_fix_command_calls) == 1, \
        f"Expected 1 generate_fix_command call, got {len(provider.generate_fix_command_calls)}"
    
    fix_call = provider.generate_fix_command_calls[0]
    
    assert "documents" in fix_call['exploration_output'], \
        f"Expected 'documents' in exploration_output, got: '{fix_call['exploration_output']}'"
    
    assert "downloads" in fix_call['exploration_output'], \
        f"Expected 'downloads' in exploration_output"
    
    print(f"\nExploration output passed to generate_fix_command:")
    print(f"  {fix_call['exploration_output']}")
    print("\n[PASS] Exploration runs before fix and output is passed to generate_fix_command")
    return True


def test_no_exploration_when_not_needed():
    """Verify exploration is skipped when AI returns None"""
    from ttyt_cli.core import run_agentic_loop, ExecutionResult
    
    provider = MockProvider()
    provider.commands_to_return = ["python script.py"]
    provider.exploration_commands_to_return = [None]
    provider.fix_commands_to_return = ["python3 script.py"]
    provider.goal_results = [
        (False, "python not found"),
        (True, "Script executed")
    ]
    
    fail_result = ExecutionResult(exit_code=127, output="python: command not found", interrupted=False)
    success_result = ExecutionResult(exit_code=0, output="Done", interrupted=False)
    
    execution_results = [fail_result, success_result]
    call_index = [0]
    
    def mock_execute(cmd):
        result = execution_results[call_index[0]]
        call_index[0] += 1
        return result
    
    with patch('ttyt_cli.core.execute_for_agent', side_effect=mock_execute), \
         patch('ttyt_cli.core.format_history', return_value=""), \
         patch('ttyt_cli.core.is_esc_pressed', return_value=False):
        
        run_agentic_loop(provider, "run script", "/test")
    
    print("\n" + "=" * 60)
    print("TEST: No exploration when not needed")
    print("=" * 60)
    
    assert len(provider.suggest_exploration_calls) == 1, \
        f"Expected 1 suggest_exploration call, got {len(provider.suggest_exploration_calls)}"
    
    fix_call = provider.generate_fix_command_calls[0]
    assert fix_call['exploration_output'] == "", \
        f"Expected empty exploration_output when exploration returns None, got: '{fix_call['exploration_output']}'"
    
    print("\n[PASS] No exploration executed when AI says it's not needed")
    return True


if __name__ == "__main__":
    print("Testing Agentic Loop Retry Behavior")
    print("=" * 60)
    
    all_passed = True
    
    try:
        all_passed &= test_first_attempt_uses_generate_command()
    except AssertionError as e:
        print(f"\n[FAIL] {e}")
        all_passed = False
    
    try:
        all_passed &= test_generate_fix_command_is_called_on_retry()
    except AssertionError as e:
        print(f"\n[FAIL] {e}")
        all_passed = False
    
    try:
        all_passed &= test_error_output_is_passed_not_summary()
    except AssertionError as e:
        print(f"\n[FAIL] {e}")
        all_passed = False
    
    try:
        all_passed &= test_exploration_before_fix()
    except AssertionError as e:
        print(f"\n[FAIL] {e}")
        all_passed = False
    
    try:
        all_passed &= test_no_exploration_when_not_needed()
    except AssertionError as e:
        print(f"\n[FAIL] {e}")
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED")
        sys.exit(1)
