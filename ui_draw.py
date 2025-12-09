import pygame
from config import *
from colors import *
from fonts import FONT_BIG, FONT_MAIN
from grid import cell_center
from animations import anim_mgr
from effects import flame_tiles


def draw_card_shape(surf, x, y, size, color, is_circle=False):
    rect = pygame.Rect(x - size//2, y - size//2, size, size)
    if is_circle:
        pygame.draw.circle(surf, color, (x, y), size//2)
    else:
        pygame.draw.rect(surf, color, rect, border_radius=12)


def draw_ui(screen, grid, selected_pos, hovered_cell):
    screen.fill(C_BG)

    # Draw Grid
    for c in range(GRID_COLS):
        for r in range(GRID_ROWS):
            rect = pygame.Rect(c*TILE_SIZE, r*TILE_SIZE, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(screen, C_GRID, rect, 1)

            # Flame Tiles
            for ft in flame_tiles:
                if ft[0] == c and ft[1] == r:
                    alpha = int((ft[2] / (FPS * 3)) * 255)
                    flame = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                    pygame.draw.circle(flame, (*E_FIRE, alpha), (TILE_SIZE//2, TILE_SIZE//2), TILE_SIZE//3)
                    screen.blit(flame, (c*TILE_SIZE, r*TILE_SIZE))

            # Hover effect
            if (c, r) == hovered_cell:
                s = pygame.Surface((TILE_SIZE, TILE_SIZE))
                s.set_alpha(30)
                s.fill(C_HIGHLIGHT)
                screen.blit(s, (c*TILE_SIZE, r*TILE_SIZE))

    # Draw Cards
    for c in range(grid.cols):
        for r in range(grid.rows):
            card = grid.tiles[c][r].card
            if card:
                cx, cy = cell_center(c, r)

                color = C_PLAYER if card.owner == "player" else C_ENEMY
                draw_card_shape(screen, cx, cy, TILE_SIZE - 10, color, is_circle=(card.owner == "enemy"))

                label = f"P{card.index+1}" if card.owner == "player" else f"E{card.index+1}"
                label_surface = FONT_BIG.render(label, True, C_WHITE)
                screen.blit(label_surface, (cx - label_surface.get_width()//2, cy - TILE_SIZE//2 - 10))

    # VFX
    anim_mgr.draw(screen)
