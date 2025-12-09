# cpu_controller.py

import random
from grid import cell_center
from animations import anim_mgr
from logic_attack import perform_attack_logic

# FIXED IMPORTS
from logic_cpu.greedy_move import greedy_nearest_move
from logic_cpu.greedy_escape import greedy_escape_move
from logic_cpu.greedy_attack_max import greedy_max_damage_attack
from logic_cpu.greedy_target_weakest import greedy_weakest_target
from logic_cpu.greedy_element import greedy_element_attack
from logic_cpu.greedy_fire import greedy_fire_spread
from logic_cpu.greedy_heal import greedy_heal_distribution


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

        # 🔵 MOVEMENT GREEDY
        if e_card.element in ["water", "leaf"]:
            new_pos = greedy_escape_move(e_pos, players, grid)
        else:
            new_pos = greedy_nearest_move(e_pos, players, grid)

        if new_pos != e_pos:
            grid.tiles[new_pos[0]][new_pos[1]].card = e_card
            grid.tiles[e_pos[0]][e_pos[1]].card = None

        # 🔥 ATTACK GREEDY
        if e_card.element == "fire":
            target_pos = greedy_fire_spread(new_pos, players, grid)
            atk = next(atk for atk in e_card.attacks if atk.name == "Burning Trail")

        elif e_card.element == "leaf":
            # If leaf has healing attack
            heal_attack = next((atk for atk in e_card.attacks if atk.name == "Nature's Embrace"), None)
            if heal_attack:
                target_pos = greedy_heal_distribution(enemies, grid)
                if target_pos:
                    atk = heal_attack
                else:
                    target_pos = greedy_weakest_target(players, grid)
                    atk = greedy_element_attack(e_card, target_pos, grid)
            else:
                 # Leaf enemy has no healing ability → fallback to normal targeting
                target_pos = greedy_weakest_target(players, grid)
                atk = greedy_element_attack(e_card, target_pos, grid)

        else:
            target_pos = greedy_weakest_target(players, grid)
            atk = greedy_element_attack(e_card, target_pos, grid)

        # Trigger attack animation
        start = cell_center(*new_pos)
        end = cell_center(*target_pos)

        anim_mgr.trigger_attack_anim(
            start, end, atk.element,
            lambda: perform_attack_logic(new_pos[0], new_pos[1], target_pos[0], target_pos[1], atk, grid)
        )

        break
