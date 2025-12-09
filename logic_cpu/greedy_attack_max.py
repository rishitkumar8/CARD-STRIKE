# greedy_attack_max.py
def greedy_max_damage_attack(e_card):
    return max(e_card.attacks, key=lambda a: a.dmg)
