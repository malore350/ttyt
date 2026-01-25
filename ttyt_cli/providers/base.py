from abc import ABC, abstractmethod

class AIProvider(ABC):
    @abstractmethod
    def generate_command(self, user_input: str, cwd: str, history_context: str) -> str:
        pass

    @abstractmethod
    def generate_answer(self, user_input: str, cwd: str, history_context: str) -> str:
        pass
