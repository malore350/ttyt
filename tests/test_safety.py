"""Tests for CommandSafety classifier."""

from ttyt_cli.safety import CommandSafety, CommandRisk


class TestCommandSafety:
    """Verify classification of various commands."""

    def test_classify(self):
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

        for command, expected_risk in test_cases:
            actual_risk = CommandSafety.classify(command)
            assert actual_risk == expected_risk, (
                f"Mismatch for {command!r}: expected {expected_risk.value}, got {actual_risk.value}"
            )
