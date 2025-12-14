def greedy_best_target(e_pos, players, grid):
    """
    Greedy target selection based on:
    - Low HP (kill potential)
    - Distance (prefer closer)
    - Threat (high damage players)
    """

    best_score = -9999
    best_target = None

    for (px, py) in players:
        card = grid.tiles[px][py].card
        if not card:
            continue

        # 1️⃣ Prefer low HP targets
        hp_factor = 1 - (card.hp / card.max_hp)  # 0..1

        # 2️⃣ Prefer closer targets
        dist = abs(e_pos[0] - px) + abs(e_pos[1] - py)
        dist_factor = 1 / max(dist, 1)

        # 3️⃣ Prefer high-damage threats
        threat = max(a.dmg for a in card.attacks)

        score = (
            hp_factor * 10 +
            dist_factor * 5 +
            threat * 0.3
        )

        if score > best_score:
            best_score = score
            best_target = (px, py)

    return best_target
