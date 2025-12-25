import random
from grid import cell_center
from animations import anim_mgr
from logic_attack import perform_attack_logic

from logic_cpu.greedy_move import greedy_nearest_move
from logic_cpu.greedy_escape import greedy_escape_move
from logic_cpu.greedy_target_weakest import greedy_best_target
from logic_cpu.greedy_element import greedy_element_attack


# ------------------------------
# CPU MEMORY (Human-like state)
# ------------------------------
last_attacked_enemy = None
last_attacked_turn = -1
current_turn = 0

threatened_ally = None
threatened_turn = -1


# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def is_heal_attack(atk):
    return atk.name in ["Nature's Embrace", "Healing Wave"]


def move_callback(grid, e_pos, new_pos, e_card):
    grid.tiles[new_pos[0]][new_pos[1]].card = e_card
    grid.tiles[e_pos[0]][e_pos[1]].card = None


def find_ally_to_heal(grid):
    weakest = None
    lowest_ratio = 1.0

    for c in range(grid.cols):
        for r in range(grid.rows):
            card = grid.tiles[c][r].card
            if card and card.owner == "enemy":
                ratio = card.hp / card.max_hp
                if ratio < 0.5 and ratio < lowest_ratio:
                    lowest_ratio = ratio
                    weakest = (c, r)

    return weakest


# --------------------------------------------------
# ENEMY PRIORITY
# --------------------------------------------------
def enemy_priority(e_pos, e_card, players, grid):
    global threatened_ally, threatened_turn

    from logic_cpu.cpu_controller import (
        last_attacked_enemy, last_attacked_turn, current_turn
    )

    if last_attacked_enemy == e_pos and current_turn - last_attacked_turn <= 1:
        return 1500

    if threatened_ally and current_turn - threatened_turn <= 1 and e_pos != threatened_ally:
        dist = abs(e_pos[0] - threatened_ally[0]) + abs(e_pos[1] - threatened_ally[1])
        return 1200 - dist * 10

    target = greedy_best_target(e_pos, players, grid)
    if target:
        atk = greedy_element_attack(e_card, target, grid)
        dist = abs(e_pos[0] - target[0]) + abs(e_pos[1] - target[1])
        if dist <= atk.attack_range:
            return 1000

    hp_factor = 1 - (e_card.hp / e_card.max_hp)
    min_dist = min(abs(e_pos[0] - p[0]) + abs(e_pos[1] - p[1]) for p in players)

    return hp_factor * 100 + (10 / max(min_dist, 1))


