MAX_HISTORY = 10
MAX_CONTEXT_CHARS = 4000
command_history = []

def get_context_size() -> int:
    return sum(len(e["command"]) + len(e["output"]) for e in command_history)

def add_to_history(command: str, output: str = "", entry_type: str = "command"):
    command_history.append({
        "command": command,
        "output": output[:2000] if output else "",
        "type": entry_type
    })
    while len(command_history) > MAX_HISTORY:
        command_history.pop(0)
    while get_context_size() > MAX_CONTEXT_CHARS and len(command_history) > 1:
        command_history.pop(0)

def add_chat_to_history(question: str, answer: str = ""):
    add_to_history(f"Q: {question}", f"A: {answer}" if answer else "", entry_type="chat")

def clear_history() -> None:
    command_history.clear()

def format_history() -> str:
    if not command_history:
        return "No previous commands."
    
    lines = []
    for i, entry in enumerate(command_history[-5:], 1):
        if entry.get("type") == "chat":
            lines.append(f"{entry['command']}")
        else:
            lines.append(f"{i}. > {entry['command']}")
        
        if entry['output']:
            output_lines = entry['output'].strip().split('\n')
            for line in output_lines:
                lines.append(f"   {line}")
    return "\n".join(lines)
