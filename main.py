import pygame
from config import *
from grid import Grid, cell_center
from animations import anim_mgr
from effects import flame_tiles, regen_effects, burn_effects, process_flame_tiles, process_regen, process_burn
from logic_attack import initiate_player_attack
from logic_cpu.cpu_controller import cpu_turn
from ui_draw import draw_ui
from card import Card
from attack import Attack
from colors import *
from fonts import *
import random

pygame.init()
pygame.display.set_caption("Card Strike: Elemental GUI")
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
clock = pygame.time.Clock()

grid = Grid(GRID_COLS, GRID_ROWS)

selected_pos = None
hovered_cell = (0,0)
placing_phase = True
placed_count = 0
cpu_pending = False

def create_player_card(slot_index: int) -> Card:
    # FIRE/LEAF MIXED CARD — ALL PLAYERS USE SAME ABILITIES
    attacks = [
        Attack("Burning Trail", dmg=12, element="fire", attack_range=5),
        Attack("Nature's Embrace", dmg=12, element="leaf", attack_range=5),
        Attack("Burning-Embrace Fusion", dmg=12, element="fire_leaf", attack_range=5)
    ]

    card = Card(
        owner="player",
        name=f"Hero {slot_index+1}",
        hp=100,
        max_hp=100,
        attacks=attacks,
        move_range=3,
        element="fire_leaf",
        index=slot_index
    )
    card.display_hp = card.hp
    return card

def create_enemy_card(slot_index: int) -> Card:
    e = random.choice(['fire', 'water', 'leaf', 'null'])
    attacks = [
        Attack("Bite", dmg=10, element=e, attack_range=5),
        Attack("Claw", dmg=14, element='null', attack_range=5),
    ]
    card = Card(owner="enemy", name=f"Beast {slot_index+1}", hp=100, max_hp=100, attacks=attacks, move_range=2, element=e, index=slot_index)
    card.display_hp = card.hp
    return card

def check_win_lose(grid):
    player_alive = any(tile.card and tile.card.owner == "player" for row in grid.tiles for tile in row)
    enemy_alive = any(tile.card and tile.card.owner == "enemy" for row in grid.tiles for tile in row)
    if not enemy_alive:
        return "victory"
    elif not player_alive:
        return "defeat"
    return "playing"

game_state = "playing"
running = True
while running:
    # Logic Update
    anim_mgr.update()

    # PROCESS FLAME TILES
    process_flame_tiles(grid)

    # PROCESS REGEN
    process_regen()

    # PROCESS BURN DOT
    process_burn(grid)

    # If CPU is pending and no animations are blocking, perform cpu_turn automatically
    if cpu_pending and not anim_mgr.blocking and not placing_phase:
        cpu_pending = False
        cpu_turn(grid)
        game_state = check_win_lose(grid)

    mx, my = pygame.mouse.get_pos()
    hovered_cell = (mx // TILE_SIZE, my // TILE_SIZE)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.MOUSEBUTTONDOWN and not anim_mgr.blocking:
            c, r = hovered_cell
            if grid.in_bounds(c, r):
                if placing_phase:
                    if grid.tiles[c][r].card is None:
                        grid.tiles[c][r].card = create_player_card(placed_count)
                        placed_count += 1
                        anim_mgr.add_particle(*(cell_center(c,r)), 'leaf') # Spawn puff
                        if placed_count >= 3:
                            placing_phase = False
                            # Spawn enemies
                            empties = [(xx, yy) for xx in range(GRID_COLS) for yy in range(GRID_ROWS) if not grid.tiles[xx][yy].card]
                            for i in range(3):
                                ex, ey = random.choice(empties)
                                grid.tiles[ex][ey].card = create_enemy_card(i)
                                empties.remove((ex,ey))
                else:
                    # Gameplay clicks
                    clicked = grid.tiles[c][r].card
                    if clicked and clicked.owner == "player":
                        selected_pos = (c,r)
                    elif selected_pos:
                        # Move
                        sc, sr = selected_pos
                        mover = grid.tiles[sc][sr].card
                        dist = abs(c-sc) + abs(r-sr)
                        if mover and dist <= mover.move_range and not clicked:
                            grid.tiles[c][r].card = mover
                            grid.tiles[sc][sr].card = None
                            selected_pos = None
                            anim_mgr.add_particle(*(cell_center(c,r)), 'air') # Dash effect
                            cpu_pending = True  # schedule CPU to act after this player's move

        if event.type == pygame.KEYDOWN and not placing_phase and not anim_mgr.blocking:
            if event.key == pygame.K_m:
                cpu_turn(grid)
            
            # Key Mapping for attacks
            # Structure: Key -> (PlayerIndex, AttackIndex)
            controls = {
                pygame.K_q: (0,0), pygame.K_w: (0,1), pygame.K_e: (0,2),
                pygame.K_a: (1,0), pygame.K_s: (1,1), pygame.K_d: (1,2),
                pygame.K_z: (2,0), pygame.K_x: (2,1), pygame.K_c: (2,2),
            }
            
            if event.key in controls:
                pid, aid = controls[event.key]
                # Check if we are holding a number key for targeting
                keys = pygame.key.get_pressed()
                target_idx = -1
                if keys[pygame.K_1]: target_idx = 0
                elif keys[pygame.K_2]: target_idx = 1
                elif keys[pygame.K_3]: target_idx = 2
                
                if target_idx != -1:
                    initiate_player_attack(pid, aid, target_idx, grid)
                    cpu_pending = True  # schedule CPU to act after this player's attack
                else:
                    anim_mgr.add_floating_text("Hold 1/2/3!", mx, my, (255, 255, 0))

    draw_ui(screen, grid, selected_pos, hovered_cell, game_state)
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
