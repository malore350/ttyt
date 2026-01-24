import os
from dialogs import show_radio_list, show_input
from styles import get_ttyt_style
from providers import GeminiProvider, ZAIProvider, OpenRouterProvider
from utils import safe_input

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(SCRIPT_DIR, ".env")

def load_env():
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value

def save_config(config: dict):
    lines = []
    if os.path.exists(ENV_PATH):
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

def setup_api_keys():
    current = os.getenv("AI_PROVIDER")
    provider_choice = show_radio_list(
        title="Manage API Keys",
        values=[
            ("gemini", "Gemini (Google)"),
            ("zai", "Z.ai (GLM)"),
            ("openrouter", "OpenRouter (GLM-4.5-Air Free)")
        ],
        default=current,
        style=get_ttyt_style()
    )
    
    if not provider_choice:
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
    
    env_key = env_key_map[provider_choice]
    url = url_map[provider_choice]
    
    api_key = show_input(
        title=f"Set {provider_choice.upper()} API Key",
        text=f"Get your key at: {url}\n\nEnter API Key:",
        password=True,
        style=get_ttyt_style()
    )
    
    if api_key:
        save_config({env_key: api_key})
        os.environ[env_key] = api_key
        return True
    return False

def select_model():
    current = os.getenv("AI_PROVIDER", "gemini")
    result = show_radio_list(
        title="Switch AI Provider",
        values=[
            ("gemini", "Gemini (Google)"),
            ("zai", "Z.ai (GLM)"),
            ("openrouter", "OpenRouter (GLM-4.5-Air Free)"),
        ],
        default=current,
        style=get_ttyt_style()
    )
    
    if not result:
        return False
    
    save_config({"AI_PROVIDER": result})
    os.environ["AI_PROVIDER"] = result
    return True

def setup_provider():
    if not select_model():
        return False
    
    provider_name = os.getenv("AI_PROVIDER")
    env_key_map = {"gemini": "GEMINI_API_KEY", "zai": "ZAI_API_KEY", "openrouter": "OPENROUTER_API_KEY"}
    env_key = env_key_map.get(provider_name)
    
    if not os.getenv(env_key):
        return setup_api_keys()
    return True

def get_current_provider():
    provider_name = os.getenv("AI_PROVIDER", "gemini")
    
    key_map = {
        "gemini": "GEMINI_API_KEY",
        "zai": "ZAI_API_KEY",
        "openrouter": "OPENROUTER_API_KEY"
    }
    
    api_key = os.getenv(key_map.get(provider_name, "GEMINI_API_KEY"))
    
    if not api_key:
        return None
    
    try:
        if provider_name == "gemini":
            return GeminiProvider(api_key)
        elif provider_name == "zai":
            return ZAIProvider(api_key)
        elif provider_name == "openrouter":
            return OpenRouterProvider(api_key)
    except Exception as e:
        print(f"\033[31mError initializing provider {provider_name}: {e}\033[0m")
        return None
