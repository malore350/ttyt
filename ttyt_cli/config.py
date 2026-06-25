import os
from pathlib import Path
from .dialogs import show_radio_list, show_input
from .styles import get_ttyt_style
from .providers import get_registered_providers
from .utils import safe_input
from .trust import TrustLevel

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
    providers = get_registered_providers()
    if provider not in providers:
        return True

    info = providers[provider]
    env_key = info["env_key"]
    api_url = info["api_url"]

    if os.getenv(env_key):
        return True
    
    api_key = show_input(
        title=f"Set {provider.upper()} API Key",
        text=f"API Key for {provider} not found.\nGet your key at: {api_url}\n\nEnter API Key:",
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
    providers = get_registered_providers()
    while True:
        provider = show_radio_list(
            title="Manage API Keys",
            values=[(name, name.capitalize()) for name in providers],
            default=current,
            style=get_ttyt_style()
        )
        
        if not provider:
            return False

        if provider not in providers:
            continue
            
        info = providers[provider]
        env_key = info["env_key"]
        api_url = info["api_url"]
        
        api_key = show_input(
            title=f"Set {provider.upper()} API Key",
            text=f"Get your key at: {api_url}\n\nEnter API Key:",
            password=True,
            style=get_ttyt_style()
        )
        
        if api_key:
            save_config({env_key: api_key})
            os.environ[env_key] = api_key
            return True

def select_model():
    current_provider = os.getenv("AI_PROVIDER", "gemini")
    providers = get_registered_providers()
    display_names = {
        "gemini": "Google (Gemini)",
        "zai": "Z.ai (GLM)",
        "openrouter": "OpenRouter"
    }
    while True:
        provider = show_radio_list(
            title="Switch AI Provider",
            values=[(name, display_names.get(name, name.capitalize())) for name in providers],
            default=current_provider,
            style=get_ttyt_style()
        )
        
        if not provider:
            return False

        if not ensure_api_key_for_provider(provider):
            continue

        info = providers[provider]
        model_env_key = f"{provider.upper()}_MODEL"
        current_model = os.getenv(model_env_key) if provider == current_provider else None
            
        model_values = [("__unset__", "Select a model...")]
        for model in info["models"]:
            model_values.append((model, model))
        
        model_choice = show_radio_list(
            title=f"Select {provider.capitalize()} Model",
            values=model_values,
            default=current_model or ("__unset__" if current_provider != provider else None),
            style=get_ttyt_style()
        )
        if not model_choice or model_choice == "__unset__":
            continue

        config_update = {"AI_PROVIDER": provider, model_env_key: model_choice}
        save_config(config_update)
        os.environ["AI_PROVIDER"] = provider
        os.environ[model_env_key] = model_choice
        return True

def setup_provider():
    return select_model()

def get_current_provider():
    provider_name = os.getenv("AI_PROVIDER", "gemini")
    providers = get_registered_providers()
    
    if provider_name not in providers:
        return None
    
    info = providers[provider_name]
    key_name = info["env_key"]
    api_key = os.getenv(key_name)
    
    if not api_key:
        return None
    
    try:
        ProviderClass = info["class"]
        model_env_key = f"{provider_name.upper()}_MODEL"
        return ProviderClass(api_key, os.getenv(model_env_key))
    except Exception as e:
        print(f"\033[31mError initializing provider {provider_name}: {e}\033[0m")
        return None

def get_trust_level() -> TrustLevel:
    level = os.getenv("TRUST_LEVEL", "cautious").lower()
    mapping = {"cautious": TrustLevel.CAUTIOUS, "balanced": TrustLevel.BALANCED, "expert": TrustLevel.EXPERT}
    return mapping.get(level, TrustLevel.CAUTIOUS)
