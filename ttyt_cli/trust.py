from enum import Enum

class TrustLevel(Enum):
    CAUTIOUS = "cautious"    # Confirm CAUTION, never auto-execute risky
    BALANCED = "balanced"    # Auto-execute CAUTION with notice  
    EXPERT = "expert"        # Auto-execute CAUTION silently
