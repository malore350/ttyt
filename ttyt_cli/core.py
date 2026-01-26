import os
import signal
import subprocess
import threading
import time
import shlex
from typing import Any, List, Tuple, NamedTuple, Optional
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from .safety import CommandSafety, CommandRisk
from .history import add_to_history, add_chat_to_history, format_history
from .utils import safe_input, is_esc_pressed, GoBackException
from .project_context import get_context_for_prompt

console = Console()

class ExecutionResult(NamedTuple):
    exit_code: int
    output: str
    interrupted: bool = False

def interruptible_generate(provider, user_input, cwd, history_context, project_context=""):
    result: dict[str, Any] = {"command": None, "error": None}
    def target():
        try:
            result["command"] = provider.generate_command(user_input, cwd, history_context, project_context)
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

def interruptible_fix_command(provider, goal: str, failed_command: str, error_output: str, cwd: str, history_context: str, project_context: str = "", exploration_output: str = ""):
    result: dict[str, Any] = {"command": None, "error": None}
    def target():
        try:
            result["command"] = provider.generate_fix_command(goal, failed_command, error_output, cwd, history_context, project_context, exploration_output)
        except Exception as e:
            result["error"] = str(e)

    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()

    with Live(Text("Generating fix...", style="cyan"), refresh_per_second=10) as live:
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

def interruptible_exploration(provider, goal: str, failed_command: str, error_output: str, cwd: str) -> Optional[str]:
    result: dict[str, Any] = {"command": None, "error": None}
    def target():
        try:
            result["command"] = provider.suggest_exploration_command(goal, failed_command, error_output, cwd)
        except Exception as e:
            result["error"] = str(e)

    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()

    with Live(Text("Analyzing error...", style="cyan"), refresh_per_second=10) as live:
        while thread.is_alive():
            if is_esc_pressed():
                live.update(Text("Cancelled.", style="red"))
                raise GoBackException()
            time.sleep(0.02)
        
        if result["error"]:
            live.update(Text(""))
            return None
        
        live.update(Text(""))
    
    return result["command"]

def get_command(provider, user_input: str, cwd: str) -> str:
    history_context = format_history()
    project_context = get_context_for_prompt(cwd, user_input)
    try:
        return interruptible_generate(provider, user_input, cwd, history_context, project_context)
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

def execute_with_streaming(command: str) -> ExecutionResult:
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

    output_full: List[str] = []
    was_interrupted = False
    
    def sigint_handler(sig, frame):
        nonlocal was_interrupted
        was_interrupted = True
    
    old_handler = signal.signal(signal.SIGINT, sigint_handler)
    
    def stream_reader(pipe, is_stderr=False):
        import sys
        for line in iter(pipe.readline, ''):
            if is_stderr:
                sys.stderr.write(line)
                sys.stderr.flush()
            else:
                sys.stdout.write(line)
                sys.stdout.flush()
            output_full.append(line)

    t1 = threading.Thread(target=stream_reader, args=(process.stdout, False))
    t2 = threading.Thread(target=stream_reader, args=(process.stderr, True))
    t1.daemon = True
    t2.daemon = True
    t1.start()
    t2.start()

    try:
        while process.poll() is None:
            if was_interrupted or is_esc_pressed():
                console.print("\n[red][CTRL+C] Stopping process...[/red]")
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], 
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                process.terminate()
                was_interrupted = True
                break
            time.sleep(0.02)
    finally:
        signal.signal(signal.SIGINT, old_handler)

    t1.join(timeout=1)
    t2.join(timeout=1)
    
    output = "".join(output_full)
    exit_code = process.returncode if process.returncode is not None else -1
    
    add_to_history(command, output)
    
    return ExecutionResult(exit_code=exit_code, output=output, interrupted=was_interrupted)

def _format_chain_breakdown(chain_results: List[Tuple[str, CommandRisk]]) -> str:
    """Format breakdown of chained command risks for display."""
    if len(chain_results) <= 1:
        return ""
    
    lines: List[str] = []
    for i, (subcmd, risk) in enumerate(chain_results, 1):
        if risk == CommandRisk.DANGER:
            color = "red"
            label = "DANGER"
        elif risk == CommandRisk.CAUTION:
            color = "yellow" 
            label = "CAUTION"
        else:
            color = "green"
            label = "SAFE"
        lines.append(f"  [{color}]{i}. [{label}][/{color}] [dim]{subcmd}[/dim]")
    
    return "\n".join(lines)

def execute_command_with_safety(command: str) -> bool:
    risk = CommandSafety.classify(command)
    description = CommandSafety.get_risk_description(risk)
    chain_results = CommandSafety.classify_chain(command)
    chain_breakdown = _format_chain_breakdown(chain_results)

    if risk == CommandRisk.DANGER:
        content = f"[bold red]BLOCKED:[/bold red] {description}\n[dim]Command: {command}[/dim]"
        if chain_breakdown:
            content += f"\n\n[bold]Command breakdown:[/bold]\n{chain_breakdown}"
        console.print(Panel(
            Text.from_markup(content),
            title="[bold red]DANGER[/bold red]",
            border_style="red"
        ))
        return False

    if risk == CommandRisk.CAUTION:
        content = f"[bold yellow]WARNING:[/bold yellow] {description}\n[dim]Command: {command}[/dim]"
        if chain_breakdown:
            content += f"\n\n[bold]Command breakdown:[/bold]\n{chain_breakdown}"
        console.print(Panel(
            Text.from_markup(content),
            title="[bold yellow]CAUTION[/bold yellow]",
            border_style="yellow"
        ))
        confirm = safe_input("\033[33mExecute? [y/N]\033[0m ")
        if confirm.lower() != 'y':
            return False

    if risk == CommandRisk.SAFE:
        console.print(f"[cyan][SAFE] {description}[/cyan]")

    try:
        parts = shlex.split(command)
    except:
        parts = command.strip().split()

    if parts and parts[0] == "cd":
        shell_operators = ['&&', '||', ';', '|', '>', '<', '`', '$', '(', ')']
        has_operator = any(op in command for op in shell_operators)
        
        if len(parts) <= 2 and not has_operator:
            path = "~"
            if len(parts) > 1:
                path = parts[1]
            
            if path.startswith('/') and len(path) >= 3 and path[1].isalpha() and path[2] == '/':
                path = f"{path[1]}:{path[2:]}"
            
            path = os.path.expanduser(path)
            try:
                os.chdir(path)
            except Exception as e:
                console.print(f"[red]cd: {e}[/red]")
            return True


    try:
        result = execute_with_streaming(command)
        if result.interrupted:
            raise GoBackException()
        return True
    except GoBackException:
        raise
    except Exception as e:
        console.print(f"[bold red]Execution Error:[/bold red] {e}")
        return False

