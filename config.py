import os
from providers import GeminiProvider, ZAIProvider, OpenRouterProvider

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
    print("\033[36m\nManage API Keys:\033[0m")
    print("1. Gemini (Google)")
    print("2. Z.ai (GLM)")
    print("3. OpenRouter (GLM-4.5-Air Free)")
    choice = input("\033[33mSelect provider to set key [1/2/3]: \033[0m").strip()
    
    provider_map = {"1": "gemini", "2": "zai", "3": "openrouter"}
    provider_name = provider_map.get(choice)
    
    if not provider_name:
        print("Invalid choice.")
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
    
    env_key = env_key_map[provider_name]
    url = url_map[provider_name]
    
    print(f"\n\033[36mGet your key at: {url}\033[0m\n")
    api_key = input(f"\033[33mEnter your {provider_name.upper()} API key:\033[0m ").strip()
    
    if api_key:
        save_config({env_key: api_key})
        os.environ[env_key] = api_key
        print(f"\033[32m[OK] {provider_name.upper()} API key saved!\033[0m")
        return True
    return False

def select_model():
    print("\033[36m\nSwitch AI Provider:\033[0m")
    print("1. Gemini (Google)")
    print("2. Z.ai (GLM)")
    print("3. OpenRouter (GLM-4.5-Air Free)")
    choice = input("\033[33mChoice [1/2/3]: \033[0m").strip()
    
    provider_map = {"1": "gemini", "2": "zai", "3": "openrouter"}
    provider_name = provider_map.get(choice)
    
    if not provider_name:
        print("Invalid choice.")
        return False
    
    save_config({"AI_PROVIDER": provider_name})
    os.environ["AI_PROVIDER"] = provider_name
    return True

def setup_provider():
    print("\033[36m\nInitial Setup:\033[0m")
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
