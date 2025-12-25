import pygame
import random

from config import *
from grid import Grid, cell_center
from animations import anim_mgr
from effects import (
    flame_tiles, regen_effects, burn_effects,
    process_flame_tiles, process_regen, process_burn
)
from logic_attack import initiate_player_attack
from logic_cpu.cpu_controller import cpu_turn
from ui_draw import draw_ui
from card import Card
from attack import Attack
from colors import *
from fonts import *

pygame.init()
pygame.display.set_caption("Card Strike: Elemental GUI")
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
clock = pygame.time.Clock()

# -------------------------------------------------
# GAME STATE
# -------------------------------------------------
grid = Grid(GRID_COLS, GRID_ROWS)

selected_pos = None
hovered_cell = (0, 0)

placing_phase = True
placed_count = 0
cpu_pending = False

# Player variant selection during placement
selected_player_element = "fire"  # default

# -------------------------------------------------
# CARD FACTORIES
# -------------------------------------------------
def create_player_card(slot_index: int, element: str) -> Card:
    if element == "fire":
        attacks = [
            Attack("Burning Trail", 12, "fire", 5),
            Attack("Fire Claw", 14, "fire", 4),
            Attack("Inferno Burst", 16, "fire", 5),
        ]
    elif element == "water":
        attacks = [
            Attack("Water Lash", 10, "water", 5),
            Attack("Tidal Push", 12, "water", 4),
            Attack("Healing Wave", 8, "water", 4),
        ]
    elif element == "leaf":
        attacks = [
            Attack("Nature's Embrace", 10, "leaf", 4),
            Attack("Vine Whip", 12, "leaf", 5),
            Attack("Thorn Burst", 14, "leaf", 4),
        ]
    else:  # null
        attacks = [
            Attack("Strike", 12, "null", 4),
            Attack("Guard Break", 14, "null", 4),
            Attack("Focused Blow", 16, "null", 3),
        ]

    card = Card(
        owner="player",
        name=f"Hero {slot_index+1}",
        hp=100,
        max_hp=100,
        attacks=attacks,
        move_range=3,
        element=element,
        index=slot_index
    )
    card.display_hp = card.hp
    return card


def create_enemy_card(slot_index: int) -> Card:
    e = random.choice(["fire", "water", "leaf", "null"])
    if e == "fire":
        attacks = [
            Attack("Burning Trail", 12, "fire", 5),
            Attack("Fire Claw", 14, "fire", 4),
            Attack("Inferno Burst", 16, "fire", 5),
        ]
    elif e == "water":
        attacks = [
            Attack("Water Lash", 10, "water", 5),
            Attack("Tidal Push", 12, "water", 4),
            Attack("Healing Wave", 8, "water", 4),
        ]
    elif e == "leaf":
        attacks = [
            Attack("Nature's Embrace", 10, "leaf", 4),
            Attack("Vine Whip", 12, "leaf", 5),
            Attack("Thorn Burst", 14, "leaf", 4),
        ]
    else:  # null
        attacks = [
            Attack("Strike", 12, "null", 4),
            Attack("Guard Break", 14, "null", 4),
            Attack("Focused Blow", 16, "null", 3),
        ]
    card = Card(
        owner="enemy",
        name=f"Beast {slot_index+1}",
        hp=100,
        max_hp=100,
        attacks=attacks,
        move_range=2,
        element=e,
        index=slot_index
    )
    card.display_hp = card.hp
    return card


def check_win_lose(grid):
    player_alive = any(
        tile.card and tile.card.owner == "player"
        for col in grid.tiles for tile in col
    )
    enemy_alive = any(
        tile.card and tile.card.owner == "enemy"
        for col in grid.tiles for tile in col
    )
    if not enemy_alive:
        return "victory"
    if not player_alive:
        return "defeat"
    return "playing"


# -------------------------------------------------
# MAIN LOOP
# -------------------------------------------------
game_state = "playing"
running = True

