import os
from pathlib import Path
from .dialogs import show_radio_list, show_input
from .styles import get_ttyt_style
from .providers import GeminiProvider, ZAIProvider, OpenRouterProvider
from .utils import safe_input

CONFIG_DIR = Path.home() / ".ttyt"
ENV_PATH = CONFIG_DIR / ".env"

def ensure_config_dir():
    if not CONFIG_DIR.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def load_env():
    if ENV_PATH.exists():
        with open(ENV_PATH) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value

def save_config(config: dict[str, str]):
    ensure_config_dir()
    lines = []
    if ENV_PATH.exists():
        with open(ENV_PATH, "r") as f:
            existing = {}
            for line in f:
                line = line.strip()
                if line and "=" in line:
                    k, v = line.split("=", 1)
                    existing[k] = v
            existing.update(config)
            for k, v in existing.items():
                lines.append(f"{k}={v}")
    else:
        for k, v in config.items():
            lines.append(f"{k}={v}")
    
    with open(ENV_PATH, "w") as f:
        f.write("\n".join(lines) + "\n")

def ensure_api_key_for_provider(provider: str) -> bool:
    env_key_map = {
        "gemini": "GEMINI_API_KEY",
        "zai": "ZAI_API_KEY",
        "openrouter": "OPENROUTER_API_KEY"
    }
    url_map = {
        "gemini": "https://aistudio.google.com/apikey",
        "zai": "https://z.ai/model-api",
        "openrouter": "https://openrouter.ai/keys"
    }

    env_key = env_key_map.get(provider)
    if not env_key:
        return True

    if os.getenv(env_key):
        return True
    
    url = url_map.get(provider, "")
    api_key = show_input(
        title=f"Set {provider.upper()} API Key",
        text=f"API Key for {provider} not found.\nGet your key at: {url}\n\nEnter API Key:",
        password=True,
        style=get_ttyt_style()
    )
    
    if api_key:
        save_config({env_key: api_key})
        os.environ[env_key] = api_key
        return True
    
    return False

def setup_api_keys():
    current = os.getenv("AI_PROVIDER")
    while True:
        provider = show_radio_list(
            title="Manage API Keys",
            values=[
                ("gemini", "Google (Gemini)"),
                ("zai", "Z.ai (GLM)"),
                ("openrouter", "OpenRouter (Nemotron-3-nano)")
            ],
            default=current,
            style=get_ttyt_style()
        )
        
        if not provider:
            return False

        env_key_map = {
            "gemini": "GEMINI_API_KEY",
            "zai": "ZAI_API_KEY",
            "openrouter": "OPENROUTER_API_KEY"
        }
        url_map = {
            "gemini": "https://aistudio.google.com/apikey",
            "zai": "https://z.ai/model-api",
            "openrouter": "https://openrouter.ai/keys"
        }
        
        env_key = env_key_map.get(provider)
        if not env_key:
            continue
            
        url = url_map.get(provider, "")
        api_key = show_input(
            title=f"Set {provider.upper()} API Key",
            text=f"Get your key at: {url}\n\nEnter API Key:",
            password=True,
            style=get_ttyt_style()
        )
        
        if api_key:
            save_config({env_key: api_key})
            os.environ[env_key] = api_key
            return True

