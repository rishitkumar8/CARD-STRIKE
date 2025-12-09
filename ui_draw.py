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

                # ===============================
                #         ADVANCED HP BAR
                # ===============================

                # Animated HP ratio
                hp_ratio = max(0, card.display_hp / card.max_hp)

                # Bar position
                hp_bar_width = 70
                hp_bar_height = 9
                hp_x = cx - hp_bar_width // 2
                hp_y = cy - TILE_SIZE // 2 - 28

                # Background
                pygame.draw.rect(screen, (0,0,0), (hp_x, hp_y, hp_bar_width, hp_bar_height), border_radius=3)

                # GRADIENT BAR
                for i in range(int(hp_ratio * hp_bar_width)):
                    t = i / hp_bar_width
                    # Green → Yellow → Red gradient
                    if t > 0.6:
                        color = (255, int(255 * (1 - t)), 0)
                    elif t > 0.3:
                        color = (255, 200, 0)
                    else:
                        color = (0, 255, 0)

                    pygame.draw.line(screen, color, (hp_x + i, hp_y), (hp_x + i, hp_y + hp_bar_height))

                # Critical HP Glow
                if hp_ratio < 0.25:
                    glow_surf = pygame.Surface((hp_bar_width, hp_bar_height), pygame.SRCALPHA)
                    pygame.draw.rect(glow_surf, (255,0,0,120), (0,0,hp_bar_width,hp_bar_height), border_radius=3)
                    screen.blit(glow_surf, (hp_x, hp_y))

                # Shield overlay
                if card.shield > 0:
                    shield_ratio = min(1, card.shield / 40)
                    pygame.draw.rect(screen, (100,200,255), (hp_x, hp_y, int(shield_ratio * hp_bar_width), 3), border_radius=2)

                # HP TEXT
                hp_text = FONT_MAIN.render(f"{card.hp}", True, (255,255,255))
                screen.blit(hp_text, (cx - hp_text.get_width()//2, hp_y + 12))

                # Damage Flash (card blink)
                if card.flash_timer > 0:
                    card.flash_timer -= 1
                    flash_overlay = pygame.Surface((TILE_SIZE-10, TILE_SIZE-10), pygame.SRCALPHA)
                    pygame.draw.rect(flash_overlay, (255,50,50,150), (0,0,TILE_SIZE-10,TILE_SIZE-10), border_radius=12)
                    screen.blit(flash_overlay, (cx-(TILE_SIZE-10)//2, cy-(TILE_SIZE-10)//2))

                # Rare Card Border
                if card.rarity == "rare":
                    pygame.draw.circle(screen, (0,255,255), (cx, cy), TILE_SIZE//2, 4)
                elif card.rarity == "epic":
                    pygame.draw.circle(screen, (255,0,255), (cx, cy), TILE_SIZE//2, 5)
                elif card.rarity == "legendary":
                    pygame.draw.circle(screen, (255,220,0), (cx, cy), TILE_SIZE//2, 6)

    # VFX
    anim_mgr.draw(screen)
