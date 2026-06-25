import os
import sys
from datetime import datetime
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from .styles import get_ttyt_style
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.filters import Condition, has_completions
from prompt_toolkit.application import get_app
from prompt_toolkit.shortcuts import print_formatted_text

from .utils import is_ctrl_pressed
from .config import get_trust_level

COMMANDS = {
    "/api": "Set/update AI provider API keys",
    "/models": "Switch AI provider or model",
    "/settings": "Configure ttyt behavior",
    "/new": "Start a new session",
    "/uninstall": "Remove ttyt configuration",
    "/ask": "Ask a question (no command execution)",
    "/agent": "Agentic mode - retry until goal achieved",
    "/cmd": "Run a shell command directly (bypass AI)",
    "/clear": "Clear the screen",
    "/exit": "Exit ttyt",
    "/status": "Show current status",
    "/help": "Show help and command safety info",
    "/history": "Show command history",
}

class TerminalUI:
    def __init__(self):
        self.style = get_ttyt_style()
        self.session = self._create_session()
        self.current_provider = None

    def _create_session(self):
        from prompt_toolkit.history import InMemoryHistory
        from .history import command_history

        completer = WordCompleter(
            list(COMMANDS.keys()), 
            meta_dict=COMMANDS,
            ignore_case=True, 
            sentence=True
        )

        history = InMemoryHistory()
        for entry in command_history:
            history.append_string(entry.get("command", ""))

        @Condition
        def is_command():
            return get_app().current_buffer.text.startswith('/')

        kb = KeyBindings()

        @kb.add('enter', filter=has_completions)
        def _(event):
            b = event.current_buffer
            if b.complete_state:
                completion = b.complete_state.current_completion
                if not completion and b.complete_state.completions:
                    completion = b.complete_state.completions[0]
                if completion:
                    b.apply_completion(completion)
                    return
            b.validate_and_handle()

        @kb.add('escape', eager=True)
        def _(event):
            event.current_buffer.reset()

        @kb.add('backspace')
        def _(event):
            buffer = event.current_buffer
            if is_ctrl_pressed():
                pos = buffer.document.find_start_of_previous_word(count=1)
                if pos:
                    buffer.delete_before_cursor(count=-pos)
            else:
                buffer.delete_before_cursor(count=1)
                
            if buffer.completer and buffer.text.startswith('/'):
                buffer.start_completion(select_first=False)

        @kb.add('c-w')
        @kb.add('escape', 'backspace')
        def _(event):
            buffer = event.current_buffer
            pos = buffer.document.find_start_of_previous_word(count=1)
            if pos:
                buffer.delete_before_cursor(count=-pos)
            if buffer.completer and buffer.text.startswith('/'):
                buffer.start_completion(select_first=False)

        return PromptSession(
            history=history,
            completer=completer,
            complete_while_typing=is_command,
            key_bindings=kb,
            bottom_toolbar=self._get_bottom_toolbar,
            refresh_interval=0.5
        )

    def _get_bottom_toolbar(self):
        if not self.current_provider:
             return HTML('<toolbar> <style color="#f38ba8">⚠ No Provider Selected</style> </toolbar>')
        
        provider_key = os.getenv('AI_PROVIDER', 'Unknown')
        provider_name = "GOOGLE" if provider_key == "gemini" else provider_key.upper()
        model_name = getattr(self.current_provider, 'model_name', 'Unknown')
        trust_level = get_trust_level().value
        
        return HTML(
            f'<toolbar>'
            f'<toolbar_label>PROVIDER:</toolbar_label> <toolbar_value>{provider_name}</toolbar_value> '
            f'<toolbar_dim>|</toolbar_dim> '
            f'<toolbar_label>MODEL:</toolbar_label> <toolbar_value>{model_name}</toolbar_value> '
            f'<toolbar_dim>|</toolbar_dim> '
            f'<toolbar_label>TRUST:</toolbar_label> <toolbar_value>{trust_level}</toolbar_value> '
            f'<toolbar_dim>ESC to clear • /help</toolbar_dim>'
            f'</toolbar>'
        )

    def _get_prompt_tokens(self):
        cwd = os.getcwd()
        home = os.path.expanduser('~')
        
        if cwd.startswith(home):
            cwd = '~' + cwd[len(home):]
            
        time_str = datetime.now().strftime('%H:%M')
        
        return [
            ('class:path', f'{cwd} '),
            ('class:separator', 'at '),
            ('class:path', f'{time_str}'),
            ('class:separator', '\n'),
            ('class:input-symbol', '❯ '),
        ]

    def prompt(self, current_provider):
        self.current_provider = current_provider
        return self.session.prompt(self._get_prompt_tokens, style=self.style).strip()

    def print_welcome(self, provider):
        print_formatted_text(HTML(
            f'\n<welcome_title>ttyt</welcome_title> <welcome_text>terminal assistant</welcome_text>\n'
            f'<path>Talk to your terminal. Type a command or a question. Hit /help for commands.</path>\n'
        ), style=self.style)

    def print_message(self, text, style_class=''):
        if style_class:
            print_formatted_text(HTML(f'<{style_class}>{text}</{style_class}>'), style=self.style)
        else:
            print(text)
