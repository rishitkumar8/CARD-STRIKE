import pygame
from config import FPS
from colors import E_FIRE, E_LEAF
from grid import cell_center
from animations import anim_mgr

# Global Effect Lists
flame_tiles = []      # (c, r, time_left)
regen_effects = []    # [card, heal_per_tick, time_left, (c,r)]
burn_effects = []     # [card, dmg_per_tick, time_left, (c,r)]

def process_flame_tiles(grid):
    for ft in flame_tiles[:]:
        c, r, t = ft
        t -= 1
        ft[2] = t

        if t <= 0:
            flame_tiles.remove(ft)
            continue

        card = grid.tiles[c][r].card
        if card and card.owner == "enemy":
            card.hp -= 10
            anim_mgr.add_floating_text("-10🔥", *cell_center(c, r), E_FIRE)

def process_regen():
    for eff in regen_effects[:]:
        card, heal, t, pos = eff
        t -= 1
        eff[2] = t
        card.hp = min(card.max_hp, card.hp + heal)
        anim_mgr.add_floating_text(f"+{heal}", *cell_center(*pos), E_LEAF)
        if t <= 0:
            regen_effects.remove(eff)

def process_burn(grid):
    for eff in burn_effects[:]:
        card, dmg, t, pos = eff
        t -= 1
        eff[2] = t
        card.hp -= dmg
        anim_mgr.add_floating_text(f"-{dmg}", *cell_center(*pos), E_FIRE)
        if card.hp <= 0:
            grid.tiles[pos[0]][pos[1]].card = None
        if t <= 0:
            burn_effects.remove(eff)
