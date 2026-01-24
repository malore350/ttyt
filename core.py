import os
import sys
import subprocess
from safety import CommandSafety, CommandRisk
from history import add_to_history, format_history

def get_command(provider, user_input: str, cwd: str) -> str:
    history_context = format_history()
    try:
        return provider.generate_command(user_input, cwd, history_context)
    except Exception as e:
        return f"echo AI Error: {e}"

def execute_command_with_safety(command: str) -> bool:
    risk = CommandSafety.classify(command)
    description = CommandSafety.get_risk_description(risk)

    if risk == CommandRisk.DANGER:
        print(f"\033[31m[DANGER] BLOCKED: {description}\033[0m")
        print(f"\033[31m  Command: {command}\033[0m")
        return False

    if risk == CommandRisk.CAUTION:
        print(f"\033[33m[CAUTION] {description}\033[0m")
        print(f"\033[33m  Command: {command}\033[0m")
        confirm = input("\033[33mExecute? [y/N]\033[0m ")
        if confirm.lower() != 'y':
            return False

    if risk == CommandRisk.SAFE:
        print(f"\033[36m[SAFE] {description}\033[0m")

    cmd_parts = command.strip().split()
    if cmd_parts and cmd_parts[0] == "cd":
        path = "~"
        if len(cmd_parts) > 1:
            path = command.strip()[3:].strip()
            if (path.startswith('"') and path.endswith('"')) or (path.startswith("'") and path.endswith("'")):
                path = path[1:-1]
        
        if path.startswith('/') and len(path) >= 3 and path[1].isalpha() and path[2] == '/':
            path = f"{path[1]}:{path[2:]}"
        
        path = os.path.expanduser(path)
        try:
            os.chdir(path)
        except Exception as e:
            print(f"cd: {e}")
        return True

    try:
        bash_path = r"C:\Program Files\Git\bin\bash.exe"
        if not os.path.exists(bash_path):
            bash_path = "bash"

        result = subprocess.run([bash_path, "-c", command], capture_output=True, text=True)

        print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        add_to_history(command, result.stdout + result.stderr)
    except FileNotFoundError:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        add_to_history(command, result.stdout + result.stderr)
    except Exception as e:
        print(f"\033[31mExecution Error: {e}\033[0m")
        return False
        
    return True
