import os
import platform
import signal
import subprocess
import threading
import time
import shlex
from typing import Any, List, Tuple, NamedTuple, Optional
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from .safety import CommandSafety, CommandRisk
from .history import add_to_history, add_chat_to_history, format_history
from .utils import safe_input, is_cancel_pressed, GoBackException, to_posix_path, get_bash_path, from_posix_path, get_os_info, kill_process_tree
from .project_context import get_context_for_prompt
from .trust import TrustLevel
from .policy import get_confirmation_policy, ConfirmationAction
from . import llm_wrapper

console = Console()

class ExecutionResult(NamedTuple):
    exit_code: int
    output: str
    interrupted: bool = False

def get_command(provider, user_input: str, cwd: str) -> str:
    cwd_posix = to_posix_path(cwd)
    os_name = get_os_info()
    history_context = format_history()
    project_context = get_context_for_prompt(cwd, user_input)
    try:
        return llm_wrapper.interruptible_generate(provider, user_input, cwd_posix, history_context, os_name, project_context)
    except GoBackException:
        raise
    except Exception as e:
        return f"echo AI Error: {e}"

def get_answer(provider, user_input: str, cwd: str) -> str:
    cwd_posix = to_posix_path(cwd)
    os_name = get_os_info()
    history_context = format_history()
    try:
        answer = llm_wrapper.interruptible_answer(provider, user_input, cwd_posix, history_context, os_name)
        add_chat_to_history(user_input, answer)
        return answer
    except GoBackException:
        raise
    except Exception as e:
        return f"AI Error: {e}"

def execute_with_streaming(command: str, timeout: int = 0) -> ExecutionResult:
    if timeout == 0:
        timeout_str = os.getenv("COMMAND_TIMEOUT", "120")
        try:
            timeout = int(timeout_str)
        except (ValueError, TypeError):
            timeout = 120

    bash_path = get_bash_path()
    is_windows = platform.system() == "Windows"

    popen_kwargs = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "text": True,
        "bufsize": 1,
        "universal_newlines": True
    }
    
    if not is_windows:
        popen_kwargs["preexec_fn"] = os.setsid

    try:
        process = subprocess.Popen(
            [bash_path, "-c", command],
            **popen_kwargs
        )
    except FileNotFoundError:
        process = subprocess.Popen(
            command,
            shell=True,
            **popen_kwargs
        )

    output_full: List[str] = []
    was_interrupted = False
    timed_out = False
    
    def sigint_handler(sig, frame):
        nonlocal was_interrupted
        was_interrupted = True
    
    old_handler = signal.signal(signal.SIGINT, sigint_handler)
    
    # Timeout setup: SIGALRM on Unix, threading.Timer on Windows
    timeout_timer = None
    old_alarm_handler = None
    
    if timeout > 0:
        if is_windows:
            def _on_timeout():
                nonlocal timed_out
                timed_out = True
                kill_process_tree(process.pid)
            timeout_timer = threading.Timer(timeout, _on_timeout)
            timeout_timer.start()
        else:
            def _alarm_handler(signum, frame):
                nonlocal timed_out
                timed_out = True
            old_alarm_handler = signal.signal(signal.SIGALRM, _alarm_handler)
            signal.alarm(timeout)
    
    def stream_reader(pipe, is_stderr=False):
        import sys
        try:
            for line in iter(pipe.readline, ''):
                if is_stderr:
                    sys.stderr.write(line)
                    sys.stderr.flush()
                else:
                    sys.stdout.write(line)
                    sys.stdout.flush()
                output_full.append(line)
        except UnicodeDecodeError:
            msg = '[binary output omitted]\n'
            if is_stderr:
                sys.stderr.write(msg)
                sys.stderr.flush()
            else:
                sys.stdout.write(msg)
                sys.stdout.flush()
            output_full.append(msg)

    t1 = threading.Thread(target=stream_reader, args=(process.stdout, False))
    t2 = threading.Thread(target=stream_reader, args=(process.stderr, True))
    t1.daemon = True
    t2.daemon = True
    t1.start()
    t2.start()

    try:
        while process.poll() is None:
            if timed_out:
                console.print(f"\n[red]Command timed out after {timeout}s. Killing process...[/red]")
                kill_process_tree(process.pid)
                try:
                    process.terminate()
                except ProcessLookupError:
                    pass
                was_interrupted = True
                break
            if was_interrupted or llm_wrapper._cancel_requested or is_cancel_pressed():
                console.print("\n[red][CTRL+C] Stopping process...[/red]")
                kill_process_tree(process.pid)
                try:
                    process.terminate()
                except ProcessLookupError:
                    pass
                was_interrupted = True
                break
            time.sleep(0.02)
    finally:
        signal.signal(signal.SIGINT, old_handler)
        if timeout > 0:
            if is_windows and timeout_timer:
                timeout_timer.cancel()
            else:
                signal.alarm(0)
                if old_alarm_handler is not None:
                    signal.signal(signal.SIGALRM, old_alarm_handler)
        # Reap zombie process
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        # Close file descriptors
        try:
            process.stdout.close()
        except Exception:
            pass
        try:
            process.stderr.close()
        except Exception:
            pass

    t1.join(timeout=1)
    t2.join(timeout=1)
    
    output = "".join(output_full)
    exit_code = process.returncode if process.returncode is not None else -1
    
    add_to_history(command, output)
    
    if timed_out:
        return ExecutionResult(exit_code=-1, output=f"Command timed out after {timeout}s", interrupted=True)
    
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

