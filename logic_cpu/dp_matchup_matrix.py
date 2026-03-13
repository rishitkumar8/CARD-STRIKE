def optimize_matchups(attackers, targets, score_fn):
    """
    Find the optimal assignment of attackers to targets to maximize total score.
    Uses DP with Bitmasking (assuming N attackers <= ~20, N targets can act as slots).
    
    attackers: List of attacker objects
    targets: List of target objects
    score_fn: Function(attacker, target) -> float score
    """
    n = len(attackers)
    m = len(targets)   
    memo = {}
    def solve(attacker_idx, target_mask):
        if attacker_idx == n:
            return (0, [])
        state = (attacker_idx, target_mask)
        if state in memo: return memo[state]
        # Option 1: Attacker doesn't attack anyone (skip)
        # Note: If we skip, we just move to next attacker
        best_score, best_assign = solve(attacker_idx + 1, target_mask)
        # Option 2: Attack one of the available targets
        for t_idx in range(m):
            if not (target_mask & (1 << t_idx)):
                # Target available
                action_score = score_fn(attackers[attacker_idx], targets[t_idx])
                # Recurse
                rem_score, rem_assign = solve(attacker_idx + 1, target_mask | (1 << t_idx))
                total_score = action_score + rem_score
                if total_score > best_score:
                    best_score = total_score
                    # Current assignment + recursive assignments
                    best_assign = [(attackers[attacker_idx], targets[t_idx])] + rem_assign
        memo[state] = (best_score, best_assign)
        return (best_score, best_assign)

    return solve(0, 0)
