from grid import bfs_reachable

# greedy_move.py
def greedy_nearest_move(e_pos, players, grid, move_range):
    possible_moves = []

    for c in range(
        max(0, e_pos[0] - move_range),
        min(grid.cols, e_pos[0] + move_range + 1)
    ):
        for r in range(
            max(0, e_pos[1] - move_range),
            min(grid.rows, e_pos[1] + move_range + 1)
        ):
            # Manhattan distance constraint
            reachable = bfs_reachable(e_pos, move_range, grid)
            
            for (c, r) in reachable:
                if grid.tiles[c][r].card is None:
                    possible_moves.append((c, r))



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

