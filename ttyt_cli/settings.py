import os
from .dialogs import show_radio_list
from .styles import get_ttyt_style
from .config import save_config, get_trust_level

def show_settings_menu():
    while True:
        current_trust = get_trust_level()
        trust_display = current_trust.value.capitalize()

        values = [
            ("trust_level", f"Trust Level: {trust_display}"),
            ("back", "\u2190 Back to terminal"),
        ]

        choice = show_radio_list(
            title="Settings",
            values=values,
            default=None,
            style=get_ttyt_style()
        )

        if not choice or choice == "back":
            return

        if choice == "trust_level":
            trust_selection_dialog()

def trust_selection_dialog():
    trust_values = [
        ("cautious", "Cautious \u2014 Confirm before executing potentially dangerous commands (recommended)"),
        ("balanced", "Balanced \u2014 Auto-execute with a notice, no confirmation needed"),
        ("expert", "Expert \u2014 Auto-execute silently. DANGER commands are still always blocked."),
    ]

    choice = show_radio_list(
        title="Select Trust Level",
        values=trust_values,
        default=get_trust_level().value,
        style=get_ttyt_style()
    )

    if not choice:
        return

    save_config({"TRUST_LEVEL": choice})
    os.environ["TRUST_LEVEL"] = choice
    print(f"\n\u2713 Trust level set to: {choice.capitalize()}\n")
