from enum import Enum, auto
from dataclasses import dataclass

class StatusType(Enum):
    FLAME = auto()      # DoT: 2 dmg/turn
    REGEN = auto()      # HoT: 2 hp/turn
    FROST = auto()      # Debuff: Move range -1
    WEAKEN = auto()     # Debuff: Damage -2
    VULNERABLE = auto() # Debuff: Incoming Damage +2
    THORNS = auto()     # Buff: Return 1 dmg on hit
    EMPOWER = auto()    # Buff: Damage +2
    STUN = auto()       # Debuff: Skip turn
    ROOT = auto()       # Debuff: Cannot move

@dataclass
class StatusEffect:
    name: str
    type: StatusType
    duration: int       # Turns remaining
    value: int = 0      # Magnitude (e.g. 2 damage)
    source_str: str = "" # Description for UI

    def decrement(self):
        self.duration -= 1
        return self.duration <= 0

# Helper to create standard effects
def create_flame_effect():
    return StatusEffect("Flame", StatusType.FLAME, duration=2, value=2, source_str="2 DMG/Turn")

def create_regen_effect():
    return StatusEffect("Regen", StatusType.REGEN, duration=3, value=2, source_str="+2 HP/Turn")

def create_frost_effect():
    return StatusEffect("Frost", StatusType.FROST, duration=2, value=1, source_str="-1 Move")

def create_shock_effect():
    return StatusEffect("Shock", StatusType.STUN, duration=1, value=0, source_str="Stunned")

def create_weaken_effect():
    return StatusEffect("Weaken", StatusType.WEAKEN, duration=2, value=2, source_str="-2 ATK")

def create_thorns_effect():
    return StatusEffect("Thorns", StatusType.THORNS, duration=3, value=1, source_str="Reflect 1")

def create_vulnerable_effect():
    return StatusEffect("Vulnerable", StatusType.VULNERABLE, duration=2, value=2, source_str="+2 Incoming DMG")

def create_empower_effect():
    return StatusEffect("Empower", StatusType.EMPOWER, duration=2, value=2, source_str="+2 ATK")

def create_root_effect():
    return StatusEffect("Root", StatusType.ROOT, duration=1, value=0, source_str="Cannot Move")
