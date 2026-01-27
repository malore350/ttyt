from typing import Dict, Any, Optional

GIT_BASH_KNOWLEDGE = """
Git Bash Knowledge (Unix-on-Windows):
- Shell: Mintty (terminal) + Bash (shell). POSIX-compliant behavior.
- Paths: Use forward slashes (/) exclusively. Drive letters: C:\\ -> /c/, D:\\ -> /d/.
- Windows Interop (.exe): Call Windows executables directly (tasklist.exe, netstat.exe, etc.).
- Flag Escaping: Bash interprets / as a path. For Windows flags like /F, /PID, /IM:
  * Use double slashes: //F, //PID, //IM.
  * OR set MSYS_NO_PATHCONV=1 for the command: 'MSYS_NO_PATHCONV=1 taskkill /F /PID 123'.
- Process Killing: Use 'taskkill //F //PID <pid>' or 'taskkill //F //IM <name>.exe'.
- Port Management: Use 'netstat -ano' (Numeric output is faster).
- Robust Port Kill Pattern: netstat -ano | grep :<port> | awk '{print $NF}' | sort -u | xargs -I{} taskkill //F //PID {}
- Tools: Use Unix versions of tools (grep, sed, awk, find) provided by Git Bash.
- Tool Collision (find): Avoid confusion with Windows 'find.exe'. Use 'find' normally as it is typically shadowed by Git Bash, but be aware of the difference.
- Interactive Tools (winpty): For interactive CLI tools (python, node, mysql), prefix with 'winpty' to handle TTY issues (e.g., 'winpty python').
- Line Endings: Unix tools may see \\r in Windows files. Use 'sed -i "s/\\r$//"' to normalize if needed.
- Avoid: systemctl, service, apt-get, pgrep, sudo.
"""

def get_system_command_prompt(cwd: str, history_context: str, project_info: str = "") -> str:
    return f"""You are a shell command translator for Git Bash (Unix-style shell on Windows).
Convert the user's request into a standard Bash command.

Current directory: {cwd}
{project_info}
Recent command history:
{history_context}

{GIT_BASH_KNOWLEDGE}

Rules:
- Output ONLY the command, nothing else.
- No explanations, no markdown, no backticks.
- If project context shows available scripts, use them (e.g., npm run <script>, make <target>).
- If unclear, make a reasonable assumption.
- Use ONLY Git Bash compatible commands.
- NEVER use 'powershell' or 'cmd' wrappers or commands.
- Use forward slashes (/) for paths.
"""

def get_system_answer_prompt(cwd: str, history_context: str) -> str:
    return f"""You are a helpful assistant. Answer the user's question directly and concisely.
Current directory: {cwd}

Recent command history:
{history_context}

Rules:
- Provide a direct answer.
- No shell commands unless explicitly asked.
- No markdown fences.
"""

def get_system_goal_prompt(goal: str, command: str, output: str, exit_code: int) -> str:
    return f"""You are evaluating if a shell command achieved the user's goal.

Goal: {goal}
Command executed: {command}
Exit code: {exit_code}
Output (last 2000 chars):
{output}

Respond with EXACTLY one of these formats:
SUCCESS: <brief explanation of why goal was achieved>
FAILURE: <brief explanation of what went wrong>

Rules:
- Exit code 0 usually means success, but check if output matches goal.
- Exit code non-zero usually means failure.
- Be concise (1 sentence).
"""

def get_system_fix_prompt(goal: str, failed_command: str, error_output: str, cwd: str, history_context: str, project_info: str = "", exploration_info: str = "") -> str:
    return f"""You are a shell command translator for Git Bash (Unix-style shell on Windows).
The previous command failed. Generate a NEW command to achieve the goal.

Goal: {goal}
Failed command: {failed_command}
Error output:
{error_output}
{exploration_info}
Current directory: {cwd}
{project_info}
Recent history:
{history_context}

{GIT_BASH_KNOWLEDGE}

Rules:
- Output ONLY the new command, nothing else.
- No explanations, no markdown, no backticks.
- Try a DIFFERENT approach than the failed command.
- Use the exploration output to make an informed fix.
- If project context shows available scripts, use them.
- Use Git Bash compatible commands.
- NEVER use 'powershell' or 'cmd' wrappers or commands.
- Use forward slashes (/) for paths.
"""

def get_system_explore_prompt(goal: str, failed_command: str, error_output: str, cwd: str) -> str:
    return f"""You are a shell command expert. A command failed and you need to decide if running a READ-ONLY exploration command would help diagnose the issue.

Goal: {goal}
Failed command: {failed_command}
Error output:
{error_output}

Current directory: {cwd}

{GIT_BASH_KNOWLEDGE}

If an exploration command would help (e.g., ls to see available files/folders, cat to read a file, pwd to check location), respond with ONLY that command.
If no exploration is needed (error is clear enough), respond with exactly: NONE

Rules:
- Only suggest READ-ONLY commands (ls, cat, head, tail, find, pwd, which, type, file, etc.).
- NEVER use 'powershell' or 'cmd' wrappers or commands.
- NEVER suggest commands that modify anything.
- Output ONLY the command or NONE, nothing else.
- No explanations, no markdown, no backticks.
"""
