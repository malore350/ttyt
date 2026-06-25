from enum import Enum, auto
from .utils import is_natural_language


class IntentType(Enum):
    COMMAND = auto()   # User wants to run a shell command (NL → LLM → command)
    QUESTION = auto()  # User wants an answer, no execution
    GOAL = auto()      # User wants multi-step agent assistance
    SHELL = auto()     # User typed a direct shell command, no LLM needed


_QUESTION_STARTS = [
    "what", "how", "why", "who", "when", "where", "which",
    "can you", "could you", "explain", "tell me about",
    "describe", "show me how to",
]

_INTERROGATIVE_STARTS = [
    "is ", "are ", "does ", "do ", "should ", "would ", "could ",
]

_GOAL_PHRASES = [
    "and then", "after that", "make sure", "set up", "configure",
    "deploy", "fix the issue", "fix all", "solve the problem",
    "migrate", "refactor", "install and configure",
]


def classify_intent(user_input: str) -> IntentType:
    text = user_input.strip()
    text_lower = text.lower()

    # 1. Slash commands — default to COMMAND since dispatch table handles them first
    if text.startswith("/"):
        return IntentType.COMMAND

    # 2. Direct shell command (improved heuristics, no LLM needed)
    if not is_natural_language(text):
        return IntentType.SHELL

    # 3. Question detection
    if text_lower.endswith("?"):
        return IntentType.QUESTION

    for qs in _QUESTION_STARTS:
        if text_lower.startswith(qs):
            return IntentType.QUESTION

    for iq in _INTERROGATIVE_STARTS:
        if text_lower.startswith(iq):
            return IntentType.QUESTION

    # 4. Multi-step goal detection
    for gp in _GOAL_PHRASES:
        if gp in text_lower:
            return IntentType.GOAL

_SINGLE_ACTION_VERBS = [
    "uninstall", "remove", "delete", "show", "list", "get",
    "find", "check", "download", "install", "create", "open",
    "run", "start", "stop", "restart", "build", "test", "push",
    "pull", "clone", "copy", "move", "rename", "export",
]

...

    if len(text) > 50:
        first_word = text_lower.split()[0] if text_lower.split() else ""
        if first_word not in _SINGLE_ACTION_VERBS:
            return IntentType.GOAL

    # 5. Default — natural language that should be translated to a command
    return IntentType.COMMAND
