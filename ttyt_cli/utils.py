import sys
import os
import re
import platform
import shutil
import signal
from typing import Optional
from prompt_toolkit import prompt
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import ANSI, HTML
from .dialogs import show_message
from .styles import get_ttyt_style

try:
    import msvcrt
except ImportError:
    msvcrt = None

try:
    import select
    import termios
    import tty
except ImportError:
    select = None
    termios = None
    tty = None

class GoBackException(Exception):
    pass

def get_os_info() -> str:
    system = platform.system()
    if system == "Windows":
        if os.environ.get("PSVersionTable"):
            return "Windows (PowerShell)"
        if shutil.which("powershell") or shutil.which("pwsh"):
            return "Windows (PowerShell)"
        return "Windows (Git Bash)"
    elif system == "Darwin":
        return "macOS"
    elif system == "Linux":
        try:
            with open('/proc/sys/kernel/osrelease', 'r') as f:
                if 'microsoft' in f.read().lower():
                    return "WSL (Linux)"
        except (IOError, FileNotFoundError):
            pass
        return "Linux"
    return system

def to_posix_path(path: str) -> str:
    if not path:
        return path
    
    if platform.system() != "Windows":
        return path.replace('\\', '/')
    
    path = path.replace('\\', '/')
    
    drive_match = re.match(r'^([a-zA-Z]):/', path)
    if drive_match:
        drive_letter = drive_match.group(1).lower()
        path = f"/{drive_letter}{path[2:]}"
    elif re.match(r'^([a-zA-Z]):$', path):
        path = f"/{path[0].lower()}"
        
    return path

def from_posix_path(path: str) -> str:
    if not path:
        return path
        
    if platform.system() != "Windows":
        return path
        
    if path.startswith('/') and len(path) >= 3 and path[1].isalpha() and (path[2] == '/' or len(path) == 2):
        drive_letter = path[1].upper()
        suffix = path[2:] if len(path) > 2 else ""
        if suffix == "/":
            suffix = ""
        path = f"{drive_letter}:{suffix}"
    
    return os.path.expanduser(path)

def get_bash_path() -> str:
    if platform.system() != "Windows":
        return "bash"

    bash_in_path = shutil.which("bash")
    if bash_in_path:
        return bash_in_path
        
    paths = [
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files (x86)\Git\bin\bash.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Git\bin\bash.exe"),
    ]
    
    for p in paths:
        if os.path.exists(p):
            return p
            
    return "bash"

def kill_process_tree(pid: int):
    if platform.system() == "Windows":
        import subprocess
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], 
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            os.waitpid(-os.getpgid(pid), os.WNOHANG)
        except (ChildProcessError, OSError):
            pass

def clear_screen():
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

def exit_handler(sig, frame):
    print("\n\033[31mExiting...\033[0m")
    sys.exit(0)

def is_ctrl_pressed() -> bool:
    if platform.system() != "Windows":
        return False
    try:
        import ctypes
        return (ctypes.windll.user32.GetAsyncKeyState(0x11) & 0x8000) != 0
    except Exception:
        return False

def safe_input(text: str) -> str:
    kb = KeyBindings()
    
    @kb.add('escape', eager=True)
    def _(event):
        event.app.exit(exception=GoBackException)
        
    @kb.add('backspace')
    def _(event):
        buffer = event.current_buffer
        if is_ctrl_pressed():
            pos = buffer.document.find_start_of_previous_word(count=1)
            if pos:
                buffer.delete_before_cursor(count=-pos)
        else:
            buffer.delete_before_cursor(count=1)

    @kb.add('c-w')
    @kb.add('escape', 'backspace')
    def _(event):
        buffer = event.current_buffer
        pos = buffer.document.find_start_of_previous_word(count=1)
        if pos:
            buffer.delete_before_cursor(count=-pos)

    try:
        return prompt(ANSI(text), key_bindings=kb).strip()
    except GoBackException:
        raise
    except EOFError:
        raise KeyboardInterrupt()

