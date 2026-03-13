import pygame
import random
import math
import os

from colors import *
from config import *
from fonts import *

# Pre-render checkerboard for performance
_checker_surface = None
_last_selected_pos = None
_cached_move_range = set()
_cached_atk_range = set()

# Text Cache to avoid per-frame font rendering
_text_cache = {}

def get_cached_text(text, font, color):
    key = (text, id(font), color)
    if key not in _text_cache:
        _text_cache[key] = font.render(text, True, color)
    return _text_cache[key]

from game_grid import cell_center
from animations import anim_mgr
from effects import flame_tiles

# ═══════════════════════════════════════════════════════
# GLOBAL CACHES
# ═══════════════════════════════════════════════════════
_bg_surface = None
_frame_count = 0

# ═══════════════════════════════════════════════════════
# AMBIENT PARTICLE SYSTEM (floating dust motes)
# ═══════════════════════════════════════════════════════
ambient_particles = []
for _ in range(50):
    ambient_particles.append({
        "x": random.uniform(0, WIDTH),
        "y": random.uniform(0, GRID_ROWS * TILE_SIZE),
        "size": random.uniform(1.0, 2.5),
        "alpha": random.randint(15, 45),
        "speed_x": random.uniform(-0.12, 0.12),
        "speed_y": random.uniform(-0.08, 0.08),
        "phase": random.uniform(0, math.pi * 2),
    })


def _draw_ambient(screen, frame):
    grid_h = GRID_ROWS * TILE_SIZE
    for p in ambient_particles:
        p["x"] += p["speed_x"] + math.sin(frame * 0.008 + p["phase"]) * 0.12
        p["y"] += p["speed_y"] + math.cos(frame * 0.006 + p["phase"]) * 0.08
        if p["x"] < 0: p["x"] = WIDTH
        if p["x"] > WIDTH: p["x"] = 0
        if p["y"] < 0: p["y"] = grid_h
        if p["y"] > grid_h: p["y"] = 0

        pulse = 0.6 + 0.4 * math.sin(frame * 0.02 + p["phase"])
        a = int(p["alpha"] * pulse)
        sz = max(1, int(p["size"] * pulse))
        # Direct circle draw
        pygame.draw.circle(screen, (*C_ACCENT_GLOW, a), (int(p["x"]), int(p["y"])), sz)


# ═══════════════════════════════════════════════════════
# CONFETTI SYSTEM (200 particles — Victory)
# ═══════════════════════════════════════════════════════
confetti_particles = []

def spawn_confetti():
    confetti_particles.clear()
    for _ in range(200):
        confetti_particles.append({
            "x": random.randint(0, WIDTH),
            "y": random.randint(-HEIGHT, 0),
            "vy": random.uniform(1.5, 4.0),
            "vx": random.uniform(-0.5, 0.5),
            "color": random.choice(C_CONFETTI),
            "size": random.randint(3, 7),
            "rot": random.uniform(0, 360),
            "rot_speed": random.uniform(-4, 4),
        })


def update_and_draw_confetti(screen):
    for p in confetti_particles:
        p["y"] += p["vy"]
        p["x"] += p["vx"]
        p["rot"] += p["rot_speed"]
        if p["y"] > HEIGHT:
            p["y"] = random.randint(-60, -10)
            p["x"] = random.randint(0, WIDTH)
        
        # Draw as a direct polygon instead of a rotated surface
        s = p["size"]
        angle = math.radians(p["rot"])
        points = []
        for a in [angle, angle + math.pi/2, angle + math.pi, angle + 3*math.pi/2]:
            points.append((p["x"] + math.cos(a) * s, p["y"] + math.sin(a) * s))
        pygame.draw.polygon(screen, (*p["color"], 210), points)


# ═══════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════
ELEM_COLORS = {
    "fire": E_FIRE, "water": E_WATER, "leaf": E_LEAF,
    "air": E_AIR, "wind": E_AIR, "null": E_NULL,
}
ELEM_GLOW = {
    "fire": E_FIRE_GLOW, "water": E_WATER_GLOW, "leaf": E_LEAF_GLOW,
    "air": E_AIR_GLOW, "wind": E_AIR_GLOW, "null": E_NULL_GLOW,
}


