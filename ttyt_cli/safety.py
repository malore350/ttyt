import re
from enum import Enum
from typing import List, Tuple

class CommandRisk(Enum):
    SAFE = "safe"
    CAUTION = "caution"
    DANGER = "danger"
    
    def __lt__(self, other):
        order = {CommandRisk.SAFE: 0, CommandRisk.CAUTION: 1, CommandRisk.DANGER: 2}
        return order[self] < order[other]
    
    def __gt__(self, other):
        order = {CommandRisk.SAFE: 0, CommandRisk.CAUTION: 1, CommandRisk.DANGER: 2}
        return order[self] > order[other]

class CommandSafety:
    """Command safety classifier with three-tier risk assessment (Bash-centric)"""

    # Safe commands - read-only operations
    SAFE_COMMANDS = {
        # Unix/Bash commands (read-only)
        "ls", "cat", "pwd", "whoami", "hostname", "date", "uptime",
        "grep", "egrep", "fgrep", "locate", "which", "whereis",
        "head", "tail", "less", "more", "wc", "sort", "uniq", "du", "df",
        "ps", "top", "free", "id", "groups", "env", "printenv",
        "git",
        "java", "rustc", "bc", "expr",
        "cd", "dir", "type",
        "diff", "basename", "dirname", "realpath", "file", "stat",
        "md5sum", "sha1sum", "sha256sum", "base64", "strings",
        "uname", "history", "echo", "clear", "man", "help",
        "tasklist", "ipconfig", "systeminfo", "netstat", "findstr", "attrib", "where",
        "ll", "la", "l", "winpty",
    }

    # Git commands that are always safe
    SAFE_GIT_COMMANDS = {
        "git status", "git log", "git branch", "git show", "git diff", "git remote",
        "git config --get", "git describe", "git rev-parse", "git tag", "git blame",
        "git log --oneline", "git log --graph", "git branch -a", "git reflog",
        "git version", "git help", "git ls-files", "git ls-tree", "git branch --list",
        "git remote -v", "git stash list", "git shortlog", "git cat-file",
    }

    # Danger commands - destructive operations
    DANGER_COMMANDS = {
        # Unix destructive
        "rm -rf /", "rm -rf *", "rm -rf ~", "rm -rf $HOME", "rm -rf /*",
        "rm -rf .", "rm -rf / ", "rm -rf /home", "rm -rf /var",
        "rm -rf /etc", "rm -rf /tmp/", "rm -rf --no-preserve-root",
        "rm -r ~", "rm -r $HOME", "rm -r /*", "rm -r .", "rm -r /",
        "mkfs", "dd", "shred", "wipe",
        "chmod -R 777 /", "chown -R",
        # Process termination
        "kill -9", "pkill -9", "killall -9",
        # System-destructive (if running with sudo/privilege)
        "format", "fdisk", "parted", "del", "rmdir",
        # Dangerous wrappers
        "eval", "exec rm", "exec sh", "exec bash", "exec zsh",
        "source", "pwsh",
    }

    # Danger regex patterns for variable-path destructive commands
    DANGER_REGEX = [
        r'^rm\s+-r[fv]?\s+~',
        r'^rm\s+-r[fv]?\s+\$home',
        r'^rm\s+-r[fv]?\s+/',
        r'^rm\s+-r[fv]?\s+\.',
    ]

    # Caution patterns - commands requiring confirmation (excluding chain operators, handled separately)
    CAUTION_PATTERNS = [
        r'&\s*$',
        r'>',
        r'>>',
        r'<',
        r'\$\(',
        r'`',
        r'sudo',
        r'powershell',
        r'cmd',
        r'msys_no_pathconv',
        r'^pwsh\b',
        r'^\bsource\s+',
        r'^\.\s+',
        r'^doas\b',
        r'^pkexec\b',
        r'^run0\b',
    ]
    
    # Chain operators that require splitting and individual analysis
    CHAIN_OPERATORS = ['&&', '||', ';', '\n']

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
    def _split_chained_command(cls, command: str) -> List[str]:
        """Split command on chain operators (&&, ||, ;) while respecting quotes."""
        parts: List[str] = []
        current: List[str] = []
        in_single_quote = False
        in_double_quote = False
        i = 0
        
        while i < len(command):
            char = command[i]
            
            if char == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
                current.append(char)
                i += 1
            elif char == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
                current.append(char)
                i += 1
            elif not in_single_quote and not in_double_quote:
                remaining = command[i:]
                matched = False
                for op in cls.CHAIN_OPERATORS:
                    if remaining.startswith(op):
                        part = ''.join(current).strip()
                        if part:
                            parts.append(part)
                        current = []
                        i += len(op)
                        matched = True
                        break
                if not matched:
                    current.append(char)
                    i += 1
            else:
                current.append(char)
                i += 1
                    
        part = ''.join(current).strip()
        if part:
            parts.append(part)
            
        return parts if len(parts) > 1 else []

    @classmethod
    def _classify_single(cls, command: str) -> CommandRisk:
        if not command or not command.strip():
            return CommandRisk.CAUTION

        cmd_lower = command.strip().lower()

        # Fix 7: Backslash-escaped commands — strip leading backslash and re-classify
        if cmd_lower.startswith("\\"):
            return cls._classify_single(command.strip()[1:])

        if cmd_lower.startswith("winpty "):
            return cls._classify_single(command.strip()[7:])

        if cmd_lower.startswith("msys_no_pathconv=1 "):
            return cls._classify_single(command.strip()[19:])

        # Privilege escalation prefix stripping
        if cmd_lower.startswith("doas "):
            return cls._classify_single(command.strip()[5:])
        if cmd_lower.startswith("pkexec "):
            return cls._classify_single(command.strip()[7:])
        if cmd_lower.startswith("run0 "):
            return cls._classify_single(command.strip()[5:])

        if cmd_lower.startswith("taskkill"):
            if "/im" in cmd_lower or "//im" in cmd_lower:
                return CommandRisk.DANGER
            elif "/pid" in cmd_lower or "//pid" in cmd_lower:
                return CommandRisk.CAUTION
            else:
                return CommandRisk.DANGER

        # Fix 6: Brace expansion detection
        stripped = command.strip()
        if stripped.startswith('{') and '}' in stripped and ',' in stripped:
            close_idx = stripped.find('}')
            if close_idx > 0 and close_idx <= 20 and ',' in stripped[1:close_idx]:
                return CommandRisk.DANGER

        # Fix 4: DANGER regex patterns for variable-path rm commands
        for pattern in cls.DANGER_REGEX:
            if re.search(pattern, cmd_lower):
                return CommandRisk.DANGER

        for danger_cmd in cls.DANGER_COMMANDS:
            danger_lower = danger_cmd.lower()
            if cmd_lower.startswith(danger_lower + " ") or cmd_lower == danger_lower:
                return CommandRisk.DANGER

        for pattern in cls.CAUTION_PATTERNS:
            if re.search(pattern, command):
                return CommandRisk.CAUTION

        # Fix 3: Argument-aware classification for interpreters
        tokens = cmd_lower.split()
        if tokens:
            first = tokens[0]

            if first in ("python", "python3"):
                if len(tokens) > 1:
                    if tokens[1] == "-c":
                        return CommandRisk.CAUTION
                    if tokens[1] == "-m":
                        return CommandRisk.CAUTION
                    if tokens[1].endswith(".py"):
                        return CommandRisk.SAFE
                return CommandRisk.CAUTION

            if first == "node":
                if len(tokens) > 1 and tokens[1] == "-e":
                    return CommandRisk.CAUTION
                return CommandRisk.SAFE

            if first == "ruby":
                if len(tokens) > 1 and tokens[1] == "-e":
                    return CommandRisk.CAUTION
                return CommandRisk.SAFE

            if first == "perl":
                if len(tokens) > 1 and tokens[1] == "-e":
                    return CommandRisk.CAUTION
                return CommandRisk.SAFE

            if first == "go":
                if len(tokens) > 1 and tokens[1] == "run":
                    return CommandRisk.CAUTION
                return CommandRisk.SAFE

            if first == "find":
                if "-exec" in tokens or "-execdir" in tokens:
                    return CommandRisk.CAUTION
                return CommandRisk.SAFE

            if first == "awk":
                if "system(" in cmd_lower:
                    return CommandRisk.CAUTION
                return CommandRisk.SAFE

            if first == "sed":
                if "-i" in tokens:
                    return CommandRisk.CAUTION
                return CommandRisk.SAFE

        if '|' in command:
            parts = command.split('|')
            all_safe = True
            for idx, part in enumerate(parts):
                part = part.strip()
                if not part:
                    all_safe = False
                    break

                part_lower = part.lower()

                # Fix 8: Pipe-to-shell detection — any segment after the first that is a shell interpreter
                if idx > 0:
                    shell_interps = ("bash", "sh", "zsh", "fish", "python", "python3", "perl", "ruby", "node")
                    for interp in shell_interps:
                        if part_lower.startswith(interp + " ") or part_lower == interp:
                            return CommandRisk.DANGER

                part_is_safe = False

                for safe_cmd in cls.SAFE_COMMANDS:
                    if part_lower.startswith(safe_cmd + " ") or part_lower == safe_cmd:
                        if safe_cmd == "git":
                            git_risk = cls._classify_git_command(part)
                            if git_risk == CommandRisk.SAFE:
                                part_is_safe = True
                        else:
                            part_is_safe = True
                        break

                if not part_is_safe:
                    for safe_git in cls.SAFE_GIT_COMMANDS:
                        if part_lower.startswith(safe_git):
                            part_is_safe = True
                            break

                if not part_is_safe:
                    all_safe = False
                    break

            if all_safe:
                return CommandRisk.SAFE
            return CommandRisk.CAUTION

        first_token = cmd_lower.split()[0] if cmd_lower.split() else ""
        if first_token in cls.PACKAGE_MANAGERS:
            return CommandRisk.CAUTION

        for safe_cmd in cls.SAFE_COMMANDS:
            if cmd_lower.startswith(safe_cmd + " ") or cmd_lower == safe_cmd:
                if safe_cmd == "git":
                    return cls._classify_git_command(command)
                return CommandRisk.SAFE

        file_mod_commands = {"copy", "move", "ren", "rename", "xcopy", "robocopy", "md", "mkdir"}
        for mod_cmd in file_mod_commands:
            if cmd_lower.startswith(mod_cmd + " ") or cmd_lower == mod_cmd:
                return CommandRisk.CAUTION

        return CommandRisk.CAUTION

    @classmethod
    def classify_chain(cls, command: str) -> List[Tuple[str, CommandRisk]]:
        """Classify each part of a chained command. Returns list of (subcmd, risk) tuples."""
        parts = cls._split_chained_command(command)
        if not parts:
            return [(command, cls._classify_single(command))]
        return [(part, cls._classify_single(part)) for part in parts]

    @classmethod
    def classify(cls, command: str) -> CommandRisk:
        """
        Classify a command by risk level.
        For chained commands, returns the HIGHEST risk level found (minimum CAUTION).
        Returns: CommandRisk (SAFE, CAUTION, DANGER)
        """
        if not command or not command.strip():
            return CommandRisk.CAUTION

        chain_results = cls.classify_chain(command)
        
        if len(chain_results) > 1:
            highest_risk = CommandRisk.CAUTION
            for _, risk in chain_results:
                if risk > highest_risk:
                    highest_risk = risk
            return highest_risk
        
        return cls._classify_single(command)

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
