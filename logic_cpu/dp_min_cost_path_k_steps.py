def get_min_costs_table(start_node, k_max, grid, cost_fn):
    """
    Returns the DP table: dp[r][c] = min cost to reach (c,r) in <= k_max steps.
    Since we care about "reached within k steps", we should track min over 1..k.
    """
    rows, cols = grid.rows, grid.cols
    infinity = float('inf')
    
    # dp[k][r][c]
    dp = [[[infinity for _ in range(cols)] for _ in range(rows)] for _ in range(k_max + 1)]
    
    start_c, start_r = start_node
    dp[0][start_r][start_c] = 0
    
    from game_grid import get_neighbors
    
    for k in range(1, k_max + 1):
        for r in range(rows):
            for c in range(cols):
                # Check neighbors who could have moved here
                predecessors = get_neighbors(c, r, grid, diagonal=False)
                
                best_prev = infinity
                for prn in predecessors:
                    pc, pr = prn
                    if dp[k-1][pr][pc] != infinity:
                         best_prev = min(best_prev, dp[k-1][pr][pc])
                
                if best_prev != infinity:
                     current_tile_cost = cost_fn(c, r)
                     dp[k][r][c] = best_prev + current_tile_cost
                     
    # Collapse to 2D: min cost to reach (r,c) in any step k <= k_max
    # Or just use the k_max layer if we assume we always move k steps?
    # Actually units can move < k steps (wait).
    # But this DP assumes movement every step.
    # For now, return the whole table or the min over all k for each cell
    
    min_dp = [[infinity for _ in range(cols)] for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            val = infinity
            for k in range(1, k_max + 1):
                val = min(val, dp[k][r][c])
            min_dp[r][c] = val
            
    # Include start pos (cost 0)
    min_dp[start_r][start_c] = 0
            
    return min_dp
    
def min_cost_path_k_steps(start_node, target_node, k_max, grid, cost_fn):
    table = get_min_costs_table(start_node, k_max, grid, cost_fn)
    tc, tr = target_node
    val = table[tr][tc]
    return val if val != float('inf') else -1
