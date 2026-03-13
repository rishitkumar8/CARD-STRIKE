"""
Divide & Conquer Retain Selection (Recursive Implementation)

Problem: Select the best card to RETAIN from the CPU's current hand.

Algorithm: Recursive Divide & Conquer
1. Divide: Split the list of cards in the hand into two halves.
2. Conquer: Recursively find the best "retain candidate" in each half.
3. Combine: Compare the candidates from left and right halves and return the superior one.

Time Complexity: O(N)
Space Complexity: O(log N) due to recursion stack.
"""

def evaluate_retain_value(card_data):
    """
    Heuristic scoring for retention.
    Prioritizes versatility (High HP + Good Attacks).
    """
    hp = card_data.get("hp", 50)
    score = hp * 0.5  # Base score from HP
    
    attacks = card_data.get("attacks", [])
    max_dmg = 0
    utility_bonus = 0
    
    for atk in attacks:
        dmg = atk.get("damage", 0)
        rng = atk.get("range", 3)
        cd = atk.get("cooldown", 0)
        
        # Penalize high cooldowns heavily for retention (reliability is key)
        val = dmg - (cd * 2)
        if val > max_dmg:
            max_dmg = val
            
        # Bonus for utility
        if atk.get("is_healing", False):
            utility_bonus += 15
        if atk.get("status_type", "none") != "none":
            utility_bonus += 10
            
    score += max_dmg * 2
    score += utility_bonus
    
    # Element preference (optional, can be adjusted)
    if card_data.get("element") in ["fire", "combined"]:
        score += 5
        
    return score

def select_card_recursive(card_indices, card_pool):
    # Base Case: Single card or empty
    if not card_indices:
        return None
    if len(card_indices) == 1:
        return card_indices[0]
        
    # DIVIDE
    mid = len(card_indices) // 2
    left_half = card_indices[:mid]
    right_half = card_indices[mid:]
    
    # CONQUER
    left_best = select_card_recursive(left_half, card_pool)
    right_best = select_card_recursive(right_half, card_pool)
    
    # COMBINE
    return compare_cards(left_best, right_best, card_pool)

def compare_cards(idx1, idx2, card_pool):
    if idx1 is None: return idx2
    if idx2 is None: return idx1
    
    val1 = evaluate_retain_value(card_pool[idx1])
    val2 = evaluate_retain_value(card_pool[idx2])
    
    return idx1 if val1 >= val2 else idx2

def select_best_retain(cpu_hand_indices, card_pool):
    """
    Main entry point for DC Retain logic.
    """
    return select_card_recursive(cpu_hand_indices, card_pool)
