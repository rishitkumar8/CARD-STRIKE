# greedy_target_weakest.py
def greedy_weakest_target(players, grid):
    return min(players, key=lambda pos: grid.tiles[pos[0]][pos[1]].card.hp)
