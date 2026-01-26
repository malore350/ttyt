from abc import ABC, abstractmethod
from typing import Optional

class AIProvider(ABC):
    @abstractmethod
    def generate_command(self, user_input: str, cwd: str, history_context: str, project_context: str = "") -> str:
        pass

    @abstractmethod
    def generate_answer(self, user_input: str, cwd: str, history_context: str) -> str:
        pass

    @abstractmethod
    def check_goal_achieved(self, goal: str, command: str, output: str, exit_code: int) -> tuple[bool, str]:
        pass

    @abstractmethod
    def generate_fix_command(self, goal: str, failed_command: str, error_output: str, cwd: str, history_context: str, project_context: str = "", exploration_output: str = "") -> str:
        pass

    @abstractmethod
    def suggest_exploration_command(self, goal: str, failed_command: str, error_output: str, cwd: str) -> Optional[str]:
        """Suggest a read-only command to gather info before retrying. Returns None if no exploration needed."""
        pass
