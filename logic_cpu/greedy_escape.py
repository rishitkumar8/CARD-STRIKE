# greedy_escape.py
def greedy_escape_move(e_pos, players, grid):
    possible_moves = []
    for c in range(max(0, e_pos[0] - 2), min(grid.cols, e_pos[0] + 3)):
        for r in range(max(0, e_pos[1] - 2), min(grid.rows, e_pos[1] + 3)):
            if grid.tiles[c][r].card is None:
                possible_moves.append((c, r))

    if not possible_moves:
        return e_pos

    best_tile = e_pos
    best_threat = 9999
    for (c, r) in possible_moves:
        threat = 0
        for (px, py) in players:
            dist = abs(px - c) + abs(py - r)
            if dist == 0:
                dist = 1
            attacker = grid.tiles[px][py].card
            for (px, py) in players:
                attacker = grid.tiles[px][py].card
                dist = abs(px - c) + abs(py - r)

                if dist <= attacker.attacks[0].attack_range:
                    threat += attacker.attacks[0].dmg * 2
                else:
                    threat += attacker.attacks[0].dmg / max(dist, 1)

        if threat < best_threat:
            best_threat = threat
            best_tile = (c, r)
    return best_tile
