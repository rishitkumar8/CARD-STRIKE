# greedy_move.py
def greedy_nearest_move(e_pos, players, grid):
    possible_moves = []
    for c in range(max(0, e_pos[0] - 2), min(grid.cols, e_pos[0] + 3)):
        for r in range(max(0, e_pos[1] - 2), min(grid.rows, e_pos[1] + 3)):
            if grid.tiles[c][r].card is None:
                possible_moves.append((c, r))

    if not possible_moves:
        return e_pos

    best_move = e_pos
    best_score = 9999

    IDEAL_RANGE = 3  # optimal distance for your game (ranged-heavy)

    for (c, r) in possible_moves:
        for (px, py) in players:
            d = abs(px - c) + abs(py - r)

            # Prefer tiles that place enemy at an ideal attack distance
            score = abs(d - IDEAL_RANGE)

            if score < best_score:
                best_score = score
                best_move = (c, r)

    return best_move