def _handle_cd(command: str) -> Optional[ExecutionResult]:
    """Handle cd commands specially. Returns ExecutionResult if handled, None otherwise."""
    try:
        parts = shlex.split(command)
    except Exception:
        parts = command.strip().split()

    if parts and parts[0] == "cd":
        shell_operators = ['&&', '||', ';', '|', '>', '<', '`', '$', '(', ')']
        has_operator = any(op in command for op in shell_operators)

        if len(parts) <= 2 and not has_operator:
            path = "~"
            if len(parts) > 1:
                path = parts[1]

            path = from_posix_path(path)
            try:
                os.chdir(path)
                return ExecutionResult(exit_code=0, output=f"Changed directory to {path}", interrupted=False)
            except Exception as e:
                error_msg = f"cd: {e}"
                console.print(f"[red]{error_msg}[/red]")
                return ExecutionResult(exit_code=1, output=error_msg, interrupted=False)

    return None

def execute_command(command: str, *, auto_approve_caution: bool = False, trust_level=None) -> ExecutionResult:
    """Classify, confirm if needed, and execute a command. Returns ExecutionResult."""
    if trust_level is None:
        trust_level = TrustLevel.CAUTIOUS

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
        return ExecutionResult(exit_code=-1, output="BLOCKED: Command is classified as DANGER", interrupted=False)

    if risk == CommandRisk.CAUTION:
        action = get_confirmation_policy(trust_level, CommandRisk.CAUTION)
        content = f"[bold yellow]WARNING:[/bold yellow] {description}\n[dim]Command: {command}[/dim]"
        if chain_breakdown:
            content += f"\n\n[bold]Command breakdown:[/bold]\n{chain_breakdown}"

        if action == ConfirmationAction.REQUIRE_CONFIRMATION:
            console.print(Panel(
                Text.from_markup(content),
                title="[bold yellow]CAUTION[/bold yellow]",
                border_style="yellow"
            ))
            confirm = safe_input("\033[33mExecute? [y/N]\033[0m ")
            if confirm.lower() != 'y':
                return ExecutionResult(exit_code=-1, output="Cancelled", interrupted=False)
        elif action == ConfirmationAction.AUTO_EXECUTE_WITH_NOTICE:
            console.print(f"[dim]Auto-executing (trust: {trust_level.value})[/dim]")
        elif action == ConfirmationAction.AUTO_EXECUTE_SILENT:
            pass  # execute without any extra output

    if risk == CommandRisk.SAFE:
        console.print(f"[cyan][SAFE] {description}[/cyan]")

    cd_result = _handle_cd(command)
    if cd_result is not None:
        return cd_result

    try:
        return execute_with_streaming(command)
    except Exception as e:
        console.print(f"[bold red]Execution Error:[/bold red] {e}")
        return ExecutionResult(exit_code=-1, output=str(e), interrupted=False)


