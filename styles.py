from prompt_toolkit.styles import Style

def get_ttyt_style():
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

        'dialog': 'bg:#1e1e2e',
        'dialog.body': 'bg:#1e1e2e #cdd6f4',
        'dialog.shadow': 'bg:#000000',
        'dialog border': '#89b4fa',
        'label': '#cdd6f4',
        
        'button': 'bg:#313244 #cdd6f4',
        'button.focused': 'bg:#89b4fa #1e1e2e bold',
        
        'text-area': 'bg:#181825 #cdd6f4',
        'text-area.cursor': 'bg:#cdd6f4 #181825',
        
        'radio-list': 'bg:#1e1e2e #cdd6f4',
        'radio-list.current': '#89b4fa bold',
        'radio-list.selection': '#89b4fa bold',
        
        'frame.label': '#89b4fa bold',
        'frame.border': '#585b70',
    })
