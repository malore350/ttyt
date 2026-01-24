import sys
import msvcrt
from prompt_toolkit import prompt
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import ANSI, HTML
from dialogs import show_message
from styles import get_ttyt_style

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
        
    @kb.add('backspace')
    def _(event):
        buffer = event.current_buffer
        # Check if Ctrl is pressed (Windows workaround for Ctrl+Backspace)
        is_ctrl = False
        try:
            import ctypes
            # 0x11 is VK_CONTROL
            is_ctrl = (ctypes.windll.user32.GetAsyncKeyState(0x11) & 0x8000) != 0
        except Exception:
            pass

        if is_ctrl:
            # Ctrl+Backspace behavior
            pos = buffer.document.find_start_of_previous_word(count=1)
            if pos:
                buffer.delete_before_cursor(count=-pos)
        else:
            # Normal Backspace behavior
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

def is_esc_pressed():
    while msvcrt.kbhit():
        if msvcrt.getch() == b'\x1b':
            return True
    return False

def show_help():
    help_text = HTML(
        '<bold>Commands</bold>\n'
        '<style color="#89b4fa">/api</style>       Set/update API keys\n'
        '<style color="#89b4fa">/models</style>    Switch AI provider/model\n'
        '<style color="#89b4fa">/new</style>       Start a new session\n'
        '<style color="#89b4fa">/uninstall</style> Remove configuration\n'
        '<style color="#89b4fa">/ask</style>       Ask a question (no command execution)\n'
        '<style color="#89b4fa">/help</style>      Show this help\n'
        '<style color="#89b4fa">/cmd</style>       Run command directly\n'
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
    
    text_lower = text.lower()
    if text_lower in shell_commands:
        return False
    return not any(text_lower.startswith(s.lower()) for s in shell_starters)
