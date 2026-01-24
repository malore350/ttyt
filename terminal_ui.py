import os
import sys
from datetime import datetime
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.filters import has_completions
from prompt_toolkit.shortcuts import print_formatted_text

COMMANDS = {
    "/api": "Set/update AI provider API keys",
    "/models": "Switch AI provider or model",
    "/uninstall": "Remove ttyt configuration",
    "/help": "Show help and command safety info",
}

class TerminalUI:
    def __init__(self):
        self.style = self._create_style()
        self.session = self._create_session()
        self.current_provider = None

    def _create_style(self):
        return Style.from_dict({
            'prefix': '#5af78e bold',
            'path': '#6c7086 italic',
            'separator': '#45475a',
            'input-symbol': '#89b4fa bold',
            
            'toolbar': 'bg:#1e1e2e #cdd6f4',
            'toolbar_label': '#bac2de',
            'toolbar_value': '#fab387 bold',
            'toolbar_dim': '#585b70',
            
            'welcome_title': '#89b4fa bold',
            'welcome_text': '#cdd6f4',

            'completion-menu.completion': 'bg:#313244 #cdd6f4',
            'completion-menu.completion.current': 'bg:#45475a #89b4fa bold',
            'completion-menu.scrollbar.background': 'bg:#313244',
            'completion-menu.scrollbar.button': 'bg:#585b70',
            'completion-menu.meta.completion': 'bg:#1e1e2e #6c7086 italic',
            'completion-menu.meta.completion.current': 'bg:#1e1e2e #bac2de italic',
        })

    def _create_session(self):
        completer = WordCompleter(
            list(COMMANDS.keys()), 
            meta_dict=COMMANDS,
            ignore_case=True, 
            sentence=True
        )
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
        @kb.add('c-h')
        def _(event):
            event.current_buffer.delete_before_cursor(count=1)
            if event.current_buffer.completer:
                event.current_buffer.start_completion(select_first=False)

        return PromptSession(

            completer=completer,
            complete_while_typing=True,
            key_bindings=kb,
            bottom_toolbar=self._get_bottom_toolbar,
            refresh_interval=0.5
        )

    def _get_bottom_toolbar(self):
        if not self.current_provider:
             return HTML('<toolbar> <style color="#f38ba8">⚠ No Provider Selected</style> </toolbar>')
        
        provider_name = os.getenv('AI_PROVIDER', 'Unknown').upper()
        model_name = getattr(self.current_provider, 'model_name', 'Unknown')
        
        return HTML(
            f'<toolbar>'
            f'<toolbar_label>PROVIDER:</toolbar_label> <toolbar_value>{provider_name}</toolbar_value> '
            f'<toolbar_dim>|</toolbar_dim> '
            f'<toolbar_label>MODEL:</toolbar_label> <toolbar_value>{model_name}</toolbar_value> '
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
            f'<path>Talk to your terminal. Type a command or a question.</path>\n'
        ), style=self.style)

    def print_message(self, text, style_class=''):
        if style_class:
            print_formatted_text(HTML(f'<{style_class}>{text}</{style_class}>'), style=self.style)
        else:
            print(text)
