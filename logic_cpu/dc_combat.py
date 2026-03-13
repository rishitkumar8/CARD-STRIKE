"""
D&C Combat Logic: Target, Position, Attack Selection

    Recursive Implementation of Divide & Conquer Strategies.
    
    Time Complexity: O(N) for all functions (where N is candidates/tiles/attacks).
    Although recursive, it visits each element once in the base cases or merge steps.
    """

from logic_cpu.greedy_target_weakest import greedy_best_target
from logic_cpu.greedy_move import greedy_nearest_move
from game_grid import bfs_reachable, chebyshev_dist

# ===========================================================================================
# 1. RECURSIVE TARGET SELECTION
# ===========================================================================================
def select_attack_target(attacker_card, attacker_pos, players, grid, prioritize_range=False):
    """
    Select best target using Recursive Divide & Conquer.
    Divide: Split list of candidates in half.
    Conquer: Recursively find best target in each half.
    Combine: Compare two finalists using scoring logic (Low HP, Distance, Threat).
    """
    candidates_pool = players

    # --- Pre-filter: Range Prioritization ---
    if prioritize_range:
        max_range = 0
        has_available_attack = False
        for atk in attacker_card.attacks:
            if atk.current_cooldown == 0:
                has_available_attack = True
                if atk.attack_range > max_range:
                    max_range = atk.attack_range
        
        if has_available_attack:
            in_range = []
            ax, ay = attacker_pos
            for px, py in players:
                dist = chebyshev_dist(ax, ay, px, py)
                if dist <= max_range:
                    in_range.append((px, py))
            
            if in_range:
                candidates_pool = in_range

    if not candidates_pool:
        return None

    # --- Recursive Helper ---
    def find_best_recursive(subset):
        # Base Case
        if len(subset) == 0:
            return None
        if len(subset) == 1:
            return subset[0]
        
        # Divide
        mid = len(subset) // 2
        left_best = find_best_recursive(subset[:mid])
        right_best = find_best_recursive(subset[mid:])
        
        # Combine
        return compare_targets(left_best, right_best)

    # --- Comparison Logic (Inline Greedy Scoring) ---
    def compare_targets(t1, t2):
        if t1 is None: return t2
        if t2 is None: return t1
        
        s1 = get_target_score(t1)
        s2 = get_target_score(t2)
        return t1 if s1 >= s2 else t2

    def get_target_score(pos):
        px, py = pos
        card = grid.tiles[px][py].card
        if not card: return -9999
        
        # Scoring based on greedy_target_weakest logic
        hp_factor = 1 - (card.hp / card.max_hp)  # 0..1 (higher is weaker)
        dist = abs(attacker_pos[0] - px) + abs(attacker_pos[1] - py)
        dist_factor = 1 / max(dist, 1)
        threat = max((a.dmg for a in card.attacks), default=0)
        
        return (hp_factor * 10) + (dist_factor * 5) + (threat * 0.3)

    # Start Recursion
    return find_best_recursive(list(candidates_pool))


