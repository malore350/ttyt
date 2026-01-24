def exit_handler(sig, frame):
    print()
    raise InterruptedError()

def show_help():
    print("\033[36m!api\033[0m       - Set/update API keys")
    print("\033[36m!models\033[0m    - Switch AI provider/model")
    print("\033[36m!uninstall\033[0m - Remove configuration")
    print("\033[36m!help\033[0m      - Show this help")
    print("\033[36m!cmd\033[0m       - Run cmd directly")
    print("\033[36m\nCommand Safety:\033[0m")
    print("\033[32m[SAFE]\033[0m      - Read-only commands auto-execute")
    print("\033[33m[CAUTION]\033[0m   - Confirm before execution")
    print("\033[31m[DANGER]\033[0m    - Destructive commands blocked")
    print()

def is_natural_language(text: str) -> bool:
    if text.startswith("!"):
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