def execute_for_agent(command: str) -> Optional[ExecutionResult]:
    """Execute command and return full result for agentic processing."""
    risk = CommandSafety.classify(command)
    
    if risk == CommandRisk.DANGER:
        console.print(f"[red][BLOCKED] Dangerous command: {command}[/red]")
        return ExecutionResult(exit_code=-1, output="BLOCKED: Dangerous command", interrupted=False)

    if risk == CommandRisk.CAUTION:
        console.print(f"[yellow][AUTO-APPROVED for agent] {command}[/yellow]")

    if risk == CommandRisk.SAFE:
        console.print(f"[cyan][SAFE] {command}[/cyan]")

    try:
        parts = shlex.split(command)
    except:
        parts = command.strip().split()

    if parts and parts[0] == "cd":
        shell_operators = ['&&', '||', ';', '|', '>', '<', '`', '$', '(', ')']
        has_operator = any(op in command for op in shell_operators)
        
        if len(parts) <= 2 and not has_operator:
            path = "~"
            if len(parts) > 1:
                path = parts[1]
            
            if path.startswith('/') and len(path) >= 3 and path[1].isalpha() and path[2] == '/':
                path = f"{path[1]}:{path[2:]}"
            
            path = os.path.expanduser(path)
            try:
                os.chdir(path)
                return ExecutionResult(exit_code=0, output=f"Changed directory to {path}", interrupted=False)
            except Exception as e:
                return ExecutionResult(exit_code=1, output=f"cd: {e}", interrupted=False)

    try:
        return execute_with_streaming(command)
    except Exception as e:
        return ExecutionResult(exit_code=-1, output=str(e), interrupted=False)

MAX_AGENT_ITERATIONS = 3

def run_agentic_loop(provider, goal: str, cwd: str) -> bool:
    history_context = format_history()
    project_context = get_context_for_prompt(cwd, goal)
    last_command: str = ""
    last_output: str = ""
    exploration_output: str = ""
    
    console.print(Panel(
        f"[bold cyan]Goal:[/bold cyan] {goal}\n[dim]Max attempts: {MAX_AGENT_ITERATIONS}[/dim]",
        title="[bold cyan]Agent Mode[/bold cyan]",
        border_style="cyan"
    ))
    
    if project_context:
        console.print(f"[dim]Detected project context[/dim]")
    
    for attempt in range(1, MAX_AGENT_ITERATIONS + 1):
        console.print(f"\n[bold cyan]Attempt {attempt}/{MAX_AGENT_ITERATIONS}[/bold cyan]")
        
        if attempt == 1:
            command = interruptible_generate(provider, goal, cwd, history_context, project_context)
        else:
            explore_cmd = interruptible_exploration(provider, goal, last_command, last_output, cwd)
            
            if explore_cmd:
                console.print(f"[dim]Exploring:[/dim] {explore_cmd}")
                explore_result = execute_for_agent(explore_cmd)
                if explore_result and not explore_result.interrupted:
                    exploration_output = explore_result.output
                    console.print(f"[dim]Got {len(exploration_output)} chars of context[/dim]")
            
            command = interruptible_fix_command(
                provider,
                goal,
                last_command,
                last_output,
                cwd,
                history_context,
                project_context,
                exploration_output
            )
            exploration_output = ""
        
        console.print(f"[yellow]Command:[/yellow] {command}")
        
        result = execute_for_agent(command)
        if result is None:
            console.print("[red]Execution returned no result[/red]")
            last_command = command
            last_output = "No execution result"
            continue
            
        if result.interrupted:
            console.print("[yellow]Interrupted by user[/yellow]")
            return False
        
        success, explanation = provider.check_goal_achieved(goal, command, result.output, result.exit_code)
        
        if success and result.exit_code == 0:
            console.print(Panel(
                f"[bold green]Goal achieved![/bold green]\n{explanation}",
                title="[bold green]Success[/bold green]",
                border_style="green"
            ))
            return True
        
        last_command = command
        last_output = result.output
        console.print(f"[red]Failed:[/red] {explanation}")
        
        if attempt < MAX_AGENT_ITERATIONS:
            history_context = format_history()
    
    console.print(Panel(
        f"[bold red]Goal not achieved after {MAX_AGENT_ITERATIONS} attempts[/bold red]\n[dim]Last output: {last_output[-500:] if len(last_output) > 500 else last_output}[/dim]",
        title="[bold red]Agent Failed[/bold red]",
        border_style="red"
    ))
    return False