# ==================================================================================
# 2. RECURSIVE POSITION SELECTION
# ==================================================================================
def select_position(attacker_card, attacker_pos, target_pos, grid):
    """
    Select best move position using DP Minimum Cost Path + Recursive Divide & Conquer.
    
    1. DP: Calculate cost to reach all tiles (avoiding hazards).
    2. Filter: Only consider valid empty tiles reachable in move_range.
    3. Score: Combine (Distance to Target) and (DP Safety Cost).
    4. D&C: Select best tile.
    """
    if not target_pos:
        return attacker_pos
        
    # Import locally to avoid circular deps if any, or just for clarity
    from logic_cpu.dp_min_cost_path_k_steps import get_min_costs_table
    from effects import flame_tiles

    # -----------------------------------------------------------------
    # DP MOVEMENT SCORING with HAZARD AVOIDANCE
    # -----------------------------------------------------------------
    def movement_cost(c, r):
        # 1. Check Blockage (Units) - Handled by BFS usually, but DP needs to know
        # Cost function should return infinity for blocked tiles
        if (c,r) != attacker_pos and grid.tiles[c][r].card is not None:
            return float('inf')
        
        cost = 1
        # 2. Check Hazards (Fire)
        # flame_tiles structure: [c, r, time, owner, tick]
        for ft in flame_tiles:
            if ft[0] == c and ft[1] == r:
                cost += 10 # High penalty for fire
                break
                
        return cost

    # Calculate DP table for costs
    # K=move_range
    dp_costs = get_min_costs_table(attacker_pos, attacker_card.move_range, grid, movement_cost)

    # Get reachable tiles using BFS to handle connectivity (walls/units) correctly
    all_reachable = bfs_reachable(attacker_pos, attacker_card.move_range, grid, diagonal=False)
    
    # Filter to EMPTY tiles only (or current)
    valid_candidates = []
    scores = {}

    for (rx, ry) in all_reachable:
        if (rx, ry) == attacker_pos:
            valid_candidates.append((rx, ry))
        elif grid.tiles[rx][ry].card is None:
            valid_candidates.append((rx, ry))
            
    if not valid_candidates:
        return attacker_pos

    # -----------------------------------------------------------------
    # IDEAL RANGE — CPU should stop WHERE it can shoot, not WHERE the enemy is
    # -----------------------------------------------------------------
    # Use ALL attacks regardless of cooldown:
    # CPU positions for next turn even when currently on cooldown.
    # Skipping on-cooldown attacks caused ideal_range to default to 1 (melee)
    # making ranged units walk into danger for no reason.
    ideal_range = 1  # fallback melee
    for atk in attacker_card.attacks:
        is_heal = "heal" in atk.name.lower() or getattr(atk, 'is_healing', False)
        if not is_heal and atk.attack_range > ideal_range:
            ideal_range = atk.attack_range

    # Find the enemy's best return-fire range (so we can penalise tiles inside it)
    tx, ty = target_pos
    target_card = grid.tiles[tx][ty].card if grid.tiles[tx][ty].card else None
    enemy_threat_range = 1  # default melee
    if target_card:
        for atk in target_card.attacks:
            is_heal = "heal" in atk.name.lower() or getattr(atk, 'is_healing', False)
            if not is_heal and atk.attack_range > enemy_threat_range:
                enemy_threat_range = atk.attack_range

    # -----------------------------------------------------------------
    # SCORING — Lower is better
    # Goal: Position at exactly ideal_range from target.
    # Penalty: Being inside enemy threat range.
    # -----------------------------------------------------------------
    for tile in valid_candidates:
        cx, cy = tile
        path_cost = dp_costs[cy][cx]  # dp[r][c]

        if path_cost == float('inf'):
            path_cost = 999

        # Use CHEBYSHEV distance — matches how attack ranges are checked in the game
        dist = chebyshev_dist(cx, cy, tx, ty)

        # --- Range deviation penalty ---
        # Being too close is worse than being too far (we prefer to kite)
        if dist < ideal_range:
            # Inside ideal range — penalty scales with how far inside we are
            range_penalty = (ideal_range - dist) * 15
        else:
            # Outside or exactly at ideal range — small penalty for distance beyond
            range_penalty = (dist - ideal_range) * 5

        # --- Danger penalty — being inside enemy return-fire range ---
        if dist <= enemy_threat_range:
            danger_penalty = (enemy_threat_range - dist + 1) * 12
        else:
            danger_penalty = 0

        # --- Fire hazard from DP path cost ---
        hazard_penalty = path_cost * 2

        scores[tile] = range_penalty + danger_penalty + hazard_penalty
        # print(f"  [Pos] {tile}: dist={dist} ideal={ideal_range} threat={enemy_threat_range}"
        #       f" rpen={range_penalty} dpen={danger_penalty} -> S={scores[tile]}")


    # -----------------------------------------------------------------
    # RECURSIVE D&C SELECTION
    # -----------------------------------------------------------------
    def find_best_pos_recursive(tiles):
        if len(tiles) == 0: return None
        if len(tiles) == 1: return tiles[0]
        
        mid = len(tiles) // 2
        left = find_best_pos_recursive(tiles[:mid])
        right = find_best_pos_recursive(tiles[mid:])
        
        return get_better(left, right)

    def get_better(p1, p2):
        if p1 is None: return p2
        if p2 is None: return p1
        
        s1 = scores.get(p1, 9999)
        s2 = scores.get(p2, 9999)
        
        return p1 if s1 <= s2 else p2

    # Always return the best tile — CPU must always move toward optimal position.
    # Removed the "stay put" fallback: it caused CPU to freeze when all reachable
    # tiles had high scores (e.g. all close to an enemy threat range), even when
    # staying also had a terrible score. The D&C already picked the BEST tile;
    # we trust it and always move there.
    best = find_best_pos_recursive(list(valid_candidates))
    return best if best else attacker_pos


# ==================================================================================
# 3. RECURSIVE ATTACK SELECTION (Element-Aware)
# ==================================================================================
def select_attack_placement(attacker_card, attacker_pos, target_pos, grid):
    """
    Select best attack using DP Knapsack Optimization.
    
    Problem: Select subset of attacks with max total damage subject to Cooldown constraint.
    Constraint: Cooldown <= 99 (assume infinite energy/time for now, effectively "Best subset").
    Since game allows only 1 attack, we force capacity=1 in logic or just use Knapsack
    to find the single best one (implicitly, if all have weight 1? No cooldowns vary).
    
    Actually, to match Game Rules (One Attack Per Turn):
    We treat "Attack Slot" as capacity 1?
    Knapsack selects BEST attack based on Value (Damage).
    """
    if not target_pos:
        return None

    ax, ay = attacker_pos
    tx, ty = target_pos
    dist_to_target = chebyshev_dist(ax, ay, tx, ty)

    target_card = grid.tiles[tx][ty].card
    target_element = getattr(target_card, 'element', 'null') if target_card else 'null'

    # valid_attacks
    valid_attacks = []
    
    from logic_attack import get_element_multiplier
    
    class AttackEvaluator:
        def __init__(self, atk):
            self.atk = atk
            self.cost = 1  # Weight for knapsack: 1 attack slot per attack
            self.max_cooldown = 1 # Force weight 1 (Pick 1 attack)
            # Value = Effective Damage
            elem_mult = get_element_multiplier(atk.element, target_element)
            self.dmg = int(atk.dmg * elem_mult)
            self.real_cooldown = atk.current_cooldown

    for atk in attacker_card.attacks:
        is_heal = ("heal" in atk.name.lower()) or ("heal" in getattr(atk, "animation", "").lower())
        if is_heal: continue
        if atk.current_cooldown > 0: continue
        if dist_to_target > atk.attack_range: continue
        
        valid_attacks.append(AttackEvaluator(atk))

    if not valid_attacks:
        return None
        
    # Import DP Knapsack
    from logic_cpu.dp_knapsack_damage import max_damage_knapsack
    
    # Capacity 1 (Select at most 1 attack)
    best_score, selected = max_damage_knapsack(valid_attacks, 1)
    
    if selected:
        chosen = selected[0].atk
        em = get_element_multiplier(chosen.element, target_element)
        print(f"[Knapsack] Chose {chosen.name} Score={best_score} (Mult: {em}x)")
        return chosen
        
    return None
