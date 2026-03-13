from dataclasses import dataclass

@dataclass
class Attack:
    name: str
    dmg: int
    element: str = "null"  # fire, water, leaf, air, null, combined
    attack_range: int = 3
    animation: str = "projectile_fire"
    max_cooldown: int = 0
    current_cooldown: int = 0
    is_healing: bool = False
    heal_amount: int = 0
    is_life_drain: bool = 0
    
    # Status Effects Application
    status_type: str = "none" # "stun", "root", "burn"
    status_duration: int = 0
    status_value: int = 0

