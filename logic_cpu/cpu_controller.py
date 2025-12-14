 # cpu_controller.py

import random
from grid import cell_center
from animations import anim_mgr
from logic_attack import perform_attack_logic

# FIXED IMPORTS
from logic_cpu.greedy_move import greedy_nearest_move
from logic_cpu.greedy_escape import greedy_escape_move
from logic_cpu.greedy_attack_max import greedy_max_damage_attack
from logic_cpu.greedy_target_weakest import greedy_best_target
from logic_cpu.greedy_element import greedy_element_attack
from logic_cpu.greedy_fire import greedy_fire_spread
from logic_cpu.greedy_heal import greedy_heal_distribution


def move_callback(grid, e_pos, new_pos, e_card):
    # Update the grid after the move animation completes
    grid.tiles[new_pos[0]][new_pos[1]].card = e_card
    grid.tiles[e_pos[0]][e_pos[1]].card = None


def calculate_move_score(e_pos, players, grid, e_card):
    def dist(p1, p2):
        return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

    if not players:
        return 0

    current_dist = min(dist(e_pos, p) for p in players)

    if e_card.element in ["water", "leaf"]:
        new_pos = greedy_escape_move(e_pos, players, grid)
    else:
        new_pos = greedy_nearest_move(e_pos, players, grid)

    if new_pos == e_pos:
        return 0

    new_dist = min(dist(new_pos, p) for p in players)

    score = current_dist - new_dist
    return score if score is not None else 0


def calculate_attack_score(e_card, players, grid, e_pos):
    # Calculate score for attacking: potential damage, prefer low health targets, element advantage, can kill
    target_pos = greedy_best_target(e_pos, players, grid)

    if not target_pos:
        return 0

    target_card = grid.tiles[target_pos[0]][target_pos[1]].card
    atk = greedy_element_attack(e_card, target_pos, grid)

    # Base damage
    dmg = atk.dmg * 0.7

    # Prefer low health
    health_factor = 1 - (target_card.hp / target_card.max_hp)

    # Element advantage: simple, fire beats leaf, etc. But for now, assume 1
    element_bonus = 1

    # Can kill bonus
    kill_bonus = 10 if dmg >= target_card.hp else 0

    # Consider player attacks: if enemy is weak, higher score to attack preemptively
    enemy_weak = 1 if e_card.hp < e_card.max_hp * 0.5 else 0
    self_hp_ratio = e_card.hp / e_card.max_hp
    survival_penalty = (1 - self_hp_ratio) * 10

    # Distance penalty (don’t attack from far)
    dist = abs(e_pos[0] - target_pos[0]) + abs(e_pos[1] - target_pos[1])
    range_penalty = max(0, dist - atk.attack_range) * 5

    score = (
        dmg * (1 + health_factor)
        + kill_bonus
        - survival_penalty
        - range_penalty
    )
    return score

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

        # Calculate scores using greedy algorithm with distance parameters
        # Element-based behavior bias
        # Calculate scores using greedy algorithm
        move_score = calculate_move_score(e_pos, players, grid, e_card) or 0
        attack_score = calculate_attack_score(e_card, players, grid, e_pos) or 0

        # Element-based behavior bias
        if e_card.element == "fire":
            attack_score *= 1.2   # Fire enemies are aggressive
        elif e_card.element in ["water", "leaf"]:
            move_score *= 1.2     # Water/Leaf prefer positioning & survival


        if attack_score > move_score:
            # Perform attack
            target_pos = greedy_best_target(e_pos,players, grid)
            if target_pos:
                atk = greedy_element_attack(e_card, target_pos, grid)
                # Check range
                dist = abs(e_pos[0] - target_pos[0]) + abs(e_pos[1] - target_pos[1])
                if dist > atk.attack_range:
                    # OUT OF RANGE → MOVE ONLY (NO ATTACK)
                    if e_card.element in ["water", "leaf"]:
                        new_pos = greedy_escape_move(e_pos, players, grid)
                    else:
                        new_pos = greedy_nearest_move(e_pos, players, grid)

                    if new_pos != e_pos:
                        start = cell_center(*e_pos)
                        end = cell_center(*new_pos)

                        anim_mgr.trigger_move_anim(
                            start, end,
                            lambda: move_callback(grid, e_pos, new_pos, e_card)
                        )

                else:
                    # IN RANGE → ATTACK
                    start = cell_center(*e_pos)
                    end = cell_center(*target_pos)

                    anim_mgr.trigger_attack_anim(
                        start, end, atk.element,
                        lambda: perform_attack_logic(
                            e_pos[0], e_pos[1],
                            target_pos[0], target_pos[1],
                            atk, grid, dist
                        )
                    )

        else:
            # Perform move
            if e_card.element in ["water", "leaf"]:
                new_pos = greedy_escape_move(e_pos, players, grid)
            else:
                new_pos = greedy_nearest_move(e_pos, players, grid)

            if new_pos != e_pos:
                start = cell_center(*e_pos)
                end = cell_center(*new_pos)

                anim_mgr.trigger_move_anim(
                    start, end,
                    lambda: move_callback(grid, e_pos, new_pos, e_card)
                )

        break  # Only one enemy acts per turn
