# greedy_fire.py
import random

def greedy_fire_spread(e_pos, players, grid):
    directions = [(1, 0), (-1, 0)]
    best_dir = (1, 0)
    max_hits = -1

    for dx, dy in directions:
        hits = 0
        for i in range(1, 6):
            nc = e_pos[0] + dx * i
            nr = e_pos[1] + dy * i
            if grid.in_bounds(nc, nr) and grid.tiles[nc][nr].card and grid.tiles[nc][nr].card.owner == "player":
                hits += 1
        if hits > max_hits:
            max_hits = hits
            best_dir = (dx, dy)

    # target in direction
    for i in range(1, 6):
        nc = e_pos[0] + best_dir[0] * i
        nr = e_pos[1] + best_dir[1] * i
        if grid.in_bounds(nc, nr) and grid.tiles[nc][nr].card and grid.tiles[nc][nr].card.owner == "player":
            return (nc, nr)

    return random.choice(players)
