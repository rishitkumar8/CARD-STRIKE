# Time Complexity:
# BFS Reachability: O(V + E) ≈ O(grid_cells)
# Greedy scoring of reachable tiles: O(r * p)
# Overall bounded by grid size and move range

from game_grid import bfs_reachable

# greedy_move.py  — Greedy Algorithm for position selection
def greedy_nearest_move(e_pos, players, grid, move_range):
    """
    Greedy nearest-move: BFS to find reachable tiles,
    then greedily pick the tile closest to ideal combat range.
    """
    # BFS once to get all reachable cells within move_range
    reachable = bfs_reachable(e_pos, move_range, grid)

    # Filter to empty tiles only
    possible_moves = [
        (c, r) for (c, r) in reachable
        if grid.tiles[c][r].card is None or (c, r) == e_pos
    ]

    if not possible_moves:
        return e_pos

    best_move = e_pos
    best_score = 9999

    IDEAL_RANGE = 3  # optimal distance for your game (ranged-heavy)

    for (c, r) in possible_moves:
        total_score = 0
        for (px, py) in players:
            d = abs(px - c) + abs(py - r)
            total_score += abs(d - IDEAL_RANGE)

        edge_penalty = 2 if c in (0, grid.cols-1) or r in (0, grid.rows-1) else 0
        score = total_score + edge_penalty

        if score < best_score:
            best_score = score
            best_move = (c, r)

    # Prevent useless movement
    if best_move == e_pos:
        return e_pos

    return best_move

