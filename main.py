import asyncio
import logging
import math
import random
import sys

import pygame

from animations import anim_mgr
from attack import Attack
from card import Card
from colors import *
from config import *
from effects import process_burn, process_flame_tiles, process_regen
from fonts import *
from game_grid import Grid, cell_center
from logic_attack import decrement_cooldowns, initiate_player_attack, process_turn_start_statuses
from logic_cpu.advanced_cpu import advanced_cpu_turn as cpu_turn
from stealing_phase import StealingPhase
from ui_draw import draw_help_overlay, draw_ui, spawn_confetti, update_and_draw_confetti


def get_window_size() -> tuple[int, int]:
    if IS_WEB:
        try:
            import platform as web_platform

            browser_w = int(getattr(web_platform.window, "innerWidth", WIDTH))
            browser_h = int(getattr(web_platform.window, "innerHeight", HEIGHT))
            return max(320, browser_w), max(240, browser_h)
        except Exception:
            display_info = pygame.display.Info()
            return max(320, display_info.current_w or WIDTH), max(240, display_info.current_h or HEIGHT)

    display_info = pygame.display.Info()
    max_width = max(960, min(WIDTH, display_info.current_w or WIDTH))
    max_height = max(720, min(HEIGHT, display_info.current_h or HEIGHT))
    return max_width, max_height


def compute_viewport(window_size: tuple[int, int]) -> tuple[pygame.Rect, tuple[float, float]]:
    win_w, win_h = window_size
    if IS_WEB:
        return pygame.Rect(0, 0, max(1, win_w), max(1, win_h)), (
            max(win_w / WIDTH, 0.0001),
            max(win_h / HEIGHT, 0.0001),
        )

    scale = min(win_w / WIDTH, win_h / HEIGHT)
    scaled_w = max(1, int(WIDTH * scale))
    scaled_h = max(1, int(HEIGHT * scale))
    offset_x = (win_w - scaled_w) // 2
    offset_y = (win_h - scaled_h) // 2
    return pygame.Rect(offset_x, offset_y, scaled_w, scaled_h), (scale, scale)


def screen_to_world(pos: tuple[int, int], viewport: pygame.Rect, scale: tuple[float, float]) -> tuple[int, int]:
    scale_x, scale_y = scale
    x = (pos[0] - viewport.x) / scale_x
    y = (pos[1] - viewport.y) / scale_y
    return int(max(0, min(WIDTH - 1, x))), int(max(0, min(HEIGHT - 1, y)))


def configure_logging() -> None:
    logger = logging.getLogger()
    if logger.handlers:
        return

    logger.setLevel(logging.DEBUG)

    if sys.platform != "emscripten":
        file_handler = logging.FileHandler("game.log", mode="w")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(console_handler)


def exception_handler(exc_type, exc_value, exc_traceback) -> None:
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logging.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


