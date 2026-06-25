from typing import Optional
from rich.panel import Panel
from .core import execute_command, console
from .llm_wrapper import interruptible_generate, interruptible_fix_command, interruptible_exploration
from .project_context import get_context_for_prompt
from .utils import to_posix_path, get_os_info
from .history import format_history
from .trust import TrustLevel

MAX_AGENT_ITERATIONS = 3

def run_agentic_loop(provider, goal: str, cwd: str, trust_level=None, initial_command: str = "", initial_error: str = "") -> bool:
    if trust_level is None:
        trust_level = TrustLevel.CAUTIOUS
    cwd_posix = to_posix_path(cwd)
    os_name = get_os_info()
    history_context = format_history()
    project_context = get_context_for_prompt(cwd, goal)
    last_command: str = ""
    last_output: str = ""
    exploration_output: str = ""

    if initial_command:
        console.print(f"[dim]Escalating from failed command: {initial_command}[/dim]")
        last_command = initial_command
        last_output = initial_error

    console.print(Panel(
        f"[bold cyan]Goal:[/bold cyan] {goal}\n[dim]Max attempts: {MAX_AGENT_ITERATIONS}[/dim]",
        title="[bold cyan]Agent Mode[/bold cyan]",
        border_style="cyan"
    ))

    if project_context:
        console.print(f"[dim]Detected project context[/dim]")

    for attempt in range(1, MAX_AGENT_ITERATIONS + 1):
        console.print(f"\n[bold cyan]Attempt {attempt}/{MAX_AGENT_ITERATIONS}[/bold cyan]")

        if attempt == 1 and not initial_command:
            try:
                command = interruptible_generate(provider, goal, cwd_posix, history_context, os_name, project_context)
            except Exception as e:
                console.print(f"[red]Error generating command: {e}[/red]")
                last_command = ""
                last_output = f"Error generating command: {e}"
                if attempt < MAX_AGENT_ITERATIONS:
                    history_context = format_history()
                continue
        else:
            explore_cmd = interruptible_exploration(provider, goal, last_command, last_output, cwd_posix, os_name)
            
            if explore_cmd:
                console.print(f"[dim]Exploring:[/dim] {explore_cmd}")
                explore_result = execute_command(explore_cmd, auto_approve_caution=True, trust_level=trust_level)
                if explore_result and not explore_result.interrupted:
                    exploration_output = explore_result.output
                    console.print(f"[dim]Got {len(exploration_output)} chars of context[/dim]")
            
            try:
                command = interruptible_fix_command(
                    provider,
                    goal,
                    last_command,
                    last_output,
                    cwd_posix,
                    history_context,
                    os_name,
                    project_context,
                    exploration_output
                )
            except Exception as e:
                console.print(f"[red]Error generating fix: {e}[/red]")
                last_output = f"Error generating fix: {e}"
                exploration_output = ""
                if attempt < MAX_AGENT_ITERATIONS:
                    history_context = format_history()
                continue
            exploration_output = ""
        
        console.print(f"[yellow]Command:[/yellow] {command}")

        result = execute_command(command, auto_approve_caution=True, trust_level=trust_level)

        if result.interrupted:
            console.print("[yellow]Interrupted by user[/yellow]")
            return False
        
        try:
            success, explanation = provider.check_goal_achieved(goal, command, result.output, result.exit_code, os_name)
        except Exception as e:
            console.print(f"[red]Error checking goal: {e}[/red]")
            last_command = command
            last_output = result.output
            if attempt < MAX_AGENT_ITERATIONS:
                history_context = format_history()
            continue
        
        if success:
            if result.exit_code == 0:
                msg = f"[bold green]Goal achieved![/bold green]\n{explanation}"
            else:
                msg = f"[bold green]Goal achieved[/bold green] (exit code {result.exit_code})\n{explanation}"
            console.print(Panel(
                msg,
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
