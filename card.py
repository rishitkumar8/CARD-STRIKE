from dataclasses import dataclass, field
from typing import Optional, List
from attack import Attack
from status_system import StatusEffect

@dataclass
class Card:
    owner: str
    name: str
    hp: int
    max_hp: int
    attacks: list
    move_range: int = 2
    element: str = "null" # Base element of the card
    index: int = 0
    flash_timer: int = 0
    shield: int = 0
    display_hp: int = None   # animated hp
    rarity: str = "normal"   # normal / rare / epic / legendary
    heal_flash_timer: int = 0
    healed_once: bool = False   # 🔥 HEAL ONLY ONCE
    
    # Status Effects
    stun_duration: int = 0      # Cannot Attack
    root_duration: int = 0      # Cannot Move
    burn_duration: int = 0      # Takes damage at start of turn
    burn_damage: int = 0
    
    active_effects: List[StatusEffect] = field(default_factory=list)

    def __hash__(self):
        return id(self)
    
    def __eq__(self, other):
        return self is other

@dataclass
class Tile:
    col: int
    row: int
    card: Optional[Card] = None
