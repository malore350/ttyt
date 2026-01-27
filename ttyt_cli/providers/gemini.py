import os
from typing import Optional, Tuple
from .base import AIProvider
from ..prompts import (
    get_system_command_prompt,
    get_system_answer_prompt,
    get_system_goal_prompt,
    get_system_fix_prompt,
    get_system_explore_prompt
)

class GeminiProvider(AIProvider):
    def __init__(self, api_key: str, model_name: Optional[str] = None):
        self.model_name = model_name or os.getenv("GEMINI_MODEL") or "gemini-2.5-flash-lite"
        try:
            from google import genai
            self.client = genai.Client(api_key=api_key)
        except ImportError:
            raise ImportError("google-genai library not found. Run: pip install google-genai")

    def generate_command(self, user_input: str, cwd: str, history_context: str, os_name: str, project_context: str = "") -> str:
        project_info = ""
        if project_context:
            project_info = f"Project information:\n{project_context}\n"
        
        prompt = get_system_command_prompt(cwd, history_context, os_name, project_info)
        prompt += f"\nUser request: {user_input}"
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt
        )
        return (response.text or "").strip()

    def check_goal_achieved(self, goal: str, command: str, output: str, exit_code: int, os_name: str) -> Tuple[bool, str]:
        output_truncated = output[-2000:] if len(output) > 2000 else output
        prompt = get_system_goal_prompt(goal, command, output_truncated, exit_code, os_name)

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt
        )
        result = (response.text or "").strip()
        
        if result.upper().startswith("SUCCESS"):
            return (True, result[8:].strip() if len(result) > 8 else "Goal achieved")
        return (False, result[8:].strip() if result.upper().startswith("FAILURE") and len(result) > 8 else result)

    def generate_fix_command(self, goal: str, failed_command: str, error_output: str, cwd: str, history_context: str, os_name: str, project_context: str = "", exploration_output: str = "") -> str:
        error_truncated = error_output[-1500:] if len(error_output) > 1500 else error_output
        
        project_info = ""
        if project_context:
            project_info = f"Project information:\n{project_context}\n"
            
        exploration_info = ""
        if exploration_output:
            exploration_info = f"Exploration output (from investigating the error):\n{exploration_output[-1500:] if len(exploration_output) > 1500 else exploration_output}\n"
            
        prompt = get_system_fix_prompt(goal, failed_command, error_truncated, cwd, history_context, os_name, project_info, exploration_info)

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt
        )
        return (response.text or "").strip()

    def suggest_exploration_command(self, goal: str, failed_command: str, error_output: str, cwd: str, os_name: str) -> Optional[str]:
        error_truncated = error_output[-1000:] if len(error_output) > 1000 else error_output
        prompt = get_system_explore_prompt(goal, failed_command, error_truncated, cwd, os_name)

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt
        )
        result = (response.text or "").strip()
        
        if result.upper() == "NONE" or not result:
            return None
        return result

    def generate_answer(self, user_input: str, cwd: str, history_context: str, os_name: str) -> str:
        prompt = get_system_answer_prompt(cwd, history_context, os_name)
        prompt += f"\nUser question: {user_input}"
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt
        )
        return (response.text or "").strip()
