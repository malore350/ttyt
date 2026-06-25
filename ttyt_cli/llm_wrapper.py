import signal
import threading
import time
from typing import Any, Optional
from rich.live import Live
from rich.text import Text
from .utils import is_cancel_pressed, GoBackException

_cancel_requested = False

def set_cancel_flag():
    global _cancel_requested
    _cancel_requested = True

def interruptible_call(provider, method_name: str, args: tuple = (),
                      spinner_text: str = "Thinking...", silent_error: bool = False):
    """Generic interruptible wrapper around any provider method.

    Runs the provider method in a daemon thread, shows a Live spinner,
    and allows cancellation via SIGINT (Ctrl+C) or ESC key.

    Args:
        provider: The AI provider instance.
        method_name: Name of the method to call on the provider.
        args: Tuple of positional arguments to pass to the method.
        spinner_text: Text shown during the spinner animation.
        silent_error: If True, returns None on error instead of raising.

    Returns:
        The provider method's return value, or None on silent error.

    Raises:
        GoBackException: If the user cancels via SIGINT or ESC.
        Exception: If the provider raises and silent_error is False.
    """
    result: dict[str, Any] = {"value": None, "error": None}
    method = getattr(provider, method_name)

    def target():
        try:
            result["value"] = method(*args)
        except Exception as e:
            result["error"] = str(e)

    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()

    original_handler = signal.signal(signal.SIGINT, lambda sig, frame: set_cancel_flag())
    try:
        with Live(Text(spinner_text, style="cyan"), refresh_per_second=10) as live:
            while thread.is_alive():
                if _cancel_requested or is_cancel_pressed():
                    live.update(Text("Cancelled.", style="red"))
                    raise GoBackException()
                time.sleep(0.02)

            if result["error"]:
                if silent_error:
                    live.update(Text(""))
                    return None
                live.update(Text(f"Error: {result['error']}", style="red"))
                raise Exception(result["error"])

            live.update(Text(""))
    finally:
        signal.signal(signal.SIGINT, original_handler)

    if silent_error:
        return result["value"]
    return result["value"] or ""


def interruptible_generate(provider, user_input, cwd, history_context, os_name, project_context=""):
    return interruptible_call(provider, "generate_command",
        (user_input, cwd, history_context, os_name, project_context),
        spinner_text="Generating command...", silent_error=False)


def interruptible_answer(provider, user_input, cwd, history_context, os_name):
    return interruptible_call(provider, "generate_answer",
        (user_input, cwd, history_context, os_name),
        spinner_text="Thinking...", silent_error=False)


def interruptible_fix_command(provider, goal, failed_command, error_output, cwd, history_context, os_name, project_context="", exploration_output=""):
    return interruptible_call(provider, "generate_fix_command",
        (goal, failed_command, error_output, cwd, history_context, os_name, project_context, exploration_output),
        spinner_text="Generating fix command...", silent_error=False)


def interruptible_exploration(provider, goal, failed_command, error_output, cwd, os_name):
    return interruptible_call(provider, "suggest_exploration_command",
        (goal, failed_command, error_output, cwd, os_name),
        spinner_text="Exploring error...", silent_error=True)
