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
    best_dist = 9999
    for (c, r) in possible_moves:
        for (px, py) in players:
            d = abs(px - c) + abs(py - r)
            if d < best_dist:
                best_dist = d
                best_move = (c, r)
    return best_move