# --------------------------------------------------
# MOVE SCORE
# --------------------------------------------------
def calculate_move_score(e_pos, players, grid, e_card):
    def dist(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    current_dist = min(dist(e_pos, p) for p in players)

    if e_card.element in ["water", "leaf"] and e_card.hp < e_card.max_hp * 0.5:
        new_pos = greedy_escape_move(e_pos, players, grid, e_card.move_range)
    else:
        new_pos = greedy_nearest_move(e_pos, players, grid, e_card.move_range)

    if new_pos == e_pos:
        return -5

    new_dist = min(dist(new_pos, p) for p in players)
    return current_dist - new_dist


# --------------------------------------------------
# ATTACK SCORE
# --------------------------------------------------
def calculate_attack_score(e_card, players, grid, e_pos):
    target_pos = greedy_best_target(e_pos, players, grid)
    if not target_pos:
        return -10

    target_card = grid.tiles[target_pos[0]][target_pos[1]].card
    atk = greedy_element_attack(e_card, target_pos, grid)

    dist = abs(e_pos[0] - target_pos[0]) + abs(e_pos[1] - target_pos[1])
    if dist > atk.attack_range:
        return -5

    kill_bonus = 15 if atk.dmg >= target_card.hp else 0
    return atk.dmg + kill_bonus


# --------------------------------------------------
# CPU TURN
# --------------------------------------------------
def cpu_turn(grid):
    global current_turn, threatened_ally, threatened_turn
    current_turn += 1

    if anim_mgr.blocking:
        return

    enemies, players = [], []

    for c in range(grid.cols):
        for r in range(grid.rows):
            card = grid.tiles[c][r].card
            if card:
                if card.owner == "enemy":
                    enemies.append((c, r))
                else:
                    players.append((c, r))

    if not enemies or not players:
        return

    # Select best enemy
    best_enemy = max(
        enemies,
        key=lambda pos: enemy_priority(pos, grid.tiles[pos[0]][pos[1]].card, players, grid)
    )

    e_pos = best_enemy
    e_card = grid.tiles[e_pos[0]][e_pos[1]].card

    panic = e_card.hp < e_card.max_hp * 0.35

    needs_self_heal = (
        e_card.element in ["leaf", "water"] and
        e_card.hp < e_card.max_hp * 0.45
    )

    ally_to_heal = find_ally_to_heal(grid)
    if ally_to_heal == e_pos:
        ally_to_heal = None

    move_score = calculate_move_score(e_pos, players, grid, e_card)
    attack_score = calculate_attack_score(e_card, players, grid, e_pos)

    # --------------------------------------------------
    # HEALING (SELF / ALLY)
    # --------------------------------------------------
    if e_card.element in ["leaf", "water"]:

        if needs_self_heal:
            for atk in e_card.attacks:
                if is_heal_attack(atk):
                    anim_mgr.trigger_attack_anim(
                        cell_center(*e_pos),
                        cell_center(*e_pos),
                        atk.element,
                        lambda: perform_attack_logic(
                            e_pos[0], e_pos[1],
                            e_pos[0], e_pos[1],
                            atk, grid, 0
                        )
                    )
                    return

        if ally_to_heal:
            ax, ay = ally_to_heal
            dist = abs(e_pos[0] - ax) + abs(e_pos[1] - ay)

            for atk in e_card.attacks:
                if is_heal_attack(atk) and dist <= atk.attack_range:
                    anim_mgr.trigger_attack_anim(
                        cell_center(*e_pos),
                        cell_center(ax, ay),
                        atk.element,
                        lambda: perform_attack_logic(
                            e_pos[0], e_pos[1],
                            ax, ay,
                            atk, grid, dist
                        )
                    )
                    return

    # --------------------------------------------------
    # PANIC ATTACK (ALL ENEMIES)
    # --------------------------------------------------
    if panic:
        threatened_ally = e_pos
        threatened_turn = current_turn

        target_pos = greedy_best_target(e_pos, players, grid)
        if target_pos:
            atk = greedy_element_attack(e_card, target_pos, grid)
            dist = abs(e_pos[0] - target_pos[0]) + abs(e_pos[1] - target_pos[1])

            if dist <= atk.attack_range:
                anim_mgr.trigger_attack_anim(
                    cell_center(*e_pos),
                    cell_center(*target_pos),
                    atk.element,
                    lambda: perform_attack_logic(
                        e_pos[0], e_pos[1],
                        target_pos[0], target_pos[1],
                        atk, grid, dist
                    )
                )
                return

    # --------------------------------------------------
    # NORMAL ATTACK
    # --------------------------------------------------
    if attack_score >= move_score:
        target_pos = greedy_best_target(e_pos, players, grid)
        if target_pos:
            atk = greedy_element_attack(e_card, target_pos, grid)
            dist = abs(e_pos[0] - target_pos[0]) + abs(e_pos[1] - target_pos[1])

            if dist <= atk.attack_range:
                anim_mgr.trigger_attack_anim(
                    cell_center(*e_pos),
                    cell_center(*target_pos),
                    atk.element,
                    lambda: perform_attack_logic(
                        e_pos[0], e_pos[1],
                        target_pos[0], target_pos[1],
                        atk, grid, dist
                    )
                )
                return

    # --------------------------------------------------
    # MOVE
    # --------------------------------------------------
    if threatened_ally and current_turn - threatened_turn <= 1 and e_pos != threatened_ally:
        new_pos = greedy_nearest_move(e_pos, [threatened_ally], grid, e_card.move_range)
    else:
        if e_card.element in ["water", "leaf"]:
            new_pos = greedy_escape_move(e_pos, players, grid, e_card.move_range)
        else:
            new_pos = greedy_nearest_move(e_pos, players, grid, e_card.move_range)

    if new_pos != e_pos:
        anim_mgr.trigger_move_anim(
            cell_center(*e_pos),
            cell_center(*new_pos),
            lambda: move_callback(grid, e_pos, new_pos, e_card)
        )
