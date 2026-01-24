import os
import sys
import subprocess
import threading
import time
from safety import CommandSafety, CommandRisk
from history import add_to_history, format_history
from utils import safe_input, is_esc_pressed, GoBackException

def interruptible_generate(provider, user_input, cwd, history_context):
    result = {"command": None, "error": None}
    def target():
        try:
            result["command"] = provider.generate_command(user_input, cwd, history_context)
        except Exception as e:
            result["error"] = e

    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()

    print("\033[36mThinking... (ESC to cancel)\033[0m", end="\r")
    while thread.is_alive():
        if is_esc_pressed():
            print("\n\033[31mCancelled.\033[0m")
            raise GoBackException()
        time.sleep(0.02)
    
    print(" " * 30, end="\r")
    if result["error"]:
        raise result["error"]
    return result["command"]

def get_command(provider, user_input: str, cwd: str) -> str:
    history_context = format_history()
    try:
        return interruptible_generate(provider, user_input, cwd, history_context)
    except GoBackException:
        raise
    except Exception as e:
        return f"echo AI Error: {e}"

def execute_with_streaming(command: str):
    bash_path = r"C:\Program Files\Git\bin\bash.exe"
    if not os.path.exists(bash_path):
        bash_path = "bash"

    try:
        process = subprocess.Popen(
            [bash_path, "-c", command],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
    except FileNotFoundError:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

    output_full = []
    
    def stream_reader(pipe, is_stderr=False):
        for line in iter(pipe.readline, ''):
            if is_stderr:
                print(line, end="", file=sys.stderr)
            else:
                print(line, end="")
            output_full.append(line)

    t1 = threading.Thread(target=stream_reader, args=(process.stdout, False))
    t2 = threading.Thread(target=stream_reader, args=(process.stderr, True))
    t1.daemon = True
    t2.daemon = True
    t1.start()
    t2.start()

    while process.poll() is None:
        if is_esc_pressed():
            print("\n\033[31m[ESC] Stopping process tree...\033[0m")
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], 
                           capture_output=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            process.terminate()
            raise GoBackException()
        time.sleep(0.02)

    t1.join(timeout=1)
    t2.join(timeout=1)
    
    add_to_history(command, "".join(output_full))

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
        confirm = safe_input("\033[33mExecute? [y/N]\033[0m ")
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
        execute_with_streaming(command)
    except GoBackException:
        raise
    except Exception as e:
        print(f"\033[31mExecution Error: {e}\033[0m")
        return False
        
    return True