def _draw_key_badge(surf, text, x, y, size=30):
    """Keyboard key visual"""
    rect = pygame.Rect(x, y, size, size)
    pygame.draw.rect(surf, C_BG_TERTIARY, rect, border_radius=6)
    pygame.draw.rect(surf, C_ACCENT_DARK, rect, 2, border_radius=6)
    t = FONT_MEDIUM.render(text, True, C_TEXT)
    surf.blit(t, (x + (size - t.get_width()) // 2, y + (size - t.get_height()) // 2))


# ═══════════════════════════════════════════════════════
# MAIN UI DRAW
# ═══════════════════════════════════════════════════════
def draw_ui(
    screen,
    grid,
    selected_pos,
    hovered_cell,
    placing_phase=False,
    selected_player_element="fire"
):
    global _bg_surface, _frame_count
    _frame_count += 1
    grid_pixel_h = GRID_ROWS * TILE_SIZE

    # Initialize background if needed
    if _bg_surface is None:
        _bg_surface = pygame.Surface((WIDTH, HEIGHT))
        # Draw premium gradient background
        for y in range(HEIGHT):
            # Gradient from C_BG_GRADIENT_T to C_BG_GRADIENT_B
            t = y / HEIGHT
            r = int(C_BG_GRADIENT_T[0] * (1 - t) + C_BG_GRADIENT_B[0] * t)
            g = int(C_BG_GRADIENT_T[1] * (1 - t) + C_BG_GRADIENT_B[1] * t)
            b = int(C_BG_GRADIENT_T[2] * (1 - t) + C_BG_GRADIENT_B[2] * t)
            pygame.draw.line(_bg_surface, (r, g, b), (0, y), (WIDTH, y))
        
        # Add some subtle grid texture to background
        for x in range(0, WIDTH, TILE_SIZE * 2):
            pygame.draw.line(_bg_surface, (*C_BG_TERTIARY, 15), (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, TILE_SIZE * 2):
            pygame.draw.line(_bg_surface, (*C_BG_TERTIARY, 15), (0, y), (WIDTH, y))

    screen.blit(_bg_surface, (0, 0))

    # Pre-render checker if needed
    global _checker_surface
    if _checker_surface is None:
        _checker_surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(_checker_surface, (255, 255, 255, 4), (0, 0, TILE_SIZE, TILE_SIZE))

    _draw_ambient(screen, _frame_count)

    # ═════════════════════════════════════
    # RANGE CACHING
    # ═════════════════════════════════════
    global _last_selected_pos, _cached_move_range, _cached_atk_range
    if selected_pos != _last_selected_pos:
        _last_selected_pos = selected_pos
        if selected_pos:
            from game_grid import bfs_reachable
            sc, sr = selected_pos
            sel_card = grid.tiles[sc][sr].card
            if sel_card and sel_card.owner == "player":
                _cached_move_range = bfs_reachable((sc, sr), sel_card.move_range, grid, diagonal=False)
                max_atk = max((atk.attack_range for atk in sel_card.attacks), default=0)
                _cached_atk_range = bfs_reachable((sc, sr), max_atk, grid, diagonal=True)
            else:
                _cached_move_range = set()
                _cached_atk_range = set()
        else:
            _cached_move_range = set()
            _cached_atk_range = set()

    # ═════════════════════════════════════
    # GRID TILES
    # ═════════════════════════════════════
    for c in range(GRID_COLS):
        for r in range(GRID_ROWS):
            tx, ty = c * TILE_SIZE, r * TILE_SIZE
            tile_rect = pygame.Rect(tx, ty, TILE_SIZE, TILE_SIZE)

            # Checkerboard
            if (c + r) % 2 == 0:
                screen.blit(_checker_surface, (tx, ty))

            # Grid line
            pygame.draw.rect(screen, C_GRID, tile_rect, 1)

            # Flame tiles
            for ft in flame_tiles:
                if ft[0] == c and ft[1] == r:
                    alpha = int((ft[2] / (FPS * 3)) * 200)
                    # Draw directly to screen instead of creating Surface
                    pad = TILE_SIZE // 6
                    pygame.draw.rect(screen, (*E_FIRE, alpha // 3), (tx, ty, TILE_SIZE, TILE_SIZE), border_radius=4)
                    pygame.draw.rect(screen, (*E_FIRE_GLOW, alpha // 2),
                                     (tx + pad, ty + pad, TILE_SIZE - pad * 2, TILE_SIZE - pad * 2), border_radius=4)
                    for _ in range(2):
                        fx = tx + random.randint(pad, TILE_SIZE - pad)
                        fy = ty + random.randint(pad, TILE_SIZE - pad)
                        pygame.draw.circle(screen, (*E_FIRE_GLOW, alpha), (fx, fy), random.randint(2, 4))

            # Hover
            if (c, r) == hovered_cell and r < GRID_ROWS:
                # Direct draw without Surface creation
                pygame.draw.rect(screen, (*C_ACCENT_GLOW, 55), (tx, ty, TILE_SIZE, TILE_SIZE), 2, border_radius=3)

            # Selection ranges (from cache)
            if (c, r) in _cached_move_range:
                pulse = 40 + int(15 * math.sin(_frame_count * 0.1))
                pygame.draw.rect(screen, (*C_RANGE_MOVE, pulse), (tx+2, ty+2, TILE_SIZE-4, TILE_SIZE-4), border_radius=6)
                pygame.draw.rect(screen, (*C_ACCENT_GLOW, 80), (tx, ty, TILE_SIZE, TILE_SIZE), 2, border_radius=6)
            elif (c, r) in _cached_atk_range:
                pulse_a = 25 + int(10 * math.sin(_frame_count * 0.08 + 1.0))
                pygame.draw.rect(screen, (*C_RANGE_ATK, pulse_a), (tx+4, ty+4, TILE_SIZE-8, TILE_SIZE-8), border_radius=6)
                pygame.draw.rect(screen, (180, 100, 255, 60), (tx+4, ty+4, TILE_SIZE-8, TILE_SIZE-8), 1, border_radius=6)

    # ═════════════════════════════════════
    # CARDS ON GRID
    # ═════════════════════════════════════
    for c in range(grid.cols):
        for r in range(grid.rows):
            card = grid.tiles[c][r].card
            if not card:
                continue

            cx, cy = cell_center(c, r)
            if card.display_hp is None:
                card.display_hp = card.hp
            card.display_hp = card.hp

            elem_c = ELEM_COLORS.get(card.element, E_NULL)
            elem_g = ELEM_GLOW.get(card.element, E_NULL_GLOW)
            owner_c = C_PLAYER if card.owner == "player" else C_ENEMY
            owner_g = C_PLAYER_GLOW if card.owner == "player" else C_ENEMY_GLOW

            body_c = owner_c
            if card.flash_timer > 0:
                body_c = C_WHITE
                card.flash_timer -= 1
            elif card.heal_flash_timer > 0:
                body_c = C_SUCCESS
                card.heal_flash_timer -= 1

            # Selection glow
            if selected_pos == (c, r):
                pa = int(50 + 30 * math.sin(_frame_count * 0.08))
                pygame.draw.circle(screen, (*C_GOLD, pa), (int(cx), int(cy)), TILE_SIZE // 2 + 8, 3)
            # Element ring
            ring_r = TILE_SIZE // 2 - 4
            pygame.draw.circle(screen, (*elem_c, 120), (int(cx), int(cy)), ring_r, 3)
            angle = (_frame_count * 0.02) + (c * 1.3 + r * 0.7)
            dx = int(cx + math.cos(angle) * ring_r)
            dy = int(cy + math.sin(angle) * ring_r)
            pygame.draw.circle(screen, (*elem_g, 220), (dx, dy), 5)

            # Card body
            inner_r = TILE_SIZE // 2 - 10
            # Direct circle draw for better performance & modern flat-glass look
            pygame.draw.circle(screen, (*body_c, 190), (int(cx), int(cy)), inner_r)
            pygame.draw.circle(screen, (255, 255, 255, 40), (int(cx), int(cy)), inner_r, 2) # Inner rim
            pygame.draw.circle(screen, (0, 0, 0, 100), (int(cx), int(cy)), inner_r, 1)    # Outer border

            # Rarity glow
            if card.rarity == "legendary":
                pa = int(120 + 60 * math.sin(_frame_count * 0.06))
                pygame.draw.circle(screen, (*C_GOLD, pa), (int(cx), int(cy)), inner_r + 2, 3)

            # Heal ring
            if card.heal_flash_timer > 0:
                ha = int(150 * (card.heal_flash_timer / 10))
                ha = min(255, max(0, ha))
                pygame.draw.circle(screen, (*C_SUCCESS, ha), (int(cx), int(cy)), TILE_SIZE // 2 - 2, 4)

            # Label
            label = f"P{card.index + 1}" if card.owner == "player" else f"E{card.index + 1}"
            lt = get_cached_text(label, FONT_BIG, C_WHITE)
            screen.blit(lt, (cx - lt.get_width() // 2, cy - lt.get_height() // 2))

            # HP bar
            hp_ratio = max(0, card.display_hp / card.max_hp)
            bar_w, bar_h = TILE_SIZE - 8, 10
            hx = cx - bar_w // 2
            hy = cy - TILE_SIZE // 2 - PADDING_SM - bar_h

            hp_color = C_SUCCESS if hp_ratio > 0.6 else C_WARNING if hp_ratio > 0.3 else C_DEFEAT

            pygame.draw.rect(screen, (*C_SHADOW, 180), (hx - 1, hy - 1, bar_w + 2, bar_h + 2), border_radius=5)
            fill_w = max(0, int(bar_w * hp_ratio))
            if fill_w > 0:
                pygame.draw.rect(screen, hp_color, (hx, hy, fill_w, bar_h), border_radius=4)
            hp_txt = get_cached_text(str(card.hp), FONT_SMALL, C_TEXT)
            screen.blit(hp_txt, (cx - hp_txt.get_width() // 2, hy + bar_h + 2))
            
            # ── Status Badges ──
            status_y = hy - 14
            # 1. Burn
            if card.burn_duration > 0:
                bs = get_cached_text(f"BURN {card.burn_duration}", FONT_MICRO, E_FIRE_GLOW)
                screen.blit(bs, (hx, status_y))
                status_y -= 10
            
            # 2. Stun/Root
            if card.stun_duration > 0:
                ss = get_cached_text(f"STUN {card.stun_duration}", FONT_MICRO, (200, 200, 200))
                screen.blit(ss, (hx, status_y))
                status_y -= 10
            elif card.root_duration > 0:
                rs = get_cached_text(f"ROOT {card.root_duration}", FONT_MICRO, (150, 200, 100))
                screen.blit(rs, (hx, status_y))
                # Visual Root Effect (Vine Ring)
                for i in range(8):
                    angle = _frame_count * 0.05 + i * (math.pi / 4)
                    vx = int(cx + math.cos(angle) * (inner_r + 2))
                    vy = int(cy + math.sin(angle) * (inner_r + 2))
                    pygame.draw.circle(screen, (80, 160, 60, 180), (vx, vy), 3)

    # ═════════════════════════════════════
    # ANIMATIONS
    # ═════════════════════════════════════
    anim_mgr.draw(screen)

    # ═════════════════════════════════════
    # BOTTOM PANEL — Card Details + Controls
    # ═════════════════════════════════════
    panel_y = grid_pixel_h
    panel_h = HEIGHT - panel_y

    # Layout: 38% left — 24% center — 38% right
    left_w = int(WIDTH * 0.38)
    center_w = WIDTH - left_w * 2
    right_x = left_w + center_w

    # Background
    panel = pygame.Surface((WIDTH, panel_h), pygame.SRCALPHA)
    panel.fill((*C_BG_SECONDARY, 245))
    pygame.draw.line(panel, C_ACCENT_DARK, (0, 0), (WIDTH, 0), 2)
    for i in range(6):
        pygame.draw.line(panel, (*C_SHADOW, 14 - i * 2), (0, i + 2), (WIDTH, i + 2))
    screen.blit(panel, (0, panel_y))

    # Column separators
    pygame.draw.line(screen, (*C_ACCENT_DARK, 80), (left_w, panel_y + 8), (left_w, HEIGHT - 8))
    pygame.draw.line(screen, (*C_ACCENT_DARK, 80), (right_x, panel_y + 8), (right_x, HEIGHT - 8))

    base_y = panel_y + 10

    # ── Gather all cards on the grid ──
    player_cards = []
    enemy_cards = []
    for gc in range(grid.cols):
        for gr in range(grid.rows):
            cd = grid.tiles[gc][gr].card
            if cd and cd.owner == "player":
                player_cards.append(cd)
            elif cd and cd.owner == "enemy":
                enemy_cards.append(cd)
    player_cards.sort(key=lambda c: c.index)
    enemy_cards.sort(key=lambda c: c.index)

    # ── Which player card is selected? ──
    sel_card_idx = -1
    if selected_pos:
        sc, sr = selected_pos
        sel_c = grid.tiles[sc][sr].card
        if sel_c and sel_c.owner == "player":
            sel_card_idx = sel_c.index

    # ──────────────────────────────────
    # Helper: Draw one card info block
    # ──────────────────────────────────
    def _draw_card_block(card, bx, by, block_w, block_h, owner_color, owner_glow, atk_keys=None, is_selected=False):
        elem_c = ELEM_COLORS.get(card.element, E_NULL)
        elem_g = ELEM_GLOW.get(card.element, E_NULL_GLOW)

        frame_rect = pygame.Rect(bx, by, block_w, block_h)

        # Selected card highlight
        if is_selected:
            pa = int(35 + 20 * math.sin(_frame_count * 0.07))
            pygame.draw.rect(screen, (*C_GOLD, pa), (bx - 4, by - 4, block_w + 8, block_h + 8), border_radius=RADIUS_SM + 4)

        # Frame bg
        pygame.draw.rect(screen, (*C_BG_TERTIARY, 200), frame_rect, border_radius=RADIUS_SM)

        # Element color stripe at top
        pygame.draw.rect(screen, elem_c, (bx, by, block_w, 3), border_radius=2)

        # ── Row 1: Tag + Name ──
        ny = by + 6
        label = f"P{card.index + 1}" if card.owner == "player" else f"E{card.index + 1}"
        tag = FONT_MAIN.render(label, True, owner_glow)
        screen.blit(tag, (bx + 6, ny))

        # Card name — clip to available width
        name_x = bx + 6 + tag.get_width() + 4
        name_avail = block_w - tag.get_width() - 16
        cname = card.name
        name_s = FONT_SMALL.render(cname, True, C_TEXT)
        while name_s.get_width() > name_avail and len(cname) > 3:
            cname = cname[:-1]
            name_s = FONT_SMALL.render(cname + "…", True, C_TEXT)
        if len(cname) < len(card.name):
            name_s = FONT_SMALL.render(cname + "…", True, C_TEXT)
        screen.blit(name_s, (name_x, ny + 3))

        # ── Row 2: Element badge + HP bar ──
        hp_y = ny + 24
        # Element badge (left)
        elem_str = card.element[:4].upper()
        elem_surf = FONT_MICRO.render(elem_str, True, elem_g)
        eb_rect = pygame.Rect(bx + 6, hp_y, elem_surf.get_width() + 8, 16)
        pygame.draw.rect(screen, (*elem_c, 50), eb_rect, border_radius=4)
        pygame.draw.rect(screen, (*elem_c, 100), eb_rect, 1, border_radius=4)
        screen.blit(elem_surf, (bx + 10, hp_y + 1))

        # HP bar (right of badge)
        hp_ratio = max(0.0, card.hp / card.max_hp) if card.max_hp > 0 else 0
        bar_x = eb_rect.right + 6
        bar_w = block_w - (bar_x - bx) - 50
        bar_h = 10
        hp_color = C_SUCCESS if hp_ratio > 0.6 else C_WARNING if hp_ratio > 0.3 else C_DEFEAT

        pygame.draw.rect(screen, (*C_SHADOW, 140), (bar_x, hp_y + 3, bar_w, bar_h), border_radius=5)
        fill_w = max(0, int(bar_w * hp_ratio))
        if fill_w > 0:
            pygame.draw.rect(screen, hp_color, (bar_x, hp_y + 3, fill_w, bar_h), border_radius=5)

        hp_num = FONT_MICRO.render(f"{card.hp}/{card.max_hp}", True, C_TEXT)
        screen.blit(hp_num, (bx + block_w - hp_num.get_width() - 6, hp_y + 1))

        # ── Divider ──
        div_y = hp_y + 22
        pygame.draw.line(screen, (*C_ACCENT_DARK, 50), (bx + 6, div_y), (bx + block_w - 6, div_y))

        # ── Attacks list ──
        ay = div_y + 6
        for i, atk in enumerate(card.attacks):
            if ay + 22 > by + block_h - 4:
                break
            atk_ec = ELEM_COLORS.get(atk.element, E_NULL)
            atk_eg = ELEM_GLOW.get(atk.element, E_NULL_GLOW)

            # Alternating row bg
            if i % 2 == 0:
                row_bg = pygame.Rect(bx + 4, ay - 1, block_w - 8, 22)
                pygame.draw.rect(screen, (*C_BG_PRIMARY, 50), row_bg, border_radius=3)

            # Key badge or element dot
            if atk_keys and i < len(atk_keys):
                _draw_key_badge(screen, atk_keys[i], bx + 6, ay, 20)
                atk_x = bx + 30
            else:
                pygame.draw.circle(screen, atk_ec, (bx + 14, ay + 9), 4)
                atk_x = bx + 24

            # Attack name — auto-clip
            aname = atk.name
            stat_space = 56  # space for "16 r3"
            name_max_w = block_w - (atk_x - bx) - stat_space
            an = FONT_SMALL.render(aname, True, atk_eg)
            while an.get_width() > name_max_w and len(aname) > 3:
                aname = aname[:-1]
                an = FONT_SMALL.render(aname + "…", True, atk_eg)
            if len(aname) < len(atk.name):
                an = FONT_SMALL.render(aname + "…", True, atk_eg)
            screen.blit(an, (atk_x, ay + 1))

            # Damage + Range + Cooldown (right)
            # Check cooldown status
            if atk.current_cooldown > 0:
                stats = f"WAIT {atk.current_cooldown}"
                dmg_c = (255, 50, 50) # Red for cooldown wait
            else:
                cd_str = f" c{atk.max_cooldown}" if atk.max_cooldown > 0 else ""
                stats = f"{atk.dmg} r{atk.attack_range}{cd_str}"
                dmg_c = C_DEFEAT if atk.dmg >= 14 else C_WARNING if atk.dmg >= 10 else C_TEXT_SEC
            
            st = FONT_SMALL.render(stats, True, dmg_c)
            screen.blit(st, (bx + block_w - st.get_width() - 8, ay + 1))

            ay += 24

        # Frame border
        border_color = C_GOLD if is_selected else (*owner_color, 100)
        bw = 2 if is_selected else 1
        pygame.draw.rect(screen, border_color, frame_rect, bw, border_radius=RADIUS_SM)

    # ──────────────────────────────────
    # LEFT COLUMN: Player Cards
    # ──────────────────────────────────
    lx = PADDING_SM
    section_title = FONT_BIG.render("YOUR UNITS", True, C_PLAYER_GLOW)
    screen.blit(section_title, (lx, base_y))

    card_area_y = base_y + 34
    card_area_h = panel_h - 50
    num_p = max(len(player_cards), 1)
    gap = 8
    avail_w = left_w - PADDING_SM * 2
    pc_block_w = (avail_w - gap * (num_p - 1)) // num_p
    pc_block_w = min(pc_block_w, 230)

    player_atk_keys_map = {0: ["Q", "W", "E"], 1: ["A", "S", "D"], 2: ["Z", "X", "C"]}
    for i, pc in enumerate(player_cards):
        px = lx + i * (pc_block_w + gap)
        _draw_card_block(pc, px, card_area_y, pc_block_w, card_area_h,
                         C_PLAYER, C_PLAYER_GLOW,
                         atk_keys=player_atk_keys_map.get(pc.index),
                         is_selected=(pc.index == sel_card_idx))

    # ──────────────────────────────────
    # CENTER COLUMN: Status + Controls
    # ──────────────────────────────────
    cx = left_w + PADDING_MD
    cw = center_w - PADDING_MD * 2

    # Turn badge
    turn_label = "ENEMY TURN" if anim_mgr.blocking else "YOUR TURN"
    turn_color = C_ENEMY_GLOW if anim_mgr.blocking else C_PLAYER_GLOW
    badge_w = min(220, cw)
    badge_rect = pygame.Rect(cx + (cw - badge_w) // 2, base_y, badge_w, 32)
    pygame.draw.rect(screen, (*turn_color, 30), badge_rect, border_radius=RADIUS_SM)
    pygame.draw.rect(screen, turn_color, badge_rect, 2, border_radius=RADIUS_SM)
    tl = FONT_BIG.render(turn_label, True, turn_color)
    screen.blit(tl, (badge_rect.x + (badge_w - tl.get_width()) // 2, base_y + 2))

    if placing_phase:
        ey = base_y + 46
        screen.blit(FONT_MAIN.render("PLACE YOUR UNITS", True, C_GOLD), (cx, ey))
        ey += 30
        screen.blit(FONT_SMALL.render("Select element, then click grid:", True, C_TEXT_SEC), (cx, ey))
        ey += 28
        elems = [("1  Fire", E_FIRE, "fire"), ("2  Water", E_WATER, "water"),
                 ("3  Leaf", E_LEAF, "leaf"), ("4  Null", E_NULL, "null")]
        for lbl, col, key in elems:
            is_sel = key == selected_player_element
            pill = pygame.Rect(cx, ey, cw, 28)
            if is_sel:
                pygame.draw.rect(screen, (*col, 40), pill, border_radius=6)
                pygame.draw.rect(screen, col, pill, 2, border_radius=6)
                marker = FONT_MAIN.render("▸ " + lbl, True, col)
            else:
                marker = FONT_SMALL.render("  " + lbl, True, C_TEXT_DIM)
            screen.blit(marker, (cx + 8, ey + 3))
            ey += 32
    else:
        # ── Compact key reference ──
        iy = base_y + 46
        screen.blit(FONT_SMALL.render("CONTROLS", True, C_GOLD), (cx, iy))
        iy += 22

        # Key rows — compact
        key_rows = [
            ("P1", C_PLAYER_GLOW, ["Q", "W", "E"]),
            ("P2", C_PLAYER_GLOW, ["A", "S", "D"]),
            ("P3", C_PLAYER_GLOW, ["Z", "X", "C"]),
        ]
        for lbl, lbl_c, keys in key_rows:
            l = FONT_MICRO.render(lbl, True, lbl_c)
            screen.blit(l, (cx, iy + 3))
            kx = cx + 30
            for k in keys:
                _draw_key_badge(screen, k, kx, iy, 22)
                kx += 28
            iy += 28

        # Target keys
        iy += 4
        screen.blit(FONT_MICRO.render("Target", True, C_WARNING), (cx, iy + 3))
        tkx = cx + 50
        for tk in ["1", "2", "3"]:
            _draw_key_badge(screen, tk, tkx, iy, 22)
            tkx += 28
        iy += 28

        # Move + CPU keys
        screen.blit(FONT_MICRO.render("Move", True, C_ACCENT_GLOW), (cx, iy + 3))
        screen.blit(FONT_MICRO.render("Click card → tile", True, C_TEXT_DIM), (cx + 50, iy + 3))
        iy += 22
        screen.blit(FONT_MICRO.render("CPU", True, C_TEXT_SEC), (cx, iy + 3))
        _draw_key_badge(screen, "M", cx + 50, iy, 22)
        iy += 28

        # Help hint
        pygame.draw.line(screen, (*C_ACCENT_DARK, 50), (cx, iy), (cx + cw, iy))
        iy += 6
        screen.blit(FONT_MICRO.render("Press H for help", True, C_TEXT_DIM), (cx, iy))

    # ──────────────────────────────────
    # RIGHT COLUMN: Enemy Cards
    # ──────────────────────────────────
    rx = right_x + PADDING_SM
    section_title_e = FONT_BIG.render("ENEMY UNITS", True, C_ENEMY_GLOW)
    screen.blit(section_title_e, (rx, base_y))

    num_e = max(len(enemy_cards), 1)
    avail_w_r = WIDTH - right_x - PADDING_SM * 2
    ec_block_w = (avail_w_r - gap * (num_e - 1)) // num_e
    ec_block_w = min(ec_block_w, 230)

    for i, ec in enumerate(enemy_cards):
        ex = rx + i * (ec_block_w + gap)
        _draw_card_block(ec, ex, card_area_y, ec_block_w, card_area_h,
                         C_ENEMY, C_ENEMY_GLOW)


# ═══════════════════════════════════════════════════════
# HELP OVERLAY (toggled with H key)
# ═══════════════════════════════════════════════════════
def draw_help_overlay(screen):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    screen.blit(overlay, (0, 0))

    # Panel
    pw, ph = 600, 460
    px = WIDTH // 2 - pw // 2
    py = HEIGHT // 2 - ph // 2
    panel_rect = pygame.Rect(px, py, pw, ph)
    pygame.draw.rect(screen, (*C_BG_SECONDARY, 250), panel_rect, border_radius=RADIUS_LG)
    pygame.draw.rect(screen, C_ACCENT, panel_rect, 2, border_radius=RADIUS_LG)

    # Title
    title = FONT_BIG.render("HOW TO PLAY", True, C_GOLD)
    screen.blit(title, (px + pw // 2 - title.get_width() // 2, py + 16))

    iy = py + 56
    indent = px + 32

    sections = [
        ("MOVEMENT", C_ACCENT_GLOW, [
            "• Click one of your heroes on the grid to select it",
            "• Click an empty tile within move range to move",
            "• Blue tiles show move range, red tiles show attack range",
        ]),
        ("ATTACKING", C_DEFEAT, [
            "• Hold  1 / 2 / 3  to target enemy E1 / E2 / E3",
            "• While holding target key, press attack key:",
            "    P1 attacks: Q  W  E    (3 attacks)",
            "    P2 attacks: A  S  D",
            "    P3 attacks: Z  X  C",
        ]),
        ("HEALING", E_LEAF, [
            "• Leaf cards with 'Nature Heal' restore HP to your unit",
            "• Use the heal attack key while targeting any enemy",
        ]),
        ("OTHER", C_TEXT_SEC, [
            "• Press  M  to trigger CPU turn",
            "• Fire trail tiles damage enemies walking over them",
            "• Each card has an element — check matchups!",
        ]),
    ]

    for sec_title, sec_color, lines in sections:
        st = FONT_MAIN.render(sec_title, True, sec_color)
        screen.blit(st, (indent, iy))
        iy += 24
        for line in lines:
            lt = FONT_SMALL.render(line, True, C_TEXT_SEC)
            screen.blit(lt, (indent, iy))
            iy += 20
        iy += 10

    # Close hint
    close = FONT_SMALL.render("Press  H  to close", True, C_TEXT_DIM)
    screen.blit(close, (px + pw // 2 - close.get_width() // 2, py + ph - 32))
