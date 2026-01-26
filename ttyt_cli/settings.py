import os
from .dialogs import show_radio_list
from .styles import get_ttyt_style
from .config import save_config, get_agent_require_confirmation

def show_settings_menu():
    while True:
        current_agent_confirmation = get_agent_require_confirmation()
        
        agent_status = "ON" if current_agent_confirmation else "OFF"
        
        values = [
            ("agent_confirmation", f"Agent Mode Safety: Require confirmation for CAUTION commands [{agent_status}]"),
            ("back", "← Back to terminal"),
        ]
        
        choice = show_radio_list(
            title="Settings",
            values=values,
            default=None,
            style=get_ttyt_style()
        )
        
        if not choice or choice == "back":
            return
        
        if choice == "agent_confirmation":
            toggle_agent_confirmation()

def toggle_agent_confirmation():
    current = get_agent_require_confirmation()
    new_value = not current
    
    status_text = "ENABLED" if new_value else "DISABLED"
    value_str = "true" if new_value else "false"
    
    save_config({"AGENT_REQUIRE_CONFIRMATION": value_str})
    os.environ["AGENT_REQUIRE_CONFIRMATION"] = value_str
    
    description = (
        f"\n✓ Agent Mode Safety: {status_text}\n\n"
        f"{'When enabled, the agent will ask for confirmation before executing' if new_value else 'When disabled, the agent will auto-approve'}\n"
        f"CAUTION commands (npm install, git push, file modifications, etc.)\n\n"
        f"DANGER commands are always blocked in agent mode."
    )
    
    print(f"\n{description}\n")
