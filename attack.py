from dataclasses import dataclass

@dataclass
class Attack:
    name: str
    dmg: int
    element: str = "null" # fire, water, leaf, air, null
    attack_range: int = 3
