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

class OpenRouterProvider(AIProvider):
    def __init__(self, api_key: str, model_name: Optional[str] = None):
        self.model_name = model_name or os.getenv("OPENROUTER_MODEL") or "nvidia/nemotron-3-nano-30b-a3b:free"
        try:
            from openai import OpenAI
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key,
                default_headers={
                    "HTTP-Referer": "https://github.com/kamranahmedse/ttyt",
                    "X-Title": "ttyt",
                }
            )
        except ImportError:
            raise ImportError("openai library not found. Run: pip install openai")

    def generate_command(self, user_input: str, cwd: str, history_context: str, project_context: str = "") -> str:
        project_info = ""
        if project_context:
            project_info = f"Project information:\n{project_context}\n"
        
        prompt = get_system_command_prompt(cwd, history_context, project_info)
        prompt += f"\nUser request: {user_input}"
        
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content
        return (content or "").strip()

    def generate_answer(self, user_input: str, cwd: str, history_context: str) -> str:
        prompt = get_system_answer_prompt(cwd, history_context)
        prompt += f"\nUser question: {user_input}"

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content
        return (content or "").strip()

    def check_goal_achieved(self, goal: str, command: str, output: str, exit_code: int) -> Tuple[bool, str]:
        output_truncated = output[-2000:] if len(output) > 2000 else output
        prompt = get_system_goal_prompt(goal, command, output_truncated, exit_code)

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        result = (response.choices[0].message.content or "").strip()
        
        if result.upper().startswith("SUCCESS"):
            return (True, result[8:].strip() if len(result) > 8 else "Goal achieved")
        return (False, result[8:].strip() if result.upper().startswith("FAILURE") and len(result) > 8 else result)

    def generate_fix_command(self, goal: str, failed_command: str, error_output: str, cwd: str, history_context: str, project_context: str = "", exploration_output: str = "") -> str:
        error_truncated = error_output[-1500:] if len(error_output) > 1500 else error_output
        
        project_info = ""
        if project_context:
            project_info = f"Project information:\n{project_context}\n"
            
        exploration_info = ""
        if exploration_output:
            exploration_info = f"Exploration output (from investigating the error):\n{exploration_output[-1500:] if len(exploration_output) > 1500 else exploration_output}\n"
            
        prompt = get_system_fix_prompt(goal, failed_command, error_truncated, cwd, history_context, project_info, exploration_info)

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        return (response.choices[0].message.content or "").strip()

    def suggest_exploration_command(self, goal: str, failed_command: str, error_output: str, cwd: str) -> Optional[str]:
        error_truncated = error_output[-1000:] if len(error_output) > 1000 else error_output
        prompt = get_system_explore_prompt(goal, failed_command, error_truncated, cwd)

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        result = (response.choices[0].message.content or "").strip()
        
        if result.upper() == "NONE" or not result:
            return None
        return result
