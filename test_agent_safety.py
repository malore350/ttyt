#!/usr/bin/env python
"""Test script for agent mode safety configuration"""

import os
import sys
sys.path.insert(0, '.')

from ttyt_cli.config import get_agent_require_confirmation

def test_agent_require_confirmation():
    """Test the AGENT_REQUIRE_CONFIRMATION configuration"""
    
    test_cases = [
        (None, False, "Not set - should default to False"),
        ("false", False, "Explicitly false"),
        ("true", True, "Explicitly true"),
        ("FALSE", False, "Case insensitive false"),
        ("TRUE", True, "Case insensitive true"),
        ("0", False, "Numeric 0"),
        ("1", True, "Numeric 1"),
        ("no", False, "String no"),
        ("yes", True, "String yes"),
        ("off", False, "String off"),
        ("on", True, "String on"),
        ("invalid", False, "Invalid value - should default to False"),
    ]
    
    print("Testing AGENT_REQUIRE_CONFIRMATION configuration:")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for env_value, expected, description in test_cases:
        if env_value is None:
            if "AGENT_REQUIRE_CONFIRMATION" in os.environ:
                del os.environ["AGENT_REQUIRE_CONFIRMATION"]
        else:
            os.environ["AGENT_REQUIRE_CONFIRMATION"] = env_value
        
        actual = get_agent_require_confirmation()
        status = "PASS" if actual == expected else "FAIL"
        
        if actual == expected:
            passed += 1
        else:
            failed += 1
        
        env_display = f"'{env_value}'" if env_value is not None else "None"
        print(f"{status} | {env_display:15} -> {str(expected):5} | {description}")
        
        if actual != expected:
            print(f"         Expected: {expected}, Got: {actual}")
    
    print("=" * 80)
    print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    
    return failed == 0

if __name__ == "__main__":
    success = test_agent_require_confirmation()
    sys.exit(0 if success else 1)
