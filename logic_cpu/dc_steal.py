# logic_cpu/dc_steal.py
"""
Divide & Conquer Steal Target Selection (Recursive DAC-MAX)

Algorithm:
- Divide candidates by element (semantic partition)
- Apply recursive maximum selection within each partition
- Reduce partition winners using context-aware utility comparison

Overall Time Complexity: O(n)
Space Complexity: O(n)
"""

# -------------------------------------------------
# Evaluation Function (raw card strength)
# -------------------------------------------------
def evaluate_card(card_data):
    hp = card_data.get("hp", 50)
    score = hp

    for atk in card_data.get("attacks", []):
        dmg = atk.get("damage", 0)
        rng = atk.get("range", 3)
        cd = atk.get("cooldown", 0)
        heal = atk.get("heal_amount", 0)

        if atk.get("is_healing", False):
            score += heal * 1.5
        elif atk.get("is_life_drain", False):
            score += (dmg + heal) * 1.2
        else:
            val = dmg + (rng * 2) - (cd * 3)
            score += max(0, val)

    return score


# -------------------------------------------------
# CLASSIC DAC-MAX (Recursive Maximum Selection)
# -------------------------------------------------
def dac_max(indices, card_pool):
    """
    Recursive Divide & Conquer MAX selection
    """
    if len(indices) == 1:
        return indices[0]

    mid = len(indices) // 2
    left = indices[:mid]
    right = indices[mid:]

    left_best = dac_max(left, card_pool)
    right_best = dac_max(right, card_pool)

    if evaluate_card(card_pool[left_best]) >= evaluate_card(card_pool[right_best]):
        return left_best
    else:
        return right_best


# -------------------------------------------------
# PARTITION STEP (Semantic Divide)
# -------------------------------------------------
def divide_by_element(card_indices, card_pool):
    groups = {}
    for idx in card_indices:
        elem = card_pool[idx]["element"]
        groups.setdefault(elem, []).append(idx)
    return groups


# -------------------------------------------------
# CONTEXT-AWARE UTILITY (used only in COMBINE)
# -------------------------------------------------
def compute_utility(card_idx, card_pool, cpu_cards):
    card = card_pool[card_idx]

    # Base strength
    utility = evaluate_card(card)

    # Element priority bonus
    elem = card.get("element")

    # Redundancy penalty (cpu_cards are INDICES)
    same_elem_count = sum(
        1 for idx in cpu_cards
        if card_pool[idx].get("element") == elem
    )

    utility -= same_elem_count * 6

    return utility



# -------------------------------------------------
# TOP-LEVEL SELECTION (DAC + CONTEXT-AWARE COMBINE)
# -------------------------------------------------
def select_steal_target(card_indices, card_pool, cpu_cards):
    """
    Full Divide & Conquer Steal Target Selection
    """

    # DIVIDE
    groups = divide_by_element(card_indices, card_pool)

    # CONQUER
    group_winners = []
    for indices in groups.values():
        group_winners.append(dac_max(indices, card_pool))

    # COMBINE (context-aware reduction)
    best_card = None
    best_score = float("-inf")

    for idx in group_winners:
        score = compute_utility(idx, card_pool, cpu_cards)
        if score > best_score:
            best_score = score
            best_card = idx

    return best_card