def is_cancel_pressed() -> bool:
    """Non-blocking check for ESC key press. Cross-platform: msvcrt on Windows, select+termios on Unix."""
    if msvcrt is not None:
        if msvcrt.kbhit():
            if msvcrt.getch() == b'\x1b':
                return True
        return False

    if select is not None and termios is not None and tty is not None:
        if not sys.stdin.isatty():
            return False
        try:
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            tty.setraw(fd)
            try:
                ready, _, _ = select.select([sys.stdin], [], [], 0.02)
                if ready:
                    ch = sys.stdin.read(1)
                    if ch == '\x1b':
                        return True
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except (termios.error, OSError, ValueError):
            pass
        return False

    return False

def show_help():
    help_text = HTML(
        '<bold>Commands</bold>\n'
        '<style color="#89b4fa">/api</style>       Set/update API keys\n'
        '<style color="#89b4fa">/models</style>    Switch AI provider/model\n'
        '<style color="#89b4fa">/settings</style>  Configure ttyt behavior\n'
        '<style color="#89b4fa">/new</style>       Start a new session\n'
        '<style color="#89b4fa">/uninstall</style> Remove configuration\n'
        '<style color="#89b4fa">/ask</style>       Ask a question (no command execution)\n'
        '<style color="#89b4fa">/agent</style>     Agentic mode - retry until goal achieved\n'
        '<style color="#89b4fa">/help</style>      Show this help\n'
        '<style color="#89b4fa">/cmd</style>       Run command directly\n'
        '<style color="#89b4fa">/clear</style>     Clear the screen\n'
        '<style color="#89b4fa">/exit</style>      Exit ttyt\n'
        '<style color="#89b4fa">/status</style>    Show current status\n'
        '\n'
        '<bold>Command Safety</bold>\n'
        '<style color="green">[SAFE]</style>    Read-only commands auto-execute\n'
        '<style color="yellow">[CAUTION]</style> Confirm before execution\n'
        '<style color="red">[DANGER]</style>  Destructive commands blocked'
    )
    
    show_message(
        title="Help",
        text=help_text,
        style=get_ttyt_style()
    )


def is_natural_language(text: str) -> bool:
    if text.startswith("/"):
        return False

    shell_commands = ["ls", "cd", "clear", "exit", "pwd", "cp", "rm", "mv",
                      "mkdir", "rmdir", "cat", "echo", "export", "grep", "find",
                      "ssh", "scp", "git", "npm", "node", "python", "pip"]

    shell_starters = ["cd ", "ls ", "echo ", "cat ", "cp ", "rm ", "mv ", "mkdir ",
                      "rmdir ", "git ", "npm ", "node ", "npx ", "python ", "pip ",
                      "ssh ", "./", "../", "/", "export ", "grep "]

    nl_words = {
        "my", "the", "our", "some", "any", "all", "this", "that", "these", "those",
        "a", "an", "me", "you", "him", "her", "us", "them", "it",
        "to", "for", "with", "in", "on", "at", "by", "from", "of", "about",
        "into", "through", "during", "before", "after", "above", "below", "between", "under",
        "again", "further", "then", "once", "here", "there",
        "when", "where", "why", "how", "which", "who", "what", "whose", "whom",
    }

    text_lower = text.lower().strip()

    if text_lower in shell_commands:
        return False

    matched_starter = None
    for starter in shell_starters:
        if text_lower.startswith(starter.lower()):
            matched_starter = starter
            break

    if matched_starter is None:
        return True

    rest = text_lower[len(matched_starter):].strip()

    rest_words = set(rest.split())
    if rest_words & nl_words:
        return True

    if re.search(r'(^|\s)-[a-zA-Z0-9-]', rest):
        return False
    if re.search(r'(^|\s)[/~.]', rest):
        return False
    if re.search(r'\.\w{1,5}(\s|$)', rest):
        return False

    return False

