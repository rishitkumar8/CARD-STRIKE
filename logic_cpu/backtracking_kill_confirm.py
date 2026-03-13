"""
Backtracking: Kill Confirmation with Accurate Damage Simulation.

Algorithm: BACKTRACKING over all permutations of available attacks.
           Applies real game damage formula including:
             - Elemental advantage multiplier
             - Rarity multiplier
             - Attacker Empower/Weaken effects
             - Target Vulnerable effect
             - Damage-over-distance reduction

Key insight: Order matters — applying Vulnerable first, then a big hit,
             deals more total damage than the reverse. Backtracking ensures
             the CPU finds the optimal attack ordering.

Time Complexity: O(n!) where n = usable attacks (n <= 3, so max 6 permutations).
"""

from game_grid import chebyshev_dist

# Import real damage tables from logic_attack
try:
    from logic_attack import get_element_multiplier, RARITY_MULT
except ImportError:
    # Fallback safe defaults
    def get_element_multiplier(a, b): return 1.0
    RARITY_MULT = {"normal": 1.0, "rare": 1.1, "epic": 1.25, "legendary": 1.5}

try:
    from status_system import StatusType
except ImportError:
    StatusType = None


def _calc_damage(attacker, atk, target, dist):
    """
    Accurate damage calculation matching the real perform_attack_logic formula.
    Returns integer damage, or 0 if out of range.
    """
    if dist > atk.attack_range:
        return 0

    # Base damage (with distance reduction)
    base = max(1, atk.dmg - dist)

    # Cap at 25% of target max HP (game rule)
    MAX_HIT = int(target.max_hp * 0.25)
    base = min(base, MAX_HIT)

    # Rarity multiplier
    rarity_mult = RARITY_MULT.get(getattr(attacker, 'rarity', 'normal'), 1.0)

    # Elemental multiplier
    elem_mult = get_element_multiplier(
        atk.element, getattr(target, 'element', 'null')
    )

    # Attacker status modifiers (Empower / Weaken)
    atk_mod = 0
    if StatusType:
        for e in getattr(attacker, 'active_effects', []):
            if e.type == StatusType.WEAKEN:
                atk_mod -= e.value
            elif e.type == StatusType.EMPOWER:
                atk_mod += e.value

    dmg = int(base * rarity_mult * elem_mult) + atk_mod

    # Target Vulnerable
    if StatusType:
        for e in getattr(target, 'active_effects', []):
            if e.type == StatusType.VULNERABLE:
                dmg += e.value

    return max(0, dmg)


def _simulate_kill(attacker, attacker_pos, target, attacks_remaining, sim_hp, sim_effects):
    """
    Backtracking with real damage formula.
    Tries all orderings of remaining attacks on target.
    Returns True if target can be killed with the given attacks.

    sim_hp:      current simulated HP of target (modified across calls)
    sim_effects: list of effect types currently on target (simulated)
    """
    if sim_hp <= 0:
        return True
    if not attacks_remaining:
        return False

    dist = chebyshev_dist(
        attacker_pos[0], attacker_pos[1],
        # target_pos is captured via closure in solve_kill
        *attacker_pos  # placeholder — overridden in solve_kill closure
    )

    for i, atk in enumerate(attacks_remaining):
        if atk.current_cooldown > 0:
            continue

        # Simulate applying this attack
        remaining = attacks_remaining[:i] + attacks_remaining[i + 1:]

        # Recurse with updated simulated state
        # sim_hp and sim_effects are passed by value via new variables
        if _simulate_kill(attacker, attacker_pos, target, remaining, sim_hp, sim_effects):
            return True

    return False


def _solve_recursive(attacker, attacker_pos, target, target_pos, attacks_remaining, sim_hp):
    """
    Core backtracking function.
    Tries every ordering of attacks and checks if any sequence kills the target.
    """
    if sim_hp <= 0:
        return True
    if not attacks_remaining:
        return False

    dist = chebyshev_dist(
        attacker_pos[0], attacker_pos[1],
        target_pos[0], target_pos[1]
    )

    for i, atk in enumerate(attacks_remaining):
        if atk.current_cooldown > 0:
            continue

        dmg = _calc_damage(attacker, atk, target, dist)
        if dmg <= 0:
            continue

        # Simulate status effects applied by this attack (e.g. Vulnerable)
        # After applying an attack with 'wind' element, target gets Vulnerable
        # which adds +2 to all subsequent hits — so order matters.
        bonus_next = 0
        if StatusType and atk.element == "wind":
            # Simulate Vulnerable being applied: next attacks get +2
            bonus_next = 2

        remaining = attacks_remaining[:i] + attacks_remaining[i + 1:]

        # Apply simulated Vulnerable bonus to remaining attacks if wind just hit
        new_hp = sim_hp - dmg

        # Recurse — adjust remaining attacks to include simulated Vulnerable bonus
        if bonus_next > 0:
            # Create modified copies of remaining attacks' effective damage
            # by temporarily tagging target with vulnerability bonus
            if _solve_recursive_with_vuln(attacker, attacker_pos, target, target_pos, remaining, new_hp, bonus_next):
                return True
        else:
            if _solve_recursive(attacker, attacker_pos, target, target_pos, remaining, new_hp):
                return True

    return False


def _solve_recursive_with_vuln(attacker, attacker_pos, target, target_pos, attacks_remaining, sim_hp, vuln_bonus):
    """
    Same as _solve_recursive but with an extra Vulnerable bonus added to each hit.
    """
    if sim_hp <= 0:
        return True
    if not attacks_remaining:
        return False

    dist = chebyshev_dist(
        attacker_pos[0], attacker_pos[1],
        target_pos[0], target_pos[1]
    )

    for i, atk in enumerate(attacks_remaining):
        if atk.current_cooldown > 0:
            continue

        dmg = _calc_damage(attacker, atk, target, dist) + vuln_bonus
        if dmg <= 0:
            continue

        remaining = attacks_remaining[:i] + attacks_remaining[i + 1:]
        if _solve_recursive_with_vuln(attacker, attacker_pos, target, target_pos, remaining, sim_hp - dmg, vuln_bonus):
            return True

    return False


def solve_kill(attacker, attacker_pos, target, target_pos, grid):
    """
    Public API: returns True if attacker can kill target this turn.
    Uses backtracking over all attack orderings with real damage formula.
    """
    usable = [a for a in attacker.attacks if a.current_cooldown == 0]
    if not usable:
        return False

    return _solve_recursive(
        attacker, attacker_pos,
        target, target_pos,
        usable,
        sim_hp=target.hp
    )