def select_model():
    current_provider = os.getenv("AI_PROVIDER", "gemini")
    while True:
        provider = show_radio_list(
            title="Switch AI Provider",
            values=[
                ("gemini", "Google (Gemini)"),
                ("zai", "Z.ai (GLM)"),
                ("openrouter", "OpenRouter"),
            ],
            default=current_provider,
            style=get_ttyt_style()
        )
        
        if not provider:
            return False

        if not ensure_api_key_for_provider(provider):
            continue

        gemini_model = None
        zai_model = None
        openrouter_model = None
        if provider == "gemini" and current_provider == "gemini":
            gemini_model = os.getenv("GEMINI_MODEL")
        if provider == "zai" and current_provider == "zai":
            zai_model = os.getenv("ZAI_MODEL")
        if provider == "openrouter" and current_provider == "openrouter":
            openrouter_model = os.getenv("OPENROUTER_MODEL")
            
        if provider == "gemini":
            gemini_values = [
                ("__unset__", "Select a model..."),
                ("gemini-3-flash-preview", "gemini-3-flash-preview"),
                ("gemini-2.5-flash", "gemini-2.5-flash"),
                ("gemini-2.5-flash-lite", "gemini-2.5-flash-lite"),
            ]
            model_choice = show_radio_list(
                title="Select Gemini Model",
                values=gemini_values,
                default=gemini_model or ("__unset__" if current_provider != "gemini" else None),
                style=get_ttyt_style()
            )
            if not model_choice or model_choice == "__unset__":
                continue
            gemini_model = model_choice
        elif provider == "zai":
            zai_values = [
                ("__unset__", "Select a model..."),
                ("glm-4.7", "glm-4.7"),
                ("glm-4.7-flashx", "glm-4.7-flashx"),
                ("glm-4.7-flash", "glm-4.7-flash"),
                ("glm-4.6", "glm-4.6"),
            ]
            model_choice = show_radio_list(
                title="Select Z.ai Model",
                values=zai_values,
                default=zai_model or ("__unset__" if current_provider != "zai" else None),
                style=get_ttyt_style()
            )
            if not model_choice or model_choice == "__unset__":
                continue
            zai_model = model_choice
        elif provider == "openrouter":
            openrouter_values = [
                ("__unset__", "Select a model..."),
                ("nvidia/nemotron-3-nano-30b-a3b:free", "nvidia/nemotron-3-nano-30b-a3b:free"),
                ("google/gemma-3-27b-it:free", "google/gemma-3-27b-it:free"),
            ]
            model_choice = show_radio_list(
                title="Select OpenRouter Model",
                values=openrouter_values,
                default=openrouter_model or ("__unset__" if current_provider != "openrouter" else None),
                style=get_ttyt_style()
            )
            if not model_choice or model_choice == "__unset__":
                continue
            openrouter_model = model_choice

        config_update = {"AI_PROVIDER": provider}
        if gemini_model:
            config_update["GEMINI_MODEL"] = gemini_model
        if zai_model:
            config_update["ZAI_MODEL"] = zai_model
        if openrouter_model:
            config_update["OPENROUTER_MODEL"] = openrouter_model

        save_config(config_update)
        os.environ["AI_PROVIDER"] = provider
        if gemini_model:
            os.environ["GEMINI_MODEL"] = gemini_model
        if zai_model:
            os.environ["ZAI_MODEL"] = zai_model
        if openrouter_model:
            os.environ["OPENROUTER_MODEL"] = openrouter_model
        return True

def setup_provider():
    return select_model()

def get_current_provider():
    provider_name = os.getenv("AI_PROVIDER", "gemini")
    
    key_map = {
        "gemini": "GEMINI_API_KEY",
        "zai": "ZAI_API_KEY",
        "openrouter": "OPENROUTER_API_KEY"
    }
    
    key_name = key_map.get(provider_name, "GEMINI_API_KEY")
    api_key = os.getenv(key_name)
    
    if not api_key:
        return None
    
    try:
        if provider_name == "gemini":
            return GeminiProvider(api_key, os.getenv("GEMINI_MODEL"))
        elif provider_name == "zai":
            return ZAIProvider(api_key, os.getenv("ZAI_MODEL"))
        elif provider_name == "openrouter":
            return OpenRouterProvider(api_key, os.getenv("OPENROUTER_MODEL"))
    except Exception as e:
        print(f"\033[31mError initializing provider {provider_name}: {e}\033[0m")
        return None

def get_agent_require_confirmation() -> bool:
    value = os.getenv("AGENT_REQUIRE_CONFIRMATION", "false").lower()
    return value in ("true", "1", "yes", "on")
