"""
Stealing Phase — 4K Premium Card Draft System
Each player gets 5 cards, then STEAL or RETAIN until both have 3.
"""

"""
    CPU Stealing Phase — Full Divide & Conquer

    Time Complexity:
    - Action evaluation (STEAL / SWAP / RETAIN): O(n)
    - DAC MAX combination: O(log k), k = number of actions (constant)
    Overall: O(n)

    n = number of cards in player hand
    """

import pygame
import random
import os
import json
import math
from config import WIDTH, HEIGHT, FPS, IS_WEB, PADDING_SM, PADDING_MD, PADDING_LG, PADDING_XL, RADIUS_SM, RADIUS_MD, RADIUS_LG
from card import Card
from attack import Attack
from colors import *
from colors import *
from logic_cpu.dc_steal import select_steal_target, evaluate_card


# ═══════════════════════════════════════
# JSON Card Pool
# ═══════════════════════════════════════
def load_card_data():
    json_path = os.path.join(os.path.dirname(__file__), "cards.json")
    with open(json_path, 'r') as f:
        data = json.load(f)
    return data["cards"]

CARD_POOL = load_card_data()

def get_asset_name(card_data):
    return card_data.get("asset", "1.jpg")

# ═══════════════════════════════════════
# Elemental Colors (PBR-ready)
# ═══════════════════════════════════════
ELEMENT_COLORS = {
    "fire": E_FIRE, "water": E_WATER, "leaf": E_LEAF,
    "wind": E_AIR, "null": E_NULL, "combined": C_GOLD,
}
ELEMENT_GLOW = {
    "fire": E_FIRE_GLOW, "water": E_WATER_GLOW, "leaf": E_LEAF_GLOW,
    "wind": E_AIR_GLOW, "null": E_NULL_GLOW, "combined": C_GOLD_BRIGHT,
}

# ═══════════════════════════════════════
# Card Dimensions (8px grid aligned)
# ═══════════════════════════════════════
CARD_WIDTH = 160 if IS_WEB else 200
CARD_HEIGHT = 220 if IS_WEB else 264
CARD_SPACING = 172 if IS_WEB else 216
CARD_IMAGE_HEIGHT = 112 if IS_WEB else 152


