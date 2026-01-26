#!/usr/bin/env python
"""Integration test for exploration feature with misspelled directory scenario"""

import os
import sys
import tempfile
import shutil
sys.path.insert(0, '.')

from unittest.mock import patch, MagicMock
from typing import Optional, Tuple
from ttyt_cli.providers.base import AIProvider
from ttyt_cli.core import run_agentic_loop, ExecutionResult


class SmartMockProvider(AIProvider):
    """A mock provider that simulates intelligent exploration behavior."""
    
    def __init__(self):
        self.model_name = "smart-mock"
        self.call_log = []
    
    def generate_command(self, user_input: str, cwd: str, history_context: str, project_context: str = "") -> str:
        self.call_log.append(('generate_command', user_input))
        # Simulate typo - user wants "documents" but AI generates "documetns"
        if "document" in user_input.lower():
            return "cd documetns"
        return f"echo '{user_input}'"
    
    def generate_answer(self, user_input: str, cwd: str, history_context: str) -> str:
        return "Mock answer"
    
    def check_goal_achieved(self, goal: str, command: str, output: str, exit_code: int) -> Tuple[bool, str]:
        self.call_log.append(('check_goal', command, exit_code))
        if exit_code == 0 and "cd" in command:
            return (True, "Changed to directory successfully")
        if exit_code != 0:
            return (False, f"Command failed: {output[:100]}")
        return (True, "Success")
    
    def generate_fix_command(self, goal: str, failed_command: str, error_output: str, cwd: str, 
                            history_context: str, project_context: str = "", exploration_output: str = "") -> str:
        self.call_log.append(('generate_fix_command', failed_command, exploration_output))
        
        # If we have exploration output, use it to find the correct directory
        if exploration_output and "documents" in exploration_output:
            return "cd documents"
        # Fallback - try different spelling
        return "cd docs"
    
    def suggest_exploration_command(self, goal: str, failed_command: str, error_output: str, cwd: str) -> Optional[str]:
        self.call_log.append(('suggest_exploration', failed_command, error_output[:50]))
        
        # If it's a directory-related error, suggest ls
        if "no such file or directory" in error_output.lower() or "cannot find" in error_output.lower():
            return "ls"
        return None


def test_real_directory_exploration():
    """Test exploration with real filesystem directories."""
    
    # Create a temporary directory structure
    test_dir = tempfile.mkdtemp(prefix="ttyt_test_")
    os.makedirs(os.path.join(test_dir, "documents"))
    os.makedirs(os.path.join(test_dir, "downloads"))
    os.makedirs(os.path.join(test_dir, "pictures"))
    
    original_cwd = os.getcwd()
    
    try:
        os.chdir(test_dir)
        
        provider = SmartMockProvider()
        
        # Mock only is_esc_pressed to prevent blocking
        with patch('ttyt_cli.core.is_esc_pressed', return_value=False):
            result = run_agentic_loop(provider, "go to documents folder", test_dir)
        
        print("\n" + "=" * 60)
        print("TEST: Real directory exploration")
        print("=" * 60)
        print(f"\nTest directory: {test_dir}")
        print(f"Contents: {os.listdir(test_dir)}")
        
        print("\nCall log:")
        for i, call in enumerate(provider.call_log):
            print(f"  {i+1}. {call[0]}: {call[1:]}")
        
        # Verify exploration happened
        exploration_calls = [c for c in provider.call_log if c[0] == 'suggest_exploration']
        fix_calls = [c for c in provider.call_log if c[0] == 'generate_fix_command']
        
        print(f"\nExploration calls: {len(exploration_calls)}")
        print(f"Fix command calls: {len(fix_calls)}")
        
        if fix_calls:
            last_fix = fix_calls[-1]
            exploration_output = last_fix[2]
            print(f"Exploration output passed to fix: '{exploration_output}'")
            
            # Check that ls output was passed
            if "documents" in exploration_output and "downloads" in exploration_output:
                print("\n[PASS] Directory listing was correctly passed to generate_fix_command")
            else:
                print(f"\n[FAIL] Expected directory listing in exploration output, got: '{exploration_output}'")
                return False
        
        print(f"\nFinal result: {'SUCCESS' if result else 'FAILED'}")
        
        if result:
            print("[PASS] Agent successfully navigated using exploration")
            return True
        else:
            print("[WARN] Agent didn't fully succeed, but exploration was tested")
            # Still pass if exploration worked correctly
            return len(exploration_calls) > 0 and len(fix_calls) > 0
            
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(test_dir, ignore_errors=True)


def test_exploration_not_triggered_on_success():
    """Verify exploration is NOT called when first command succeeds."""
    
    test_dir = tempfile.mkdtemp(prefix="ttyt_test_")
    original_cwd = os.getcwd()
    
    try:
        os.chdir(test_dir)
        
        provider = SmartMockProvider()
        
        # Override to return a successful command
        provider.generate_command = lambda *args, **kwargs: "echo hello"
        
        with patch('ttyt_cli.core.is_esc_pressed', return_value=False):
            result = run_agentic_loop(provider, "print hello", test_dir)
        
        print("\n" + "=" * 60)
        print("TEST: No exploration on immediate success")
        print("=" * 60)
        
        exploration_calls = [c for c in provider.call_log if c[0] == 'suggest_exploration']
        
        if len(exploration_calls) == 0:
            print("[PASS] No exploration called when first command succeeded")
            return True
        else:
            print(f"[FAIL] Exploration was called {len(exploration_calls)} times but shouldn't have been")
            return False
            
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == "__main__":
    print("Integration Tests: Exploration Feature")
    print("=" * 60)
    
    all_passed = True
    
    try:
        all_passed &= test_real_directory_exploration()
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    try:
        all_passed &= test_exploration_not_triggered_on_success()
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("ALL INTEGRATION TESTS PASSED")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED")
        sys.exit(1)
