from typing import Dict, Any, Optional

WINDOWS_KNOWLEDGE = """
Windows (Git Bash) Knowledge:
- Shell: Mintty (terminal) + Bash (shell). POSIX-compliant behavior.
- Paths: Use forward slashes (/) exclusively. Drive letters: C:\\ -> /c/, D:\\ -> /d/.
- Windows Interop (.exe): Call Windows executables directly (tasklist.exe, netstat.exe, etc.).
- Flag Escaping: Bash interprets / as a path. For Windows flags like /F, /PID, /IM:
  * Use double slashes: //F, //PID, //IM.
  * OR set MSYS_NO_PATHCONV=1 for the command: 'MSYS_NO_PATHCONV=1 taskkill /F /PID 123'.
- Process Killing: Use 'taskkill //F //PID <pid>' or 'taskkill //F //IM <name>.exe'.
- Port Management: Use 'netstat -ano' (Numeric output is faster).
- Robust Port Kill Pattern: netstat -ano | grep :<port> | awk '{print $NF}' | sort -u | xargs -I{} taskkill //F //PID {}
- Interactive Tools (winpty): For interactive tools (python, node), prefix with 'winpty' (e.g., 'winpty python').
- Avoid: systemctl, service, apt-get, pgrep, sudo.
"""

LINUX_KNOWLEDGE = """
Linux Knowledge:
- Shell: Bash/Zsh.
- Paths: Standard Unix paths (/home/user/...).
- Package Management: Use apt, yum, or dnf based on distribution context.
- Process Management: Use 'ps -ef' or 'ps aux'.
- Process Killing: 'kill -9 <pid>' or 'pkill <name>'.
- Port Management: Use 'ss -tulnp' or 'netstat -tulnp'.
- In-place editing: 'sed -i' works without an extension (GNU sed).
- Utilities: GNU versions of find, xargs, awk, and grep.
- Robust Port Kill: fuser -k <port>/tcp or ss -K ...
- Hardware Info: /proc/cpuinfo, lscpu, free -m.
- Network: ip addr, ip link, nmcli.
"""

MACOS_KNOWLEDGE = """
macOS (BSD) Knowledge:
- Shell: Zsh (default) or Bash.
- Paths: Standard Unix paths (/Users/user/...).
- Package Management: Use 'brew'.
- Process Management: Use 'ps aux'. 
- Process Killing: 'kill -9 <pid>'.
- Port Management: Use 'lsof -i :<port>'.
- In-place editing (BSD sed): REQUIRES an extension for -i. Use 'sed -i "" "s/old/new/g" file'.
- Utilities: BSD versions of find and stat (flags differ from GNU). BSD find lacks -executable (use -perm +111).
- Hardware info: Use 'sysctl'.
- Case Sensitivity: Filesystem is typically case-insensitive but case-preserving.
- Permissions: Visible via 'ls -le' (ACLs) or 'ls -l@' (Extended Attributes).
"""

def get_os_knowledge(os_name: str) -> str:
    if "Windows" in os_name:
        return WINDOWS_KNOWLEDGE
    elif "macOS" in os_name:
        return MACOS_KNOWLEDGE
    elif "Linux" in os_name:
        return LINUX_KNOWLEDGE
    return ""

def get_system_command_prompt(cwd: str, history_context: str, os_name: str, project_info: str = "") -> str:
    os_knowledge = get_os_knowledge(os_name)
    return f"""You are a shell command translator for {os_name}.
Convert the user's request into a standard shell command.

Current directory: {cwd}
{project_info}
Recent command history:
{history_context}

{os_knowledge}

Rules:
- Output ONLY the command, nothing else.
- No explanations, no markdown, no backticks.
- If project context shows available scripts, use them.
- If unclear, make a reasonable assumption.
- Use ONLY {os_name} compatible commands.
- NEVER use 'powershell' or 'cmd' wrappers or commands.
- Use forward slashes (/) for paths.
"""

def get_system_answer_prompt(cwd: str, history_context: str, os_name: str) -> str:
    return f"""You are a helpful assistant running on {os_name}. Answer the user's question directly and concisely.
Current directory: {cwd}

Recent command history:
{history_context}

Rules:
- Provide a direct answer.
- No shell commands unless explicitly asked.
- No markdown fences.
"""

def get_system_goal_prompt(goal: str, command: str, output: str, exit_code: int, os_name: str) -> str:
    return f"""You are evaluating if a shell command achieved the user's goal on {os_name}.

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

def get_system_fix_prompt(goal: str, failed_command: str, error_output: str, cwd: str, history_context: str, os_name: str, project_info: str = "", exploration_info: str = "") -> str:
    os_knowledge = get_os_knowledge(os_name)
    return f"""You are a shell command translator for {os_name}.
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

{os_knowledge}

Rules:
- Output ONLY the new command, nothing else.
- No explanations, no markdown, no backticks.
- Try a DIFFERENT approach than the failed command.
- Use the exploration output to make an informed fix.
- If project context shows available scripts, use them.
- Use {os_name} compatible commands.
- NEVER use 'powershell' or 'cmd' wrappers or commands.
- Use forward slashes (/) for paths.
"""

def get_system_explore_prompt(goal: str, failed_command: str, error_output: str, cwd: str, os_name: str) -> str:
    os_knowledge = get_os_knowledge(os_name)
    return f"""You are a shell command expert on {os_name}. A command failed and you need to decide if running a READ-ONLY exploration command would help diagnose the issue.

Goal: {goal}
Failed command: {failed_command}
Error output:
{error_output}

Current directory: {cwd}

{os_knowledge}

If an exploration command would help (e.g., ls, cat, pwd), respond with ONLY that command.
If no exploration is needed (error is clear enough), respond with exactly: NONE

Rules:
- Only suggest READ-ONLY commands.
- NEVER use 'powershell' or 'cmd' wrappers or commands.
- NEVER suggest commands that modify anything.
- Output ONLY the command or NONE, nothing else.
- No explanations, no markdown, no backticks.
"""