class StealingPhase:
    def __init__(self, screen):
        self.screen = screen
        self.frame = 0

        # Fonts
        self.font_small  = pygame.font.Font(None, 16 if IS_WEB else 18)
        self.font_body   = pygame.font.Font(None, 20 if IS_WEB else 22)
        self.font_medium = pygame.font.Font(None, 22 if IS_WEB else 24)
        self.font_big    = pygame.font.Font(None, 28 if IS_WEB else 34)
        self.font_title  = pygame.font.Font(None, 42 if IS_WEB else 56)

        # Load card images
        self.card_images = {}
        assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        for i, card_data in enumerate(CARD_POOL):
            asset_name = get_asset_name(card_data)
            path = os.path.join(assets_dir, asset_name)
            if os.path.exists(path):
                img = pygame.image.load(path)
                self.card_images[i] = pygame.transform.scale(img, (CARD_WIDTH - 16, CARD_IMAGE_HEIGHT))

        # Background particle cache
        self._bg_hex = []
        for _ in range(40):
            self._bg_hex.append({
                "x": random.uniform(0, WIDTH),
                "y": random.uniform(0, HEIGHT),
                "phase": random.uniform(0, math.pi * 2),
                "size": random.uniform(1, 2.5),
            })

        self.reset()

    def reset(self):
        shuffled = random.sample(range(len(CARD_POOL)), min(10, len(CARD_POOL)))
        self.player_hand = shuffled[:5]
        self.cpu_hand = shuffled[5:10]
        self.player_deck = []
        self.cpu_deck = []
        self.current_turn = "player"
        self.phase_complete = False
        self.selected_card = None
        self.hovered_card = None
        self.action_message = "Your turn: Click YOUR card to RETAIN or OPPONENT's card to STEAL"
        self.cpu_rects = []
        self.player_rects = []

    def get_card_data(self, idx):
        return CARD_POOL[idx]

    # ═══════════════════════════════════════
    # CARD RENDERING (Premium Design)
    # ═══════════════════════════════════════
    def draw_card(self, idx, x, y, selected=False, owner="player", hovered=False):
        data = self.get_card_data(idx)
        elem = data["element"]
        elem_color = ELEMENT_COLORS.get(elem, E_NULL)
        elem_glow = ELEMENT_GLOW.get(elem, E_NULL_GLOW)

        card_rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)

        # ── Glow effect for hovered/selected ──
        if selected:
            glow = pygame.Surface((CARD_WIDTH + 24, CARD_HEIGHT + 24), pygame.SRCALPHA)
            for i in range(12, 0, -2):
                a = int(60 * (i / 12))
                pygame.draw.rect(glow, (*C_GOLD, a),
                    (12 - i, 12 - i, CARD_WIDTH + i * 2, CARD_HEIGHT + i * 2), border_radius=RADIUS_MD + i)
            self.screen.blit(glow, (x - 12, y - 12))
        elif hovered:
            glow = pygame.Surface((CARD_WIDTH + 16, CARD_HEIGHT + 16), pygame.SRCALPHA)
            for i in range(8, 0, -2):
                a = int(40 * (i / 8))
                pygame.draw.rect(glow, (*C_ACCENT_GLOW, a),
                    (8 - i, 8 - i, CARD_WIDTH + i * 2, CARD_HEIGHT + i * 2), border_radius=RADIUS_MD + i)
            self.screen.blit(glow, (x - 8, y - 8))

        # ── Card body ──
        card_surf = pygame.Surface((CARD_WIDTH, CARD_HEIGHT), pygame.SRCALPHA)

        # Gradient background
        for row in range(CARD_HEIGHT):
            t = row / CARD_HEIGHT
            # Top: element primary → Bottom: darker
            r = int(elem_color[0] * (1 - t * 0.6) + C_BG_SECONDARY[0] * t * 0.6)
            g = int(elem_color[1] * (1 - t * 0.6) + C_BG_SECONDARY[1] * t * 0.6)
            b = int(elem_color[2] * (1 - t * 0.6) + C_BG_SECONDARY[2] * t * 0.6)
            pygame.draw.line(card_surf, (r, g, b, 230), (0, row), (CARD_WIDTH, row))
        pygame.draw.rect(card_surf, (0, 0, 0, 0), (0, 0, CARD_WIDTH, CARD_HEIGHT), border_radius=RADIUS_MD)

        # Clip to rounded rect (fill then overlay)
        mask = pygame.Surface((CARD_WIDTH, CARD_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, CARD_WIDTH, CARD_HEIGHT), border_radius=RADIUS_MD)
        card_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        self.screen.blit(card_surf, (x, y))

        # ── Border ──
        if selected:
            pygame.draw.rect(self.screen, C_GOLD_BRIGHT, card_rect, 4, border_radius=RADIUS_MD)
        elif hovered:
            pygame.draw.rect(self.screen, C_ACCENT_GLOW, card_rect, 3, border_radius=RADIUS_MD)
        else:
            pygame.draw.rect(self.screen, (*C_ACCENT_DARK, ), card_rect, 2, border_radius=RADIUS_MD)

        # ── Card image ──
        if idx in self.card_images:
            img_x = x + 8
            img_y = y + 8
            self.screen.blit(self.card_images[idx], (img_x, img_y))
            pygame.draw.rect(self.screen, (*C_BG_PRIMARY, ), (img_x, img_y, CARD_WIDTH - 16, CARD_IMAGE_HEIGHT), 2, border_radius=RADIUS_SM)

        # ── Card name ──
        name = data["name"]
        name_surf = self.font_medium.render(name, True, C_TEXT)
        while name_surf.get_width() > CARD_WIDTH - 16 and len(name) > 4:
            name = name[:-1]
            name_surf = self.font_medium.render(name + "…", True, C_TEXT)
        if len(name) < len(data["name"]):
            name_surf = self.font_medium.render(name + "…", True, C_TEXT)
        nx = x + (CARD_WIDTH - name_surf.get_width()) // 2
        self.screen.blit(name_surf, (nx, y + CARD_IMAGE_HEIGHT + 10))

        # ── Stats row ──
        hp_text = f"HP:{data['hp']}"
        spd_text = f"SPD:{data.get('speed', '?')}"
        stats_surf = self.font_small.render(f"{hp_text}  {spd_text}  MV:{data.get('move', 3)}", True, C_TEXT_SEC)
        sx = x + (CARD_WIDTH - stats_surf.get_width()) // 2
        self.screen.blit(stats_surf, (sx, y + CARD_IMAGE_HEIGHT + 32))

        # ── Element badge at bottom ──
        elem_text = elem.upper()
        sec = data.get("secondary")
        if sec and sec != elem:
            elem_text += f"/{sec.upper()}"
        badge_surf = self.font_small.render(elem_text, True, elem_glow)
        bx = x + (CARD_WIDTH - badge_surf.get_width()) // 2
        by = y + CARD_HEIGHT - 24
        # Badge background
        badge_bg = pygame.Rect(bx - 8, by - 3, badge_surf.get_width() + 16, 22)
        pygame.draw.rect(self.screen, (*elem_color, 50), badge_bg, border_radius=4)
        pygame.draw.rect(self.screen, (*elem_color, 100), badge_bg, 1, border_radius=4)
        self.screen.blit(badge_surf, (bx, by))

        return card_rect

    # ═══════════════════════════════════════
    # ATTACK DETAILS TOOLTIP
    # ═══════════════════════════════════════
    # ═══════════════════════════════════════
    # ATTACK DETAILS TOOLTIP
    # ═══════════════════════════════════════
    def draw_card_details(self, idx, x, y):
        data = self.get_card_data(idx)
        panel_w, panel_h = 440, 360  # Increased height

        # Clamp to screen
        if x + panel_w > WIDTH: x = WIDTH - panel_w - 10
        if y + panel_h > HEIGHT: y = HEIGHT - panel_h - 10
        if x < 10: x = 10
        if y < 10: y = 10

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel, (*C_BG_SECONDARY, 245), (0, 0, panel_w, panel_h), border_radius=RADIUS_MD)
        pygame.draw.rect(panel, C_ACCENT_DARK, (0, 0, panel_w, panel_h), 2, border_radius=RADIUS_MD)
        self.screen.blit(panel, (x, y))

        title = self.font_medium.render(f"{data['name']} — Attacks", True, C_GOLD)
        self.screen.blit(title, (x + PADDING_MD, y + PADDING_SM))

        # Divider
        pygame.draw.line(self.screen, C_ACCENT_DARK, (x + PADDING_MD, y + 42), (x + panel_w - PADDING_MD, y + 42))

        ay = y + 54
        for i, atk in enumerate(data.get("attacks", [])):
            ec = ELEMENT_COLORS.get(atk["element"], C_TEXT_SEC)
            eg = ELEMENT_GLOW.get(atk["element"], C_TEXT_SEC)

            # Dot indicator
            pygame.draw.circle(self.screen, ec, (x + PADDING_MD + 6, ay + 10), 5)
            # Name
            an = self.font_body.render(f"{atk['name']}", True, eg)
            self.screen.blit(an, (x + PADDING_MD + 18, ay))
            
            # Stats + Cooldown
            cd_text = f"CD:{atk.get('cooldown', 0)}"
            if atk.get('cooldown', 0) == 0:
                cd_text = "Instant"
                
            stats = f"DMG: {atk['damage']}   RNG: {atk['range']}   {cd_text}"
            st = self.font_small.render(stats, True, C_TEXT_SEC)
            self.screen.blit(st, (x + PADDING_MD + 18, ay + 20))
            
            # Description
            desc = atk.get("description", "")
            if atk.get("is_healing", False):
                desc += f" (Heal {atk.get('heal_amount', 0)})"
            elif atk.get("is_life_drain", False):
                desc += f" (Drain {atk.get('heal_amount', 0)})"
                
            d_surf = self.font_small.render(desc, True, (180, 180, 180)) # Dimmer text
            self.screen.blit(d_surf, (x + PADDING_MD + 18, ay + 38))

            ay += 68 # Increased spacing

    # ═══════════════════════════════════════
    # MAIN DRAW
    # ═══════════════════════════════════════
    def draw(self):
        self.frame += 1

        # ── Background ──
        self.screen.fill(C_BG_PRIMARY)
        # Floating dots
        for p in self._bg_hex:
            pulse = 0.5 + 0.5 * math.sin(self.frame * 0.015 + p["phase"])
            a = int(25 * pulse)
            sz = max(1, int(p["size"] * pulse))
            pygame.draw.circle(self.screen, (*C_ACCENT_DARK, a),
                               (int(p["x"]), int(p["y"])), sz)

        # ── Title ──
        title_text = "STEALING PHASE"
        # Shadow
        sh = self.font_title.render(title_text, True, C_SHADOW)
        self.screen.blit(sh, (WIDTH // 2 - sh.get_width() // 2 + 3, 23))
        # Main
        title = self.font_title.render(title_text, True, C_GOLD_BRIGHT)
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 20))

        # ── Progress dots ──
        dots_y = 82
        total_dots = 6
        dot_spacing = 20
        dots_start = WIDTH // 2 - (total_dots * dot_spacing) // 2
        for i in range(3):
            filled = i < len(self.player_deck)
            color = C_PLAYER if filled else C_TEXT_DIM
            pygame.draw.circle(self.screen, color, (dots_start + i * dot_spacing + 10, dots_y), 7)
        for i in range(3):
            filled = i < len(self.cpu_deck)
            color = C_ENEMY if filled else C_TEXT_DIM
            pygame.draw.circle(self.screen, color, (dots_start + (3 + i) * dot_spacing + 30, dots_y), 7)

        # ── Turn indicator ──
        turn_text = "YOUR TURN" if self.current_turn == "player" else "CPU THINKING..."
        turn_color = C_PLAYER_GLOW if self.current_turn == "player" else C_ENEMY_GLOW
        # Pill background
        ts = self.font_big.render(turn_text, True, turn_color)
        pill_w = ts.get_width() + PADDING_XL
        pill_h = 44
        pill_x = WIDTH // 2 - pill_w // 2
        pill_y = 100
        pill_rect = pygame.Rect(pill_x, pill_y, pill_w, pill_h)
        pygame.draw.rect(self.screen, (*turn_color, 20), pill_rect, border_radius=RADIUS_LG)
        pygame.draw.rect(self.screen, (*turn_color, 80), pill_rect, 2, border_radius=RADIUS_LG)
        self.screen.blit(ts, (WIDTH // 2 - ts.get_width() // 2, pill_y + 6))

        # ── Action message ──
        msg = self.font_body.render(self.action_message, True, C_TEXT_SEC)
        self.screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, 156))

        # ── CPU Hand (top) ──
        cpu_label = self.font_body.render(f"CPU Hand  ({len(self.cpu_hand)} cards)", True, C_ENEMY_GLOW)
        cpu_hand_w = len(self.cpu_hand) * CARD_SPACING
        cpu_sx = (WIDTH - cpu_hand_w) // 2 + 8
        self.screen.blit(cpu_label, (cpu_sx, 170))

        self.cpu_rects = []
        for i, card_idx in enumerate(self.cpu_hand):
            cx = cpu_sx + i * CARD_SPACING
            is_sel = self.selected_card == ("cpu", i)
            is_hov = self.hovered_card == ("cpu", i)
            rect = self.draw_card(card_idx, cx, 192, selected=is_sel, owner="cpu", hovered=is_hov)
            self.cpu_rects.append(rect)

        # ── Player Hand (bottom) ──
        player_y = HEIGHT - CARD_HEIGHT - 60
        player_label = self.font_body.render(f"Your Hand  ({len(self.player_hand)} cards)", True, C_PLAYER_GLOW)
        player_hand_w = len(self.player_hand) * CARD_SPACING
        player_sx = (WIDTH - player_hand_w) // 2 + 8
        self.screen.blit(player_label, (player_sx, player_y - 22))

        self.player_rects = []
        for i, card_idx in enumerate(self.player_hand):
            cx = player_sx + i * CARD_SPACING
            is_sel = self.selected_card == ("player", i)
            is_hov = self.hovered_card == ("player", i)
            rect = self.draw_card(card_idx, cx, player_y, selected=is_sel, owner="player", hovered=is_hov)
            self.player_rects.append(rect)

        # ── Hover tooltip ──
        if self.hovered_card:
            owner, idx = self.hovered_card
            if owner == "cpu" and idx < len(self.cpu_hand):
                self.draw_card_details(self.cpu_hand[idx], WIDTH - 460, 200)
            elif owner == "player" and idx < len(self.player_hand):
                self.draw_card_details(self.player_hand[idx], WIDTH - 460, player_y - 150)

        # ── Bottom instructions / completion ──
        if self.phase_complete:
            # Completion banner
            banner_text = "Phase Complete!  Press SPACE to begin battle"
            bt = self.font_big.render(banner_text, True, C_GOLD_BRIGHT)
            bw = bt.get_width() + PADDING_XL * 2
            bh = 56
            bx = WIDTH // 2 - bw // 2
            by = HEIGHT - 60
            br = pygame.Rect(bx, by, bw, bh)
            pygame.draw.rect(self.screen, (*C_BG_TERTIARY, 230), br, border_radius=RADIUS_MD)
            pygame.draw.rect(self.screen, C_GOLD, br, 3, border_radius=RADIUS_MD)
            self.screen.blit(bt, (WIDTH // 2 - bt.get_width() // 2, by + 10))
        else:
            inst = "Click YOUR card to RETAIN  |  Click CPU's card to STEAL"
            it = self.font_small.render(inst, True, C_TEXT_DIM)
            self.screen.blit(it, (WIDTH // 2 - it.get_width() // 2, HEIGHT - 35))

    # ═══════════════════════════════════════
    # INPUT HANDLERS
    # ═══════════════════════════════════════
    def handle_mouse_move(self, pos):
        self.hovered_card = None
        for i, rect in enumerate(self.cpu_rects):
            if rect.collidepoint(pos):
                self.hovered_card = ("cpu", i)
                return
        for i, rect in enumerate(self.player_rects):
            if rect.collidepoint(pos):
                self.hovered_card = ("player", i)
                return

    def handle_click(self, pos):
        if self.current_turn != "player" or self.phase_complete:
            return
        for i, rect in enumerate(self.player_rects):
            if rect.collidepoint(pos):
                self.retain_card("player", i)
                return
        for i, rect in enumerate(self.cpu_rects):
            if rect.collidepoint(pos):
                self.steal_card(i)
                return

    # ═══════════════════════════════════════
    # GAME LOGIC
    # ═══════════════════════════════════════
    def retain_card(self, owner, idx):
        if owner == "player" and len(self.player_deck) < 3:
            card_idx = self.player_hand.pop(idx)
            self.player_deck.append(card_idx)
            self.action_message = f"Retained {CARD_POOL[card_idx]['name']}!"
            print(f"[Steal] Player Retained {CARD_POOL[card_idx]['name']}")
            self.end_turn()

    def steal_card(self, idx):
        if len(self.player_deck) < 3 and idx < len(self.cpu_hand):
            card_idx = self.cpu_hand.pop(idx)
            self.player_deck.append(card_idx)
            self.action_message = f"Stole {CARD_POOL[card_idx]['name']}!"
            print(f"[Steal] Player Stole {CARD_POOL[card_idx]['name']}")
            self.end_turn()

    def end_turn(self):
        self.check_phase_complete()
        if not self.phase_complete:
            self.current_turn = "cpu" if self.current_turn == "player" else "player"
            if self.current_turn == "cpu":
                pygame.time.set_timer(pygame.USEREVENT + 1, 1000)

    def _card_score(self, card_idx):
        return evaluate_card(CARD_POOL[card_idx])



    def cpu_turn(self):
         

        # ==================================================
        # STEP 1 & 2: DIVIDE & CONQUER — Synergy-Based Action Selection
        # ==================================================
        best_phase_action = None
        try:
            from logic_cpu.backtracking_deck_subset import find_best_phase_action
            # find_best_phase_action returns (action_type, card_idx, score)
            best_phase_action = find_best_phase_action(
                self.cpu_deck, self.cpu_hand, self.player_hand, CARD_POOL
            )
        except Exception as e:
            print(f"[Backtracking] Error: {e}")

        # ---------- Final Action Decision ----------
        actions = []
        
        # 1. Synergy-based Action (Primary choice from 10C3 evaluation)
        if best_phase_action:
            action_type, card_idx, score = best_phase_action
            # Synergy score is usually ~100-300. We add a base to ensure it's picked.
            actions.append((action_type, 500 + score, card_idx))

        # 2. Individual SWAP (for when deck is full but we can improve it)
        if self.player_hand and len(self.cpu_deck) >= 3:
            best_player = max(self.player_hand, key=lambda c: self._card_score(c))
            worst_cpu = min(self.cpu_deck, key=lambda c: self._card_score(c))
            gain = self._card_score(best_player) - self._card_score(worst_cpu)
            if gain > 0:
                actions.append(("SWAP", 600 + gain, (best_player, worst_cpu)))

        # 3. Fallback (if no synergy action found)
        if not actions:
            if self.cpu_hand:
                best_retain = max(self.cpu_hand, key=lambda c: self._card_score(c))
                actions.append(("RETAIN", self._card_score(best_retain), best_retain))
            if self.player_hand and len(self.cpu_deck) < 3:
                best_steal = select_steal_target(self.player_hand, CARD_POOL, self.cpu_hand)
                if best_steal is not None:
                    actions.append(("STEAL", self._card_score(best_steal), best_steal))

        if not actions:
            self.end_turn()
            return

        def dac_max(arr):
            if len(arr) == 1:
                return arr[0]
            mid = len(arr) // 2
            left = dac_max(arr[:mid])
            right = dac_max(arr[mid:])
            return left if left[1] >= right[1] else right

        best_action, best_score, payload = dac_max(actions)

        # ==================================================
        # STEP 4: EXECUTE RESULT
        # ==================================================
        if best_action == "STEAL" and payload is not None:
            # Ensure payload is a valid index before removal
            if payload in self.player_hand:
                self.player_hand.remove(payload)
                self.cpu_deck.append(payload)
                self.action_message = f"CPU stole {CARD_POOL[payload]['name']} (DAC)"
                print("[DAC] Action = STEAL")
            else:
                print(f"[DAC] Warning: Attempted to steal card {payload} not found in player_hand.")


        elif best_action == "SWAP" and payload[0] is not None:
            steal_card, drop_card = payload
            # Ensure cards are present before attempting to remove/add
            if steal_card in self.player_hand and drop_card in self.cpu_deck:
                self.player_hand.remove(steal_card)
                self.cpu_deck.remove(drop_card)
                self.cpu_deck.append(steal_card)
                self.action_message = (
                    f"CPU swapped {CARD_POOL[drop_card]['name']} "
                    f"for {CARD_POOL[steal_card]['name']} (DAC)"
                )
                print("[DAC] Action = SWAP")
            else:
                print(f"[DAC] Warning: Attempted to swap cards not found. Steal: {steal_card in self.player_hand}, Drop: {drop_card in self.cpu_deck}")


        elif best_action == "RETAIN" and payload is not None:
            # Ensure payload is a valid index before removal
            if payload in self.cpu_hand:
                self.cpu_hand.remove(payload)
                self.cpu_deck.append(payload)
                self.action_message = f"CPU retained {CARD_POOL[payload]['name']} (DAC)"
                print("[DAC] Action = RETAIN")
            else:
                print(f"[DAC] Warning: Attempted to retain card {payload} not found in cpu_hand.")

        self.end_turn()


    def check_phase_complete(self):
        if len(self.player_deck) >= 3 and len(self.cpu_deck) >= 3:
            self.phase_complete = True
            self.action_message = "Stealing Phase Complete! Press SPACE to begin battle!"

    def create_card_from_pool(self, idx, owner, slot):
        data = CARD_POOL[idx]
        attacks = []
        for a in data.get("attacks", []):
            atk = Attack(
                name=a["name"],
                dmg=a["damage"],
                element=a["element"],
                attack_range=a.get("range", 3),
                animation=a.get("animation", "projectile_fire"),
                max_cooldown=a.get("cooldown", 0),
                is_healing=a.get("is_healing", False),
                heal_amount=a.get("heal_amount", 0)
            )
            atk.is_life_drain = a.get("is_life_drain", False)
            attacks.append(atk)
            
        card = Card(
            owner=owner, name=data["name"], hp=data["hp"], max_hp=data["hp"],
            attacks=attacks, move_range=data.get("move", 3),
            element=data["element"], index=slot
        )
        card.display_hp = card.hp
        return card

    def get_final_decks(self):
        player_cards = [self.create_card_from_pool(idx, "player", i) for i, idx in enumerate(self.player_deck)]
        cpu_cards = [self.create_card_from_pool(idx, "enemy", i) for i, idx in enumerate(self.cpu_deck)]
        return player_cards, cpu_cards