def create_player_card(slot_index: int, element: str) -> Card:
    if element == "fire":
        attacks = [
            Attack("Burning Trail", 12, "fire", 5, max_cooldown=0),
            Attack("Fire Claw", 14, "fire", 4, max_cooldown=2),
            Attack("Inferno Burst", 16, "fire", 5, max_cooldown=3),
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
    else:
        attacks = [
            Attack("Strike", 12, "null", 4),
            Attack("Guard Break", 14, "null", 4),
            Attack("Focused Blow", 16, "null", 3),
        ]

    card = Card(
        owner="player",
        name=f"Hero {slot_index + 1}",
        hp=100,
        max_hp=100,
        attacks=attacks,
        move_range=3,
        element=element,
        index=slot_index,
    )
    card.display_hp = card.hp
    return card


def check_win_lose(grid: Grid) -> str:
    player_alive = any(tile.card and tile.card.owner == "player" for col in grid.tiles for tile in col)
    enemy_alive = any(tile.card and tile.card.owner == "enemy" for col in grid.tiles for tile in col)
    if not enemy_alive:
        return "victory"
    if not player_alive:
        return "defeat"
    return "playing"


async def main() -> None:
    configure_logging()
    sys.excepthook = exception_handler
    logging.info("Game Starting...")

    pygame.init()
    pygame.display.set_caption("Card Strike: Elemental GUI")
    window_size = get_window_size()
    screen = pygame.display.set_mode(window_size, pygame.RESIZABLE)
    game_surface = pygame.Surface((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    grid = Grid(GRID_COLS, GRID_ROWS)
    selected_pos = None
    hovered_cell = (0, 0)
    placing_phase = True
    placed_count = 0
    cpu_pending = False
    show_help = False
    selected_player_element = "fire"

    stealing_phase = StealingPhase(screen)
    stealing_phase_active = True
    player_final_cards = []
    cpu_final_cards = []
    game_state = "playing"
    running = True

    while running:
        try:
            clock.tick(FPS)
            viewport, scale = compute_viewport(screen.get_size())

            if stealing_phase_active:
                stealing_phase.update()

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False

                    if event.type == pygame.VIDEORESIZE:
                        screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                        viewport, scale = compute_viewport(screen.get_size())

                    if event.type == pygame.MOUSEMOTION:
                        stealing_phase.handle_mouse_move(screen_to_world(event.pos, viewport, scale))

                    if event.type == pygame.MOUSEBUTTONDOWN:
                        stealing_phase.handle_click(screen_to_world(event.pos, viewport, scale))

                    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and stealing_phase.phase_complete:
                        player_final_cards, cpu_final_cards = stealing_phase.get_final_decks()
                        stealing_phase_active = False
                        placing_phase = True

                if IS_WEB and stealing_phase.phase_complete:
                    player_final_cards, cpu_final_cards = stealing_phase.get_final_decks()
                    stealing_phase_active = False
                    placing_phase = True

                game_surface.fill(C_BG_PRIMARY)
                stealing_phase.screen = game_surface
                stealing_phase.draw()
                screen.fill(C_BG_GRADIENT_B)
                scaled_surface = pygame.transform.smoothscale(game_surface, viewport.size)
                screen.blit(scaled_surface, viewport.topleft)
                pygame.display.flip()
                await asyncio.sleep(0)
                continue

            anim_mgr.update()
            process_flame_tiles(grid)
            process_regen()
            process_burn(grid)

            if cpu_pending and not anim_mgr.blocking and not placing_phase:
                cpu_pending = False
                try:
                    cpu_turn(grid)
                except Exception as error:
                    logging.error(f"CPU turn crashed: {error}", exc_info=True)
                    anim_mgr.blocking = False

                decrement_cooldowns(grid, "player")
                process_turn_start_statuses(grid, "player")
                game_state = check_win_lose(grid)

            mx, my = screen_to_world(pygame.mouse.get_pos(), viewport, scale)
            hovered_cell = (mx // TILE_SIZE, my // TILE_SIZE)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.VIDEORESIZE:
                    screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                    viewport, scale = compute_viewport(screen.get_size())

                if event.type == pygame.KEYDOWN and placing_phase:
                    if event.key == pygame.K_1:
                        selected_player_element = "fire"
                    elif event.key == pygame.K_2:
                        selected_player_element = "water"
                    elif event.key == pygame.K_3:
                        selected_player_element = "leaf"
                    elif event.key == pygame.K_4:
                        selected_player_element = "null"

                if event.type == pygame.KEYDOWN and event.key == pygame.K_h:
                    show_help = not show_help

                if event.type == pygame.MOUSEBUTTONDOWN and not anim_mgr.blocking:
                    mx, my = screen_to_world(event.pos, viewport, scale)
                    hovered_cell = (mx // TILE_SIZE, my // TILE_SIZE)
                    c, r = hovered_cell
                    if not grid.in_bounds(c, r):
                        continue

                    if placing_phase:
                        if grid.tiles[c][r].card is None and placed_count < len(player_final_cards):
                            grid.tiles[c][r].card = player_final_cards[placed_count]
                            anim_mgr.add_particle(*cell_center(c, r), "leaf")

                            if placed_count < len(cpu_final_cards):
                                cpu_card = cpu_final_cards[placed_count]
                                empties = [
                                    (x, y)
                                    for x in range(GRID_COLS)
                                    for y in range(GRID_ROWS)
                                    if not grid.tiles[x][y].card
                                ]
                                if empties:
                                    right_side = [(ex, ey) for (ex, ey) in empties if ex > GRID_COLS // 2]
                                    ex, ey = random.choice(right_side if right_side else empties)
                                    grid.tiles[ex][ey].card = cpu_card
                                    anim_mgr.add_particle(*cell_center(ex, ey), "fire")

                            placed_count += 1
                            if placed_count >= len(player_final_cards):
                                placing_phase = False

                    else:
                        clicked = grid.tiles[c][r].card
                        if clicked and clicked.owner == "player":
                            selected_pos = (c, r)
                        elif selected_pos:
                            sc, sr = selected_pos
                            mover = grid.tiles[sc][sr].card
                            if mover:
                                from status_system import StatusType

                                is_rooted = (
                                    getattr(mover, "root_duration", 0) > 0
                                    or any(effect.type == StatusType.ROOT for effect in mover.active_effects)
                                )
                                if is_rooted:
                                    anim_mgr.add_floating_text("ROOTED!", *cell_center(sc, sr), (150, 100, 50))
                                    selected_pos = None
                                    continue

                                frost_reduction = sum(
                                    effect.value
                                    for effect in mover.active_effects
                                    if effect.type == StatusType.FROST
                                )
                                effective_range = max(0, mover.move_range - frost_reduction)
                                if frost_reduction > 0:
                                    anim_mgr.add_floating_text(
                                        f"FROST: MV-{frost_reduction}",
                                        *cell_center(sc, sr),
                                        (150, 220, 255),
                                    )

                                dist = abs(c - sc) + abs(r - sr)
                                if dist <= effective_range and not clicked:
                                    grid.tiles[c][r].card = mover
                                    grid.tiles[sc][sr].card = None
                                    selected_pos = None
                                    anim_mgr.add_particle(*cell_center(c, r), "air")
                                    cpu_pending = True
                                elif clicked and clicked.owner == "enemy" and IS_WEB:
                                    target_positions = []
                                    for col in range(grid.cols):
                                        for row in range(grid.rows):
                                            target_card = grid.tiles[col][row].card
                                            if target_card and target_card.owner == "enemy":
                                                target_positions.append((col, row))

                                    clicked_enemy_index = next(
                                        (
                                            idx
                                            for idx, (ec, er) in enumerate(target_positions)
                                            if (ec, er) == (c, r)
                                        ),
                                        -1,
                                    )
                                    if clicked_enemy_index >= 0:
                                        attack_triggered = False
                                        for attack_idx in range(len(mover.attacks)):
                                            if initiate_player_attack(mover.index, attack_idx, clicked_enemy_index, grid):
                                                selected_pos = None
                                                cpu_pending = True
                                                attack_triggered = True
                                                break
                                        if not attack_triggered:
                                            anim_mgr.add_floating_text("No attack in range!", *cell_center(c, r), (255, 180, 90))
                                elif not clicked:
                                    anim_mgr.add_floating_text("OUT OF RANGE!", *cell_center(c, r), (255, 100, 100))
                                    selected_pos = None

                if event.type == pygame.KEYDOWN and not placing_phase and not anim_mgr.blocking:
                    if event.key == pygame.K_m:
                        cpu_turn(grid)

                    controls = {
                        pygame.K_q: (0, 0),
                        pygame.K_w: (0, 1),
                        pygame.K_e: (0, 2),
                        pygame.K_a: (1, 0),
                        pygame.K_s: (1, 1),
                        pygame.K_d: (1, 2),
                        pygame.K_z: (2, 0),
                        pygame.K_x: (2, 1),
                        pygame.K_c: (2, 2),
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

                        if initiate_player_attack(pid, aid, target_idx, grid):
                            cpu_pending = True
                        elif target_idx == -1:
                            anim_mgr.add_floating_text("Hold 1/2/3!", mx, my, (255, 255, 0))

            game_surface.fill(C_BG_PRIMARY)
            draw_ui(game_surface, grid, selected_pos, hovered_cell, placing_phase, selected_player_element)

            if show_help and game_state == "playing":
                draw_help_overlay(game_surface)

            if game_state != "playing":
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 200))
                game_surface.blit(overlay, (0, 0))

                finish_frame = getattr(pygame, "_finish_frame", 0) + 1
                pygame._finish_frame = finish_frame

                if game_state == "victory":
                    if finish_frame == 1:
                        spawn_confetti()
                    update_and_draw_confetti(screen)
                    title_text = "VICTORY"
                    title_color = C_VICTORY
                    icon_text = "*"
                else:
                    title_text = "DEFEAT"
                    title_color = C_DEFEAT
                    icon_text = "X"
                    for _ in range(2):
                        ax = random.randint(0, WIDTH)
                        ay = random.randint(0, HEIGHT)
                        ash_a = random.randint(20, 60)
                        pygame.draw.circle(game_surface, (*C_TEXT_DIM, ash_a), (ax, ay), random.randint(1, 3))

                icon_surf = FONT_HERO.render(icon_text, True, title_color)
                game_surface.blit(icon_surf, (WIDTH // 2 - icon_surf.get_width() // 2, HEIGHT // 2 - 180))

                shadow = FONT_HERO.render(title_text, True, C_SHADOW)
                game_surface.blit(shadow, (WIDTH // 2 - shadow.get_width() // 2 + 4, HEIGHT // 2 - 90 + 4))
                txt_surf = FONT_HERO.render(title_text, True, title_color)
                game_surface.blit(txt_surf, (WIDTH // 2 - txt_surf.get_width() // 2, HEIGHT // 2 - 90))

                panel_w, panel_h = 400, 120
                px = WIDTH // 2 - panel_w // 2
                py = HEIGHT // 2 + 20
                panel_rect = pygame.Rect(px, py, panel_w, panel_h)
                pygame.draw.rect(screen, (*C_BG_TERTIARY, 220), panel_rect, border_radius=RADIUS_MD)
                pygame.draw.rect(screen, C_ACCENT_DARK, panel_rect, 2, border_radius=RADIUS_MD)

                p_alive = sum(1 for col in grid.tiles for tile in col if tile.card and tile.card.owner == "player")
                e_alive = sum(1 for col in grid.tiles for tile in col if tile.card and tile.card.owner == "enemy")
                stat1 = FONT_MAIN.render(f"Your Units Alive: {p_alive}", True, C_PLAYER_GLOW)
                stat2 = FONT_MAIN.render(f"Enemy Units Alive: {e_alive}", True, C_ENEMY_GLOW)
                game_surface.blit(stat1, (px + 24, py + 24))
                game_surface.blit(stat2, (px + 24, py + 60))

                btn_w, btn_h = 280, 56
                btn_x = WIDTH // 2 - btn_w // 2
                btn_y = HEIGHT // 2 + 170
                btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
                btn_hov = btn_rect.collidepoint((mx, my))
                btn_color = C_ACCENT_GLOW if btn_hov else C_ACCENT
                pygame.draw.rect(game_surface, btn_color, btn_rect, border_radius=RADIUS_MD)
                pygame.draw.rect(game_surface, C_GOLD if btn_hov else C_ACCENT_DARK, btn_rect, 3, border_radius=RADIUS_MD)
                btn_text = FONT_BIG.render("PLAY AGAIN", True, C_TEXT)
                game_surface.blit(btn_text, (btn_x + (btn_w - btn_text.get_width()) // 2, btn_y + 12))

                for ev in pygame.event.get(pygame.MOUSEBUTTONDOWN):
                    world_pos = screen_to_world(ev.pos, viewport, scale)
                    if btn_rect.collidepoint(world_pos):
                        grid = Grid(GRID_COLS, GRID_ROWS)
                        selected_pos = None
                        placing_phase = True
                        placed_count = 0
                        cpu_pending = False
                        game_state = "playing"
                        show_help = False
                        stealing_phase.reset()
                        stealing_phase_active = True
                        player_final_cards = []
                        cpu_final_cards = []
                        anim_mgr.blocking = False
                        pygame._finish_frame = 0

                anim_mgr.blocking = True

            screen.fill(C_BG_GRADIENT_B)
            scaled_surface = pygame.transform.smoothscale(game_surface, viewport.size)
            screen.blit(scaled_surface, viewport.topleft)
            pygame.display.flip()

        except Exception as error:
            logging.error(f"Main loop exception: {error}", exc_info=True)
            try:
                anim_mgr.add_floating_text(f"Error: {error}", WIDTH // 2, 40, (255, 50, 50))
                anim_mgr.blocking = False
            except Exception:
                pass

        await asyncio.sleep(0)

    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())
