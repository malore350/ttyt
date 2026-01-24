import sys
import msvcrt
from prompt_toolkit import prompt
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import ANSI
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

class GoBackException(Exception):
    pass

def exit_handler(sig, frame):
    print("\n\033[31mExiting...\033[0m")
    sys.exit(0)

def safe_input(text: str) -> str:
    kb = KeyBindings()
    
    @kb.add('escape', eager=True)
    def _(event):
        event.app.exit(exception=GoBackException)

    try:
        return prompt(ANSI(text), key_bindings=kb).strip()
    except GoBackException:
        raise
    except EOFError:
        raise KeyboardInterrupt()

def is_esc_pressed():
    while msvcrt.kbhit():
        if msvcrt.getch() == b'\x1b':
            return True
    return False

def show_help():
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_row("[cyan]/api[/cyan]", "Set/update API keys")
    table.add_row("[cyan]/models[/cyan]", "Switch AI provider/model")
    table.add_row("[cyan]/uninstall[/cyan]", "Remove configuration")
    table.add_row("[cyan]/help[/cyan]", "Show this help")
    table.add_row("[cyan]/cmd[/cyan]", "Run command directly")

    safety_table = Table(show_header=False, box=None, padding=(0, 2))
    safety_table.add_row("[green][SAFE][/green]", "Read-only commands auto-execute")
    safety_table.add_row("[yellow][CAUTION][/yellow]", "Confirm before execution")
    safety_table.add_row("[red][DANGER][/red]", "Destructive commands blocked")

    console.print(Panel(table, title="Commands", border_style="blue", expand=False))
    console.print(Panel(safety_table, title="Command Safety", border_style="blue", expand=False))

def is_natural_language(text: str) -> bool:
    if text.startswith("/"):
        return False
    shell_commands = ["ls", "cd", "clear", "exit", "pwd", "cp", "rm", "mv", 
                      "mkdir", "rmdir", "cat", "echo", "export", "grep", "find", 
                      "ssh", "scp", "git", "npm", "node", "python", "pip"]
    
    shell_starters = ["cd ", "ls ", "echo ", "cat ", "cp ", "rm ", "mv ", "mkdir ", 
                      "rmdir ", "git ", "npm ", "node ", "npx ", "python ", "pip ", 
                      "ssh ", "./", "../", "/", "export ", "grep "]
    
    text_lower = text.lower()
    if text_lower in shell_commands:
        return False
    return not any(text_lower.startswith(s.lower()) for s in shell_starters)
