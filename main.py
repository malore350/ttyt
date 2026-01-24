import signal
import os
import sys
try:
    import colorama
except ImportError:
    colorama = None

from utils import exit_handler, show_help, is_natural_language, GoBackException, safe_input
from config import load_env, setup_provider, get_current_provider, select_model, setup_api_keys, ENV_PATH
from core import get_command, execute_command_with_safety
from terminal_ui import TerminalUI

def main():
    signal.signal(signal.SIGINT, exit_handler)
    load_env()

    if colorama:
        colorama.init()

    provider = get_current_provider()
    if not provider:
        setup_provider()
        provider = get_current_provider()

    if not provider:
        print("\033[31mNo provider configured. Exiting.\033[0m")
        sys.exit(1)

    ui = TerminalUI()
    ui.print_welcome(provider)
    show_help()

    while True:
        try:
            cwd = os.getcwd()
            user_input = ui.prompt(provider)
            
            if not user_input:
                continue

            if user_input == "/api":
                setup_api_keys()
                provider = get_current_provider()
                continue
            
            if user_input == "/models":
                if select_model():
                    provider = get_current_provider()
                    if provider:
                        ui.print_message(f"Switched to: {os.getenv('AI_PROVIDER')} ({provider.model_name})", "path")
                continue
            
            if user_input == "/uninstall":
                confirm = safe_input("\033[33mRemove configuration? [y/N]\033[0m ")
                if confirm.lower() == "y":
                    if os.path.exists(ENV_PATH):
                        os.remove(ENV_PATH)
                    ui.print_message("[OK] Configuration removed", "prefix")
                    sys.exit(0)
                continue
            
            if user_input == "/help":
                show_help()
                continue
            
            if user_input.startswith("/"):
                cmd = user_input[1:]
                if not cmd:
                    continue
                if not execute_command_with_safety(cmd):
                    continue
            
            elif not is_natural_language(user_input):
                if not execute_command_with_safety(user_input):
                    continue
            else:
                command = get_command(provider, user_input, cwd)
                execute_command_with_safety(command)
            
        except GoBackException:
            print()
            continue
        except (EOFError, InterruptedError, KeyboardInterrupt):
            print("\n\033[31mExiting...\033[0m")
            sys.exit(0)
        except Exception as e:
            err = str(e)
            if "429" in err or "quota" in err.lower():
                print("\033[31mrate limit hit - wait a moment and try again\033[0m")
            elif "InterruptedError" not in err and "KeyboardInterrupt" not in err:
                print(f"\033[31merror: {err[:100]}\033[0m")

if __name__ == "__main__":
    main()
