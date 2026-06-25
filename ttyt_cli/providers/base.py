from abc import ABC, abstractmethod
from typing import Optional, Tuple

# Registry storage for all decorated providers
_providers: dict = {}


def register_provider(name: str, env_key: str, api_url: str, models: list):
    """Class decorator that registers a provider in the global registry."""
    def decorator(cls):
        _providers[name] = {
            "class": cls,
            "env_key": env_key,
            "api_url": api_url,
            "models": models,
        }
        return cls
    return decorator


def get_registered_providers() -> dict:
    """Return a shallow copy of the provider registry."""
    return dict(_providers)


def truncate_output(text: str, max_chars: int, strategy: str = "suffix") -> str:
    """Truncate text to max_chars using the given strategy."""
    if len(text) <= max_chars:
        return text
    if strategy == "suffix":
        return "..." + text[-(max_chars - 3):]
    if strategy == "prefix":
        return text[:max_chars - 3] + "..."
    return text[:max_chars]


def truncate_to_tokens(text: str, max_tokens: int, strategy: str = "suffix") -> str:
    """Truncate text to approximate token count (chars/4 for English, chars/2 for CJK-safe).

    Uses approximation: ~4 chars per token for English/code, ~2 for CJK safety.
    If text is shorter than limit, return as-is.
    """
    max_chars = max_tokens * 4  # chars/4 approximation for English
    if len(text) <= max_chars:
        return text
    if strategy == "suffix":
        return "..." + text[-(max_chars - 3):]
    else:  # prefix
        return text[:max_chars - 3] + "..."


def _parse_goal_result(result: str) -> Tuple[bool, str]:
    """Parse a goal-check result string, stripping SUCCESS:/FAILURE: prefixes."""
    if result.upper().startswith("SUCCESS:"):
        return (True, result[8:].strip())
    if result.upper().startswith("FAILURE:"):
        return (False, result[8:].strip())
    return (False, result.strip())


def _parse_exploration_result(result: str) -> Optional[str]:
    """Parse an exploration suggestion, returning None if empty or NONE."""
    if not result or result.strip() == "" or result.strip().upper() == "NONE":
        return None
    return result.strip()


class AIProvider(ABC):
    @abstractmethod
    def generate_command(self, user_input: str, cwd: str, history_context: str, os_name: str, project_context: str = "") -> str:
        pass

    @abstractmethod
    def generate_answer(self, user_input: str, cwd: str, history_context: str, os_name: str) -> str:
        pass

    @abstractmethod
    def check_goal_achieved(self, goal: str, command: str, output: str, exit_code: int, os_name: str) -> tuple[bool, str]:
        pass

    @abstractmethod
    def generate_fix_command(self, goal: str, failed_command: str, error_output: str, cwd: str, history_context: str, os_name: str, project_context: str = "", exploration_output: str = "") -> str:
        pass

    @abstractmethod
    def suggest_exploration_command(self, goal: str, failed_command: str, error_output: str, cwd: str, os_name: str) -> Optional[str]:
        """Suggest a read-only command to gather info before retrying. Returns None if no exploration needed."""
        pass
