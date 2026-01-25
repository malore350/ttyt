import os
import subprocess
import threading
import time
from typing import Any
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from .safety import CommandSafety, CommandRisk
from .history import add_to_history, add_chat_to_history, format_history
from .utils import safe_input, is_esc_pressed, GoBackException

console = Console()

def interruptible_generate(provider, user_input, cwd, history_context):
    result: dict[str, Any] = {"command": None, "error": None}
    def target():
        try:
            result["command"] = provider.generate_command(user_input, cwd, history_context)
        except Exception as e:
            result["error"] = str(e)

    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()

    with Live(Text("Thinking...", style="cyan"), refresh_per_second=10) as live:
        while thread.is_alive():
            if is_esc_pressed():
                live.update(Text("Cancelled.", style="red"))
                raise GoBackException()
            time.sleep(0.02)
        
        if result["error"]:
            live.update(Text(f"Error: {result['error']}", style="red"))
            raise Exception(result["error"])
        
        live.update(Text(""))
    
    return result["command"] or ""

def interruptible_answer(provider, user_input, cwd, history_context):
    result: dict[str, Any] = {"answer": None, "error": None}
    def target():
        try:
            result["answer"] = provider.generate_answer(user_input, cwd, history_context)
        except Exception as e:
            result["error"] = str(e)

    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()

    with Live(Text("Thinking...", style="cyan"), refresh_per_second=10) as live:
        while thread.is_alive():
            if is_esc_pressed():
                live.update(Text("Cancelled.", style="red"))
                raise GoBackException()
            time.sleep(0.02)

        if result["error"]:
            live.update(Text(f"Error: {result['error']}", style="red"))
            raise Exception(result["error"])

        live.update(Text(""))

    return result["answer"] or ""

def get_command(provider, user_input: str, cwd: str) -> str:
    history_context = format_history()
    try:
        return interruptible_generate(provider, user_input, cwd, history_context)
    except GoBackException:
        raise
    except Exception as e:
        return f"echo AI Error: {e}"

def get_answer(provider, user_input: str, cwd: str) -> str:
    history_context = format_history()
    try:
        answer = interruptible_answer(provider, user_input, cwd, history_context)
        add_chat_to_history(user_input, answer)
        return answer
    except GoBackException:
        raise
    except Exception as e:
        return f"AI Error: {e}"

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
                console.print(line, end="", style="red")
            else:
                console.print(line, end="")
            output_full.append(line)

    t1 = threading.Thread(target=stream_reader, args=(process.stdout, False))
    t2 = threading.Thread(target=stream_reader, args=(process.stderr, True))
    t1.daemon = True
    t2.daemon = True
    t1.start()
    t2.start()

    while process.poll() is None:
        if is_esc_pressed():
            console.print("\n[red][ESC] Stopping process tree...[/red]")
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
        console.print(Panel(
            Text.from_markup(f"[bold red]BLOCKED:[/bold red] {description}\n[dim]Command: {command}[/dim]"),
            title="[bold red]DANGER[/bold red]",
            border_style="red"
        ))
        return False

    if risk == CommandRisk.CAUTION:
        console.print(Panel(
            Text.from_markup(f"[bold yellow]WARNING:[/bold yellow] {description}\n[dim]Command: {command}[/dim]"),
            title="[bold yellow]CAUTION[/bold yellow]",
            border_style="yellow"
        ))
        confirm = safe_input("\033[33mExecute? [y/N]\033[0m ")
        if confirm.lower() != 'y':
            return False

    if risk == CommandRisk.SAFE:
        console.print(f"[cyan][SAFE] {description}[/cyan]")

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
            console.print(f"[red]cd: {e}[/red]")
        return True

    try:
        execute_with_streaming(command)
    except GoBackException:
        raise
    except Exception as e:
        console.print(f"[bold red]Execution Error:[/bold red] {e}")
        return False
        
    return True
