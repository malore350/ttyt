from prompt_toolkit.application import Application
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.widgets import RadioList, Label, Frame, TextArea, Button
from prompt_toolkit.styles import Style
from prompt_toolkit.filters import Condition

def show_radio_list(title, values, default=None, style=None):
    radio_list = RadioList(values=values)
    
    if default:
        radio_list.current_value = default
    
    help_msg = Label(text="Use ↑/↓ to navigate, Enter to select, Esc to cancel", style="class:toolbar_dim")

    root_container = Frame(
        HSplit([
            Label(text=title, style="class:frame.label"),
            Window(height=1, char='-'),
            radio_list,
            Window(height=1),
            help_msg
        ]),
        title=title,
        style="class:dialog"
    )

    kb = KeyBindings()

    @kb.add("enter", eager=True)
    def _(event):
        if hasattr(radio_list, '_selected_index'):
             try:
                 selected_val = values[radio_list._selected_index][0]
                 radio_list.current_value = selected_val
                 event.app.exit(result=selected_val)
             except (IndexError, AttributeError):
                 event.app.exit(result=radio_list.current_value)
        else:
             event.app.exit(result=radio_list.current_value)

    @kb.add("c-c")
    @kb.add("escape")
    def _(event):
        event.app.exit(result=None)

    layout = Layout(root_container)
    
    layout.focus(radio_list)

    app = Application(
        layout=layout,
        key_bindings=kb,
        style=style,
        full_screen=False,
        erase_when_done=True,
        mouse_support=True,
    )

    return app.run()

def show_input(title, text, password=False, style=None):
    text_area = TextArea(
        multiline=False,
        password=password,
        style="class:text-area"
    )

    def accept(buff):
        get_app().exit(result=text_area.text)

    root_container = Frame(
        HSplit([
            Label(text=text, style="class:label"),
            Window(height=1),
            text_area,
        ]),
        title=title,
        style="class:dialog"
    )

    kb = KeyBindings()

    @kb.add("enter")
    def _(event):
        event.app.exit(result=text_area.text)

    @kb.add("c-c")
    @kb.add("escape")
    def _(event):
        event.app.exit(result=None)

    layout = Layout(root_container)
    layout.focus(text_area)

    app = Application(
        layout=layout,
        key_bindings=kb,
        style=style,
        full_screen=False,
        erase_when_done=True,
        mouse_support=True,
    )

    return app.run()

def show_message(title, text, style=None):
    from prompt_toolkit.layout.controls import FormattedTextControl
    
    if hasattr(text, '__html__'):
        control = FormattedTextControl(text)
    else:
        control = FormattedTextControl(text)

    root_container = Frame(
        HSplit([
            Window(content=control),
            Window(height=1),
            Label(text="Press Enter to close", style="class:toolbar_dim")
        ]),
        title=title,
        style="class:dialog"
    )

    kb = KeyBindings()

    @kb.add("enter")
    @kb.add("escape")
    @kb.add("c-c")
    def _(event):
        event.app.exit(result=None)

    layout = Layout(root_container)

    app = Application(
        layout=layout,
        key_bindings=kb,
        style=style,
        full_screen=False,
        erase_when_done=True,
        mouse_support=True,
    )

    app.run()
