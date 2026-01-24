#!/usr/bin/env python
"""Test script for CommandSafety classifier"""

import sys
sys.path.insert(0, '.')

from safety import CommandSafety, CommandRisk

def test_command_classification():
    """Test various commands to ensure proper classification"""

    test_cases = [
        ("dir", CommandRisk.SAFE),
        ("cd", CommandRisk.SAFE),
        ("cd ..", CommandRisk.SAFE),
        ("git status", CommandRisk.SAFE),
        ("git log", CommandRisk.SAFE),
        ("whoami", CommandRisk.SAFE),
        ("type file.txt", CommandRisk.SAFE),
        ("copy file1.txt file2.txt", CommandRisk.CAUTION),
        ("move file1.txt dest/", CommandRisk.CAUTION),
        ("mkdir newdir", CommandRisk.CAUTION),
        ("npm install", CommandRisk.CAUTION),
        ("pip install package", CommandRisk.CAUTION),
        ("dir | findstr .txt", CommandRisk.SAFE),
        ("dir && echo done", CommandRisk.CAUTION),
        ("dir > output.txt", CommandRisk.CAUTION),
        ("git add .", CommandRisk.CAUTION),
        ("git commit -m 'test'", CommandRisk.CAUTION),
        ("tasklist | grep node", CommandRisk.SAFE),
        ("ipconfig | findstr IPv4", CommandRisk.SAFE),
        ("git status | grep modified", CommandRisk.SAFE),
        ("ls | grep .py | wc -l", CommandRisk.SAFE),
        ("ls | rm -rf", CommandRisk.CAUTION),
        ("tasklist && echo done", CommandRisk.CAUTION),
        ("del file.txt", CommandRisk.DANGER),
        ("rmdir /s /q folder", CommandRisk.DANGER),
        ("git reset --hard", CommandRisk.DANGER),
        ("git clean -fd", CommandRisk.DANGER),
        ("git branch -D feature", CommandRisk.DANGER),
        ("taskkill /f /im notepad.exe", CommandRisk.DANGER),
    ]

    passed = 0
    failed = 0

    print("Testing CommandSafety classifier...")
    print("=" * 60)

    for command, expected_risk in test_cases:
        actual_risk = CommandSafety.classify(command)
        status = "PASS" if actual_risk == expected_risk else "FAIL"

        if actual_risk == expected_risk:
            passed += 1
        else:
            failed += 1

        print(f"{status} | {expected_risk.value.upper().ljust(8)} | {command}")

        if actual_risk != expected_risk:
            print(f"         Expected: {expected_risk.value}")
            print(f"         Got:      {actual_risk.value}")
            print()

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")

    return failed == 0

if __name__ == "__main__":
    success = test_command_classification()
    sys.exit(0 if success else 1)
