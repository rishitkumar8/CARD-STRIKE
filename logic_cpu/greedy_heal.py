# greedy_heal.py
def greedy_heal_distribution(enemies, grid):
    allies = [
        (c, r) for c in range(grid.cols) for r in range(grid.rows)
        if grid.tiles[c][r].card and grid.tiles[c][r].card.owner == "enemy"
    ]
    if not allies:
        return None

    weakest_ally = min(allies, key=lambda pos: grid.tiles[pos[0]][pos[1]].card.hp)
    return weakest_ally
