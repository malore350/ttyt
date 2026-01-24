import os
from typing import Optional
from providers.base import AIProvider

class ZAIProvider(AIProvider):
    def __init__(self, api_key: str, model_name: Optional[str] = None):
        self.model_name = model_name or os.getenv("ZAI_MODEL") or "glm-4.7"
        try:
            from zai import ZaiClient
            self.client = ZaiClient(api_key=api_key)
        except ImportError:
            raise ImportError("zai-sdk library not found. Run: pip install zai-sdk")

    def generate_command(self, user_input: str, cwd: str, history_context: str) -> str:
        prompt = f"""You are a shell command translator for Git Bash (Unix-style shell on Windows). 
Convert the user's request into a standard Bash command.
Current directory: {cwd}

Recent command history:
{history_context}

Rules:
- Output ONLY the command, nothing else
- No explanations, no markdown, no backticks
- If unclear, make a reasonable assumption
- Use ONLY Git Bash compatible commands.
- AVOID Linux-only commands (e.g., pgrep, ps -ef, htop, ssh-copy-id).
- For process listing, use 'tasklist | grep <name>'.
- For killing processes, use 'taskkill //F //PID <pid>'.
- Use forward slashes (/) for paths.
- User request: {user_input}"""
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
