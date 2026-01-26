import os
from typing import Optional, Tuple
from .base import AIProvider

class GeminiProvider(AIProvider):
    def __init__(self, api_key: str, model_name: Optional[str] = None):
        self.model_name = model_name or os.getenv("GEMINI_MODEL") or "gemini-2.5-flash-lite"
        try:
            from google import genai
            self.client = genai.Client(api_key=api_key)
        except ImportError:
            raise ImportError("google-genai library not found. Run: pip install google-genai")

    def generate_command(self, user_input: str, cwd: str, history_context: str, project_context: str = "") -> str:
        project_info = ""
        if project_context:
            project_info = f"""
Project information:
{project_context}

"""
        prompt = f"""You are a shell command translator for Git Bash (Unix-style shell on Windows). 
Convert the user's request into a standard Bash command.
Current directory: {cwd}
{project_info}
Recent command history:
{history_context}

Rules:
- Output ONLY the command, nothing else
- No explanations, no markdown, no backticks
- If project context shows available scripts, use them (e.g., npm run <script>, make <target>)
- If unclear, make a reasonable assumption
- Use ONLY Git Bash compatible commands.
- AVOID Linux-only commands (e.g., pgrep, ps -ef, htop, ssh-copy-id).
- For process listing, use 'tasklist | grep <name>'.
- For killing processes, use 'taskkill //F //PID <pid>'.
- Use forward slashes (/) for paths.
- User request: {user_input}"""
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt
        )
        return (response.text or "").strip()

    def check_goal_achieved(self, goal: str, command: str, output: str, exit_code: int) -> Tuple[bool, str]:
        output_truncated = output[-2000:] if len(output) > 2000 else output
        
        prompt = f"""You are evaluating if a shell command achieved the user's goal.

Goal: {goal}
Command executed: {command}
Exit code: {exit_code}
Output (last 2000 chars):
{output_truncated}

Respond with EXACTLY one of these formats:
SUCCESS: <brief explanation of why goal was achieved>
FAILURE: <brief explanation of what went wrong>

Rules:
- Exit code 0 usually means success, but check if output matches goal
- Exit code non-zero usually means failure
- Be concise (1 sentence)"""

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt
        )
        result = (response.text or "").strip()
        
        if result.upper().startswith("SUCCESS"):
            return (True, result[8:].strip() if len(result) > 8 else "Goal achieved")
        return (False, result[8:].strip() if result.upper().startswith("FAILURE") and len(result) > 8 else result)

    def generate_fix_command(self, goal: str, failed_command: str, error_output: str, cwd: str, history_context: str, project_context: str = "", exploration_output: str = "") -> str:
        error_truncated = error_output[-1500:] if len(error_output) > 1500 else error_output
        
        project_info = ""
        if project_context:
            project_info = f"""
Project information:
{project_context}

"""
        exploration_info = ""
        if exploration_output:
            exploration_info = f"""
Exploration output (from investigating the error):
{exploration_output[-1500:] if len(exploration_output) > 1500 else exploration_output}

"""
        prompt = f"""You are a shell command translator for Git Bash (Unix-style shell on Windows).
The previous command failed. Generate a NEW command to achieve the goal.

Goal: {goal}
Failed command: {failed_command}
Error output (last 1500 chars):
{error_truncated}
{exploration_info}
Current directory: {cwd}
{project_info}
Recent history:
{history_context}

Rules:
- Output ONLY the new command, nothing else
- No explanations, no markdown, no backticks
- Try a DIFFERENT approach than the failed command
- Use the exploration output to make an informed fix
- If project context shows available scripts, use them
- Use Git Bash compatible commands
- Use forward slashes (/) for paths"""

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt
        )
        return (response.text or "").strip()

    def suggest_exploration_command(self, goal: str, failed_command: str, error_output: str, cwd: str) -> Optional[str]:
        error_truncated = error_output[-1000:] if len(error_output) > 1000 else error_output
        
        prompt = f"""You are a shell command expert. A command failed and you need to decide if running a READ-ONLY exploration command would help diagnose the issue.

Goal: {goal}
Failed command: {failed_command}
Error output:
{error_truncated}

Current directory: {cwd}

If an exploration command would help (e.g., ls to see available files/folders, cat to read a file, pwd to check location), respond with ONLY that command.
If no exploration is needed (error is clear enough), respond with exactly: NONE

Rules:
- Only suggest READ-ONLY commands (ls, cat, head, tail, find, pwd, which, type, file, etc.)
- NEVER suggest commands that modify anything
- Output ONLY the command or NONE, nothing else
- No explanations, no markdown, no backticks"""

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt
        )
        result = (response.text or "").strip()
        
        if result.upper() == "NONE" or not result:
            return None
        return result

    def generate_answer(self, user_input: str, cwd: str, history_context: str) -> str:
        prompt = f"""You are a helpful assistant. Answer the user's question directly and concisely.
Current directory: {cwd}

Recent command history:
{history_context}

Rules:
- Provide a direct answer
- No shell commands unless explicitly asked
- No markdown fences
- User question: {user_input}"""
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt
        )
        return (response.text or "").strip()
