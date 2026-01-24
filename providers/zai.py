from providers.base import AIProvider

class ZAIProvider(AIProvider):
    def __init__(self, api_key: str):
        self.model_name = "glm-4.7"
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
- Prefer standard Unix/Bash commands (ls, cat, cp, mv, rm, grep, find, etc.)
- Use forward slashes (/) for paths
- User request: {user_input}"""
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
