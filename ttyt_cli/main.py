import signal
import os
import sys
import traceback
try:
    import colorama
except ImportError:
    colorama = None

from .utils import exit_handler, show_help, is_natural_language, GoBackException, safe_input, clear_screen
from .config import load_env, setup_provider, get_current_provider, select_model, setup_api_keys, ENV_PATH, get_trust_level
from .core import get_command, get_answer, execute_command, console
from .agentic import run_agentic_loop
from .intent import classify_intent, IntentType
from .output_parser import parse_llm_command
from .history import clear_history
from .terminal_ui import TerminalUI
from .settings import show_settings_menu
from .history import command_history
from .trust import TrustLevel
from rich.panel import Panel
import shlex

_should_exit = False
_escalation_count = 0


def handle_api(provider, args, ui):
    setup_api_keys()
    return get_current_provider()


def handle_models(provider, args, ui):
    if select_model():
        provider = get_current_provider()
        if provider:
            ui.print_message(f"Switched to: {os.getenv('AI_PROVIDER')} ({provider.model_name})", "path")
    return provider


def handle_settings(provider, args, ui):
    show_settings_menu()
    return provider


def handle_new(provider, args, ui):
    global _escalation_count
    clear_screen()
    clear_history()
    _escalation_count = 0
    ui.print_welcome(provider)
    return provider


def handle_uninstall(provider, args, ui):
    global _should_exit
    confirm = safe_input("\033[33mRemove configuration? [y/N]\033[0m ")
    if confirm.lower() == "y":
        if os.path.exists(ENV_PATH):
            os.remove(ENV_PATH)
        ui.print_message("[OK] Configuration removed", "prefix")
        _should_exit = True
    return provider


def handle_help(provider, args, ui):
    show_help()
    return provider


def handle_ask(provider, args, ui):
    question = args
    if not question:
        question = safe_input("Ask: ")
    if not question:
        return provider
    answer = get_answer(provider, question, os.getcwd())
    ui.print_message(answer)
    return provider


def handle_agent(provider, args, ui):
    goal = args
    if not goal:
        goal = safe_input("Goal: ")
    if not goal:
        return provider
    run_agentic_loop(provider, goal, os.getcwd())
    return provider


def handle_cmd(provider, args, ui):
    if not args:
        print("Usage: /cmd <shell command>")
        return provider
    result = execute_command(args)
    if result.interrupted:
        print("\033[33m(Exited)\033[0m")
    return provider


def handle_clear(provider, args, ui):
    clear_screen()
    return provider


def handle_exit(provider, args, ui):
    global _should_exit
    _should_exit = True
    print("\033[32mGoodbye!\033[0m")
    return provider


def handle_status(provider, args, ui):
    status_text = f"""
Provider: {provider.__class__.__name__}
Model: {getattr(provider, 'model_name', 'unknown')}
History entries: {len(command_history)}
    """
    print(Panel(status_text.strip(), title="Status", border_style="cyan"))
    return provider


def handle_history(provider, args, ui):
    from .history import get_history_entries
    from .core import console

    entries = get_history_entries()
    if not entries:
        console.print(Panel("No command history yet", title="Command History"))
        return provider

    display_entries = entries[-20:]
    lines = []
    for i, entry in enumerate(display_entries, 1):
        cmd = entry.get("command", "")
        output = entry.get("output", "")
        entry_type = entry.get("type", "")
        type_tag = " [dim](chat)[/dim]" if entry_type == "chat" else ""
        lines.append(f"{i}. > {cmd}{type_tag}")
        if output:
            truncated = output[:100].replace("\n", " ")
            suffix = "..." if len(output) > 100 else ""
            lines.append(f"   [dim]{truncated}{suffix}[/dim]")

    console.print(Panel("\n".join(lines), title="Command History"))
    return provider


SLASH_COMMANDS = {
    "/api": handle_api,
    "/models": handle_models,
    "/settings": handle_settings,
    "/new": handle_new,
    "/uninstall": handle_uninstall,
    "/help": handle_help,
    "/ask": handle_ask,
    "/agent": handle_agent,
    "/cmd": handle_cmd,
    "/clear": handle_clear,
    "/exit": handle_exit,
    "/status": handle_status,
    "/history": handle_history,
}


