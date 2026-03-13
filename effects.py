import pygame
from config import FPS
from colors import E_FIRE, E_LEAF
from game_grid import cell_center
from animations import anim_mgr

# ==================================================
# GLOBAL EFFECT LISTS
# ==================================================
# flame_tiles: [col, row, time_left, owner]
flame_tiles = []

# regen_effects: [card, heal_per_tick, time_left, (col,row)]
regen_effects = []

# burn_effects: [card, dmg_per_tick, time_left, (col,row)]
burn_effects = []


# ==================================================
# 🔥 FIRE TRAIL DAMAGE (CAN KILL)
# ==================================================
def process_flame_tiles(grid):
    for ft in flame_tiles[:]:
        c, r, t, owner = ft[0], ft[1], ft[2], ft[3]
        t -= 1
        ft[2] = t

        # remove expired fire
        if t <= 0:
            flame_tiles.remove(ft)
            continue

        if not grid.in_bounds(c, r):
            continue

        # Only deal damage once per turn (every ~FPS frames)
        # Use a tick counter stored as ft[4]
        if len(ft) < 5:
            ft.append(0)  # Initialize tick counter
        ft[4] += 1
        if ft[4] < FPS:  # Only trigger once per second/turn
            continue
        ft[4] = 0  # Reset tick counter

        card = grid.tiles[c][r].card

        # damage ONLY enemies of owner
        if card and card.owner != owner:
            card.hp -= 5
            anim_mgr.add_floating_text("-5🔥", *cell_center(c, r), E_FIRE)

            if card.hp <= 0:
                grid.tiles[c][r].card = None


# ==================================================
# 🌿 HEAL OVER TIME (LIMITED BY healed_once FLAG)
# ==================================================
def process_regen():
    for eff in regen_effects[:]:
        # eff: [card, heal_per_tick, time_left, (col,row), tick_counter]
        if len(eff) < 5:
            eff.append(0)
        
        eff[4] += 1
        if eff[4] < FPS:
            continue
        eff[4] = 0

        card, heal, t, pos = eff[0], eff[1], eff[2], eff[3]
        t -= 1
        eff[2] = t

        # card might already be dead
        if card.hp <= 0:
            regen_effects.remove(eff)
            continue

        # partial heal only
        card.hp = min(card.max_hp, card.hp + heal)
        anim_mgr.add_floating_text(f"+{heal}", *cell_center(*pos), E_LEAF)

        if t <= 0:
            regen_effects.remove(eff)
            if card:
                card.healed_once = False


# ==================================================
# 🔥 BURN DAMAGE (CAN KILL)
# ==================================================
def process_burn(grid):
    for eff in burn_effects[:]:
        # eff: [card, dmg, time_left, pos, tick_counter]
        if len(eff) < 5:
            eff.append(0)
        
        eff[4] += 1
        if eff[4] < FPS:
            continue
        eff[4] = 0

        card, dmg, t, pos = eff[0], eff[1], eff[2], eff[3]
        t -= 1
        eff[2] = t

        # card might already be dead
        if card.hp <= 0:
            burn_effects.remove(eff)
            continue

        card.hp -= dmg
        anim_mgr.add_floating_text(f"-{dmg}🔥", *cell_center(*pos), E_FIRE)

        if card.hp <= 0:
            grid.tiles[pos[0]][pos[1]].card = None
            burn_effects.remove(eff)
            continue

        if t <= 0:
            burn_effects.remove(eff)
