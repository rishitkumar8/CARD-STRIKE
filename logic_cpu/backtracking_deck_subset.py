# -------------------------------------------------
# Synergy Score 
# -------------------------------------------------
def _synergy_score(combo_data):
    total_dmg = 0
    elements = set()
    has_healer = False
    has_ranged = False

    for card in combo_data:
        for atk in card.get("attacks", []):
            total_dmg += atk.get("damage", 0)
            elements.add(atk.get("element", "null"))

            if atk.get("is_healing", False) or atk.get("is_life_drain", False):
                has_healer = True

            if atk.get("range", 1) >= 4:
                has_ranged = True

    score = total_dmg
    score += len(elements) * 8
    if has_healer:
        score += 20
    if has_ranged:
        score += 10

    return score


# -------------------------------------------------
# BACKTRACKING TEAM SEARCH
# -------------------------------------------------
def find_optimal_team(cpu_deck, cpu_hand, player_hand, card_pool):
    """
    True Backtracking version (no itertools).
    Generates all 3-card combinations using recursion.
    """

    available = list(set(cpu_deck) | set(cpu_hand) | set(player_hand))
    n = len(available)
    team_size = 3

    best_score = -1
    best_team = None

    def backtrack(start, current_team):
        nonlocal best_score, best_team
        
        # If team complete → evaluate
        if len(current_team) == team_size:
            combo_data = [card_pool[i] for i in current_team]
            score = _synergy_score(combo_data)
            if not set(cpu_deck).issubset(current_team):
                return
            if score > best_score:
                best_score = score
                best_team = list(current_team)
            return

        # PRUNING
        remaining_needed = team_size - len(current_team)
        if n - start < remaining_needed:
            return

        # ✅ Try each remaining card
        for i in range(start, n):
            current_team.append(available[i])
            backtrack(i + 1, current_team)
            current_team.pop()  # undo choice

    backtrack(0, [])

    return best_score, best_team


# -------------------------------------------------
# ACTION DECISION 
# -------------------------------------------------
def find_best_phase_action(cpu_deck, cpu_hand, player_hand, card_pool):
    score, team = find_optimal_team(cpu_deck, cpu_hand, player_hand, card_pool)

    if not team:
        return None

    deck_set = set(cpu_deck)
    missing = [idx for idx in team if idx not in deck_set]

    if not missing:
        return None

    target_idx = missing[0]

    if target_idx in player_hand:
        return ("STEAL", target_idx, score)
    else:
        return ("RETAIN", target_idx, score)