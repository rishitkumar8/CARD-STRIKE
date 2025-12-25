from dataclasses import dataclass
from typing import Optional
from attack import Attack

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

@dataclass
class Tile:
    col: int
    row: int
    card: Optional[Card] = None
