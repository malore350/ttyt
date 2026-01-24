import re
from enum import Enum

class CommandRisk(Enum):
    SAFE = "safe"
    CAUTION = "caution"
    DANGER = "danger"

class CommandSafety:
    """Command safety classifier with three-tier risk assessment (Bash-centric)"""

    # Safe commands - read-only operations
    SAFE_COMMANDS = {
        # Unix/Bash commands (read-only)
        "ls", "cat", "pwd", "whoami", "hostname", "date", "uptime",
        "grep", "egrep", "fgrep", "find", "locate", "which", "whereis",
        "head", "tail", "less", "more", "wc", "sort", "uniq", "du", "df",
        "ps", "top", "free", "id", "groups", "env", "printenv",
        "git",  # Will be refined in categorization
        "python", "python3", "node", "java", "go", "rustc", "ruby", "perl",
        "awk", "sed", "bc", "expr",
        "cd", "dir", "type",
    }

    # Git commands that are always safe
    SAFE_GIT_COMMANDS = {
        "git status", "git log", "git branch", "git show", "git diff", "git remote",
        "git config --get", "git describe", "git rev-parse", "git tag", "git blame",
        "git log --oneline", "git log --graph", "git branch -a", "git reflog",
    }

    # Danger commands - destructive operations
    DANGER_COMMANDS = {
        # Unix destructive
        "rm -rf /", "rm -rf *", "mkfs", "dd", "shred", "wipe",
        "chmod -R 777 /", "chown -R",
        # Process termination
        "kill -9", "pkill -9", "killall -9",
        # System-destructive (if running with sudo/privilege)
        "format", "fdisk", "parted", "del", "rmdir", "taskkill",
    }

    # Caution patterns - commands requiring confirmation
    CAUTION_PATTERNS = [
        r'\|\|',
        r'&&',
        r'\|',
        r';',
        r'&\s*$',
        r'>',
        r'>>',
        r'<',
        r'\$\(',
        r'`',
        r'sudo',
    ]

    # Package managers
    PACKAGE_MANAGERS = {
        "npm", "npm.exe",
        "pip", "pip3", "pip.exe",
        "yarn", "yarn.exe",
        "pnpm", "pnpm.exe",
        "nuget", "nuget.exe",
        "dotnet", "dotnet.exe",
        "cargo", "cargo.exe",
        "gem", "gem.exe",
        "composer", "composer.phar",
        "brew", "choco", "chocolatey", "scoop",
        "winget", "apt-get", "apt", "yum", "dnf", "pacman",
    }

    @classmethod
    def classify(cls, command: str) -> CommandRisk:
        """
        Classify a command by risk level.
        Returns: CommandRisk (SAFE, CAUTION, DANGER)
        """
        if not command or not command.strip():
            return CommandRisk.CAUTION

        cmd_lower = command.strip().lower()

        # Check for danger commands first (highest priority)
        for danger_cmd in cls.DANGER_COMMANDS:
            if cmd_lower.startswith(danger_cmd + " ") or cmd_lower == danger_cmd:
                return CommandRisk.DANGER

        # Check for command chaining/redirection (caution)
        for pattern in cls.CAUTION_PATTERNS:
            if re.search(pattern, command):
                return CommandRisk.CAUTION

        # Check for package managers
        first_token = cmd_lower.split()[0] if cmd_lower.split() else ""
        if first_token in cls.PACKAGE_MANAGERS:
            return CommandRisk.CAUTION

        # Check for safe commands
        for safe_cmd in cls.SAFE_COMMANDS:
            if cmd_lower.startswith(safe_cmd + " ") or cmd_lower == safe_cmd:
                # Special handling for git
                if safe_cmd == "git":
                    return cls._classify_git_command(command)
                return CommandRisk.SAFE

        # File modification commands (caution)
        file_mod_commands = {"copy", "move", "ren", "rename", "xcopy", "robocopy", "md", "mkdir"}
        for mod_cmd in file_mod_commands:
            if cmd_lower.startswith(mod_cmd + " ") or cmd_lower == mod_cmd:
                return CommandRisk.CAUTION

        # Unknown command - treat as caution
        return CommandRisk.CAUTION

    @classmethod
    def _classify_git_command(cls, command: str) -> CommandRisk:
        """
        Special classification for git commands.
        Some git commands are safe, others need caution.
        """
        cmd_lower = command.strip().lower()

        danger_git = [
            "git reset --hard", "git clean -fd", "git clean -f", "git clean -d",
            "git tag -d", "git tag --delete",
            "git push --force", "git push -f", "git push --force-with-lease",
            "git rebase",
            "git checkout -f", "git restore --force",
            "git branch -d",
            "git branch --delete --force",
        ]
        for danger in danger_git:
            if cmd_lower.startswith(danger):
                return CommandRisk.DANGER

        caution_git = [
            "git add", "git commit", "git push", "git pull", "git merge",
            "git checkout", "git switch", "git restore", "git stash",
            "git cherry-pick", "git revert", "git reset",
        ]
        for caution in caution_git:
            if cmd_lower.startswith(caution):
                return CommandRisk.CAUTION

        for safe_git in cls.SAFE_GIT_COMMANDS:
            if cmd_lower.startswith(safe_git):
                return CommandRisk.SAFE

        return CommandRisk.CAUTION

    @classmethod
    def get_risk_description(cls, risk: CommandRisk) -> str:
        """Get human-readable description for risk level"""
        descriptions = {
            CommandRisk.SAFE: "Read-only command, auto-executing",
            CommandRisk.CAUTION: "Requires confirmation - may modify system",
            CommandRisk.DANGER: "BLOCKED - destructive operation",
        }
        return descriptions.get(risk, "Unknown risk")
