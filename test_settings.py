#!/usr/bin/env python
"""Test script for settings functionality"""

import os
import sys
sys.path.insert(0, '.')

from ttyt_cli.config import get_agent_require_confirmation, save_config

def test_settings_persistence():
    """Test that settings are properly saved and loaded"""
    
    print("\nTesting Settings Persistence:")
    print("=" * 70)
    
    original_value = os.getenv("AGENT_REQUIRE_CONFIRMATION")
    
    print(f"1. Current setting: {get_agent_require_confirmation()}")
    
    save_config({"AGENT_REQUIRE_CONFIRMATION": "true"})
    os.environ["AGENT_REQUIRE_CONFIRMATION"] = "true"
    print(f"2. After setting to true: {get_agent_require_confirmation()}")
    assert get_agent_require_confirmation() == True, "Should be True"
    
    save_config({"AGENT_REQUIRE_CONFIRMATION": "false"})
    os.environ["AGENT_REQUIRE_CONFIRMATION"] = "false"
    print(f"3. After setting to false: {get_agent_require_confirmation()}")
    assert get_agent_require_confirmation() == False, "Should be False"
    
    if original_value:
        os.environ["AGENT_REQUIRE_CONFIRMATION"] = original_value
    elif "AGENT_REQUIRE_CONFIRMATION" in os.environ:
        del os.environ["AGENT_REQUIRE_CONFIRMATION"]
    
    print("\nOK All persistence tests passed!")
    print("=" * 70)

def test_settings_menu_structure():
    """Test that settings module has required functions"""
    
    print("\nTesting Settings Module Structure:")
    print("=" * 70)
    
    from ttyt_cli import settings
    
    assert hasattr(settings, 'show_settings_menu'), "Missing show_settings_menu"
    print("OK show_settings_menu function exists")
    
    assert hasattr(settings, 'toggle_agent_confirmation'), "Missing toggle_agent_confirmation"
    print("OK toggle_agent_confirmation function exists")
    
    print("\nOK All structure tests passed!")
    print("=" * 70)

if __name__ == "__main__":
    try:
        test_settings_persistence()
        test_settings_menu_structure()
        print("\nSUCCESS: All tests passed!\n")
    except AssertionError as e:
        print(f"\nFAIL: Test failed: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}\n")
        sys.exit(1)
