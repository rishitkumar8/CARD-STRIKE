import random
from config import GRID_COLS, GRID_ROWS
from grid import cell_center
from animations import anim_mgr
from logic_attack import perform_attack_logic


def cpu_turn(grid):
    if anim_mgr.blocking:
        return

    enemies = []
    players = []

    # Collect units
    for c in range(grid.cols):
        for r in range(grid.rows):
            card = grid.tiles[c][r].card
            if not card:
                continue
            if card.owner == "enemy":
                enemies.append((c, r))
            else:
                players.append((c, r))

    if not players:
        return

    # ONE enemy acts per turn
    for e_pos in enemies:
        e_card = grid.tiles[e_pos[0]][e_pos[1]].card

        # Random move
        possible_moves = []
        for c in range(max(0, e_pos[0] - 2), min(grid.cols, e_pos[0] + 3)):
            for r in range(max(0, e_pos[1] - 2), min(grid.rows, e_pos[1] + 3)):
                if grid.tiles[c][r].card is None:
                    possible_moves.append((c, r))

        new_pos = e_pos
        if possible_moves and random.random() > 0.3:
            dest = random.choice(possible_moves)
            grid.tiles[dest[0]][dest[1]].card = e_card
            grid.tiles[e_pos[0]][e_pos[1]].card = None
            new_pos = dest

        # Attack random player
        target_pos = random.choice(players)
        atk = random.choice(e_card.attacks)

        start = cell_center(*new_pos)
        end = cell_center(*target_pos)

        anim_mgr.trigger_attack_anim(
            start, end, atk.element,
            lambda: perform_attack_logic(new_pos[0], new_pos[1], target_pos[0], target_pos[1], atk, grid)
        )

        break
