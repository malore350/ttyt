import os
from typing import Optional, Tuple
from .base import AIProvider, register_provider, truncate_output, truncate_to_tokens, _parse_goal_result, _parse_exploration_result
from .retry import retry_with_backoff
from ..prompts import (
    get_system_command_prompt,
    get_system_answer_prompt,
    get_system_goal_prompt,
    get_system_fix_prompt,
    get_system_explore_prompt
)

@register_provider(
    "openrouter",
    "OPENROUTER_API_KEY",
    "https://openrouter.ai/api/v1",
    [
        "nvidia/nemotron-3-nano-30b-a3b:free",
        "google/gemma-3-27b-it:free",
    ]
)
class OpenRouterProvider(AIProvider):
    def __init__(self, api_key: str, model_name: Optional[str] = None):
        self.model_name = model_name or os.getenv("OPENROUTER_MODEL") or "nvidia/nemotron-3-nano-30b-a3b:free"
        try:
            from openai import OpenAI
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key,
                timeout=30.0,
                default_headers={
                    "HTTP-Referer": "https://github.com/kamrangasimov/ttyt",
                    "X-Title": "ttyt",
                }
            )
        except ImportError:
            raise ImportError("openai library not found. Run: pip install openai")

    @retry_with_backoff(max_retries=3, base_delay=2.0)
    def generate_command(self, user_input: str, cwd: str, history_context: str, os_name: str, project_context: str = "") -> str:
        project_info = ""
        if project_context:
            project_info = f"Project information:\n{project_context}\n"
        
        prompt = get_system_command_prompt(cwd, history_context, os_name, project_info)
        prompt += f"\nUser request: {user_input}"
        
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content
        return (content or "").strip()

    @retry_with_backoff(max_retries=3, base_delay=2.0)
    def generate_answer(self, user_input: str, cwd: str, history_context: str, os_name: str) -> str:
        prompt = get_system_answer_prompt(cwd, history_context, os_name)
        prompt += f"\nUser question: {user_input}"

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content
        return (content or "").strip()

    @retry_with_backoff(max_retries=3, base_delay=2.0)
    def check_goal_achieved(self, goal: str, command: str, output: str, exit_code: int, os_name: str) -> Tuple[bool, str]:
        output_truncated = truncate_to_tokens(output, 500)
        prompt = get_system_goal_prompt(goal, command, output_truncated, exit_code, os_name)

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        result = (response.choices[0].message.content or "").strip()
        return _parse_goal_result(result)

    @retry_with_backoff(max_retries=3, base_delay=2.0)
    def generate_fix_command(self, goal: str, failed_command: str, error_output: str, cwd: str, history_context: str, os_name: str, project_context: str = "", exploration_output: str = "") -> str:
        error_truncated = truncate_to_tokens(error_output, 375)
        
        project_info = ""
        if project_context:
            project_info = f"Project information:\n{project_context}\n"
            
        exploration_info = ""
        if exploration_output:
            exploration_info = f"Exploration output (from investigating the error):\n{truncate_to_tokens(exploration_output, 375)}\n"
            
        prompt = get_system_fix_prompt(goal, failed_command, error_truncated, cwd, history_context, os_name, project_info, exploration_info)

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        return (response.choices[0].message.content or "").strip()

    @retry_with_backoff(max_retries=3, base_delay=2.0)
    def suggest_exploration_command(self, goal: str, failed_command: str, error_output: str, cwd: str, os_name: str) -> Optional[str]:
        error_truncated = truncate_to_tokens(error_output, 250)
        prompt = get_system_explore_prompt(goal, failed_command, error_truncated, cwd, os_name)

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        result = (response.choices[0].message.content or "").strip()
        return _parse_exploration_result(result)
