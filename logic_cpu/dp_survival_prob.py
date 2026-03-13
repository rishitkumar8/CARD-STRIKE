def survive_probability(current_hp, max_hp, turns, enemy_dmg_range):
    """
    Calculate probability of surviving for N turns against an enemy dealing random damage in range [min, max].
    
    current_hp: Remaining HP
    turns: Number of turns to simulate
    enemy_dmg_range: (min_dmg, max_dmg) tuple
    """
    if current_hp <= 0: return 0.0
    if turns == 0: return 1.0
    
    # Memoization Table
    # Max damage possible per turn * turns could be large, but HP is bounded by max_hp usually ~100
    memo = {}
    
    min_d, max_d = enemy_dmg_range
    dmg_outcomes = max_d - min_d + 1
    prob_each = 1.0 / dmg_outcomes
    
    def solve(hp, t):
        if hp <= 0: return 0.0
        if t == 0: return 1.0
        
        state = (hp, t)
        if state in memo: return memo[state]
        
        total_prob = 0.0
        for d in range(min_d, max_d + 1):
            total_prob += solve(hp - d, t - 1) * prob_each
            
        memo[state] = total_prob
        return total_prob

    return solve(current_hp, turns)
