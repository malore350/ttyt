#!/usr/bin/env python
"""Integration test for agent mode safety with configuration"""

import os
import sys
sys.path.insert(0, '.')

from ttyt_cli.safety import CommandSafety, CommandRisk

def test_agent_safety_behavior():
    """Test how different commands are classified for agent mode"""
    
    test_commands = [
        ("ls -la", CommandRisk.SAFE, "Read-only"),
        ("git status", CommandRisk.SAFE, "Read-only git"),
        ("npm install", CommandRisk.CAUTION, "Package manager"),
        ("git commit -m 'test'", CommandRisk.CAUTION, "Git write operation"),
        ("mkdir newdir", CommandRisk.CAUTION, "File system modification"),
        ("taskkill /PID 5173", CommandRisk.CAUTION, "Process termination with PID"),
        ("echo 'data' > file.txt", CommandRisk.CAUTION, "File redirection"),
        ("npm install && npm run build", CommandRisk.CAUTION, "Command chain"),
        ("rm -rf /", CommandRisk.DANGER, "Destructive operation"),
        ("taskkill /IM notepad.exe", CommandRisk.DANGER, "Dangerous process kill"),
        ("git reset --hard", CommandRisk.DANGER, "Destructive git operation"),
    ]
    
    print("\nAgent Mode Safety Classification:")
    print("=" * 90)
    print(f"{'Command':<40} {'Risk Level':<15} {'Agent Behavior (default)':<25}")
    print("-" * 90)
    
    for command, expected_risk, description in test_commands:
        actual_risk = CommandSafety.classify(command)
        
        if actual_risk == CommandRisk.DANGER:
            behavior = "BLOCKED"
        elif actual_risk == CommandRisk.CAUTION:
            behavior = "AUTO-APPROVED"
        else:
            behavior = "AUTO-EXECUTE"
        
        status = "PASS" if actual_risk == expected_risk else "FAIL"
        print(f"{status} {command:<38} {actual_risk.value:<15} {behavior:<25}")
    
    print("=" * 90)
    print("\nWith AGENT_REQUIRE_CONFIRMATION=true:")
    print("  - DANGER commands: BLOCKED (same)")
    print("  - CAUTION commands: REQUIRES USER CONFIRMATION")
    print("  - SAFE commands: AUTO-EXECUTE (same)")
    print()

if __name__ == "__main__":
    test_agent_safety_behavior()
