from enum import Enum, auto
from .trust import TrustLevel
from .safety import CommandRisk

class ConfirmationAction(Enum):
    AUTO_EXECUTE = auto()         # Execute immediately, no prompt
    REQUIRE_CONFIRMATION = auto() # Show CAUTION panel, ask [y/N]
    AUTO_EXECUTE_WITH_NOTICE = auto() # Show brief notice, then execute
    AUTO_EXECUTE_SILENT = auto()  # Execute with minimal output
    BLOCK = auto()                # Show DANGER panel, refuse execution

def get_confirmation_policy(trust_level: TrustLevel, risk: CommandRisk) -> ConfirmationAction:
    # DANGER is ALWAYS BLOCK at every trust level (G2: non-negotiable)
    if risk == CommandRisk.DANGER:
        return ConfirmationAction.BLOCK
    
    if risk == CommandRisk.SAFE:
        return ConfirmationAction.AUTO_EXECUTE
    
    # risk == CommandRisk.CAUTION:
    if trust_level == TrustLevel.CAUTIOUS:
        return ConfirmationAction.REQUIRE_CONFIRMATION
    elif trust_level == TrustLevel.BALANCED:
        return ConfirmationAction.AUTO_EXECUTE_WITH_NOTICE
    elif trust_level == TrustLevel.EXPERT:
        return ConfirmationAction.AUTO_EXECUTE_SILENT
    
    # Default conservative
    return ConfirmationAction.REQUIRE_CONFIRMATION
