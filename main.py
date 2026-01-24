import signal
import os
import sys
try:
    import colorama
except ImportError:
    colorama = None

from utils import exit_handler, show_help, is_natural_language
from config import load_env, setup_provider, get_current_provider, select_model, setup_api_keys, ENV_PATH
from core import get_command, execute_command_with_safety

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

    print("\033[1mttyt (Windows Edition)\033[0m - talk to your terminal")
    print(f"Using provider: \033[36m{os.getenv('AI_PROVIDER', 'gemini')}\033[0m (\033[35m{provider.model_name}\033[0m)\n")
    show_help()

    while True:
        try:
            cwd = os.getcwd()
            prompt = f"\033[32m{cwd}\033[0m > "
            user_input = input(prompt).strip()
            
            if not user_input:
                continue

            if user_input == "!api":
                setup_api_keys()
                provider = get_current_provider()
                continue
            
            if user_input == "!models":
                if select_model():
                    provider = get_current_provider()
                    if provider:
                        print(f"Switched to: \033[36m{os.getenv('AI_PROVIDER')}\033[0m (\033[35m{provider.model_name}\033[0m)\n")
                continue
            
            if user_input == "!uninstall":
                confirm = input("\033[33mRemove configuration? [y/N]\033[0m ")
                if confirm.lower() == "y":
                    if os.path.exists(ENV_PATH):
                        os.remove(ENV_PATH)
                    print("\033[32m[OK] Configuration removed\033[0m")
                    sys.exit(0)
                continue
            
            if user_input == "!help":
                show_help()
                continue
            
            if user_input.startswith("!"):
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
            
        except (EOFError, InterruptedError, KeyboardInterrupt):
            print("\n")
            continue
        except Exception as e:
            err = str(e)
            if "429" in err or "quota" in err.lower():
                print("\033[31mrate limit hit - wait a moment and try again\033[0m")
            elif "InterruptedError" not in err and "KeyboardInterrupt" not in err:
                print(f"\033[31merror: {err[:100]}\033[0m")

if __name__ == "__main__":
    main()
