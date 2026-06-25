import json
import os
from datetime import datetime

MAX_HISTORY = 10
MAX_CONTEXT_CHARS = 4000
command_history: list = []

HISTORY_FILE = os.path.expanduser("~/.ttyt/history.json")


def _ensure_dir() -> None:
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)


def _save_history() -> None:
    _ensure_dir()
    tmp_path = HISTORY_FILE + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(command_history, f, ensure_ascii=False)
    os.rename(tmp_path, HISTORY_FILE)


def _load_history() -> None:
    if not os.path.exists(HISTORY_FILE):
        return
    try:
        with open(HISTORY_FILE, "r") as f:
            data = json.load(f)
        if isinstance(data, list):
            command_history.extend(data)
            while len(command_history) > MAX_HISTORY:
                command_history.pop(0)
            while get_context_size() > MAX_CONTEXT_CHARS and len(command_history) > 1:
                command_history.pop(0)
    except (json.JSONDecodeError, OSError):
        pass


def get_context_size() -> int:
    return sum(len(e["command"]) + len(e["output"]) for e in command_history)


def add_to_history(command: str, output: str = "", entry_type: str = "command"):
    command_history.append({
        "command": command,
        "output": output[-2000:] if output else "",
        "type": entry_type,
        "timestamp": datetime.now().isoformat(),
    })
    while len(command_history) > MAX_HISTORY:
        command_history.pop(0)
    while get_context_size() > MAX_CONTEXT_CHARS and len(command_history) > 1:
        command_history.pop(0)
    _save_history()


def add_chat_to_history(question: str, answer: str = ""):
    add_to_history(f"Q: {question}", f"A: {answer}" if answer else "", entry_type="chat")


def clear_history() -> None:
    command_history.clear()
    if os.path.exists(HISTORY_FILE):
        try:
            os.remove(HISTORY_FILE)
        except OSError:
            pass


def get_history_entries() -> list:
    return list(command_history)


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


# Load persisted history on module import
_load_history()