def main():
    signal.signal(signal.SIGINT, exit_handler)
    load_env()

    if colorama:
        colorama.init()

    provider = get_current_provider()
    if not provider:
        try:
            setup_provider()
            provider = get_current_provider()
        except GoBackException:
            print("\033[33m(Exited)\033[0m")

    if not provider:
        print("\033[31mNo provider configured. Exiting.\033[0m")
        sys.exit(1)

    ui = TerminalUI()
    ui.print_welcome(provider)

    while True:
        try:
            if _should_exit:
                break

            cwd = os.getcwd()
            user_input = ui.prompt(provider)

            if not user_input:
                continue

            parts = user_input.split(maxsplit=1)
            cmd = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""

            if cmd in SLASH_COMMANDS:
                handler = SLASH_COMMANDS[cmd]
                provider = handler(provider, args, ui)
                continue

            if cmd.startswith("/"):
                print("Unknown command. Type /help for available commands.")
                continue

            intent = classify_intent(user_input)
            current_trust = get_trust_level()

            if intent == IntentType.SHELL:
                result = execute_command(user_input, trust_level=current_trust)
                if result.interrupted:
                    print("\033[33m(Exited)\033[0m")
                    continue
                if result.exit_code != 0:
                    continue
            elif intent == IntentType.COMMAND:
                command = get_command(provider, user_input, cwd)
                command = parse_llm_command(command)
                if command is None:
                    console.print("[red]AI couldn't generate a clean command. Try rephrasing.[/red]")
                    continue
                console.print(f"[yellow]Command:[/yellow] {command}")
                result = execute_command(command, trust_level=current_trust)
                if result.interrupted:
                    print("\033[33m(Exited)\033[0m")
                    continue
                if result.exit_code != 0:
                    if result.output.startswith("BLOCKED:"):
                        continue
                    # Skip escalation for "nothing found" results:
                    # tools like lsof/grep/find exit 1 when they find nothing —
                    # that's the correct answer, not a failure.
                    if not result.output.strip():
                        continue
                    try:
                        parts = shlex.split(command)
                    except Exception:
                        parts = command.strip().split()
                    shell_operators = ['&&', '||', ';', '|', '>', '<', '`', '$', '(', ')']
                    has_operator = any(op in command for op in shell_operators)
                    is_simple_cd = parts and parts[0] == "cd" and len(parts) <= 2 and not has_operator
                    if is_simple_cd:
                        continue
                    global _escalation_count
                    if _escalation_count >= 3:
                        continue
                    _escalation_count += 1
                    if current_trust == TrustLevel.EXPERT:
                        console.print("[dim]Auto-fixing...[/dim]")
                        run_agentic_loop(provider, user_input, cwd, trust_level=current_trust, initial_command=command, initial_error=result.output)
                    else:
                        if current_trust == TrustLevel.CAUTIOUS:
                            prompt_text = "The command failed. Want me to try to fix this automatically? [y/N]"
                        else:
                            prompt_text = "The command failed. Want me to try to fix this automatically? [Y/n]"
                        confirm = safe_input(f"\033[33m{prompt_text}\033[0m ")
                        if current_trust == TrustLevel.BALANCED:
                            if confirm.lower() != "n":
                                run_agentic_loop(provider, user_input, cwd, trust_level=current_trust, initial_command=command, initial_error=result.output)
                        else:
                            if confirm.lower() == "y":
                                run_agentic_loop(provider, user_input, cwd, trust_level=current_trust, initial_command=command, initial_error=result.output)
                    continue
            elif intent == IntentType.QUESTION:
                answer = get_answer(provider, user_input, cwd)
                console.print(answer)
                continue
            elif intent == IntentType.GOAL:
                success = run_agentic_loop(provider, user_input, cwd, trust_level=current_trust)
                continue

        except GoBackException:
            print("\033[33m(Exited)\033[0m")
            continue
        except (EOFError, InterruptedError, KeyboardInterrupt):
            print("\n\033[31mExiting...\033[0m")
            sys.exit(0)
        except Exception as e:
            err = str(e)
            if "429" in err or "quota" in err.lower():
                print("\033[31mrate limit hit - wait a moment and try again\033[0m")
            elif "InterruptedError" not in err and "KeyboardInterrupt" not in err:
                if os.environ.get("TTYT_DEBUG") or os.environ.get("DEBUG"):
                    traceback.print_exc()
                else:
                    print(f"\033[31merror: {err[:100]}\033[0m")

if __name__ == "__main__":
    main()
