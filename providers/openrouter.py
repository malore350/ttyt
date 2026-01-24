from providers.base import AIProvider

class OpenRouterProvider(AIProvider):
    def __init__(self, api_key: str):
        self.model_name = "nvidia/nemotron-3-nano-30b-a3b:free"
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
