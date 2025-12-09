# greedy_element.py
def element_score(atk_el, target_el):
    if atk_el == "fire" and target_el == "leaf": return 2
    if atk_el == "water" and target_el == "fire": return 2
    if atk_el == "leaf" and target_el == "water": return 2
    if atk_el == "null": return 3
    return 1

def greedy_element_attack(e_card, target_pos, grid):
    target_card = grid.tiles[target_pos[0]][target_pos[1]].card
    best_score = -1
    best_attack = None
    for atk in e_card.attacks:
        score = atk.dmg * element_score(atk.element, target_card.element)
        if score > best_score:
            best_score = score
            best_attack = atk
    return best_attack