while running:
    clock.tick(FPS)

    # -----------------------------
    # UPDATE LOGIC
    # -----------------------------
    anim_mgr.update()
    process_flame_tiles(grid)
    process_regen()
    process_burn(grid)

    if cpu_pending and not anim_mgr.blocking and not placing_phase:
        cpu_pending = False
        cpu_turn(grid)
        game_state = check_win_lose(grid)

    mx, my = pygame.mouse.get_pos()
    hovered_cell = (mx // TILE_SIZE, my // TILE_SIZE)

    # -----------------------------
    # EVENTS
    # -----------------------------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # ---------------------------------
        # PLAYER ELEMENT SELECTION (PLACEMENT)
        # ---------------------------------
        if event.type == pygame.KEYDOWN and placing_phase:
            if event.key == pygame.K_1:
                selected_player_element = "fire"
            elif event.key == pygame.K_2:
                selected_player_element = "water"
            elif event.key == pygame.K_3:
                selected_player_element = "leaf"
            elif event.key == pygame.K_4:
                selected_player_element = "null"

        # ---------------------------------
        # MOUSE CLICK
        # ---------------------------------
        if event.type == pygame.MOUSEBUTTONDOWN and not anim_mgr.blocking:
            c, r = hovered_cell
            if not grid.in_bounds(c, r):
                continue

            if placing_phase:
                if grid.tiles[c][r].card is None:
                    grid.tiles[c][r].card = create_player_card(
                        placed_count, selected_player_element
                    )
                    placed_count += 1
                    anim_mgr.add_particle(*cell_center(c, r), "leaf")

                    if placed_count >= 3:
                        placing_phase = False
                        empties = [
                            (x, y)
                            for x in range(GRID_COLS)
                            for y in range(GRID_ROWS)
                            if not grid.tiles[x][y].card
                        ]
                        for i in range(3):
                            ex, ey = random.choice(empties)
                            grid.tiles[ex][ey].card = create_enemy_card(i)
                            empties.remove((ex, ey))

            else:
                clicked = grid.tiles[c][r].card
                if clicked and clicked.owner == "player":
                    selected_pos = (c, r)
                elif selected_pos:
                    sc, sr = selected_pos
                    mover = grid.tiles[sc][sr].card
                    if mover:
                        dist = abs(c - sc) + abs(r - sr)
                        if dist <= mover.move_range and not clicked:
                            grid.tiles[c][r].card = mover
                            grid.tiles[sc][sr].card = None
                            selected_pos = None
                            anim_mgr.add_particle(*cell_center(c, r), "air")
                            cpu_pending = True

        # ---------------------------------
        # COMBAT KEYS
        # ---------------------------------
        if event.type == pygame.KEYDOWN and not placing_phase and not anim_mgr.blocking:
            if event.key == pygame.K_m:
                cpu_turn(grid)

            controls = {
                pygame.K_q: (0, 0), pygame.K_w: (0, 1), pygame.K_e: (0, 2),
                pygame.K_a: (1, 0), pygame.K_s: (1, 1), pygame.K_d: (1, 2),
                pygame.K_z: (2, 0), pygame.K_x: (2, 1), pygame.K_c: (2, 2),
            }

            if event.key in controls:
                pid, aid = controls[event.key]
                keys = pygame.key.get_pressed()
                target_idx = (
                    0 if keys[pygame.K_1]
                    else 1 if keys[pygame.K_2]
                    else 2 if keys[pygame.K_3]
                    else -1
                )

                if target_idx != -1:
                    initiate_player_attack(pid, aid, target_idx, grid)
                    cpu_pending = True
                else:
                    anim_mgr.add_floating_text(
                        "Hold 1/2/3!", mx, my, (255, 255, 0)
                    )

    # -----------------------------
    # DRAW
    # -----------------------------
    draw_ui(
        screen,
        grid,
        selected_pos,
        hovered_cell,
        game_state,
        placing_phase,
        selected_player_element
    )

    pygame.display.flip()

pygame.quit()
